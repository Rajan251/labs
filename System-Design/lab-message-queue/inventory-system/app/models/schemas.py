"""
Pydantic schemas for API requests/responses
"""
from pydantic import BaseModel, UUID4, Field, ConfigDict
from typing import Optional, List, Dict
from decimal import Decimal
from datetime import datetime
from enum import Enum

# Enums
class TransactionType(str, Enum):
    RECEIVE = "receive"
    SHIP = "ship"
    ADJUST = "adjust"
    RESERVE = "reserve"
    RELEASE = "release"
    RETURN = "return"

class ReservationStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    RELEASED = "released"
    EXPIRED = "expired"

# Product Schemas
class ProductBase(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    category_id: Optional[UUID4] = None
    brand_id: Optional[UUID4] = None
    base_price: Decimal
    weight_kg: Optional[Decimal] = None
    dimensions: Optional[Dict] = None
    is_trackable: bool = True
    status: str = "active"

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    base_price: Optional[Decimal] = None
    status: Optional[str] = None

class Product(ProductBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Warehouse Schemas
class WarehouseBase(BaseModel):
    code: str
    name: str
    address: Optional[Dict] = None
    type: Optional[str] = None
    is_active: bool = True
    priority: int = 0

class WarehouseCreate(WarehouseBase):
    pass

class Warehouse(WarehouseBase):
    id: UUID4
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Inventory Schemas
class InventoryBase(BaseModel):
    product_id: UUID4
    variant_id: Optional[UUID4] = None
    warehouse_id: UUID4
    quantity_on_hand: int = 0
    quantity_reserved: int = 0
    reorder_point: int = 10
    reorder_quantity: int = 50
    safety_stock: int = 5

class InventoryCreate(InventoryBase):
    pass

class InventoryUpdate(BaseModel):
    quantity_on_hand: Optional[int] = None
    reorder_point: Optional[int] = None
    reorder_quantity: Optional[int] = None
    safety_stock: Optional[int] = None

class Inventory(InventoryBase):
    id: UUID4
    quantity_available: int
    last_counted_at: Optional[datetime] = None
    last_received_at: Optional[datetime] = None
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Inventory Operation Schemas
class InventoryReceive(BaseModel):
    sku: str
    warehouse_code: str
    quantity: int = Field(gt=0)
    reason: Optional[str] = None

class InventoryShip(BaseModel):
    sku: str
    warehouse_code: str
    quantity: int = Field(gt=0)
    order_id: Optional[UUID4] = None

class InventoryAdjust(BaseModel):
    sku: str
    warehouse_code: str
    new_quantity: int = Field(ge=0)
    reason: str

class InventoryTransfer(BaseModel):
    sku: str
    from_warehouse: str
    to_warehouse: str
    quantity: int = Field(gt=0)

# Reservation Schemas
class ReservationCreate(BaseModel):
    items: List[Dict]  # [{product_id, variant_id, warehouse_id, quantity}]
    order_id: UUID4
    ttl: int = 600  # seconds

class Reservation(BaseModel):
    id: UUID4
    inventory_id: UUID4
    order_id: UUID4
    quantity: int
    status: ReservationStatus
    created_at: datetime
    expires_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Transaction Schemas
class Transaction(BaseModel):
    id: UUID4
    inventory_id: UUID4
    transaction_type: TransactionType
    quantity_change: int
    quantity_before: int
    quantity_after: int
    reference_type: Optional[str] = None
    reference_id: Optional[UUID4] = None
    reason: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Stock Inquiry
class StockInquiry(BaseModel):
    sku: str
    warehouse_code: Optional[str] = None

class StockResponse(BaseModel):
    sku: str
    product_name: str
    warehouse: str
    quantity_on_hand: int
    quantity_reserved: int
    quantity_available: int

# Batch Import
class ImportResult(BaseModel):
    status: str
    processed: int
    errors: int
    error_details: Optional[List[str]] = None

# Dashboard Metrics
class DashboardMetrics(BaseModel):
    total_products: int
    total_warehouses: int
    out_of_stock_count: int
    low_stock_count: int
    total_units_on_hand: int
    total_units_reserved: int
    total_units_available: int

class LowStockItem(BaseModel):
    sku: str
    product_name: str
    warehouse: str
    quantity_available: int
    reorder_point: int
    suggested_reorder: int

# Auth Schemas
class UserCreate(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None
    role: str = "user"

class User(BaseModel):
    id: UUID4
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[UUID4] = None
