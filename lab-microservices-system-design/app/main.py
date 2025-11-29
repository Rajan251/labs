"""
Main FastAPI application
Production-ready API with sync and async endpoints
"""
import os
import logging
from datetime import datetime
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import redis

from app.models import (
    ItemCreate, ItemResponse, AsyncTaskRequest, 
    AsyncTaskResponse, TaskStatusResponse, HealthResponse
)
from app.database import db, get_items_collection
from app.celery_app import celery_app
from app.tasks import process_heavy_task

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Redis client for caching
redis_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    global redis_client
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        redis_client = redis.from_url(
            redis_url,
            decode_responses=True,
            max_connections=50
        )
        logger.info("Connected to Redis")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    if redis_client:
        redis_client.close()
        logger.info("Redis connection closed")
    
    db.close()
    logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=os.getenv("API_TITLE", "Production Microservices API"),
    version=os.getenv("API_VERSION", "1.0.0"),
    description="Production-ready API with async task processing",
    lifespan=lifespan
)

# CORS middleware
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint for load balancer
    Returns service status
    """
    services = {}
    
    # Check MongoDB
    try:
        services["mongodb"] = "connected" if db.health_check() else "disconnected"
    except Exception:
        services["mongodb"] = "disconnected"
    
    # Check Redis
    try:
        if redis_client:
            redis_client.ping()
            services["redis"] = "connected"
        else:
            services["redis"] = "disconnected"
    except Exception:
        services["redis"] = "disconnected"
    
    # Check RabbitMQ via Celery
    try:
        celery_app.control.inspect().ping()
        services["rabbitmq"] = "connected"
    except Exception:
        services["rabbitmq"] = "disconnected"
    
    overall_status = "healthy" if all(
        s == "connected" for s in services.values()
    ) else "degraded"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        services=services
    )


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Production Microservices API",
        "version": os.getenv("API_VERSION", "1.0.0"),
        "docs": "/docs",
        "health": "/health"
    }


# ============================================================================
# SYNC ENDPOINTS (Direct MongoDB operations)
# ============================================================================

@app.get("/api/items", response_model=List[ItemResponse], tags=["Items"])
async def get_items(skip: int = 0, limit: int = 100):
    """
    Get all items (sync operation)
    Fast endpoint with direct MongoDB query
    """
    try:
        collection = get_items_collection()
        
        # Query with pagination
        cursor = collection.find().skip(skip).limit(limit).sort("created_at", -1)
        
        items = []
        for doc in cursor:
            items.append(ItemResponse(
                id=str(doc["_id"]),
                name=doc["name"],
                description=doc.get("description"),
                metadata=doc.get("metadata", {}),
                created_at=doc.get("created_at", datetime.utcnow()),
                updated_at=doc.get("updated_at", datetime.utcnow())
            ))
        
        logger.info(f"Retrieved {len(items)} items")
        return items
        
    except Exception as e:
        logger.error(f"Error retrieving items: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve items: {str(e)}"
        )


@app.post("/api/items", response_model=ItemResponse, status_code=status.HTTP_201_CREATED, tags=["Items"])
async def create_item(item: ItemCreate):
    """
    Create a new item (sync operation)
    Fast endpoint with direct MongoDB insert
    """
    try:
        collection = get_items_collection()
        
        # Prepare document
        now = datetime.utcnow()
        doc = {
            "name": item.name,
            "description": item.description,
            "metadata": item.metadata,
            "created_at": now,
            "updated_at": now
        }
        
        # Insert into MongoDB
        result = collection.insert_one(doc)
        
        logger.info(f"Created item with ID: {result.inserted_id}")
        
        return ItemResponse(
            id=str(result.inserted_id),
            name=item.name,
            description=item.description,
            metadata=item.metadata,
            created_at=now,
            updated_at=now
        )
        
    except Exception as e:
        logger.error(f"Error creating item: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create item: {str(e)}"
        )


@app.get("/api/items/{item_id}", response_model=ItemResponse, tags=["Items"])
async def get_item(item_id: str):
    """Get single item by ID"""
    try:
        from bson import ObjectId
        collection = get_items_collection()
        
        doc = collection.find_one({"_id": ObjectId(item_id)})
        
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item {item_id} not found"
            )
        
        return ItemResponse(
            id=str(doc["_id"]),
            name=doc["name"],
            description=doc.get("description"),
            metadata=doc.get("metadata", {}),
            created_at=doc.get("created_at", datetime.utcnow()),
            updated_at=doc.get("updated_at", datetime.utcnow())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving item {item_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve item: {str(e)}"
        )


# ============================================================================
# ASYNC ENDPOINTS (Queue-based operations)
# ============================================================================

@app.post("/api/async/process", response_model=AsyncTaskResponse, status_code=status.HTTP_202_ACCEPTED, tags=["Async Tasks"])
async def submit_async_task(task_request: AsyncTaskRequest):
    """
    Submit heavy processing task to queue (async operation)
    Returns immediately with task_id
    Workers process the task in background
    """
    try:
        # Enqueue task to Celery via RabbitMQ
        task = process_heavy_task.apply_async(
            kwargs={
                "data": task_request.data,
                "iterations": task_request.iterations
            },
            priority={"low": 3, "normal": 5, "high": 9}.get(task_request.priority, 5)
        )
        
        logger.info(f"Submitted async task: {task.id}")
        
        return AsyncTaskResponse(
            task_id=task.id,
            status="PENDING",
            message="Task submitted successfully. Use /api/async/status/{task_id} to check progress."
        )
        
    except Exception as e:
        logger.error(f"Error submitting async task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit task: {str(e)}"
        )


@app.get("/api/async/status/{task_id}", response_model=TaskStatusResponse, tags=["Async Tasks"])
async def get_task_status(task_id: str):
    """
    Check status of async task
    Returns task status and result if completed
    """
    try:
        # Get task result from Celery
        task_result = celery_app.AsyncResult(task_id)
        
        response = TaskStatusResponse(
            task_id=task_id,
            status=task_result.status
        )
        
        if task_result.successful():
            response.result = task_result.result
        elif task_result.failed():
            response.error = str(task_result.info)
        elif task_result.state == 'PROGRESS':
            response.progress = task_result.info
        
        logger.info(f"Task {task_id} status: {task_result.status}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error checking task status {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check task status: {str(e)}"
        )


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "status_code": 500
        }
    )
