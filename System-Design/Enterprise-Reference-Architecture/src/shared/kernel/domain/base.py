from abc import ABC, abstractmethod
from typing import List, Any
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, PrivateAttr, Field

class DomainEvent(BaseModel):
    """
    Base class for all domain events.
    Immutable and carries the time it occurred.
    """
    event_id: UUID = Field(default_factory=uuid4)
    occurred_on: datetime = Field(default_factory=datetime.utcnow)

class Entity(BaseModel):
    """
    Base class for Entities.
    Identified by an ID, not attributes.
    """
    id: UUID = Field(default_factory=uuid4)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, type(self)):
            return self.id == other.id
        return False

    def __hash__(self):
        return hash(self.id)

class AggregateRoot(Entity):
    """
    Base class for Aggregate Roots.
    Collects domain events.
    """
    _domain_events: List[DomainEvent] = PrivateAttr(default_factory=list)
    _version: int = 0  # For optimistic locking

    def add_domain_event(self, event: DomainEvent):
        self._domain_events.append(event)

    def clear_domain_events(self):
        self._domain_events.clear()

    @property
    def domain_events(self) -> List[DomainEvent]:
        return list(self._domain_events)

class ValueObject(BaseModel):
    """
    Base class for Value Objects.
    Immutable and defined by attributes.
    """
    class Config:
        frozen = True

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, type(self)):
            return self.model_dump() == other.model_dump()
        return False
