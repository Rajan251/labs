from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.timeline import get_home_timeline
from app.schemas import schemas
from typing import List

router = APIRouter(prefix="/timeline", tags=["timeline"])

@router.get("/", response_model=List[schemas.Tweet])
def read_timeline(user_id: int, db: Session = Depends(get_db)):
    # Simplified: passing user_id as query param for demo
    return get_home_timeline(user_id, db)
