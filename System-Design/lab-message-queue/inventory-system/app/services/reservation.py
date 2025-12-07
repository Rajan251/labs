"""
Reservation service - handles inventory reservations
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.database import Inventory, InventoryReservation, Product, Warehouse
from app.core.redis import redis_client
from fastapi import HTTPException
from datetime import datetime, timedelta
from typing import List, Dict
import uuid

class ReservationService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def reserve(self, items: List[Dict], order_id: uuid.UUID, ttl: int = 600):
        """Reserve inventory for order"""
        reservation_ids = []
        
        for item in items:
            # Get inventory with lock
            lock_key = f"inventory_lock:{item['product_id']}:{item['warehouse_id']}"
            
            async with redis_client.lock(lock_key, timeout=5):
                inventory = await self.db.get(Inventory, item['inventory_id'])
                
                if not inventory:
                    raise HTTPException(404, "Inventory not found")
                
                # Check availability
                available = inventory.quantity_on_hand - inventory.quantity_reserved
                
                if available < item['quantity']:
                    raise HTTPException(
                        400,
                        f"Insufficient stock. Available: {available}, Requested: {item['quantity']}"
                    )
                
                # Create reservation
                reservation = InventoryReservation(
                    id=uuid.uuid4(),
                    inventory_id=inventory.id,
                    order_id=order_id,
                    quantity=item['quantity'],
                    status='pending',
                    expires_at=datetime.utcnow() + timedelta(seconds=ttl)
                )
                
                # Update reserved quantity
                inventory.quantity_reserved += item['quantity']
                
                self.db.add(reservation)
                reservation_ids.append(str(reservation.id))
        
        await self.db.commit()
        
        return {"reservation_ids": reservation_ids, "status": "reserved"}
    
    async def confirm(self, order_id: uuid.UUID):
        """Confirm reservation and decrement stock"""
        result = await self.db.execute(
            select(InventoryReservation, Inventory)
            .join(Inventory)
            .where(and_(
                InventoryReservation.order_id == order_id,
                InventoryReservation.status == 'pending'
            ))
        )
        
        reservations = result.all()
        
        for res, inv in reservations:
            # Decrement actual stock
            inv.quantity_on_hand -= res.quantity
            inv.quantity_reserved -= res.quantity
            
            # Mark confirmed
            res.status = 'confirmed'
            res.confirmed_at = datetime.utcnow()
        
        await self.db.commit()
        
        return {"status": "confirmed", "order_id": str(order_id)}
    
    async def release(self, order_id: uuid.UUID):
        """Release reservation"""
        result = await self.db.execute(
            select(InventoryReservation, Inventory)
            .join(Inventory)
            .where(and_(
                InventoryReservation.order_id == order_id,
                InventoryReservation.status == 'pending'
            ))
        )
        
        reservations = result.all()
        
        for res, inv in reservations:
            # Decrement reserved quantity
            inv.quantity_reserved -= res.quantity
            
            # Mark released
            res.status = 'released'
            res.released_at = datetime.utcnow()
        
        await self.db.commit()
        
        return {"status": "released", "order_id": str(order_id)}
