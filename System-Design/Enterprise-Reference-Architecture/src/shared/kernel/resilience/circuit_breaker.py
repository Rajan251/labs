import time
from enum import Enum
from typing import Callable, Any, Type
from ..observability.logging import logger

class State(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

class CircuitBreakerOpenException(Exception):
    pass

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = State.CLOSED
        self.failures = 0
        self.last_failure_time = 0

    def call(self, func: Callable, *args, **kwargs) -> Any:
        if self.state == State.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = State.HALF_OPEN
                logger.info("Circuit Breaker entering HALF_OPEN state")
            else:
                raise CircuitBreakerOpenException("Circuit is OPEN")

        try:
            result = func(*args, **kwargs)
            if self.state == State.HALF_OPEN:
                self.reset()
            return result
        except Exception as e:
            self.record_failure()
            raise e

    def record_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        logger.warning(f"Circuit Breaker failure recorded. Count: {self.failures}")

        if self.failures >= self.failure_threshold:
            self.state = State.OPEN
            logger.error("Circuit Breaker tripped to OPEN state")

    def reset(self):
        self.state = State.CLOSED
        self.failures = 0
        logger.info("Circuit Breaker reset to CLOSED state")
