"""
Redis-based rate limiter using token bucket algorithm.

Implements per-tenant rate limiting to prevent abuse and ensure fair usage.
"""
import redis
import time
from typing import Optional

from app.config import settings


class RateLimiter:
    """Token bucket rate limiter using Redis."""
    
    def __init__(self):
        """Initialize Redis connection."""
        self.redis_client = redis.from_url(
            settings.redis_url,
            max_connections=settings.redis_max_connections,
            decode_responses=True
        )
    
    def _get_key(self, tenant_id: int) -> str:
        """Generate Redis key for tenant rate limit."""
        return f"rate_limit:tenant:{tenant_id}"
    
    def check_rate_limit(
        self,
        tenant_id: int,
        rate_limit: Optional[int] = None,
        window: Optional[int] = None
    ) -> tuple[bool, dict]:
        """
        Check if request is within rate limit using token bucket algorithm.
        
        Args:
            tenant_id: Tenant ID
            rate_limit: Maximum requests per window (default from settings)
            window: Time window in seconds (default from settings)
            
        Returns:
            Tuple of (allowed: bool, info: dict)
            - allowed: True if request is allowed, False if rate limited
            - info: Dictionary with rate limit information
        
        Algorithm:
            Token bucket with refill rate. Each request consumes one token.
            Tokens refill at a constant rate up to the bucket capacity.
        """
        if rate_limit is None:
            rate_limit = settings.rate_limit_per_tenant
        
        if window is None:
            window = settings.rate_limit_window
        
        key = self._get_key(tenant_id)
        current_time = time.time()
        
        # Use Redis pipeline for atomic operations
        pipe = self.redis_client.pipeline()
        
        try:
            # Get current bucket state
            bucket_data = self.redis_client.hgetall(key)
            
            if not bucket_data:
                # Initialize new bucket
                tokens = rate_limit - 1  # Consume one token for this request
                last_refill = current_time
                
                pipe.hset(key, mapping={
                    "tokens": tokens,
                    "last_refill": last_refill
                })
                pipe.expire(key, window * 2)  # Set expiry to 2x window
                pipe.execute()
                
                return True, {
                    "allowed": True,
                    "limit": rate_limit,
                    "remaining": tokens,
                    "reset_at": int(current_time + window)
                }
            
            # Calculate token refill
            tokens = float(bucket_data.get("tokens", 0))
            last_refill = float(bucket_data.get("last_refill", current_time))
            
            # Calculate tokens to add based on time elapsed
            time_elapsed = current_time - last_refill
            refill_rate = rate_limit / window  # Tokens per second
            tokens_to_add = time_elapsed * refill_rate
            
            # Refill tokens (capped at rate_limit)
            tokens = min(rate_limit, tokens + tokens_to_add)
            
            # Check if we have tokens available
            if tokens >= 1:
                # Consume one token
                tokens -= 1
                
                pipe.hset(key, mapping={
                    "tokens": tokens,
                    "last_refill": current_time
                })
                pipe.expire(key, window * 2)
                pipe.execute()
                
                return True, {
                    "allowed": True,
                    "limit": rate_limit,
                    "remaining": int(tokens),
                    "reset_at": int(current_time + (window - (tokens / refill_rate)))
                }
            else:
                # Rate limit exceeded
                retry_after = int((1 - tokens) / refill_rate)
                
                return False, {
                    "allowed": False,
                    "limit": rate_limit,
                    "remaining": 0,
                    "reset_at": int(current_time + retry_after),
                    "retry_after": retry_after
                }
        
        except redis.RedisError as e:
            # On Redis error, allow request (fail open)
            print(f"Rate limiter Redis error: {e}")
            return True, {
                "allowed": True,
                "limit": rate_limit,
                "remaining": rate_limit,
                "error": "rate_limiter_unavailable"
            }
    
    def reset_rate_limit(self, tenant_id: int) -> bool:
        """
        Reset rate limit for a tenant.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            True if reset successful
        """
        key = self._get_key(tenant_id)
        try:
            self.redis_client.delete(key)
            return True
        except redis.RedisError:
            return False
    
    def get_rate_limit_info(self, tenant_id: int) -> dict:
        """
        Get current rate limit information for a tenant.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Dictionary with rate limit information
        """
        key = self._get_key(tenant_id)
        
        try:
            bucket_data = self.redis_client.hgetall(key)
            
            if not bucket_data:
                return {
                    "tokens": settings.rate_limit_per_tenant,
                    "limit": settings.rate_limit_per_tenant
                }
            
            return {
                "tokens": int(float(bucket_data.get("tokens", 0))),
                "limit": settings.rate_limit_per_tenant,
                "last_refill": float(bucket_data.get("last_refill", 0))
            }
        
        except redis.RedisError:
            return {
                "tokens": settings.rate_limit_per_tenant,
                "limit": settings.rate_limit_per_tenant,
                "error": "rate_limiter_unavailable"
            }


# Global rate limiter instance
rate_limiter = RateLimiter()
