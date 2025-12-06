"""
Tenant management API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.services.tenant_service import TenantService
from app.schemas import (
    TenantCreate, TenantUpdate, TenantResponse, TenantListResponse,
    WebhookEndpointCreate, WebhookEndpointUpdate, WebhookEndpointResponse,
    SuccessResponse
)
from app.monitoring.metrics import active_tenants_gauge, active_endpoints_gauge

router = APIRouter(prefix="/api/v1/tenants", tags=["tenants"])


@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
def create_tenant(
    tenant_data: TenantCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new tenant.
    
    Returns API key and secret key in response. Store these securely!
    """
    try:
        tenant = TenantService.create_tenant(db, tenant_data)
        
        # Update metrics
        active_count = len(TenantService.list_tenants(db, active_only=True))
        active_tenants_gauge.set(active_count)
        
        return tenant
    
    except Exception as e:
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/", response_model=List[TenantListResponse])
def list_tenants(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    """List all tenants with pagination."""
    tenants = TenantService.list_tenants(db, skip, limit, active_only)
    return tenants


@router.get("/{tenant_id}", response_model=TenantListResponse)
def get_tenant(tenant_id: int, db: Session = Depends(get_db)):
    """Get tenant by ID (without sensitive data)."""
    tenant = TenantService.get_tenant_by_id(db, tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    return tenant


@router.patch("/{tenant_id}", response_model=TenantListResponse)
def update_tenant(
    tenant_id: int,
    tenant_data: TenantUpdate,
    db: Session = Depends(get_db)
):
    """Update tenant information."""
    tenant = TenantService.update_tenant(db, tenant_id, tenant_data)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    return tenant


@router.delete("/{tenant_id}", response_model=SuccessResponse)
def delete_tenant(tenant_id: int, db: Session = Depends(get_db)):
    """Delete a tenant and all associated data."""
    success = TenantService.delete_tenant(db, tenant_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    # Update metrics
    active_count = len(TenantService.list_tenants(db, active_only=True))
    active_tenants_gauge.set(active_count)
    
    return SuccessResponse(message="Tenant deleted successfully")


@router.post("/{tenant_id}/regenerate-secret", response_model=dict)
def regenerate_secret_key(tenant_id: int, db: Session = Depends(get_db)):
    """
    Regenerate tenant's secret key.
    
    WARNING: This will invalidate all existing webhook signatures!
    """
    new_secret = TenantService.regenerate_secret_key(db, tenant_id)
    if not new_secret:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    return {
        "success": True,
        "message": "Secret key regenerated",
        "secret_key": new_secret
    }


# ============================================================================
# Webhook Endpoint Management
# ============================================================================

@router.post(
    "/{tenant_id}/endpoints",
    response_model=WebhookEndpointResponse,
    status_code=status.HTTP_201_CREATED
)
def create_webhook_endpoint(
    tenant_id: int,
    endpoint_data: WebhookEndpointCreate,
    db: Session = Depends(get_db)
):
    """Create a webhook endpoint for a tenant."""
    endpoint = TenantService.create_webhook_endpoint(db, tenant_id, endpoint_data)
    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    # Update metrics
    endpoints = db.query(db.query(TenantService.list_tenant_endpoints(db, tenant_id, active_only=True)).count()).scalar()
    active_endpoints_gauge.set(endpoints)
    
    return endpoint


@router.get("/{tenant_id}/endpoints", response_model=List[WebhookEndpointResponse])
def list_webhook_endpoints(
    tenant_id: int,
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    """List all webhook endpoints for a tenant."""
    endpoints = TenantService.list_tenant_endpoints(db, tenant_id, active_only)
    return endpoints


@router.get("/endpoints/{endpoint_id}", response_model=WebhookEndpointResponse)
def get_webhook_endpoint(endpoint_id: int, db: Session = Depends(get_db)):
    """Get webhook endpoint by ID."""
    endpoint = TenantService.get_endpoint_by_id(db, endpoint_id)
    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endpoint not found"
        )
    return endpoint


@router.patch("/endpoints/{endpoint_id}", response_model=WebhookEndpointResponse)
def update_webhook_endpoint(
    endpoint_id: int,
    endpoint_data: WebhookEndpointUpdate,
    db: Session = Depends(get_db)
):
    """Update webhook endpoint configuration."""
    endpoint = TenantService.update_webhook_endpoint(db, endpoint_id, endpoint_data)
    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endpoint not found"
        )
    return endpoint


@router.delete("/endpoints/{endpoint_id}", response_model=SuccessResponse)
def delete_webhook_endpoint(endpoint_id: int, db: Session = Depends(get_db)):
    """Delete a webhook endpoint."""
    success = TenantService.delete_webhook_endpoint(db, endpoint_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endpoint not found"
        )
    
    return SuccessResponse(message="Endpoint deleted successfully")
