"""
Dead Letter Queue (DLQ) service for managing failed webhook deliveries.

Handles storage, retrieval, and retry of events that failed all delivery attempts.
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models import DeadLetterQueue, Event, WebhookEndpoint, DeliveryAttempt


class DLQService:
    """Service for managing dead letter queue entries."""
    
    @staticmethod
    def add_to_dlq(
        db: Session,
        event_id: int,
        endpoint_id: int,
        total_attempts: int,
        last_error: Optional[str] = None,
        last_http_status: Optional[int] = None
    ) -> DeadLetterQueue:
        """
        Add a failed event to the dead letter queue.
        
        Args:
            db: Database session
            event_id: Event ID
            endpoint_id: Webhook endpoint ID
            total_attempts: Total number of delivery attempts
            last_error: Last error message
            last_http_status: Last HTTP status code
            
        Returns:
            Created DLQ entry
        """
        # Get event details
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise ValueError(f"Event {event_id} not found")
        
        # Create DLQ entry
        dlq_entry = DeadLetterQueue(
            event_id=event_id,
            tenant_id=event.tenant_id,
            endpoint_id=endpoint_id,
            total_attempts=total_attempts,
            last_error=last_error,
            last_http_status=last_http_status,
            event_type=event.event_type,
            payload=event.payload,
            is_resolved=False
        )
        
        db.add(dlq_entry)
        db.commit()
        db.refresh(dlq_entry)
        
        return dlq_entry
    
    @staticmethod
    def get_dlq_entry(db: Session, dlq_id: int) -> Optional[DeadLetterQueue]:
        """Get DLQ entry by ID."""
        return db.query(DeadLetterQueue).filter(
            DeadLetterQueue.id == dlq_id
        ).first()
    
    @staticmethod
    def list_dlq_entries(
        db: Session,
        tenant_id: Optional[int] = None,
        resolved: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[DeadLetterQueue]:
        """
        List DLQ entries with filtering and pagination.
        
        Args:
            db: Database session
            tenant_id: Filter by tenant ID
            resolved: Filter by resolution status
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of DLQ entries
        """
        query = db.query(DeadLetterQueue)
        
        if tenant_id is not None:
            query = query.filter(DeadLetterQueue.tenant_id == tenant_id)
        
        if resolved is not None:
            query = query.filter(DeadLetterQueue.is_resolved == resolved)
        
        return query.order_by(desc(DeadLetterQueue.created_at)).offset(skip).limit(limit).all()
    
    @staticmethod
    def mark_as_resolved(
        db: Session,
        dlq_id: int
    ) -> Optional[DeadLetterQueue]:
        """
        Mark a DLQ entry as resolved.
        
        Args:
            db: Database session
            dlq_id: DLQ entry ID
            
        Returns:
            Updated DLQ entry or None if not found
        """
        dlq_entry = DLQService.get_dlq_entry(db, dlq_id)
        if not dlq_entry:
            return None
        
        dlq_entry.is_resolved = True
        dlq_entry.resolved_at = datetime.utcnow()
        
        db.commit()
        db.refresh(dlq_entry)
        
        return dlq_entry
    
    @staticmethod
    def get_dlq_stats(db: Session, tenant_id: Optional[int] = None) -> dict:
        """
        Get DLQ statistics.
        
        Args:
            db: Database session
            tenant_id: Filter by tenant ID (optional)
            
        Returns:
            Dictionary with DLQ statistics
        """
        query = db.query(DeadLetterQueue)
        
        if tenant_id is not None:
            query = query.filter(DeadLetterQueue.tenant_id == tenant_id)
        
        total = query.count()
        unresolved = query.filter(DeadLetterQueue.is_resolved == False).count()
        resolved = query.filter(DeadLetterQueue.is_resolved == True).count()
        
        return {
            "total": total,
            "unresolved": unresolved,
            "resolved": resolved
        }
    
    @staticmethod
    def delete_dlq_entry(db: Session, dlq_id: int) -> bool:
        """
        Delete a DLQ entry.
        
        Args:
            db: Database session
            dlq_id: DLQ entry ID
            
        Returns:
            True if deleted, False if not found
        """
        dlq_entry = DLQService.get_dlq_entry(db, dlq_id)
        if not dlq_entry:
            return False
        
        db.delete(dlq_entry)
        db.commit()
        
        return True
