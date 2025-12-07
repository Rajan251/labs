"""
Main FastAPI application
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models import schemas
from app.services.inventory import InventoryService
from app.services.reservation import ReservationService
from typing import List, Optional
import uuid

app = FastAPI(
    title="Inventory Management System",
    description="Complete inventory management API with reservations, multi-warehouse support, and real-time tracking",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# ============ Inventory Operations ============

@app.get("/api/v1/inventory/stock", response_model=List[schemas.StockResponse])
async def check_stock(
    sku: str,
    warehouse: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Check stock availability"""
    service = InventoryService(db)
    result = await service.get_inventory_by_sku(sku, warehouse)
    
    if not result:
        raise HTTPException(404, "Product not found")
    
    return [
        schemas.StockResponse(
            sku=product.sku,
            product_name=product.name,
            warehouse=wh.code,
            quantity_on_hand=inv.quantity_on_hand,
            quantity_reserved=inv.quantity_reserved,
            quantity_available=inv.quantity_available
        )
        for inv, product, wh in result
    ]

@app.post("/api/v1/inventory/receive")
async def receive_inventory(
    data: schemas.InventoryReceive,
    db: AsyncSession = Depends(get_db)
):
    """Receive inventory into warehouse"""
    service = InventoryService(db)
    # TODO: Get user_id from auth
    user_id = uuid.uuid4()
    return await service.receive_inventory(data, user_id)

@app.post("/api/v1/inventory/ship")
async def ship_inventory(
    data: schemas.InventoryShip,
    db: AsyncSession = Depends(get_db)
):
    """Ship inventory from warehouse"""
    service = InventoryService(db)
    user_id = uuid.uuid4()
    return await service.ship_inventory(data, user_id)

@app.post("/api/v1/inventory/adjust")
async def adjust_inventory(
    data: schemas.InventoryAdjust,
    db: AsyncSession = Depends(get_db)
):
    """Manual inventory adjustment"""
    service = InventoryService(db)
    user_id = uuid.uuid4()
    return await service.adjust_inventory(data, user_id)

@app.post("/api/v1/inventory/transfer")
async def transfer_inventory(
    data: schemas.InventoryTransfer,
    db: AsyncSession = Depends(get_db)
):
    """Transfer inventory between warehouses"""
    service = InventoryService(db)
    user_id = uuid.uuid4()
    return await service.transfer_inventory(data, user_id)

# ============ Reservations ============

@app.post("/api/v1/reservations")
async def create_reservation(
    data: schemas.ReservationCreate,
    db: AsyncSession = Depends(get_db)
):
    """Reserve inventory for order"""
    service = ReservationService(db)
    return await service.reserve(data.items, data.order_id, data.ttl)

@app.post("/api/v1/reservations/{order_id}/confirm")
async def confirm_reservation(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Confirm reservation and decrement stock"""
    service = ReservationService(db)
    return await service.confirm(order_id)

@app.post("/api/v1/reservations/{order_id}/release")
async def release_reservation(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Release reservation"""
    service = ReservationService(db)
    return await service.release(order_id)

# ============ Dashboard & Metrics ============

@app.get("/api/v1/dashboard/metrics", response_model=schemas.DashboardMetrics)
async def get_dashboard_metrics(db: AsyncSession = Depends(get_db)):
    """Get inventory dashboard metrics"""
    service = InventoryService(db)
    return await service.get_dashboard_metrics()

@app.get("/api/v1/dashboard/low-stock", response_model=List[schemas.LowStockItem])
async def get_low_stock_items(
    warehouse_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get items below reorder point"""
    service = InventoryService(db)
    result = await service.get_low_stock_items(warehouse_id)
    
    return [
        schemas.LowStockItem(
            sku=product.sku,
            product_name=product.name,
            warehouse=wh.code,
            quantity_available=inv.quantity_available,
            reorder_point=inv.reorder_point,
            suggested_reorder=inv.reorder_quantity
        )
        for inv, product, wh in result
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
