from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from redis import asyncio as aioredis
import httpx
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from .core.config import settings
from .core.celery_app import process_background_job

app = FastAPI(title=settings.PROJECT_NAME)

# OpenTelemetry Instrumentation (Simulated if libs missing)
try:
    FastAPIInstrumentor.instrument_app(app)
except ImportError:
    pass

# Database Engine with Pooling config
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW
)

# HTTP Client with Connection Pooling for external calls
http_client = httpx.AsyncClient(
    limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
    timeout=10.0
)

@app.on_event("shutdown")
async def shutdown_event():
    await http_client.aclose()

@app.get("/health/live")
async def liveness_probe():
    """
    K8s Liveness Probe: Just checks if the app is responding.
    """
    return {"status": "alive"}

@app.get("/health/ready")
async def readiness_probe():
    """
    K8s Readiness Probe: Checks dependent services (DB, Redis).
    If this fails, K8s stops sending traffic to this pod.
    """
    status = {"database": False, "redis": False}
    
    # Check DB
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        status["database"] = True
    except Exception:
        pass # Log error
        
    # Check Redis
    try:
        redis = aioredis.from_url(settings.REDIS_URL)
        await redis.ping()
        await redis.close()
        status["redis"] = True
    except Exception:
        pass
        
    if all(status.values()):
        return status
    
    raise HTTPException(status_code=503, detail=status)

@app.post("/jobs")
async def create_job(data: dict):
    """
    Enqueues a background job via Celery.
    """
    task = process_background_job.delay(data)
    return {"task_id": task.id, "status": "queued"}
