import asyncio
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from contextlib import asynccontextmanager
import time
import logging

logger = logging.getLogger(__name__)

import asyncio
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from contextlib import asynccontextmanager
import time
import logging
import uuid

logger = logging.getLogger(__name__)

class Redlock:
    """
    Distributed Lock using Redis (Redlock algorithm simplified for single instance).
    Includes:
    - Random value (token) for safe release.
    - Lua scripts for atomicity.
    - Context manager support.
    """
    def __init__(self, redis_client: redis.Redis, resource: str, ttl_ms: int = 5000):
        self.redis = redis_client
        self.resource = f"lock:{resource}"
        self.ttl_ms = ttl_ms
        self.token = str(uuid.uuid4())
        
    async def __aenter__(self):
        acquired = await self.acquire()
        if not acquired:
            raise Exception(f"Could not acquire lock for {self.resource}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.release()

    async def acquire(self) -> bool:
        # SET resource token NX PX ttl_ms
        # Returns True if set, False if not
        return await self.redis.set(self.resource, self.token, nx=True, px=self.ttl_ms)

    async def release(self):
        # Lua script to check token matches before deleting
        script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        await self.redis.eval(script, 1, self.resource, self.token)

# Retaining DB Advisory Lock as is
@asynccontextmanager
async def postgres_advisory_lock(session: AsyncSession, lock_id: int):
    """
    Acquires a PostgreSQL transaction-level advisory lock.
    """
    try:
        # pg_try_advisory_xact_lock returns true if lock is acquired, false otherwise
        result = await session.execute(text("SELECT pg_try_advisory_xact_lock(:lock_id)"), {"lock_id": lock_id})
        acquired = result.scalar()
        if not acquired:
            raise Exception(f"Could not acquire database advisory lock {lock_id}")
        
        logger.info(f"Acquired PG advisory lock {lock_id}")
        yield
    finally:
        # Transaction level locks are automatically released at the end of the transaction
        logger.info(f"Released PG advisory lock {lock_id} (at transaction commit/rollback)")

