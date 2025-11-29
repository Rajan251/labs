"""
Pydantic models for request/response validation
"""
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field
from datetime import datetime


class ItemCreate(BaseModel):
    """Request model for creating an item"""
    name: str = Field(..., min_length=1, max_length=100, description="Item name")
    description: Optional[str] = Field(None, max_length=500, description="Item description")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Sample Item",
                "description": "This is a sample item",
                "metadata": {"category": "test", "priority": "high"}
            }
        }


class ItemResponse(BaseModel):
    """Response model for item"""
    id: str = Field(..., description="Item ID")
    name: str
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "name": "Sample Item",
                "description": "This is a sample item",
                "metadata": {"category": "test"},
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }


class AsyncTaskRequest(BaseModel):
    """Request model for async task"""
    data: str = Field(..., min_length=1, description="Data to process")
    iterations: int = Field(default=10, ge=1, le=1000, description="Number of iterations")
    priority: Optional[str] = Field(default="normal", pattern="^(low|normal|high)$")

    class Config:
        json_schema_extra = {
            "example": {
                "data": "heavy processing task",
                "iterations": 100,
                "priority": "high"
            }
        }


class AsyncTaskResponse(BaseModel):
    """Response model for async task submission"""
    task_id: str = Field(..., description="Celery task ID")
    status: str = Field(default="PENDING", description="Initial task status")
    message: str = Field(default="Task submitted successfully")

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "a7f8c9d0-1234-5678-9abc-def012345678",
                "status": "PENDING",
                "message": "Task submitted successfully"
            }
        }


class TaskStatusResponse(BaseModel):
    """Response model for task status check"""
    task_id: str
    status: str = Field(..., description="Task status: PENDING, STARTED, SUCCESS, FAILURE, RETRY")
    result: Optional[Any] = Field(None, description="Task result if completed")
    error: Optional[str] = Field(None, description="Error message if failed")
    progress: Optional[Dict[str, Any]] = Field(None, description="Task progress information")

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "a7f8c9d0-1234-5678-9abc-def012345678",
                "status": "SUCCESS",
                "result": {"processed": 100, "output": "Task completed"},
                "error": None,
                "progress": {"current": 100, "total": 100}
            }
        }


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(default="healthy")
    timestamp: datetime
    services: Dict[str, str] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2024-01-01T00:00:00Z",
                "services": {
                    "mongodb": "connected",
                    "redis": "connected",
                    "rabbitmq": "connected"
                }
            }
        }
