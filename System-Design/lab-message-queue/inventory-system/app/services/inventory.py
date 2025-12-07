"""
Inventory service - business logic for inventory operations
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from app.models.database import Inventory, Product, Warehouse, InventoryTransaction, InventoryReservation, ProductVariant
from app.models.schemas import InventoryReceive, InventoryShip, InventoryAdjust, InventoryTransfer
from app.core.redis import redis_client
from fastapi import HTTPException
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import uuid

class InventoryService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_inventory_by_sku(self, sku: str, warehouse_code: Optional[str] = None):
        """Get inventory for a product"""
        query = (
            select(Inventory, Product, Warehouse)
            .join(Product, Inventory.product_id == Product.id)
            .join(Warehouse, Inventory.warehouse_id == Warehouse.id)
            .where(Product.sku == sku)
        )
        
        if warehouse_code:
            query = query.where(Warehouse.code == warehouse_code)
        
        result = await self.db.execute(query)
        return result.all()
    
    async def receive_inventory(self, data: InventoryReceive, user_id: uuid.UUID):
        """Receive inventory into warehouse"""
        # Get inventory record
        inventory = await self._get_inventory_record(data.sku, data.warehouse_code)
        
        if not inventory:
            raise HTTPException(404, "Inventory record not found")
        
        # Acquire lock
        lock_key = f"inventory_lock:{inventory.id}"
        async with redis_client.lock(lock_key, timeout=5):
            # Update quantity
            old_quantity = inventory.quantity_on_hand
            new_quantity = old_quantity + data.quantity
            
            inventory.quantity_on_hand = new_quantity
            inventory.last_received_at = datetime.utcnow()
            inventory.updated_at = datetime.utcnow()
            
            # Log transaction
            transaction = InventoryTransaction(
                id=uuid.uuid4(),
                inventory_id=inventory.id,
                transaction_type="receive",
                quantity_change=data.quantity,
                quantity_before=old_quantity,
                quantity_after=new_quantity,
                reason=data.reason or "Received via API",
                performed_by=user_id
            )
            
            self.db.add(transaction)
            await self.db.commit()
            await self.db.refresh(inventory)
        
        return {
            "status": "success",
            "sku": data.sku,
            "warehouse": data.warehouse_code,
            "old_quantity": old_quantity,
            "new_quantity": new_quantity
        }
    
    async def ship_inventory(self, data: InventoryShip, user_id: uuid.UUID):
        """Ship inventory from warehouse"""
        inventory = await self._get_inventory_record(data.sku, data.warehouse_code)
        
        if not inventory:
            raise HTTPException(404, "Inventory record not found")
        
        # Acquire lock
        lock_key = f"inventory_lock:{inventory.id}"
        async with redis_client.lock(lock_key, timeout=5):
            # Check availability
            available = inventory.quantity_on_hand - inventory.quantity_reserved
            
            if available < data.quantity:
                raise HTTPException(
                    400,
                    f"Insufficient stock. Available: {available}, Requested: {data.quantity}"
                )
            
            # Decrement quantity
            old_quantity = inventory.quantity_on_hand
            new_quantity = old_quantity - data.quantity
            
            inventory.quantity_on_hand = new_quantity
            inventory.updated_at = datetime.utcnow()
            
            # Log transaction
            transaction = InventoryTransaction(
                id=uuid.uuid4(),
                inventory_id=inventory.id,
                transaction_type="ship",
                quantity_change=-data.quantity,
                quantity_before=old_quantity,
                quantity_after=new_quantity,
                reference_type="order" if data.order_id else None,
                reference_id=data.order_id,
                performed_by=user_id
            )
            
            self.db.add(transaction)
            await self.db.commit()
            await self.db.refresh(inventory)
        
        return {
            "status": "success",
            "sku": data.sku,
            "warehouse": data.warehouse_code,
            "shipped_quantity": data.quantity,
            "remaining_quantity": new_quantity
        }
    
    async def adjust_inventory(self, data: InventoryAdjust, user_id: uuid.UUID):
        """Manual inventory adjustment"""
        inventory = await self._get_inventory_record(data.sku, data.warehouse_code)
        
        if not inventory:
            raise HTTPException(404, "Inventory record not found")
        
        # Acquire lock
        lock_key = f"inventory_lock:{inventory.id}"
        async with redis_client.lock(lock_key, timeout=5):
            old_quantity = inventory.quantity_on_hand
            change = data.new_quantity - old_quantity
            
            inventory.quantity_on_hand = data.new_quantity
            inventory.last_counted_at = datetime.utcnow()
            inventory.updated_at = datetime.utcnow()
            
            # Log transaction
            transaction = InventoryTransaction(
                id=uuid.uuid4(),
                inventory_id=inventory.id,
                transaction_type="adjust",
                quantity_change=change,
                quantity_before=old_quantity,
                quantity_after=data.new_quantity,
                reason=data.reason,
                performed_by=user_id
            )
            
            self.db.add(transaction)
            await self.db.commit()
            await self.db.refresh(inventory)
        
        return {
            "status": "success",
            "sku": data.sku,
            "warehouse": data.warehouse_code,
            "adjustment": change,
            "new_quantity": data.new_quantity
        }
    
    async def transfer_inventory(self, data: InventoryTransfer, user_id: uuid.UUID):
        """Transfer inventory between warehouses"""
        # Ship from source
        await self.ship_inventory(
            InventoryShip(
                sku=data.sku,
                warehouse_code=data.from_warehouse,
                quantity=data.quantity
            ),
            user_id
        )
        
        # Receive at destination
        await self.receive_inventory(
            InventoryReceive(
                sku=data.sku,
                warehouse_code=data.to_warehouse,
                quantity=data.quantity,
                reason=f"Transfer from {data.from_warehouse}"
            ),
            user_id
        )
        
        return {
            "status": "success",
            "sku": data.sku,
            "from": data.from_warehouse,
            "to": data.to_warehouse,
            "quantity": data.quantity
        }
    
    async def _get_inventory_record(self, sku: str, warehouse_code: str):
        """Get inventory record with lock"""
        result = await self.db.execute(
            select(Inventory)
            .join(Product, Inventory.product_id == Product.id)
            .join(Warehouse, Inventory.warehouse_id == Warehouse.id)
            .where(and_(
                Product.sku == sku,
                Warehouse.code == warehouse_code
            ))
        )
        return result.scalar_one_or_none()
    
    async def get_low_stock_items(self, warehouse_id: Optional[uuid.UUID] = None):
        """Get items below reorder point"""
        query = (
            select(Inventory, Product, Warehouse)
            .join(Product, Inventory.product_id == Product.id)
            .join(Warehouse, Inventory.warehouse_id == Warehouse.id)
            .where(
                (Inventory.quantity_on_hand - Inventory.quantity_reserved) <= Inventory.reorder_point
            )
        )
        
        if warehouse_id:
            query = query.where(Inventory.warehouse_id == warehouse_id)
        
        result = await self.db.execute(query)
        return result.all()
    
    async def get_dashboard_metrics(self):
        """Get inventory dashboard metrics"""
        from sqlalchemy import func
        
        # Get counts
        result = await self.db.execute(
            select(
                func.count().filter(
                    (Inventory.quantity_on_hand - Inventory.quantity_reserved) == 0
                ).label('out_of_stock'),
                func.count().filter(
                    (Inventory.quantity_on_hand - Inventory.quantity_reserved) <= Inventory.reorder_point
                ).label('low_stock'),
                func.sum(Inventory.quantity_on_hand).label('total_on_hand'),
                func.sum(Inventory.quantity_reserved).label('total_reserved')
            )
            .select_from(Inventory)
        )
        
        metrics = result.one()
        
        # Get product and warehouse counts
        product_count = await self.db.scalar(select(func.count()).select_from(Product))
        warehouse_count = await self.db.scalar(select(func.count()).select_from(Warehouse))
        
        return {
            "total_products": product_count,
            "total_warehouses": warehouse_count,
            "out_of_stock_count": metrics.out_of_stock or 0,
            "low_stock_count": metrics.low_stock or 0,
            "total_units_on_hand": int(metrics.total_on_hand or 0),
            "total_units_reserved": int(metrics.total_reserved or 0),
            "total_units_available": int((metrics.total_on_hand or 0) - (metrics.total_reserved or 0))
        }
