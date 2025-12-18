from fastapi import FastAPI, Request, Response, Depends
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import redis.asyncio as redis
import os
import hashlib
from .inventory import router as inventory_router
from .database import engine, Base
from .dependencies import get_redis
from .utils import BackgroundCleaner
from .models import HealthStatus

# OpenTelemetry imports (Simulated availability)
try:
    from opentelemetry import trace
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    HAS_OTEL = True
except ImportError:
    HAS_OTEL = False

app = FastAPI()

if HAS_OTEL:
    FastAPIInstrumentor.instrument_app(app)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client_instance = redis.from_url(REDIS_URL, decode_responses=True)

class IdempotencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method in ["POST", "PUT", "PATCH"]:
            idempotency_key = request.headers.get("Idempotency-Key")
            if idempotency_key:
                cache_key = f"idempotency:{idempotency_key}"
                # Using the global redis client here for middleware simplicity
                # In production, use connection pool or dependency injection cleanly
                cached_response = await redis_client_instance.get(cache_key)
                
                if cached_response:
                     return JSONResponse(
                         content={"message": "Request already processed", "original_response": cached_response},
                         status_code=200 
                     )
                
                response = await call_next(request)
                
                if 200 <= response.status_code < 300:
                    await redis_client_instance.set(cache_key, "processed", ex=86400)
                
                return response
        
        return await call_next(request)

app.add_middleware(IdempotencyMiddleware)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Background task example (could use FastAPI BackgroundTasks in endpoints too)

@app.get("/health", response_model=HealthStatus)
async def health_check(redis=Depends(get_redis)):
    """
    Health check for K8s liveness/readiness probes.
    """
    redis_ok = False
    db_ok = True # simplified assumption or add real check
    
    try:
        await redis.ping()
        redis_ok = True
    except Exception:
        pass
        
    return HealthStatus(
        status="ok" if redis_ok and db_ok else "degraded",
        redis=redis_ok,
        database=db_ok
    )

app.include_router(inventory_router, prefix="/inventory")

@app.get("/")
def read_root():
    return {"message": "FastAPI Race Condition Mitigation Demo (Advanced)"}

