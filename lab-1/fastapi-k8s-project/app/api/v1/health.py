"""
Health Check Endpoints

These endpoints are used by Kubernetes for:
- Liveness probes: Check if the application is running
- Readiness probes: Check if the application is ready to serve traffic
"""

from fastapi import APIRouter, status
from datetime import datetime
from app.core.config import settings

router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Basic health check endpoint
    
    Used by Kubernetes liveness probe to determine if the pod is alive.
    If this endpoint fails, Kubernetes will restart the pod.
    
    Returns:
        dict: Health status and basic application info
    """
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness_check():
    """
    Readiness check endpoint
    
    Used by Kubernetes readiness probe to determine if the pod is ready
    to receive traffic. This should check:
    - Database connectivity
    - External service availability
    - Cache availability
    
    Returns:
        dict: Readiness status with dependency checks
    """
    # TODO: Add actual dependency checks
    # For example:
    # - Check database connection
    # - Check Redis connection
    # - Check external API availability
    
    checks = {
        "database": "ok",  # Replace with actual DB check
        "cache": "ok",     # Replace with actual cache check
    }
    
    all_healthy = all(status == "ok" for status in checks.values())
    
    return {
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/live", status_code=status.HTTP_200_OK)
async def liveness_check():
    """
    Liveness check endpoint
    
    Simple endpoint to verify the application process is running.
    This should be lightweight and not check external dependencies.
    
    Returns:
        dict: Simple alive status
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }
