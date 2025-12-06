"""
Main FastAPI application with all routes and middleware.
"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from contextlib import asynccontextmanager

from app.config import settings
from app.database import init_db
from app.monitoring.logging import logger
from app.api import tenants, events, dlq


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting webhook platform", extra={"version": settings.app_version})
    init_db()
    logger.info("Database initialized")
    yield
    # Shutdown
    logger.info("Shutting down webhook platform")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Production-ready webhook delivery platform with reliable delivery, "
                "retry mechanisms, idempotency, and comprehensive monitoring",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus instrumentation
Instrumentator().instrument(app).expose(app)

# Include routers
app.include_router(tenants.router)
app.include_router(events.router)
app.include_router(dlq.router)


@app.get("/")
def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "operational",
        "docs": "/docs",
        "metrics": "/metrics"
    }


@app.get("/health")
def health_check():
    """Health check endpoint for load balancers."""
    return {
        "status": "healthy",
        "version": settings.app_version
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(
        "Unhandled exception",
        extra={
            "path": request.url.path,
            "method": request.method,
            "error": str(exc)
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An unexpected error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
