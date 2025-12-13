from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.follow import Follow
from app.schemas import schemas
# Security imports would go here (passlib, jose) - simplified for now

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = User(username=user.username, email=user.email, hashed_password=user.password) # Hash password in real app
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/{user_id}/follow", status_code=status.HTTP_201_CREATED)
def follow_user(user_id: int, follow: schemas.FollowBase, db: Session = Depends(get_db)):
    # Simplified: Assuming current user is user_id for demo
    db_follow = Follow(follower_id=user_id, followee_id=follow.followee_id)
    db.add(db_follow)
    db.commit()
    return {"message": "Followed successfully"}
