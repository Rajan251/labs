"""
API endpoints for audit log queries.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import structlog

from ..database import get_db
from ..schemas import AuditLogResponse, AuditLogListResponse
from ..models import AuditLog

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/", response_model=AuditLogListResponse)
async def get_audit_logs(
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[int] = Query(None),
    user_id: Optional[str] = Query(None),
    app_id: Optional[str] = Query(None),
    environment: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Query audit logs with filtering.
    
    - **entity_type**: Filter by entity type (config, version, rollout)
    - **entity_id**: Filter by entity ID
    - **user_id**: Filter by user who made the change
    - **app_id**: Filter by application ID
    - **environment**: Filter by environment
    - **action**: Filter by action (create, update, delete, rollback)
    - **start_date**: Filter by start date
    - **end_date**: Filter by end date
    - **page**: Page number
    - **page_size**: Items per page
    """
    try:
        # Build query
        query = select(AuditLog)
        
        if entity_type:
            query = query.where(AuditLog.entity_type == entity_type)
        if entity_id:
            query = query.where(AuditLog.entity_id == entity_id)
        if user_id:
            query = query.where(AuditLog.user_id == user_id)
        if app_id:
            query = query.where(AuditLog.app_id == app_id)
        if environment:
            query = query.where(AuditLog.environment == environment)
        if action:
            query = query.where(AuditLog.action == action)
        if start_date:
            query = query.where(AuditLog.timestamp >= start_date)
        if end_date:
            query = query.where(AuditLog.timestamp <= end_date)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Get paginated results
        query = query.order_by(AuditLog.timestamp.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        logs = result.scalars().all()
        
        return AuditLogListResponse(
            total=total,
            page=page,
            page_size=page_size,
            logs=logs
        )
    except Exception as e:
        logger.error("get_audit_logs_error", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific audit log entry by ID."""
    result = await db.execute(select(AuditLog).where(AuditLog.id == log_id))
    log = result.scalar_one_or_none()
    
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit log not found")
    
    return log
