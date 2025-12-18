from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI HA Service"
    DATABASE_URL: str
    REDIS_URL: str
    OTEL_SERVICE_NAME: str = "fastapi-ha"
    
    # Connection Pool Settings
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    
    class Config:
        env_file = ".env"

settings = Settings()
