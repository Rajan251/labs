"""
Pydantic schemas for API request/response validation.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class EnvironmentType(str, Enum):
    """Environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class ValueType(str, Enum):
    """Configuration value types."""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    JSON = "json"


class ChangeType(str, Enum):
    """Change types."""
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    ROLLBACK = "rollback"


# Config Schemas
class ConfigBase(BaseModel):
    """Base configuration schema."""
    key: str = Field(..., min_length=1, max_length=255)
    value: Any
    value_type: ValueType
    description: Optional[str] = None
    is_encrypted: bool = False


class ConfigCreate(ConfigBase):
    """Schema for creating a configuration."""
    app_id: Optional[str] = Field(None, max_length=100)
    environment: Optional[EnvironmentType] = None
    created_by: Optional[str] = None


class ConfigUpdate(BaseModel):
    """Schema for updating a configuration."""
    value: Optional[Any] = None
    value_type: Optional[ValueType] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    updated_by: Optional[str] = None


class ConfigResponse(ConfigBase):
    """Schema for configuration response."""
    id: int
    app_id: Optional[str]
    environment: Optional[EnvironmentType]
    is_active: bool
    version: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    updated_by: Optional[str]
    
    class Config:
        from_attributes = True


class ConfigListResponse(BaseModel):
    """Schema for paginated config list."""
    total: int
    page: int
    page_size: int
    configs: List[ConfigResponse]


# Version Schemas
class VersionResponse(BaseModel):
    """Schema for version history response."""
    id: int
    config_id: int
    version: int
    value: Any
    value_type: str
    change_type: ChangeType
    change_description: Optional[str]
    changed_by: Optional[str]
    changed_at: datetime
    is_rollback: bool
    rollback_from_version: Optional[int]
    
    class Config:
        from_attributes = True


class RollbackRequest(BaseModel):
    """Schema for rollback request."""
    target_version: int = Field(..., ge=1)
    rollback_reason: Optional[str] = None
    rollback_by: Optional[str] = None


# Rollout Schemas
class RolloutStrategy(str, Enum):
    """Rollout strategy types."""
    IMMEDIATE = "immediate"
    PERCENTAGE = "percentage"
    CANARY = "canary"
    FEATURE_FLAG = "feature_flag"
    TIME_BASED = "time_based"
    USER_TARGETING = "user_targeting"


class RolloutStatus(str, Enum):
    """Rollout status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    FAILED = "failed"


class RolloutCreate(BaseModel):
    """Schema for creating a rollout."""
    config_id: int
    strategy: RolloutStrategy
    config_data: Dict[str, Any] = Field(default_factory=dict)
    target_percentage: int = Field(default=100, ge=0, le=100)
    target_users: Optional[List[str]] = None
    target_groups: Optional[List[str]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    created_by: Optional[str] = None


class RolloutUpdate(BaseModel):
    """Schema for updating a rollout."""
    status: Optional[RolloutStatus] = None
    current_percentage: Optional[int] = Field(None, ge=0, le=100)
    config_data: Optional[Dict[str, Any]] = None


class RolloutResponse(BaseModel):
    """Schema for rollout response."""
    id: int
    config_id: int
    strategy: RolloutStrategy
    status: RolloutStatus
    config_data: Dict[str, Any]
    current_percentage: int
    target_percentage: int
    target_users: Optional[List[str]]
    target_groups: Optional[List[str]]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    
    class Config:
        from_attributes = True


# Audit Schemas
class AuditLogResponse(BaseModel):
    """Schema for audit log response."""
    id: int
    entity_type: str
    entity_id: int
    action: str
    changes: Optional[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]
    user_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    timestamp: datetime
    app_id: Optional[str]
    environment: Optional[EnvironmentType]
    
    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """Schema for paginated audit log list."""
    total: int
    page: int
    page_size: int
    logs: List[AuditLogResponse]


# Client SDK Schemas
class ConfigFetchRequest(BaseModel):
    """Schema for client config fetch request."""
    app_id: str
    environment: EnvironmentType
    keys: Optional[List[str]] = None  # If None, fetch all configs
    user_id: Optional[str] = None  # For user-targeted rollouts
    group_ids: Optional[List[str]] = None  # For group-targeted rollouts


class ConfigFetchResponse(BaseModel):
    """Schema for client config fetch response."""
    configs: Dict[str, Any]
    version: str  # Combined version hash
    cache_ttl: int  # Recommended cache TTL in seconds
