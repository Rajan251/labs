"""
Tenant management service.

Handles tenant registration, API key generation, webhook endpoint configuration,
and tenant-related operations.
"""
import secrets
import hashlib
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models import Tenant, WebhookEndpoint
from app.schemas import (
    TenantCreate, TenantUpdate, TenantResponse,
    WebhookEndpointCreate, WebhookEndpointUpdate
)


class TenantService:
    """Service for managing tenants and their webhook configurations."""
    
    @staticmethod
    def generate_api_key() -> str:
        """
        Generate a secure random API key.
        
        Returns:
            32-character hex API key
        """
        return secrets.token_hex(32)
    
    @staticmethod
    def generate_secret_key() -> str:
        """
        Generate a secure random secret key for HMAC signatures.
        
        Returns:
            64-character hex secret key
        """
        return secrets.token_hex(64)
    
    @staticmethod
    def create_tenant(db: Session, tenant_data: TenantCreate) -> Tenant:
        """
        Create a new tenant with auto-generated API and secret keys.
        
        Args:
            db: Database session
            tenant_data: Tenant creation data
            
        Returns:
            Created tenant instance
            
        Raises:
            IntegrityError: If email already exists
        """
        # Generate secure keys
        api_key = TenantService.generate_api_key()
        secret_key = TenantService.generate_secret_key()
        
        # Create tenant
        tenant = Tenant(
            name=tenant_data.name,
            email=tenant_data.email,
            api_key=api_key,
            secret_key=secret_key,
            rate_limit=tenant_data.rate_limit or 100,
            is_active=True
        )
        
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        
        return tenant
    
    @staticmethod
    def get_tenant_by_id(db: Session, tenant_id: int) -> Optional[Tenant]:
        """Get tenant by ID."""
        return db.query(Tenant).filter(Tenant.id == tenant_id).first()
    
    @staticmethod
    def get_tenant_by_api_key(db: Session, api_key: str) -> Optional[Tenant]:
        """Get tenant by API key."""
        return db.query(Tenant).filter(Tenant.api_key == api_key).first()
    
    @staticmethod
    def get_tenant_by_email(db: Session, email: str) -> Optional[Tenant]:
        """Get tenant by email."""
        return db.query(Tenant).filter(Tenant.email == email).first()
    
    @staticmethod
    def list_tenants(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False
    ) -> List[Tenant]:
        """
        List all tenants with pagination.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            active_only: If True, return only active tenants
            
        Returns:
            List of tenants
        """
        query = db.query(Tenant)
        
        if active_only:
            query = query.filter(Tenant.is_active == True)
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def update_tenant(
        db: Session,
        tenant_id: int,
        tenant_data: TenantUpdate
    ) -> Optional[Tenant]:
        """
        Update tenant information.
        
        Args:
            db: Database session
            tenant_id: Tenant ID
            tenant_data: Update data
            
        Returns:
            Updated tenant or None if not found
        """
        tenant = TenantService.get_tenant_by_id(db, tenant_id)
        if not tenant:
            return None
        
        # Update fields if provided
        update_data = tenant_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tenant, field, value)
        
        db.commit()
        db.refresh(tenant)
        
        return tenant
    
    @staticmethod
    def delete_tenant(db: Session, tenant_id: int) -> bool:
        """
        Delete a tenant and all associated data.
        
        Args:
            db: Database session
            tenant_id: Tenant ID
            
        Returns:
            True if deleted, False if not found
        """
        tenant = TenantService.get_tenant_by_id(db, tenant_id)
        if not tenant:
            return False
        
        db.delete(tenant)
        db.commit()
        
        return True
    
    @staticmethod
    def regenerate_secret_key(db: Session, tenant_id: int) -> Optional[str]:
        """
        Regenerate tenant's secret key.
        
        Args:
            db: Database session
            tenant_id: Tenant ID
            
        Returns:
            New secret key or None if tenant not found
        """
        tenant = TenantService.get_tenant_by_id(db, tenant_id)
        if not tenant:
            return None
        
        new_secret = TenantService.generate_secret_key()
        tenant.secret_key = new_secret
        
        db.commit()
        
        return new_secret
    
    # ========================================================================
    # Webhook Endpoint Management
    # ========================================================================
    
    @staticmethod
    def create_webhook_endpoint(
        db: Session,
        tenant_id: int,
        endpoint_data: WebhookEndpointCreate
    ) -> Optional[WebhookEndpoint]:
        """
        Create a webhook endpoint for a tenant.
        
        Args:
            db: Database session
            tenant_id: Tenant ID
            endpoint_data: Endpoint configuration
            
        Returns:
            Created endpoint or None if tenant not found
        """
        # Verify tenant exists
        tenant = TenantService.get_tenant_by_id(db, tenant_id)
        if not tenant:
            return None
        
        endpoint = WebhookEndpoint(
            tenant_id=tenant_id,
            url=str(endpoint_data.url),
            description=endpoint_data.description,
            event_types=endpoint_data.event_types,
            is_active=endpoint_data.is_active
        )
        
        db.add(endpoint)
        db.commit()
        db.refresh(endpoint)
        
        return endpoint
    
    @staticmethod
    def get_endpoint_by_id(db: Session, endpoint_id: int) -> Optional[WebhookEndpoint]:
        """Get webhook endpoint by ID."""
        return db.query(WebhookEndpoint).filter(
            WebhookEndpoint.id == endpoint_id
        ).first()
    
    @staticmethod
    def list_tenant_endpoints(
        db: Session,
        tenant_id: int,
        active_only: bool = False
    ) -> List[WebhookEndpoint]:
        """
        List all webhook endpoints for a tenant.
        
        Args:
            db: Database session
            tenant_id: Tenant ID
            active_only: If True, return only active endpoints
            
        Returns:
            List of webhook endpoints
        """
        query = db.query(WebhookEndpoint).filter(
            WebhookEndpoint.tenant_id == tenant_id
        )
        
        if active_only:
            query = query.filter(WebhookEndpoint.is_active == True)
        
        return query.all()
    
    @staticmethod
    def update_webhook_endpoint(
        db: Session,
        endpoint_id: int,
        endpoint_data: WebhookEndpointUpdate
    ) -> Optional[WebhookEndpoint]:
        """
        Update webhook endpoint configuration.
        
        Args:
            db: Database session
            endpoint_id: Endpoint ID
            endpoint_data: Update data
            
        Returns:
            Updated endpoint or None if not found
        """
        endpoint = TenantService.get_endpoint_by_id(db, endpoint_id)
        if not endpoint:
            return None
        
        # Update fields if provided
        update_data = endpoint_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "url" and value is not None:
                value = str(value)
            setattr(endpoint, field, value)
        
        db.commit()
        db.refresh(endpoint)
        
        return endpoint
    
    @staticmethod
    def delete_webhook_endpoint(db: Session, endpoint_id: int) -> bool:
        """
        Delete a webhook endpoint.
        
        Args:
            db: Database session
            endpoint_id: Endpoint ID
            
        Returns:
            True if deleted, False if not found
        """
        endpoint = TenantService.get_endpoint_by_id(db, endpoint_id)
        if not endpoint:
            return False
        
        db.delete(endpoint)
        db.commit()
        
        return True
    
    @staticmethod
    def get_endpoints_for_event(
        db: Session,
        tenant_id: int,
        event_type: str
    ) -> List[WebhookEndpoint]:
        """
        Get all active endpoints that should receive a specific event type.
        
        Args:
            db: Database session
            tenant_id: Tenant ID
            event_type: Event type to match
            
        Returns:
            List of matching webhook endpoints
        """
        endpoints = db.query(WebhookEndpoint).filter(
            WebhookEndpoint.tenant_id == tenant_id,
            WebhookEndpoint.is_active == True
        ).all()
        
        # Filter endpoints that subscribe to this event type
        # Empty event_types list means subscribe to all events
        matching_endpoints = [
            ep for ep in endpoints
            if not ep.event_types or event_type in ep.event_types
        ]
        
        return matching_endpoints
