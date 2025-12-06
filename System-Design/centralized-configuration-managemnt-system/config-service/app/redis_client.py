"""
Redis client for caching and pub/sub functionality.
Provides connection pooling and helper methods.
"""
from typing import Optional, Any
import json
import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool
import structlog

from .config import settings

logger = structlog.get_logger(__name__)


class RedisClient:
    """Async Redis client with caching and pub/sub support."""
    
    def __init__(self):
        self.pool: Optional[ConnectionPool] = None
        self.client: Optional[redis.Redis] = None
    
    async def connect(self) -> None:
        """Initialize Redis connection pool."""
        self.pool = ConnectionPool.from_url(
            settings.redis_url,
            max_connections=settings.redis_max_connections,
            decode_responses=True,
        )
        self.client = redis.Redis(connection_pool=self.pool)
        logger.info("redis_connected", url=settings.redis_url)
    
    async def disconnect(self) -> None:
        """Close Redis connections."""
        if self.client:
            await self.client.close()
        if self.pool:
            await self.pool.disconnect()
        logger.info("redis_disconnected")
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        if not self.client:
            return None
        
        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error("redis_get_error", key=key, error=str(e))
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache with optional TTL.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (default: from settings)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False
        
        try:
            ttl = ttl or settings.redis_cache_ttl
            serialized = json.dumps(value)
            await self.client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error("redis_set_error", key=key, error=str(e))
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False
        
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error("redis_delete_error", key=key, error=str(e))
            return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching pattern.
        
        Args:
            pattern: Key pattern (e.g., "config:app123:*")
            
        Returns:
            Number of keys deleted
        """
        if not self.client:
            return 0
        
        try:
            keys = []
            async for key in self.client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                deleted = await self.client.delete(*keys)
                logger.info("cache_invalidated", pattern=pattern, count=deleted)
                return deleted
            return 0
        except Exception as e:
            logger.error("redis_invalidate_error", pattern=pattern, error=str(e))
            return 0
    
    async def publish(self, channel: str, message: dict) -> bool:
        """
        Publish message to channel.
        
        Args:
            channel: Channel name
            message: Message to publish (will be JSON serialized)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False
        
        try:
            serialized = json.dumps(message)
            await self.client.publish(channel, serialized)
            return True
        except Exception as e:
            logger.error("redis_publish_error", channel=channel, error=str(e))
            return False


# Global Redis client instance
redis_client = RedisClient()
