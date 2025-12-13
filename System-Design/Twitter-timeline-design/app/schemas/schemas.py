from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_celebrity: bool
    created_at: datetime

    class Config:
        from_attributes = True

class TweetBase(BaseModel):
    content: str
    media_urls: List[str] = []

class TweetCreate(TweetBase):
    pass

class Tweet(TweetBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class FollowBase(BaseModel):
    followee_id: int

class Token(BaseModel):
    access_token: str
    token_type: str
