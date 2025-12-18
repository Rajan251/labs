from typing import List, Protocol
from ...domain.base import DomainEvent
from ...observability.logging import logger

class EventPublisher(Protocol):
    async def publish(self, events: List[DomainEvent]) -> None:
        ...

class InMemoryEventDispatcher(EventPublisher):
    """
    Simple in-memory dispatcher for testing/monolith deployment.
    """
    async def publish(self, events: List[DomainEvent]) -> None:
        for event in events:
            logger.info(f"Dispatching event: {event.__class__.__name__} - {event.model_dump_json()}")
            # Here we would route to handle_[EventName] functions
            
class KafkaEventPublisher(EventPublisher):
    """
    Production Kafka Publisher.
    """
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
    
    async def publish(self, events: List[DomainEvent]) -> None:
        # aiokafka producer logic here
        for event in events:
            logger.info(f"Publishing to Kafka: {event.__class__.__name__}")
            # await producer.send_and_wait(...)
