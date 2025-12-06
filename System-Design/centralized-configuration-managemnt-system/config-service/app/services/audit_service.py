"""
Audit logging service for tracking all configuration changes.
"""
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import structlog

from ..models import AuditLog, EnvironmentType
from ..config import settings

logger = structlog.get_logger(__name__)


class AuditService:
    """Service for audit logging."""
    
    async def log_change(
        self,
        db: AsyncSession,
        entity_type: str,
        entity_id: int,
        action: str,
        user_id: Optional[str] = None,
        app_id: Optional[str] = None,
        environment: Optional[EnvironmentType] = None,
        changes: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """
        Log a configuration change.
        
        Args:
            db: Database session
            entity_type: Type of entity (config, version, rollout)
            entity_id: Entity ID
            action: Action performed (create, update, delete, rollback)
            user_id: User who performed the action
            app_id: Application ID
            environment: Environment
            changes: Before/after values
            metadata: Additional context
            ip_address: User's IP address
            user_agent: User's user agent
            
        Returns:
            Created audit log entry
        """
        if not settings.enable_audit_logging:
            logger.debug("audit_logging_disabled")
            return None
        
        audit_log = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            changes=changes,
            metadata=metadata,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            app_id=app_id,
            environment=environment,
            timestamp=datetime.utcnow(),
        )
        
        db.add(audit_log)
        await db.flush()
        
        logger.info(
            "audit_logged",
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            user_id=user_id,
        )
        
        return audit_log


# Global service instance
audit_service = AuditService()
