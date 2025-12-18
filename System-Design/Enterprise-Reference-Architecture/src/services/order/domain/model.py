from typing import List, Optional
from uuid import UUID
from enum import Enum
from pydantic import Field
from ....shared.kernel.domain.base import AggregateRoot, Entity, ValueObject, DomainEvent

class OrderStatus(str, Enum):
    CREATED = "CREATED"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    CANCELLED = "CANCELLED"

class Address(ValueObject):
    street: str
    city: str
    zip_code: str
    country: str

class OrderLine(Entity):
    product_id: UUID
    quantity: int
    price: float

class OrderCreatedEvent(DomainEvent):
    order_id: UUID
    customer_id: UUID
    total_amount: float

class Order(AggregateRoot):
    customer_id: UUID
    status: OrderStatus = OrderStatus.CREATED
    items: List[OrderLine] = Field(default_factory=list)
    shipping_address: Address
    total_amount: float = 0.0

    def add_item(self, product_id: UUID, quantity: int, price: float):
        if self.status != OrderStatus.CREATED:
            raise ValueError("Cannot add items to a processed order")
        
        line = OrderLine(product_id=product_id, quantity=quantity, price=price)
        self.items.append(line)
        self.calculate_total()

    def calculate_total(self):
        self.total_amount = sum(item.price * item.quantity for item in self.items)

    @staticmethod
    def create(customer_id: UUID, address: Address) -> 'Order':
        order = Order(customer_id=customer_id, shipping_address=address)
        order.add_domain_event(OrderCreatedEvent(
            order_id=order.id, 
            customer_id=customer_id,
            total_amount=0.0
        ))
        return order
    
    def mark_as_paid(self):
        if self.status != OrderStatus.CREATED:
            raise ValueError("Order must be in CREATED state to be paid")
        self.status = OrderStatus.PAID
        # Add PayEvent...
