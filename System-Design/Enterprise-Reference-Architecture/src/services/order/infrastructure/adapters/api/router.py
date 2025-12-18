from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator
from .....shared.kernel.observability.logging import logger, correlation_id_ctx
from ...application.services import OrderService, CreateOrderCommand
from ...infrastructure.adapters.db.repository import SqlAlchemyOrderRepository
# from ...db import get_session # Assuming we have a DB session provider

router = APIRouter()

# Mock Dependency for DB Session
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    yield None # In real app, this yields the session

@router.post("/orders", status_code=201)
async def create_order(
    command: CreateOrderCommand,
    session: AsyncSession = Depends(get_session)
):
    correlation_id_ctx.set("req-" + str(command.customer_id)) # Simple correlation ID
    
    repo = SqlAlchemyOrderRepository(session)
    service = OrderService(repo)
    
    try:
        order_id = await service.create_order(command)
        return {"order_id": order_id, "status": "processing"}
    except ValueError as e:
        logger.error(f"Domain error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"System error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
