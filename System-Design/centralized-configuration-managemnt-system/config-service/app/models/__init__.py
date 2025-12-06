"""
Database models for configuration management system.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column, String, Integer, DateTime, Boolean, Text, JSON, Index, ForeignKey, Enum
)
from sqlalchemy.orm import relationship
import enum

from ..database import Base


class EnvironmentType(str, enum.Enum):
    """Environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class ChangeType(str, enum.Enum):
    """Configuration change types."""
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    ROLLBACK = "rollback"


class Config(Base):
    """
    Configuration model with versioning and hierarchy support.
    
    Hierarchy levels:
    - global: Applies to all apps and environments
    - app: Applies to specific app across all environments
    - environment: Applies to specific app in specific environment
    """
    __tablename__ = "configs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Hierarchy fields
    app_id = Column(String(100), nullable=True, index=True)  # None for global configs
    environment = Column(
        Enum(EnvironmentType),
        nullable=True,
        index=True
    )  # None for app-level configs
    
    # Configuration data
    key = Column(String(255), nullable=False, index=True)
    value = Column(JSON, nullable=False)
    value_type = Column(String(50), nullable=False)  # string, number, boolean, json
    
    # Metadata
    description = Column(Text, nullable=True)
    is_encrypted = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True, index=True)
    
    # Versioning
    version = Column(Integer, default=1, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    
    # Relationships
    versions = relationship("ConfigVersion", back_populates="config", cascade="all, delete-orphan")
    rollouts = relationship("Rollout", back_populates="config", cascade="all, delete-orphan")
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_config_lookup', 'app_id', 'environment', 'key', 'is_active'),
        Index('idx_config_hierarchy', 'app_id', 'environment'),
    )
    
    def __repr__(self):
        return f"<Config(key={self.key}, app_id={self.app_id}, env={self.environment})>"


class ConfigVersion(Base):
    """Version history for configurations."""
    __tablename__ = "config_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(Integer, ForeignKey("configs.id", ondelete="CASCADE"), nullable=False)
    
    # Version data
    version = Column(Integer, nullable=False)
    value = Column(JSON, nullable=False)
    value_type = Column(String(50), nullable=False)
    
    # Change tracking
    change_type = Column(Enum(ChangeType), nullable=False)
    change_description = Column(Text, nullable=True)
    changed_by = Column(String(100), nullable=True)
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Rollback support
    is_rollback = Column(Boolean, default=False)
    rollback_from_version = Column(Integer, nullable=True)
    
    # Relationships
    config = relationship("Config", back_populates="versions")
    
    __table_args__ = (
        Index('idx_version_lookup', 'config_id', 'version'),
    )
    
    def __repr__(self):
        return f"<ConfigVersion(config_id={self.config_id}, version={self.version})>"


class RolloutStrategy(str, enum.Enum):
    """Rollout strategy types."""
    IMMEDIATE = "immediate"  # Deploy to all immediately
    PERCENTAGE = "percentage"  # Gradual percentage-based rollout
    CANARY = "canary"  # Deploy to canary group first
    FEATURE_FLAG = "feature_flag"  # Control via feature flag
    TIME_BASED = "time_based"  # Schedule deployment for specific time
    USER_TARGETING = "user_targeting"  # Target specific users/groups


class RolloutStatus(str, enum.Enum):
    """Rollout status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    FAILED = "failed"


class Rollout(Base):
    """Rollout configuration for gradual deployments."""
    __tablename__ = "rollouts"
    
    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(Integer, ForeignKey("configs.id", ondelete="CASCADE"), nullable=False)
    
    # Strategy
    strategy = Column(Enum(RolloutStrategy), nullable=False)
    status = Column(Enum(RolloutStatus), default=RolloutStatus.PENDING, index=True)
    
    # Strategy-specific configuration
    config_data = Column(JSON, nullable=False)  # Strategy-specific params
    
    # Progress tracking
    current_percentage = Column(Integer, default=0)
    target_percentage = Column(Integer, default=100)
    
    # Targeting
    target_users = Column(JSON, nullable=True)  # List of user IDs
    target_groups = Column(JSON, nullable=True)  # List of group IDs
    
    # Scheduling
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100), nullable=True)
    
    # Relationships
    config = relationship("Config", back_populates="rollouts")
    
    __table_args__ = (
        Index('idx_rollout_status', 'status', 'start_time'),
    )
    
    def __repr__(self):
        return f"<Rollout(config_id={self.config_id}, strategy={self.strategy}, status={self.status})>"


class AuditLog(Base):
    """Audit log for all configuration changes."""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # What changed
    entity_type = Column(String(50), nullable=False, index=True)  # config, version, rollout
    entity_id = Column(Integer, nullable=False, index=True)
    action = Column(String(50), nullable=False)  # create, update, delete, rollback
    
    # Change details
    changes = Column(JSON, nullable=True)  # Before/after values
    metadata = Column(JSON, nullable=True)  # Additional context
    
    # Who and when
    user_id = Column(String(100), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Context
    app_id = Column(String(100), nullable=True, index=True)
    environment = Column(Enum(EnvironmentType), nullable=True, index=True)
    
    __table_args__ = (
        Index('idx_audit_lookup', 'entity_type', 'entity_id', 'timestamp'),
        Index('idx_audit_user', 'user_id', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<AuditLog(entity_type={self.entity_type}, action={self.action}, user={self.user_id})>"
