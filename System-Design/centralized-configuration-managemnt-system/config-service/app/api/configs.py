"""
API endpoints for configuration management.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from ..database import get_db
from ..schemas import (
    ConfigCreate, ConfigUpdate, ConfigResponse, ConfigListResponse,
    ConfigFetchRequest, ConfigFetchResponse
)
from ..services.config_service import config_service
from ..models import Config

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/configs", tags=["configs"])


@router.post("/", response_model=ConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_config(
    config_data: ConfigCreate,
    db: AsyncSession = Depends(get_db),
    user_id: Optional[str] = None
):
    """
    Create a new configuration.
    
    - **key**: Configuration key (unique per app/environment)
    - **value**: Configuration value
    - **value_type**: Type of value (string, number, boolean, json)
    - **app_id**: Application identifier (optional, None for global)
    - **environment**: Environment (optional, None for app-level)
    """
    try:
        config = await config_service.create_config(db, config_data, user_id)
        return config
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("create_config_error", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/", response_model=ConfigListResponse)
async def list_configs(
    app_id: Optional[str] = Query(None),
    environment: Optional[str] = Query(None),
    is_active: bool = Query(True),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    List configurations with optional filtering.
    
    - **app_id**: Filter by application ID
    - **environment**: Filter by environment
    - **is_active**: Filter by active status
    - **page**: Page number (starts at 1)
    - **page_size**: Number of items per page
    """
    try:
        # Build query
        query = select(Config).where(Config.is_active == is_active)
        
        if app_id:
            query = query.where(Config.app_id == app_id)
        if environment:
            query = query.where(Config.environment == environment)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Get paginated results
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        configs = result.scalars().all()
        
        return ConfigListResponse(
            total=total,
            page=page,
            page_size=page_size,
            configs=configs
        )
    except Exception as e:
        logger.error("list_configs_error", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/{config_id}", response_model=ConfigResponse)
async def get_config(
    config_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific configuration by ID."""
    result = await db.execute(select(Config).where(Config.id == config_id))
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Configuration not found")
    
    return config


@router.put("/{config_id}", response_model=ConfigResponse)
async def update_config(
    config_id: int,
    update_data: ConfigUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: Optional[str] = None
):
    """
    Update an existing configuration.
    
    - **value**: New value (optional)
    - **value_type**: New value type (optional)
    - **description**: New description (optional)
    - **is_active**: Active status (optional)
    """
    try:
        config = await config_service.update_config(db, config_id, update_data, user_id)
        return config
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("update_config_error", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: Optional[str] = None
):
    """
    Soft delete a configuration (sets is_active to False).
    """
    try:
        from ..schemas import ConfigUpdate
        update_data = ConfigUpdate(is_active=False, updated_by=user_id)
        await config_service.update_config(db, config_id, update_data, user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("delete_config_error", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/fetch", response_model=ConfigFetchResponse)
async def fetch_configs(
    request: ConfigFetchRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Fetch configurations for a client with hierarchy resolution.
    
    This endpoint is used by client SDKs to fetch all applicable configurations
    based on hierarchy (environment > app > global).
    
    - **app_id**: Application identifier
    - **environment**: Environment (dev/staging/prod)
    - **keys**: Optional list of specific keys to fetch
    - **user_id**: Optional user ID for rollout targeting
    - **group_ids**: Optional group IDs for rollout targeting
    """
    try:
        configs = await config_service.resolve_configs(db, request)
        
        # Generate version hash for cache validation
        import hashlib
        import json
        version_hash = hashlib.sha256(
            json.dumps(configs, sort_keys=True).encode()
        ).hexdigest()[:16]
        
        from ..config import settings
        
        return ConfigFetchResponse(
            configs=configs,
            version=version_hash,
            cache_ttl=settings.client_cache_ttl
        )
    except Exception as e:
        logger.error("fetch_configs_error", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
