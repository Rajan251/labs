"""
Sample FastAPI Application
Production-ready Python web application with health checks and metrics
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST
import logging
import time
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="GitLab CI/CD Example App",
    description="Production-ready application with health checks and metrics",
    version="1.0.0"
)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)
REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# Middleware for metrics
@app.middleware("http")
async def add_metrics(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to GitLab CI/CD Example App",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes probes"""
    return {
        "status": "healthy",
        "timestamp": time.time()
    }

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    # Add actual readiness checks here (database, cache, etc.)
    return {
        "status": "ready",
        "timestamp": time.time()
    }

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

@app.get("/api/data")
async def get_data():
    """Example API endpoint"""
    return {
        "data": [
            {"id": 1, "name": "Item 1"},
            {"id": 2, "name": "Item 2"},
            {"id": 3, "name": "Item 3"}
        ]
    }

@app.post("/api/data")
async def create_data(item: dict):
    """Example POST endpoint"""
    logger.info(f"Creating item: {item}")
    return {
        "message": "Item created successfully",
        "item": item
    }

@app.get("/error")
async def trigger_error():
    """Endpoint to test error handling"""
    raise HTTPException(status_code=500, detail="Intentional error for testing")

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "3000"))
    logger.info(f"Starting server on port {port}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
