"""
SQLAlchemy database models for the webhook platform.

Models:
- Tenant: Represents a tenant/customer using the webhook platform
- WebhookEndpoint: Webhook URLs configured by tenants
- Event: Events published to the platform
- DeliveryAttempt: Individual delivery attempts for events
- DeadLetterQueue: Failed events that exceeded retry limits
"""
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, 
    ForeignKey, JSON, Enum as SQLEnum, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.database import Base


class DeliveryStatus(str, enum.Enum):
    """Status of webhook delivery attempts."""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


class Tenant(Base):
    """
    Tenant model representing customers using the webhook platform.
    
    Each tenant can have multiple webhook endpoints and receives events
    based on their subscriptions.
    """
    __tablename__ = "tenants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    api_key = Column(String(255), unique=True, nullable=False, index=True)
    secret_key = Column(String(255), nullable=False)  # For HMAC signature
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Rate limiting
    rate_limit = Column(Integer, default=100)  # Events per minute
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    endpoints = relationship("WebhookEndpoint", back_populates="tenant", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="tenant")


class WebhookEndpoint(Base):
    """
    Webhook endpoint configuration for tenants.
    
    Each tenant can configure multiple endpoints for different event types.
    """
    __tablename__ = "webhook_endpoints"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    url = Column(String(2048), nullable=False)
    description = Column(String(500))
    
    # Event filtering
    event_types = Column(JSON, default=list)  # List of event types to receive
    
    # Configuration
    is_active = Column(Boolean, default=True, nullable=False)
    retry_config = Column(JSON, default=dict)  # Custom retry configuration
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tenant = relationship("Tenant", back_populates="endpoints")
    
    # Indexes
    __table_args__ = (
        Index('idx_tenant_active', 'tenant_id', 'is_active'),
    )


class Event(Base):
    """
    Event model representing events published to the platform.
    
    Events are routed to appropriate tenant endpoints based on event type
    and tenant subscriptions.
    """
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(255), unique=True, nullable=False, index=True)  # External event ID
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    event_type = Column(String(255), nullable=False, index=True)
    
    # Event data
    payload = Column(JSON, nullable=False)
    
    # Idempotency
    idempotency_key = Column(String(255), unique=True, index=True)  # event_id + tenant_id hash
    
    # Status tracking
    status = Column(SQLEnum(DeliveryStatus), default=DeliveryStatus.PENDING, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tenant = relationship("Tenant", back_populates="events")
    delivery_attempts = relationship("DeliveryAttempt", back_populates="event", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_tenant_event_type', 'tenant_id', 'event_type'),
        Index('idx_status_created', 'status', 'created_at'),
    )


class DeliveryAttempt(Base):
    """
    Delivery attempt tracking for webhook events.
    
    Records each attempt to deliver an event to a webhook endpoint,
    including response status, timing, and error details.
    """
    __tablename__ = "delivery_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    endpoint_id = Column(Integer, ForeignKey("webhook_endpoints.id"), nullable=False)
    
    # Attempt details
    attempt_number = Column(Integer, nullable=False)
    status = Column(SQLEnum(DeliveryStatus), nullable=False)
    
    # HTTP details
    http_status_code = Column(Integer)
    response_body = Column(Text)
    error_message = Column(Text)
    
    # Timing
    duration_ms = Column(Integer)  # Request duration in milliseconds
    attempted_at = Column(DateTime(timezone=True), server_default=func.now())
    next_retry_at = Column(DateTime(timezone=True))  # Scheduled retry time
    
    # Relationships
    event = relationship("Event", back_populates="delivery_attempts")
    
    # Indexes
    __table_args__ = (
        Index('idx_event_attempt', 'event_id', 'attempt_number'),
        Index('idx_next_retry', 'next_retry_at'),
    )


class DeadLetterQueue(Base):
    """
    Dead Letter Queue for events that failed all retry attempts.
    
    Stores failed events for manual inspection and retry.
    """
    __tablename__ = "dead_letter_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    endpoint_id = Column(Integer, ForeignKey("webhook_endpoints.id"), nullable=False)
    
    # Failure details
    total_attempts = Column(Integer, nullable=False)
    last_error = Column(Text)
    last_http_status = Column(Integer)
    
    # Event snapshot
    event_type = Column(String(255), nullable=False)
    payload = Column(JSON, nullable=False)
    
    # Status
    is_resolved = Column(Boolean, default=False, nullable=False)
    resolved_at = Column(DateTime(timezone=True))
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_tenant_resolved', 'tenant_id', 'is_resolved'),
        Index('idx_created_at', 'created_at'),
    )
