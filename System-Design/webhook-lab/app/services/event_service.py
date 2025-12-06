"""
Event service for event ingestion, validation, and routing.

Handles event publishing, idempotency checking, and routing to appropriate
webhook endpoints.
"""
import hashlib
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models import Event, DeliveryAttempt, DeliveryStatus, Tenant
from app.schemas import EventPublish, EventResponse
from app.services.tenant_service import TenantService


class EventService:
    """Service for managing events and their delivery lifecycle."""
    
    @staticmethod
    def generate_idempotency_key(event_id: str, tenant_id: int) -> str:
        """
        Generate idempotency key from event ID and tenant ID.
        
        Args:
            event_id: External event ID
            tenant_id: Tenant ID
            
        Returns:
            SHA256 hash as idempotency key
        """
        key_string = f"{event_id}:{tenant_id}"
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    @staticmethod
    def check_duplicate(db: Session, idempotency_key: str) -> bool:
        """
        Check if event with this idempotency key already exists.
        
        Args:
            db: Database session
            idempotency_key: Idempotency key to check
            
        Returns:
            True if duplicate exists, False otherwise
        """
        existing = db.query(Event).filter(
            Event.idempotency_key == idempotency_key
        ).first()
        
        return existing is not None
    
    @staticmethod
    def create_event(
        db: Session,
        tenant_id: int,
        event_data: EventPublish
    ) -> Optional[Event]:
        """
        Create a new event with idempotency checking.
        
        Args:
            db: Database session
            tenant_id: Tenant ID
            event_data: Event data
            
        Returns:
            Created event or existing event if duplicate
        """
        # Generate idempotency key
        idempotency_key = EventService.generate_idempotency_key(
            event_data.event_id,
            tenant_id
        )
        
        # Check for duplicates
        existing_event = db.query(Event).filter(
            Event.idempotency_key == idempotency_key
        ).first()
        
        if existing_event:
            # Return existing event (idempotent behavior)
            return existing_event
        
        # Create new event
        event = Event(
            event_id=event_data.event_id,
            tenant_id=tenant_id,
            event_type=event_data.event_type,
            payload=event_data.payload,
            idempotency_key=idempotency_key,
            status=DeliveryStatus.PENDING
        )
        
        db.add(event)
        db.commit()
        db.refresh(event)
        
        return event
    
    @staticmethod
    def get_event_by_id(db: Session, event_id: int) -> Optional[Event]:
        """Get event by internal ID."""
        return db.query(Event).filter(Event.id == event_id).first()
    
    @staticmethod
    def get_event_by_external_id(
        db: Session,
        event_id: str,
        tenant_id: int
    ) -> Optional[Event]:
        """Get event by external event ID and tenant."""
        return db.query(Event).filter(
            Event.event_id == event_id,
            Event.tenant_id == tenant_id
        ).first()
    
    @staticmethod
    def list_events(
        db: Session,
        tenant_id: Optional[int] = None,
        event_type: Optional[str] = None,
        status: Optional[DeliveryStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Event]:
        """
        List events with filtering and pagination.
        
        Args:
            db: Database session
            tenant_id: Filter by tenant ID
            event_type: Filter by event type
            status: Filter by delivery status
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of events
        """
        query = db.query(Event)
        
        if tenant_id:
            query = query.filter(Event.tenant_id == tenant_id)
        
        if event_type:
            query = query.filter(Event.event_type == event_type)
        
        if status:
            query = query.filter(Event.status == status)
        
        return query.order_by(desc(Event.created_at)).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_event_status(
        db: Session,
        event_id: int,
        status: DeliveryStatus
    ) -> Optional[Event]:
        """
        Update event delivery status.
        
        Args:
            db: Database session
            event_id: Event ID
            status: New status
            
        Returns:
            Updated event or None if not found
        """
        event = EventService.get_event_by_id(db, event_id)
        if not event:
            return None
        
        event.status = status
        db.commit()
        db.refresh(event)
        
        return event
    
    @staticmethod
    def get_event_delivery_status(
        db: Session,
        event_id: str,
        tenant_id: int
    ) -> Optional[dict]:
        """
        Get detailed delivery status for an event.
        
        Args:
            db: Database session
            event_id: External event ID
            tenant_id: Tenant ID
            
        Returns:
            Dictionary with event status details
        """
        event = EventService.get_event_by_external_id(db, event_id, tenant_id)
        if not event:
            return None
        
        # Get latest delivery attempt
        latest_attempt = db.query(DeliveryAttempt).filter(
            DeliveryAttempt.event_id == event.id
        ).order_by(desc(DeliveryAttempt.attempted_at)).first()
        
        return {
            "event_id": event.event_id,
            "status": event.status,
            "total_attempts": len(event.delivery_attempts),
            "last_attempt_at": latest_attempt.attempted_at if latest_attempt else None,
            "next_retry_at": latest_attempt.next_retry_at if latest_attempt else None,
            "last_error": latest_attempt.error_message if latest_attempt else None
        }
    
    @staticmethod
    def get_endpoints_for_event(
        db: Session,
        event: Event
    ) -> List:
        """
        Get all webhook endpoints that should receive this event.
        
        Args:
            db: Database session
            event: Event instance
            
        Returns:
            List of webhook endpoints
        """
        return TenantService.get_endpoints_for_event(
            db,
            event.tenant_id,
            event.event_type
        )
    
    @staticmethod
    def record_delivery_attempt(
        db: Session,
        event_id: int,
        endpoint_id: int,
        attempt_number: int,
        status: DeliveryStatus,
        http_status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        error_message: Optional[str] = None,
        duration_ms: Optional[int] = None,
        next_retry_at: Optional[datetime] = None
    ) -> DeliveryAttempt:
        """
        Record a delivery attempt for an event.
        
        Args:
            db: Database session
            event_id: Event ID
            endpoint_id: Webhook endpoint ID
            attempt_number: Attempt number (1-indexed)
            status: Delivery status
            http_status_code: HTTP response status code
            response_body: HTTP response body
            error_message: Error message if failed
            duration_ms: Request duration in milliseconds
            next_retry_at: Scheduled retry time
            
        Returns:
            Created delivery attempt
        """
        attempt = DeliveryAttempt(
            event_id=event_id,
            endpoint_id=endpoint_id,
            attempt_number=attempt_number,
            status=status,
            http_status_code=http_status_code,
            response_body=response_body,
            error_message=error_message,
            duration_ms=duration_ms,
            next_retry_at=next_retry_at
        )
        
        db.add(attempt)
        db.commit()
        db.refresh(attempt)
        
        return attempt
    
    @staticmethod
    def get_delivery_attempts(
        db: Session,
        event_id: int
    ) -> List[DeliveryAttempt]:
        """
        Get all delivery attempts for an event.
        
        Args:
            db: Database session
            event_id: Event ID
            
        Returns:
            List of delivery attempts ordered by attempt number
        """
        return db.query(DeliveryAttempt).filter(
            DeliveryAttempt.event_id == event_id
        ).order_by(DeliveryAttempt.attempt_number).all()
