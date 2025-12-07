"""
Database models for inventory system
"""
from sqlalchemy import Column, String, Integer, Numeric, Boolean, DateTime, ForeignKey, CheckConstraint, Index, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class Product(Base):
    """Product catalog"""
    __tablename__ = "products"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sku = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(500), nullable=False)
    description = Column(String)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"))
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id"))
    base_price = Column(Numeric(10, 2), nullable=False)
    weight_kg = Column(Numeric(8, 3))
    dimensions = Column(JSONB)  # {length, width, height}
    is_trackable = Column(Boolean, default=True)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    category = relationship("Category", back_populates="products")
    brand = relationship("Brand", back_populates="products")
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    inventory = relationship("Inventory", back_populates="product", cascade="all, delete-orphan")

class Category(Base):
    """Product categories"""
    __tablename__ = "categories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"))
    level = Column(Integer, nullable=False, default=0)
    path = Column(String(1000))  # Materialized path
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    products = relationship("Product", back_populates="category")
    parent = relationship("Category", remote_side=[id])

class Brand(Base):
    """Product brands"""
    __tablename__ = "brands"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, unique=True)
    slug = Column(String(200), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    products = relationship("Product", back_populates="brand")

class ProductVariant(Base):
    """Product variants (size, color, etc.)"""
    __tablename__ = "product_variants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    sku = Column(String(100), unique=True, nullable=False)
    attributes = Column(JSONB)  # {"size": "L", "color": "red"}
    price_adjustment = Column(Numeric(10, 2), default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    product = relationship("Product", back_populates="variants")
    inventory = relationship("Inventory", back_populates="variant")

class Warehouse(Base):
    """Warehouses/locations"""
    __tablename__ = "warehouses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    address = Column(JSONB)
    type = Column(String(50))  # fulfillment, retail, dropship
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    inventory = relationship("Inventory", back_populates="warehouse")

class Inventory(Base):
    """Stock levels per warehouse"""
    __tablename__ = "inventory"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    variant_id = Column(UUID(as_uuid=True), ForeignKey("product_variants.id"))
    warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)
    
    # Quantity tracking
    quantity_on_hand = Column(Integer, nullable=False, default=0)
    quantity_reserved = Column(Integer, nullable=False, default=0)
    # quantity_available is computed: quantity_on_hand - quantity_reserved
    
    # Thresholds
    reorder_point = Column(Integer, default=10)
    reorder_quantity = Column(Integer, default=50)
    safety_stock = Column(Integer, default=5)
    
    # Metadata
    last_counted_at = Column(DateTime)
    last_received_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('quantity_on_hand >= 0', name='check_quantity_positive'),
        CheckConstraint('quantity_reserved >= 0', name='check_reserved_positive'),
        CheckConstraint('quantity_reserved <= quantity_on_hand', name='check_reserved_lte_onhand'),
        Index('idx_inventory_product_warehouse', 'product_id', 'warehouse_id'),
        Index('idx_inventory_low_stock', 'warehouse_id', 
              text('(quantity_on_hand - quantity_reserved)'),
              postgresql_where=text('(quantity_on_hand - quantity_reserved) <= reorder_point')),
    )
    
    # Relationships
    product = relationship("Product", back_populates="inventory")
    variant = relationship("ProductVariant", back_populates="inventory")
    warehouse = relationship("Warehouse", back_populates="inventory")
    transactions = relationship("InventoryTransaction", back_populates="inventory")
    reservations = relationship("InventoryReservation", back_populates="inventory")
    
    @property
    def quantity_available(self):
        """Computed available quantity"""
        return self.quantity_on_hand - self.quantity_reserved

class InventoryTransaction(Base):
    """Audit trail for inventory changes"""
    __tablename__ = "inventory_transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    inventory_id = Column(UUID(as_uuid=True), ForeignKey("inventory.id"), nullable=False)
    transaction_type = Column(String(50), nullable=False)  # receive, ship, adjust, reserve, release, return
    
    quantity_change = Column(Integer, nullable=False)
    quantity_before = Column(Integer, nullable=False)
    quantity_after = Column(Integer, nullable=False)
    
    reference_type = Column(String(50))  # order, transfer, adjustment
    reference_id = Column(UUID(as_uuid=True))
    
    reason = Column(String)
    performed_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    inventory = relationship("Inventory", back_populates="transactions")

class InventoryReservation(Base):
    """Temporary inventory holds"""
    __tablename__ = "inventory_reservations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    inventory_id = Column(UUID(as_uuid=True), ForeignKey("inventory.id"), nullable=False)
    order_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    quantity = Column(Integer, nullable=False)
    status = Column(String(20), default='pending')  # pending, confirmed, released, expired
    
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False, index=True)
    confirmed_at = Column(DateTime)
    released_at = Column(DateTime)
    
    __table_args__ = (
        Index('idx_reservation_status_expires', 'status', 'expires_at'),
    )
    
    # Relationships
    inventory = relationship("Inventory", back_populates="reservations")

class User(Base):
    """Users for authentication"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(200))
    role = Column(String(50), default='user')  # admin, manager, user
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
