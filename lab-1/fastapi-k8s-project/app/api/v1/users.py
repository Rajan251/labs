"""
User Management Endpoints

Example API endpoints for user operations.
This demonstrates a typical CRUD API structure.
"""

from fastapi import APIRouter, HTTPException, status
from typing import List
from pydantic import BaseModel

router = APIRouter()


# Pydantic models for request/response
class User(BaseModel):
    """User model"""
    id: int
    username: str
    email: str
    is_active: bool = True


class UserCreate(BaseModel):
    """User creation model"""
    username: str
    email: str


# In-memory storage (replace with actual database)
fake_users_db = {}
user_id_counter = 1


@router.get("/users", response_model=List[User])
async def get_users():
    """
    Get all users
    
    Returns:
        List[User]: List of all users
    """
    return list(fake_users_db.values())


@router.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int):
    """
    Get user by ID
    
    Args:
        user_id: User ID
        
    Returns:
        User: User object
        
    Raises:
        HTTPException: If user not found
    """
    if user_id not in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    return fake_users_db[user_id]


@router.post("/users", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    """
    Create a new user
    
    Args:
        user: User creation data
        
    Returns:
        User: Created user object
    """
    global user_id_counter
    
    new_user = User(
        id=user_id_counter,
        username=user.username,
        email=user.email
    )
    fake_users_db[user_id_counter] = new_user
    user_id_counter += 1
    
    return new_user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int):
    """
    Delete user by ID
    
    Args:
        user_id: User ID
        
    Raises:
        HTTPException: If user not found
    """
    if user_id not in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    del fake_users_db[user_id]
