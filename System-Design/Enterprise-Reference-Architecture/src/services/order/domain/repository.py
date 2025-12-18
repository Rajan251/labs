from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID
from .model import Order

class OrderRepository(ABC):
    """
    Port: Defines the contract for Order persistence.
    """
    @abstractmethod
    async def save(self, order: Order) -> None:
        pass

    @abstractmethod
    async def get_by_id(self, order_id: UUID) -> Optional[Order]:
        pass
