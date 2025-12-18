import time
import random
import functools
from typing import Type, Tuple
from ..observability.logging import logger

def retry_with_backoff(
    retries: int = 3,
    backoff_in_seconds: int = 1,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Retry decorator with exponential backoff and jitter.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            while attempt < retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    if attempt == retries:
                        logger.error(f"Function {func.__name__} failed after {retries} attempts")
                        raise e
                    
                    sleep_time = (backoff_in_seconds * (2 ** (attempt - 1))) + random.uniform(0, 0.1)
                    logger.warning(f"Retrying {func.__name__} (Attempt {attempt}/{retries}) in {sleep_time:.2f}s")
                    time.sleep(sleep_time)
        return wrapper
    return decorator
