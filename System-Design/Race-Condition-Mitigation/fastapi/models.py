from pydantic import BaseModel
from typing import Optional, Dict, Any

class IdempotencyKey(BaseModel):
    key: str
    status: str = "PROCESSING" # PROCESSING, SUCCESS, FAILED
    response: Optional[Dict[str, Any]] = None
    created_at: float

class HealthStatus(BaseModel):
    status: str
    redis: bool
    database: bool
    version: str = "1.0.0"
