"""
FastAPI application entry point.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
import structlog

from .config import settings
from .database import init_db, close_db
from .redis_client import redis_client
from .rabbitmq_client import rabbitmq_client
from .api import configs, versions, rollouts, audit, health

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("starting_application", version=settings.app_version)
    
    # Initialize database
    await init_db()
    
    # Connect to Redis
    await redis_client.connect()
    
    # Connect to RabbitMQ
    if settings.enable_notifications:
        await rabbitmq_client.connect()
    
    logger.info("application_started")
    
    yield
    
    # Shutdown
    logger.info("shutting_down_application")
    
    # Close connections
    await redis_client.disconnect()
    if settings.enable_notifications:
        await rabbitmq_client.disconnect()
    await close_db()
    
    logger.info("application_shutdown_complete")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Centralized Configuration Management Service",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(configs.router, prefix=settings.api_prefix)
app.include_router(versions.router, prefix=settings.api_prefix)
app.include_router(rollouts.router, prefix=settings.api_prefix)
app.include_router(audit.router, prefix=settings.api_prefix)

# Prometheus metrics endpoint
if settings.metrics_enabled:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "docs": f"{settings.api_prefix}/docs",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
