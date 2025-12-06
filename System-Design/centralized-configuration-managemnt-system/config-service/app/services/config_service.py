"""
Configuration service - Core business logic for config management.
Handles hierarchy resolution, versioning, and caching.
"""
from typing import Optional, List, Dict, Any
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
import hashlib
import json
import structlog

from ..models import Config, ConfigVersion, ChangeType, EnvironmentType
from ..schemas import ConfigCreate, ConfigUpdate, ConfigFetchRequest
from ..redis_client import redis_client
from ..rabbitmq_client import rabbitmq_client
from .audit_service import audit_service

logger = structlog.get_logger(__name__)


class ConfigService:
    """Service for configuration management operations."""
    
    async def create_config(
        self,
        db: AsyncSession,
        config_data: ConfigCreate,
        user_id: Optional[str] = None
    ) -> Config:
        """
        Create a new configuration.
        
        Args:
            db: Database session
            config_data: Configuration data
            user_id: User creating the config
            
        Returns:
            Created configuration
        """
        # Check if config already exists
        existing = await self.get_config_by_key(
            db,
            config_data.key,
            config_data.app_id,
            config_data.environment
        )
        
        if existing:
            raise ValueError(f"Configuration already exists: {config_data.key}")
        
        # Create config
        config = Config(
            app_id=config_data.app_id,
            environment=config_data.environment,
            key=config_data.key,
            value=config_data.value,
            value_type=config_data.value_type.value,
            description=config_data.description,
            is_encrypted=config_data.is_encrypted,
            version=1,
            created_by=user_id or config_data.created_by,
        )
        
        db.add(config)
        await db.flush()
        
        # Create initial version
        version = ConfigVersion(
            config_id=config.id,
            version=1,
            value=config_data.value,
            value_type=config_data.value_type.value,
            change_type=ChangeType.CREATED,
            changed_by=user_id or config_data.created_by,
        )
        
        db.add(version)
        await db.commit()
        await db.refresh(config)
        
        # Invalidate cache
        await self._invalidate_cache(config)
        
        # Publish notification
        if config_data.environment:
            await rabbitmq_client.publish_config_change(
                app_id=config_data.app_id or "global",
                environment=config_data.environment.value,
                config_key=config_data.key,
                change_type="created",
            )
        
        # Audit log
        await audit_service.log_change(
            db,
            entity_type="config",
            entity_id=config.id,
            action="create",
            user_id=user_id,
            app_id=config_data.app_id,
            environment=config_data.environment,
            changes={"value": config_data.value},
        )
        
        logger.info("config_created", config_id=config.id, key=config_data.key)
        return config
    
    async def update_config(
        self,
        db: AsyncSession,
        config_id: int,
        update_data: ConfigUpdate,
        user_id: Optional[str] = None
    ) -> Config:
        """
        Update an existing configuration.
        
        Args:
            db: Database session
            config_id: Configuration ID
            update_data: Update data
            user_id: User updating the config
            
        Returns:
            Updated configuration
        """
        # Get existing config
        result = await db.execute(select(Config).where(Config.id == config_id))
        config = result.scalar_one_or_none()
        
        if not config:
            raise ValueError(f"Configuration not found: {config_id}")
        
        # Track changes
        changes = {}
        
        if update_data.value is not None:
            changes["value"] = {"old": config.value, "new": update_data.value}
            config.value = update_data.value
            config.version += 1
            
            # Create new version
            version = ConfigVersion(
                config_id=config.id,
                version=config.version,
                value=update_data.value,
                value_type=update_data.value_type.value if update_data.value_type else config.value_type,
                change_type=ChangeType.UPDATED,
                changed_by=user_id or update_data.updated_by,
            )
            db.add(version)
        
        if update_data.value_type is not None:
            config.value_type = update_data.value_type.value
        
        if update_data.description is not None:
            config.description = update_data.description
        
        if update_data.is_active is not None:
            changes["is_active"] = {"old": config.is_active, "new": update_data.is_active}
            config.is_active = update_data.is_active
        
        config.updated_by = user_id or update_data.updated_by
        
        await db.commit()
        await db.refresh(config)
        
        # Invalidate cache
        await self._invalidate_cache(config)
        
        # Publish notification
        if config.environment:
            await rabbitmq_client.publish_config_change(
                app_id=config.app_id or "global",
                environment=config.environment.value,
                config_key=config.key,
                change_type="updated",
            )
        
        # Audit log
        await audit_service.log_change(
            db,
            entity_type="config",
            entity_id=config.id,
            action="update",
            user_id=user_id,
            app_id=config.app_id,
            environment=config.environment,
            changes=changes,
        )
        
        logger.info("config_updated", config_id=config.id, version=config.version)
        return config
    
    async def get_config_by_key(
        self,
        db: AsyncSession,
        key: str,
        app_id: Optional[str] = None,
        environment: Optional[EnvironmentType] = None
    ) -> Optional[Config]:
        """Get configuration by key with hierarchy."""
        result = await db.execute(
            select(Config).where(
                and_(
                    Config.key == key,
                    Config.app_id == app_id,
                    Config.environment == environment,
                    Config.is_active == True
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def resolve_configs(
        self,
        db: AsyncSession,
        request: ConfigFetchRequest
    ) -> Dict[str, Any]:
        """
        Resolve configurations with hierarchy (environment > app > global).
        
        Args:
            db: Database session
            request: Fetch request with app_id, environment, keys
            
        Returns:
            Resolved configuration dictionary
        """
        cache_key = self._get_cache_key(request.app_id, request.environment.value)
        
        # Try cache first
        cached = await redis_client.get(cache_key)
        if cached:
            logger.info("config_cache_hit", app_id=request.app_id, env=request.environment)
            return cached
        
        # Fetch from database with hierarchy
        configs = {}
        
        # 1. Global configs (no app_id, no environment)
        global_configs = await db.execute(
            select(Config).where(
                and_(
                    Config.app_id.is_(None),
                    Config.environment.is_(None),
                    Config.is_active == True
                )
            )
        )
        
        for config in global_configs.scalars():
            configs[config.key] = config.value
        
        # 2. App-level configs (specific app_id, no environment)
        if request.app_id:
            app_configs = await db.execute(
                select(Config).where(
                    and_(
                        Config.app_id == request.app_id,
                        Config.environment.is_(None),
                        Config.is_active == True
                    )
                )
            )
            
            for config in app_configs.scalars():
                configs[config.key] = config.value
        
        # 3. Environment-specific configs (specific app_id and environment)
        if request.app_id and request.environment:
            env_configs = await db.execute(
                select(Config).where(
                    and_(
                        Config.app_id == request.app_id,
                        Config.environment == request.environment,
                        Config.is_active == True
                    )
                )
            )
            
            for config in env_configs.scalars():
                configs[config.key] = config.value
        
        # Filter by requested keys if specified
        if request.keys:
            configs = {k: v for k, v in configs.items() if k in request.keys}
        
        # Cache the result
        await redis_client.set(cache_key, configs)
        
        logger.info("configs_resolved", app_id=request.app_id, env=request.environment, count=len(configs))
        return configs
    
    async def rollback_config(
        self,
        db: AsyncSession,
        config_id: int,
        target_version: int,
        user_id: Optional[str] = None,
        reason: Optional[str] = None
    ) -> Config:
        """
        Rollback configuration to a previous version.
        
        Args:
            db: Database session
            config_id: Configuration ID
            target_version: Version to rollback to
            user_id: User performing rollback
            reason: Rollback reason
            
        Returns:
            Updated configuration
        """
        # Get config
        result = await db.execute(select(Config).where(Config.id == config_id))
        config = result.scalar_one_or_none()
        
        if not config:
            raise ValueError(f"Configuration not found: {config_id}")
        
        # Get target version
        version_result = await db.execute(
            select(ConfigVersion).where(
                and_(
                    ConfigVersion.config_id == config_id,
                    ConfigVersion.version == target_version
                )
            )
        )
        target = version_result.scalar_one_or_none()
        
        if not target:
            raise ValueError(f"Version not found: {target_version}")
        
        # Update config
        old_value = config.value
        config.value = target.value
        config.value_type = target.value_type
        config.version += 1
        config.updated_by = user_id
        
        # Create rollback version
        rollback_version = ConfigVersion(
            config_id=config.id,
            version=config.version,
            value=target.value,
            value_type=target.value_type,
            change_type=ChangeType.ROLLBACK,
            change_description=reason,
            changed_by=user_id,
            is_rollback=True,
            rollback_from_version=target_version,
        )
        
        db.add(rollback_version)
        await db.commit()
        await db.refresh(config)
        
        # Invalidate cache
        await self._invalidate_cache(config)
        
        # Publish notification
        if config.environment:
            await rabbitmq_client.publish_config_change(
                app_id=config.app_id or "global",
                environment=config.environment.value,
                config_key=config.key,
                change_type="rollback",
                metadata={"target_version": target_version, "reason": reason},
            )
        
        # Audit log
        await audit_service.log_change(
            db,
            entity_type="config",
            entity_id=config.id,
            action="rollback",
            user_id=user_id,
            app_id=config.app_id,
            environment=config.environment,
            changes={
                "old_value": old_value,
                "new_value": target.value,
                "target_version": target_version,
                "reason": reason,
            },
        )
        
        logger.info("config_rolled_back", config_id=config.id, target_version=target_version)
        return config
    
    def _get_cache_key(self, app_id: str, environment: str) -> str:
        """Generate cache key for config resolution."""
        return f"config:{app_id}:{environment}"
    
    async def _invalidate_cache(self, config: Config) -> None:
        """Invalidate cache for affected configurations."""
        patterns = [
            f"config:{config.app_id or '*'}:{config.environment.value if config.environment else '*'}",
        ]
        
        for pattern in patterns:
            await redis_client.invalidate_pattern(pattern)


# Global service instance
config_service = ConfigService()
