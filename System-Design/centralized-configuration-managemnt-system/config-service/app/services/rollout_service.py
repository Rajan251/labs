"""
Rollout service for managing gradual configuration deployments.
Supports percentage-based, canary, feature flags, and time-based rollouts.
"""
from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import structlog

from ..models import Rollout, RolloutStrategy, RolloutStatus
from ..schemas import RolloutCreate, RolloutUpdate
from .audit_service import audit_service

logger = structlog.get_logger(__name__)


class RolloutService:
    """Service for rollout management."""
    
    async def create_rollout(
        self,
        db: AsyncSession,
        rollout_data: RolloutCreate,
        user_id: Optional[str] = None
    ) -> Rollout:
        """
        Create a new rollout strategy.
        
        Args:
            db: Database session
            rollout_data: Rollout configuration
            user_id: User creating the rollout
            
        Returns:
            Created rollout
        """
        rollout = Rollout(
            config_id=rollout_data.config_id,
            strategy=rollout_data.strategy,
            status=RolloutStatus.PENDING,
            config_data=rollout_data.config_data,
            current_percentage=0,
            target_percentage=rollout_data.target_percentage,
            target_users=rollout_data.target_users,
            target_groups=rollout_data.target_groups,
            start_time=rollout_data.start_time,
            end_time=rollout_data.end_time,
            created_by=user_id or rollout_data.created_by,
        )
        
        db.add(rollout)
        await db.commit()
        await db.refresh(rollout)
        
        # Audit log
        await audit_service.log_change(
            db,
            entity_type="rollout",
            entity_id=rollout.id,
            action="create",
            user_id=user_id,
            metadata={"strategy": rollout_data.strategy.value},
        )
        
        logger.info("rollout_created", rollout_id=rollout.id, strategy=rollout_data.strategy)
        return rollout
    
    async def update_rollout(
        self,
        db: AsyncSession,
        rollout_id: int,
        update_data: RolloutUpdate,
        user_id: Optional[str] = None
    ) -> Rollout:
        """
        Update rollout status or progress.
        
        Args:
            db: Database session
            rollout_id: Rollout ID
            update_data: Update data
            user_id: User updating the rollout
            
        Returns:
            Updated rollout
        """
        result = await db.execute(select(Rollout).where(Rollout.id == rollout_id))
        rollout = result.scalar_one_or_none()
        
        if not rollout:
            raise ValueError(f"Rollout not found: {rollout_id}")
        
        changes = {}
        
        if update_data.status is not None:
            changes["status"] = {"old": rollout.status.value, "new": update_data.status.value}
            rollout.status = update_data.status
        
        if update_data.current_percentage is not None:
            changes["percentage"] = {"old": rollout.current_percentage, "new": update_data.current_percentage}
            rollout.current_percentage = update_data.current_percentage
        
        if update_data.config_data is not None:
            rollout.config_data = update_data.config_data
        
        await db.commit()
        await db.refresh(rollout)
        
        # Audit log
        await audit_service.log_change(
            db,
            entity_type="rollout",
            entity_id=rollout.id,
            action="update",
            user_id=user_id,
            changes=changes,
        )
        
        logger.info("rollout_updated", rollout_id=rollout.id, status=rollout.status)
        return rollout
    
    async def should_apply_config(
        self,
        db: AsyncSession,
        config_id: int,
        user_id: Optional[str] = None,
        group_ids: Optional[list] = None
    ) -> bool:
        """
        Determine if config should be applied based on rollout strategy.
        
        Args:
            db: Database session
            config_id: Configuration ID
            user_id: User ID for targeting
            group_ids: Group IDs for targeting
            
        Returns:
            True if config should be applied, False otherwise
        """
        # Get active rollouts for this config
        result = await db.execute(
            select(Rollout).where(
                and_(
                    Rollout.config_id == config_id,
                    Rollout.status.in_([RolloutStatus.PENDING, RolloutStatus.IN_PROGRESS])
                )
            )
        )
        rollout = result.scalar_one_or_none()
        
        if not rollout:
            # No active rollout, apply config
            return True
        
        # Check strategy
        if rollout.strategy == RolloutStrategy.IMMEDIATE:
            return True
        
        elif rollout.strategy == RolloutStrategy.PERCENTAGE:
            # Simple percentage-based rollout
            # In production, use consistent hashing based on user_id
            import random
            return random.randint(0, 100) <= rollout.current_percentage
        
        elif rollout.strategy == RolloutStrategy.USER_TARGETING:
            # Check if user is in target list
            if user_id and rollout.target_users:
                return user_id in rollout.target_users
            if group_ids and rollout.target_groups:
                return any(g in rollout.target_groups for g in group_ids)
            return False
        
        elif rollout.strategy == RolloutStrategy.TIME_BASED:
            # Check if current time is within rollout window
            now = datetime.utcnow()
            if rollout.start_time and now < rollout.start_time:
                return False
            if rollout.end_time and now > rollout.end_time:
                return True
            return True
        
        elif rollout.strategy == RolloutStrategy.CANARY:
            # Canary deployment - check if user is in canary group
            if user_id and rollout.target_users:
                return user_id in rollout.target_users
            return False
        
        elif rollout.strategy == RolloutStrategy.FEATURE_FLAG:
            # Feature flag - check config_data for flag status
            return rollout.config_data.get("enabled", False)
        
        return False


# Global service instance
rollout_service = RolloutService()
