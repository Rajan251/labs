from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from .queue_manager import queue_manager, Config
import uuid

app = FastAPI(title="Scalable Translation System")

class TranslationRequest(BaseModel):
    text: str
    priority: bool = False
    word_count: Optional[int] = None 

@app.on_event("startup")
def startup_event():
    queue_manager.connect()

@app.on_event("shutdown")
def shutdown_event():
    queue_manager.close()

@app.post("/translate")
async def submit_translation(request: TranslationRequest):
    job_id = str(uuid.uuid4())
    
    # Calculate word count if not provided
    count = request.word_count if request.word_count else len(request.text.split())
    
    payload = {
        "job_id": job_id,
        "text": request.text[:100] + "...", # Truncate for log
        "word_count": count,
        "priority": request.priority
    }
    
    target_queue = Config.QUEUE_CRITICAL if request.priority else Config.QUEUE_STANDARD
    
    try:
        queue_manager.publish_message(target_queue, payload)
        return {
            "job_id": job_id, 
            "status": "queued", 
            "queue": target_queue,
            "estimated_time_seconds": (count / Config.WORDS_PER_MINUTE) * 60
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok"}
