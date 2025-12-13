from app.database import SessionLocal
from app.models.follow import Follow
from app.models.user import User
from app.models.tweet import Tweet
import redis
from celery import Celery
from app.config import settings

# Redis Connection
r = redis.Redis.from_url(settings.REDIS_URL)

# Celery App
celery_app = Celery("worker", broker=settings.RABBITMQ_URL)

@celery_app.task
def fanout_tweet(tweet_id: int, user_id: int):
    """
    Fan-out on Write: Push tweet ID to all followers' timelines.
    Skip for celebrities (Fan-out on Read).
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user.is_celebrity:
            return # Celebrity tweets are pulled, not pushed

        followers = db.query(Follow).filter(Follow.followee_id == user_id).all()
        for follow in followers:
            # Push to Redis List (Timeline)
            r.lpush(f"timeline:{follow.follower_id}", tweet_id)
            r.ltrim(f"timeline:{follow.follower_id}", 0, 99) # Keep last 100 tweets
    finally:
        db.close()

def get_home_timeline(user_id: int, db):
    """
    Hybrid Strategy:
    1. Fetch pushed tweets from Redis.
    2. Fetch tweets from followed celebrities (Pull).
    3. Merge and sort.
    """
    # 1. Get from Redis
    tweet_ids = [int(id) for id in r.lrange(f"timeline:{user_id}", 0, 99)]
    
    # 2. Get followed celebrities
    celebrity_follows = db.query(Follow).join(User, Follow.followee_id == User.id)\
        .filter(Follow.follower_id == user_id, User.is_celebrity == True).all()
    
    celebrity_ids = [f.followee_id for f in celebrity_follows]
    
    # 3. Fetch actual tweets (Optimization: Could use MGET or cache tweets)
    # Fetch normal tweets
    normal_tweets = db.query(Tweet).filter(Tweet.id.in_(tweet_ids)).all()
    
    # Fetch celebrity tweets (Pull) - Simplified: last 10
    celebrity_tweets = []
    if celebrity_ids:
        celebrity_tweets = db.query(Tweet).filter(Tweet.user_id.in_(celebrity_ids))\
            .order_by(Tweet.created_at.desc()).limit(10).all()
            
    # Merge
    all_tweets = normal_tweets + celebrity_tweets
    all_tweets.sort(key=lambda x: x.created_at, reverse=True)
    
    return all_tweets
