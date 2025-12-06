"""
Dead Letter Queue API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.services.dlq_service import DLQService
from app.schemas import DLQEntryResponse, SuccessResponse
from app.workers.delivery_worker import retry_from_dlq

router = APIRouter(prefix="/api/v1/dlq", tags=["dead-letter-queue"])


@router.get("/", response_model=List[DLQEntryResponse])
def list_dlq_entries(
    tenant_id: Optional[int] = None,
    resolved: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List Dead Letter Queue entries.
    
    Query parameters:
    - tenant_id: Filter by tenant
    - resolved: Filter by resolution status
    - skip: Pagination offset
    - limit: Maximum results
    """
    entries = DLQService.list_dlq_entries(db, tenant_id, resolved, skip, limit)
    return entries


@router.get("/stats", response_model=dict)
def get_dlq_stats(
    tenant_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get DLQ statistics."""
    stats = DLQService.get_dlq_stats(db, tenant_id)
    return stats


@router.get("/{dlq_id}", response_model=DLQEntryResponse)
def get_dlq_entry(dlq_id: int, db: Session = Depends(get_db)):
    """Get DLQ entry by ID."""
    entry = DLQService.get_dlq_entry(db, dlq_id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DLQ entry not found"
        )
    return entry


@router.post("/{dlq_id}/retry", response_model=SuccessResponse)
def retry_dlq_entry(dlq_id: int, db: Session = Depends(get_db)):
    """
    Retry a failed event from the Dead Letter Queue.
    
    This will:
    1. Reset the event status to PENDING
    2. Mark the DLQ entry as resolved
    3. Trigger a new delivery attempt
    """
    entry = DLQService.get_dlq_entry(db, dlq_id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DLQ entry not found"
        )
    
    if entry.is_resolved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="DLQ entry already resolved"
        )
    
    # Trigger retry task
    retry_from_dlq.delay(dlq_id)
    
    return SuccessResponse(
        message=f"Retry initiated for DLQ entry {dlq_id}"
    )


@router.delete("/{dlq_id}", response_model=SuccessResponse)
def delete_dlq_entry(dlq_id: int, db: Session = Depends(get_db)):
    """Delete a DLQ entry."""
    success = DLQService.delete_dlq_entry(db, dlq_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DLQ entry not found"
        )
    
    return SuccessResponse(message="DLQ entry deleted successfully")
