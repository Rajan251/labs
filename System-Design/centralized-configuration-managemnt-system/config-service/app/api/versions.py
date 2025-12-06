"""
API endpoints for version management and rollback.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from ..database import get_db
from ..schemas import VersionResponse, RollbackRequest
from ..services.config_service import config_service
from ..models import ConfigVersion, Config

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/versions", tags=["versions"])


@router.get("/config/{config_id}", response_model=list[VersionResponse])
async def get_config_versions(
    config_id: int,
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Get version history for a configuration.
    
    - **config_id**: Configuration ID
    - **limit**: Maximum number of versions to return
    """
    # Verify config exists
    config_result = await db.execute(select(Config).where(Config.id == config_id))
    config = config_result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Configuration not found")
    
    # Get versions
    result = await db.execute(
        select(ConfigVersion)
        .where(ConfigVersion.config_id == config_id)
        .order_by(ConfigVersion.version.desc())
        .limit(limit)
    )
    versions = result.scalars().all()
    
    return versions


@router.post("/rollback/{config_id}", response_model=dict)
async def rollback_config(
    config_id: int,
    rollback_data: RollbackRequest,
    db: AsyncSession = Depends(get_db),
    user_id: Optional[str] = None
):
    """
    Rollback a configuration to a previous version.
    
    - **config_id**: Configuration ID
    - **target_version**: Version number to rollback to
    - **rollback_reason**: Reason for rollback
    """
    try:
        config = await config_service.rollback_config(
            db,
            config_id,
            rollback_data.target_version,
            user_id or rollback_data.rollback_by,
            rollback_data.rollback_reason
        )
        
        return {
            "message": "Configuration rolled back successfully",
            "config_id": config.id,
            "current_version": config.version,
            "rolled_back_to": rollback_data.target_version
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("rollback_error", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
