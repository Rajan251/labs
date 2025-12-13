from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.tweet import Tweet
from app.schemas import schemas
from app.services.timeline import fanout_tweet

router = APIRouter(prefix="/tweets", tags=["tweets"])

@router.post("/", response_model=schemas.Tweet)
def create_tweet(tweet: schemas.TweetCreate, user_id: int, db: Session = Depends(get_db)):
    # Simplified: passing user_id explicitly
    db_tweet = Tweet(**tweet.dict(), user_id=user_id)
    db.add(db_tweet)
    db.commit()
    db.refresh(db_tweet)
    
    # Trigger Fan-out
    fanout_tweet.delay(db_tweet.id, user_id)
    
    return db_tweet
