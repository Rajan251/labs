"""
API endpoints for rollout management.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from ..database import get_db
from ..schemas import RolloutCreate, RolloutUpdate, RolloutResponse
from ..services.rollout_service import rollout_service
from ..models import Rollout

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/rollouts", tags=["rollouts"])


@router.post("/", response_model=RolloutResponse, status_code=status.HTTP_201_CREATED)
async def create_rollout(
    rollout_data: RolloutCreate,
    db: AsyncSession = Depends(get_db),
    user_id: Optional[str] = None
):
    """
    Create a new rollout strategy for a configuration.
    
    - **config_id**: Configuration ID
    - **strategy**: Rollout strategy (immediate, percentage, canary, etc.)
    - **config_data**: Strategy-specific configuration
    - **target_percentage**: Target percentage for gradual rollout
    - **target_users**: List of user IDs for targeting
    - **target_groups**: List of group IDs for targeting
    - **start_time**: Scheduled start time
    - **end_time**: Scheduled end time
    """
    try:
        rollout = await rollout_service.create_rollout(db, rollout_data, user_id)
        return rollout
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("create_rollout_error", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/{rollout_id}", response_model=RolloutResponse)
async def get_rollout(
    rollout_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific rollout by ID."""
    result = await db.execute(select(Rollout).where(Rollout.id == rollout_id))
    rollout = result.scalar_one_or_none()
    
    if not rollout:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rollout not found")
    
    return rollout


@router.put("/{rollout_id}", response_model=RolloutResponse)
async def update_rollout(
    rollout_id: int,
    update_data: RolloutUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: Optional[str] = None
):
    """
    Update rollout status or progress.
    
    - **status**: New status (pending, in_progress, completed, paused, cancelled, failed)
    - **current_percentage**: Current rollout percentage
    - **config_data**: Updated strategy configuration
    """
    try:
        rollout = await rollout_service.update_rollout(db, rollout_id, update_data, user_id)
        return rollout
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("update_rollout_error", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/config/{config_id}", response_model=list[RolloutResponse])
async def get_config_rollouts(
    config_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all rollouts for a specific configuration."""
    result = await db.execute(
        select(Rollout)
        .where(Rollout.config_id == config_id)
        .order_by(Rollout.created_at.desc())
    )
    rollouts = result.scalars().all()
    
    return rollouts
