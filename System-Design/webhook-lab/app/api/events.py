"""
Event publishing and management API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.services.tenant_service import TenantService
from app.services.event_service import EventService
from app.schemas import (
    EventPublish, EventResponse, EventStatusResponse,
    DeliveryAttemptResponse, SuccessResponse
)
from app.middleware.rate_limiter import rate_limiter
from app.workers.delivery_worker import deliver_webhook
from app.monitoring.metrics import (
    events_published_counter,
    events_duplicate_counter,
    rate_limit_hits_counter
)

router = APIRouter(prefix="/api/v1/events", tags=["events"])


def get_tenant_from_api_key(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: Session = Depends(get_db)
):
    """Dependency to authenticate tenant by API key."""
    tenant = TenantService.get_tenant_by_api_key(db, x_api_key)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    if not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant account is inactive"
        )
    
    return tenant


@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def publish_event(
    event_data: EventPublish,
    tenant = Depends(get_tenant_from_api_key),
    db: Session = Depends(get_db)
):
    """
    Publish an event to the webhook platform.
    
    Requires X-API-Key header for authentication.
    Events are idempotent based on event_id.
    """
    # Check rate limit
    allowed, rate_info = rate_limiter.check_rate_limit(
        tenant.id,
        tenant.rate_limit
    )
    
    if not allowed:
        # Record rate limit hit
        rate_limit_hits_counter.labels(tenant_id=tenant.id).inc()
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(rate_info["limit"]),
                "X-RateLimit-Remaining": str(rate_info["remaining"]),
                "X-RateLimit-Reset": str(rate_info["reset_at"]),
                "Retry-After": str(rate_info.get("retry_after", 60))
            }
        )
    
    # Create event (with idempotency check)
    idempotency_key = EventService.generate_idempotency_key(
        event_data.event_id,
        tenant.id
    )
    
    is_duplicate = EventService.check_duplicate(db, idempotency_key)
    
    event = EventService.create_event(db, tenant.id, event_data)
    
    if is_duplicate:
        # Record duplicate metric
        events_duplicate_counter.labels(tenant_id=tenant.id).inc()
        
        # Return existing event (idempotent)
        return event
    
    # Record event published metric
    events_published_counter.labels(
        tenant_id=tenant.id,
        event_type=event_data.event_type
    ).inc()
    
    # Get matching webhook endpoints
    endpoints = EventService.get_endpoints_for_event(db, event)
    
    # Trigger delivery for each endpoint
    for endpoint in endpoints:
        deliver_webhook.delay(
            event_id=event.id,
            endpoint_id=endpoint.id,
            endpoint_url=endpoint.url,
            secret_key=tenant.secret_key,
            payload=event.payload,
            attempt_number=1
        )
    
    return event


@router.get("/{event_id}/status", response_model=dict)
def get_event_status(
    event_id: str,
    tenant = Depends(get_tenant_from_api_key),
    db: Session = Depends(get_db)
):
    """Get delivery status for an event."""
    status_info = EventService.get_event_delivery_status(db, event_id, tenant.id)
    
    if not status_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    return status_info


@router.get("/", response_model=List[EventResponse])
def list_events(
    event_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    tenant = Depends(get_tenant_from_api_key),
    db: Session = Depends(get_db)
):
    """List events for the authenticated tenant."""
    events = EventService.list_events(
        db,
        tenant_id=tenant.id,
        event_type=event_type,
        skip=skip,
        limit=limit
    )
    return events


@router.get("/{event_id}/attempts", response_model=List[DeliveryAttemptResponse])
def get_delivery_attempts(
    event_id: str,
    tenant = Depends(get_tenant_from_api_key),
    db: Session = Depends(get_db)
):
    """Get all delivery attempts for an event."""
    event = EventService.get_event_by_external_id(db, event_id, tenant.id)
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    attempts = EventService.get_delivery_attempts(db, event.id)
    return attempts
