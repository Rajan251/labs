from fastapi import Depends, Request
from .locks import AsyncRedisLock, Redlock
import os
import redis.asyncio as redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

async def get_redis():
    client = redis.from_url(REDIS_URL, decode_responses=True)
    try:
        yield client
    finally:
        await client.close()

class LockManager:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    def get_lock(self, resource: str, ttl: int = 5):
        # Return our Redlock implementation
        return Redlock(self.redis, resource, ttl_ms=ttl*1000)

async def get_lock_manager(redis_client: redis.Redis = Depends(get_redis)) -> LockManager:
    return LockManager(redis_client)
