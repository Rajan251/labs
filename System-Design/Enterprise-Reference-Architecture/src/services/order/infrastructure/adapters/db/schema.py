from sqlalchemy import Column, String, Float, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class OrderModel(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True)
    customer_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    status = Column(String, nullable=False)
    total_amount = Column(Float, nullable=False)
    
    # Address embedded (simplified for schema)
    shipping_street = Column(String)
    shipping_city = Column(String)
    shipping_zip = Column(String)
    shipping_country = Column(String)

    items = relationship("OrderLineModel", back_populates="order", cascade="all, delete-orphan")

class OrderLineModel(Base):
    __tablename__ = "order_lines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)

    order = relationship("OrderModel", back_populates="items")
