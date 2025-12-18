from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ....domain.model import Order, OrderStatus, Address, OrderLine
from ....domain.repository import OrderRepository
from .schema import OrderModel, OrderLineModel

class SqlAlchemyOrderRepository(OrderRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, order: Order) -> None:
        # Convert Domain Entity -> DB Model (Mapper)
        # Check if exists to determine update vs insert (Simplified here to merge)
        
        # 1. Map Address
        address_dict = {
            "shipping_street": order.shipping_address.street,
            "shipping_city": order.shipping_address.city,
            "shipping_zip": order.shipping_address.zip_code,
            "shipping_country": order.shipping_address.country,
        }
        
        # 2. Map Items
        items_models = [
            OrderLineModel(
                product_id=line.product_id,
                quantity=line.quantity,
                price=line.price
            ) for line in order.items
        ]

        # 3. Create/Update Order Model
        order_model = OrderModel(
            id=order.id,
            customer_id=order.customer_id,
            status=order.status.value,
            total_amount=order.total_amount,
            items=items_models,
            **address_dict
        )
        
        # In a real app we'd handle existing items update more carefully
        self.session.add(order_model)
        await self.session.flush()

    async def get_by_id(self, order_id: UUID) -> Optional[Order]:
        stmt = select(OrderModel).where(OrderModel.id == order_id).options(selectinload(OrderModel.items))
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        # Reconstitute Domain Entity
        address = Address(
            street=model.shipping_street,
            city=model.shipping_city,
            zip_code=model.shipping_zip,
            country=model.shipping_country
        )
        
        order = Order(
            id=model.id,
            customer_id=model.customer_id,
            status=OrderStatus(model.status),
            shipping_address=address,
            total_amount=model.total_amount
        )
        
        # We need to manually inject items because pydantic _fields are tricky with private attrs
        # or just append them if using the method
        for item in model.items:
            # Reconstruct entity logic if needed, or bypass validation 
           order.items.append(OrderLine(
               product_id=item.product_id,
               quantity=item.quantity,
               price=item.price
           ))
           
        return order
