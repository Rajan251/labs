"""
Application Configuration

This module handles all application settings using Pydantic BaseSettings.
Environment variables are loaded from .env file and system environment.

Configuration Priority:
1. System environment variables (highest)
2. .env file
3. Default values (lowest)
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    
    All settings can be overridden by setting environment variables
    with the same name (case-insensitive)
    """
    
    # Application Info
    PROJECT_NAME: str = "FastAPI Production App"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Production-ready FastAPI application with K8s deployment"
    ENVIRONMENT: str = "development"  # development, staging, production
    
    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # Database Configuration
    DATABASE_URL: Optional[str] = None
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    
    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # External Services
    EXTERNAL_API_URL: Optional[str] = None
    EXTERNAL_API_KEY: Optional[str] = None
    
    # Performance
    WORKERS: int = 4
    MAX_CONNECTIONS: int = 100
    TIMEOUT: int = 30
    
    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Create and cache settings instance
    
    Using lru_cache ensures settings are loaded only once
    and reused across the application
    
    Returns:
        Settings: Cached settings instance
    """
    return Settings()


# Global settings instance
settings = get_settings()
