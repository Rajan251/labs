import asyncio
import logging
from sqlalchemy.exc import DBAPIError
from fastapi import BackgroundTasks

logger = logging.getLogger(__name__)

async def run_in_transaction(session, func, *args, **kwargs):
    """
    Executes a function within a DB transaction with retry logic for serialization failures.
    Serialized transactions (if used) often fail with 40001 error code in Postgres.
    """
    max_retries = 3
    base_delay = 0.1
    
    for attempt in range(max_retries):
        try:
            async with session.begin():
                result = await func(session, *args, **kwargs)
            return result
        except DBAPIError as e:
            # Check for serialization failure (40001) or deadlock (40P01)
            # This logic depends on the driver, here assuming generic access to pg code
            if "40001" in str(e) or "40P01" in str(e):
                if attempt == max_retries - 1:
                    logger.error(f"Transaction failed after {max_retries} retries: {e}")
                    raise
                
                delay = base_delay * (2 ** attempt)
                logger.warning(f"Transaction retry {attempt + 1}/{max_retries} due to conflict. Sleeping {delay}s")
                await asyncio.sleep(delay)
            else:
                raise

class BackgroundCleaner:
    """
    Simulates a background task that cleans up stale idempotency keys or other maintenance.
    """
    @staticmethod
    async def clean_stale_keys(redis_client):
        # In a real scenario, Redis TTL handles this automatically.
        # This is just to demonstrate background task pattern.
        logger.info("Running background cleanup task...")
        # Example: Log memory usage or similar
        info = await redis_client.info("memory")
        logger.info(f"Redis memory usage: {info.get('used_memory_human')}")
