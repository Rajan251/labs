from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import os
from datetime import datetime

app = FastAPI(title="Python API", version="1.0.0")

# Models
class User(BaseModel):
    id: int
    name: str
    email: str

class HealthResponse(BaseModel):
    status: str
    timestamp: str

# In-memory data
users_db = [
    User(id=1, name="John Doe", email="john@example.com"),
    User(id=2, name="Jane Smith", email="jane@example.com")
]

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat()
    )

@app.get("/api/status")
async def get_status():
    """API status endpoint"""
    return {
        "service": "python-api",
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.get("/api/users", response_model=list[User])
async def get_users():
    """Get all users"""
    return users_db

@app.get("/api/users/{user_id}", response_model=User)
async def get_user(user_id: int):
    """Get user by ID"""
    user = next((u for u in users_db if u.id == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/api/users", response_model=User, status_code=201)
async def create_user(user: User):
    """Create new user"""
    if any(u.id == user.id for u in users_db):
        raise HTTPException(status_code=400, detail="User ID already exists")
    users_db.append(user)
    return user

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
