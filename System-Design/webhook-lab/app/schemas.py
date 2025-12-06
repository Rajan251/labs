"""
Pydantic schemas for request/response validation and serialization.

Schemas are organized by domain:
- Tenant schemas
- Webhook endpoint schemas
- Event schemas
- Delivery attempt schemas
- DLQ schemas
"""
from pydantic import BaseModel, EmailStr, HttpUrl, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class DeliveryStatus(str, Enum):
    """Status of webhook delivery."""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


# ============================================================================
# Tenant Schemas
# ============================================================================

class TenantCreate(BaseModel):
    """Schema for creating a new tenant."""
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    rate_limit: Optional[int] = Field(default=100, ge=1, le=10000)


class TenantUpdate(BaseModel):
    """Schema for updating tenant information."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    rate_limit: Optional[int] = Field(None, ge=1, le=10000)
    is_active: Optional[bool] = None


class TenantResponse(BaseModel):
    """Schema for tenant response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    email: str
    api_key: str
    secret_key: str  # Include in creation response only
    is_active: bool
    rate_limit: int
    created_at: datetime
    updated_at: Optional[datetime] = None


class TenantListResponse(BaseModel):
    """Schema for tenant list response (without sensitive data)."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    email: str
    is_active: bool
    rate_limit: int
    created_at: datetime


# ============================================================================
# Webhook Endpoint Schemas
# ============================================================================

class WebhookEndpointCreate(BaseModel):
    """Schema for creating a webhook endpoint."""
    url: HttpUrl
    description: Optional[str] = Field(None, max_length=500)
    event_types: List[str] = Field(default_factory=list)
    is_active: bool = True


class WebhookEndpointUpdate(BaseModel):
    """Schema for updating a webhook endpoint."""
    url: Optional[HttpUrl] = None
    description: Optional[str] = Field(None, max_length=500)
    event_types: Optional[List[str]] = None
    is_active: Optional[bool] = None


class WebhookEndpointResponse(BaseModel):
    """Schema for webhook endpoint response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    tenant_id: int
    url: str
    description: Optional[str] = None
    event_types: List[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


# ============================================================================
# Event Schemas
# ============================================================================

class EventPublish(BaseModel):
    """Schema for publishing an event."""
    event_id: str = Field(..., min_length=1, max_length=255)
    event_type: str = Field(..., min_length=1, max_length=255)
    payload: Dict[str, Any]


class EventResponse(BaseModel):
    """Schema for event response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    event_id: str
    tenant_id: int
    event_type: str
    payload: Dict[str, Any]
    status: DeliveryStatus
    idempotency_key: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class EventStatusResponse(BaseModel):
    """Schema for event status check."""
    event_id: str
    status: DeliveryStatus
    total_attempts: int
    last_attempt_at: Optional[datetime] = None
    next_retry_at: Optional[datetime] = None


# ============================================================================
# Delivery Attempt Schemas
# ============================================================================

class DeliveryAttemptResponse(BaseModel):
    """Schema for delivery attempt response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    event_id: int
    endpoint_id: int
    attempt_number: int
    status: DeliveryStatus
    http_status_code: Optional[int] = None
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    attempted_at: datetime
    next_retry_at: Optional[datetime] = None


# ============================================================================
# Dead Letter Queue Schemas
# ============================================================================

class DLQEntryResponse(BaseModel):
    """Schema for DLQ entry response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    event_id: int
    tenant_id: int
    endpoint_id: int
    event_type: str
    payload: Dict[str, Any]
    total_attempts: int
    last_error: Optional[str] = None
    last_http_status: Optional[int] = None
    is_resolved: bool
    created_at: datetime
    resolved_at: Optional[datetime] = None


class DLQRetryRequest(BaseModel):
    """Schema for retrying a DLQ entry."""
    dlq_id: int


# ============================================================================
# Common Response Schemas
# ============================================================================

class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Generic error response."""
    success: bool = False
    error: str
    detail: Optional[str] = None


class PaginatedResponse(BaseModel):
    """Generic paginated response."""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
