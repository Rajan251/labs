from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, Integer, String, select, update
from sqlalchemy.exc import StaleDataError
from .database import Base, get_db
from .locks import postgres_advisory_lock
from .dependencies import get_lock_manager
import os

router = APIRouter()
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

class InventoryItem(Base):
    __tablename__ = "inventory"
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    stock = Column(Integer, default=0)
    version = Column(Integer, default=1, nullable=False) # For Optimistic Locking

    __mapper_args__ = {
        "version_id_col": version
    }

@router.post("/items/")
async def create_item(name: str, stock: int, db: AsyncSession = Depends(get_db)):
    item = InventoryItem(name=name, stock=stock)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item

@router.post("/buy/{item_id}")
async def buy_item(item_id: int, quantity: int, db: AsyncSession = Depends(get_db)):
    """
    Buy item using Optimistic Concurrency Control (SQLAlchemy Versioning).
    If the version has changed between read and write, StaleDataError is raised.
    """
    try:
        # Fetch item
        result = await db.execute(select(InventoryItem).where(InventoryItem.id == item_id))
        item = result.scalars().first()
        
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        if item.stock < quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock")
        
        # Determine new stock
        item.stock -= quantity
        
        # Commit triggers the update with version check:
        # UPDATE inventory SET stock=?, version=? WHERE id=? AND version=?
        await db.commit()
        
        return {"message": "Purchase successful", "new_stock": item.stock}

    except StaleDataError:
        # This catches the optimistic locking failure
        await db.rollback()
        raise HTTPException(status_code=409, detail="Conflict: Item was modified by another transaction. Please retry.")

@router.post("/buy-secure-redis/{item_id}")
async def buy_item_redis_lock(
    item_id: int, 
    quantity: int, 
    db: AsyncSession = Depends(get_db),
    lock_manager = Depends(get_lock_manager) # Injected LockManager
):
    """
    Buy item using Distributed Redis Lock (Redlock algorithm).
    Ensures only one process can attempt to buy this specific item at a time.
    """
    # Use the Redlock implementation from dependencies
    lock = lock_manager.get_lock(f"inventory_item_{item_id}", ttl=5)
    
    try:
        async with lock:
            # Critical Section
            result = await db.execute(select(InventoryItem).where(InventoryItem.id == item_id))
            item = result.scalars().first()
            
            if not item:
                raise HTTPException(status_code=404, detail="Item not found")
            
            if item.stock < quantity:
                raise HTTPException(status_code=400, detail="Insufficient stock")
            
            item.stock -= quantity
            await db.commit()
            
            return {"message": "Purchase successful with Redlock", "new_stock": item.stock}
            
    except Exception as e:
        if "Could not acquire lock" in str(e):
             raise HTTPException(status_code=429, detail="System busy, please try again")
        raise e

@router.post("/buy-secure-db-lock/{item_id}")
async def buy_item_db_lock(item_id: int, quantity: int, db: AsyncSession = Depends(get_db)):
    """
    Buy item using PostgreSQL Advisory Lock.
    Useful when you want to lock specifically at the DB level but not row-level (or as a complement).
    We use the item_id as the lock key.
    """
    async with postgres_advisory_lock(db, item_id):
        # We are now in a transaction with an advisory lock held
        result = await db.execute(select(InventoryItem).where(InventoryItem.id == item_id))
        item = result.scalars().first()
        
        if not item:
             raise HTTPException(status_code=404, detail="Item not found")

        if item.stock < quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock")
            
        item.stock -= quantity
        await db.commit()
        
    return {"message": "Purchase successful with DB Advisory Lock", "new_stock": item.stock}
