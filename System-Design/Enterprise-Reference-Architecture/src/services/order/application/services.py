from uuid import UUID
from typing import List, Dict
from pydantic import BaseModel
from .model import Order, Address
from .repository import OrderRepository
from ....shared.kernel.observability.logging import logger

class CreateOrderCommand(BaseModel):
    customer_id: UUID
    shipping_address: Dict[str, str]
    items: List[Dict[str, Any]] # product_id, quantity, price

class OrderService:
    def __init__(self, repository: OrderRepository):
        self.repository = repository

    async def create_order(self, command: CreateOrderCommand) -> UUID:
        logger.info(f"Creating order for customer {command.customer_id}")
        
        address = Address(**command.shipping_address)
        order = Order.create(customer_id=command.customer_id, address=address)
        
        for item in command.items:
            order.add_item(
                product_id=UUID(item['product_id']),
                quantity=item['quantity'],
                price=item['price']
            )
            
        await self.repository.save(order)
        logger.info(f"Order {order.id} created successfully with total {order.total_amount}")
        
        # Here we would also dispatch domain events to the Message Bus (Side Effect)
        # self.event_dispatcher.dispatch(order.domain_events)
        
        return order.id
