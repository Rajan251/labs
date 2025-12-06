"""
Configuration management using Pydantic Settings.
Loads configuration from environment variables and .env file.
"""
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = Field(default="webhook-platform", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    
    # Database
    database_url: str = Field(
        default="postgresql://webhook_user:webhook_pass@localhost:5432/webhook_db",
        alias="DATABASE_URL"
    )
    database_pool_size: int = Field(default=20, alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=10, alias="DATABASE_MAX_OVERFLOW")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    redis_max_connections: int = Field(default=50, alias="REDIS_MAX_CONNECTIONS")
    
    # RabbitMQ
    rabbitmq_url: str = Field(
        default="amqp://webhook_user:webhook_pass@localhost:5672/",
        alias="RABBITMQ_URL"
    )
    celery_broker_url: str = Field(
        default="amqp://webhook_user:webhook_pass@localhost:5672/",
        alias="CELERY_BROKER_URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/1",
        alias="CELERY_RESULT_BACKEND"
    )
    
    # Rate Limiting
    rate_limit_per_tenant: int = Field(default=100, alias="RATE_LIMIT_PER_TENANT")
    rate_limit_window: int = Field(default=60, alias="RATE_LIMIT_WINDOW")
    
    # Webhook Delivery
    max_retry_attempts: int = Field(default=6, alias="MAX_RETRY_ATTEMPTS")
    initial_retry_delay: int = Field(default=1, alias="INITIAL_RETRY_DELAY")
    max_retry_delay: int = Field(default=32, alias="MAX_RETRY_DELAY")
    webhook_timeout: int = Field(default=30, alias="WEBHOOK_TIMEOUT")
    
    # Security
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        alias="SECRET_KEY"
    )
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
