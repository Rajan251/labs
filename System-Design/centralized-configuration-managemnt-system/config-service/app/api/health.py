"""
Health check endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from ..database import get_db
from ..redis_client import redis_client
from ..rabbitmq_client import rabbitmq_client

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health_check():
    """Basic health check."""
    return {"status": "healthy", "service": "config-management-service"}


@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """
    Readiness check - verifies all dependencies are available.
    """
    checks = {
        "database": False,
        "redis": False,
        "rabbitmq": False,
    }
    
    # Check database
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception as e:
        logger.error("database_health_check_failed", error=str(e))
    
    # Check Redis
    try:
        if redis_client.client:
            await redis_client.client.ping()
            checks["redis"] = True
    except Exception as e:
        logger.error("redis_health_check_failed", error=str(e))
    
    # Check RabbitMQ
    try:
        if rabbitmq_client.connection and not rabbitmq_client.connection.is_closed:
            checks["rabbitmq"] = True
    except Exception as e:
        logger.error("rabbitmq_health_check_failed", error=str(e))
    
    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503
    
    return {
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks
    }


@router.get("/live")
async def liveness_check():
    """Liveness check - simple check that the service is running."""
    return {"status": "alive"}
