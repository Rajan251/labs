"""
Configuration management using Pydantic Settings.
Loads configuration from environment variables with validation.
"""
from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import json


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = Field(default="config-management-service")
    app_version: str = Field(default="1.0.0")
    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    
    # API
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    api_prefix: str = Field(default="/api/v1")
    cors_origins: str = Field(default='["http://localhost:3000"]')
    
    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://config_user:config_pass@localhost:5432/config_db"
    )
    database_pool_size: int = Field(default=20)
    database_max_overflow: int = Field(default=10)
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")
    redis_cache_ttl: int = Field(default=300)
    redis_max_connections: int = Field(default=50)
    
    # RabbitMQ
    rabbitmq_url: str = Field(default="amqp://guest:guest@localhost:5672/")
    rabbitmq_exchange: str = Field(default="config_changes")
    rabbitmq_queue: str = Field(default="config_notifications")
    
    # Security
    secret_key: str = Field(default="dev-secret-key-change-in-production")
    encryption_key: str = Field(default="dev-encryption-key-change-in-production")
    access_token_expire_minutes: int = Field(default=30)
    
    # Feature Flags
    enable_audit_logging: bool = Field(default=True)
    enable_encryption: bool = Field(default=True)
    enable_notifications: bool = Field(default=True)
    
    # Monitoring
    prometheus_port: int = Field(default=9090)
    metrics_enabled: bool = Field(default=True)
    
    # Client SDK defaults
    client_cache_ttl: int = Field(default=60)
    client_retry_max_attempts: int = Field(default=3)
    client_retry_backoff_factor: int = Field(default=2)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str) -> List[str]:
        """Parse CORS origins from JSON string."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [v]
        return v
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"


# Global settings instance
settings = Settings()
