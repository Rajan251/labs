import redis
import json
from .config import Config

class QueueManager:
    def __init__(self):
        self.redis_client = None

    def connect(self):
        # In a real app, we might use a connection pool
        self.redis_client = redis.Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, db=0)

    def publish_message(self, queue_name, message: dict):
        if not self.redis_client:
            self.connect()
            
        # Push to the tail of the list
        self.redis_client.rpush(queue_name, json.dumps(message))

    def close(self):
        if self.redis_client:
            self.redis_client.close()

queue_manager = QueueManager()
