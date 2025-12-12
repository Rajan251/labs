from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis
import uuid
import json
import time

app = FastAPI()

# Redis connection
r = redis.Redis(host='redis', port=6379, db=0)

class ChatRequest(BaseModel):
    user_id: str
    message: str
    max_tokens: int = 200

@app.post("/chat")
async def chat(request: ChatRequest):
    request_id = str(uuid.uuid4())
    task = {
        "id": request_id,
        "user_id": request.user_id,
        "message": request.message,
        "max_tokens": request.max_tokens,
        "status": "pending"
    }
    
    # Push to Redis Queue
    r.rpush("chat_queue", json.dumps(task))
    
    # In a real async system, we might return a task ID and have the client poll
    # or use WebSockets. For simplicity here, we'll just acknowledge receipt.
    return {"status": "queued", "request_id": request_id}

@app.get("/status/{request_id}")
async def get_status(request_id: str):
    # Check if result exists in Redis (worker would write it there)
    result = r.get(f"result:{request_id}")
    if result:
        return json.loads(result)
    else:
        return {"status": "processing"}
