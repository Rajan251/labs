from fastapi import FastAPI, UploadFile, File, HTTPException
import os
import shutil
import uuid
from celery import Celery
import httpx

app = FastAPI()

# Configuration
MEDIA_ROOT = os.getenv("MEDIA_ROOT", "/var/www/media")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
VIDEO_SERVICE_URL = os.getenv("VIDEO_SERVICE_URL", "http://video-service:8000")
TRANSCODER_TASK_NAME = os.getenv("TRANSCODER_TASK_NAME", "worker.transcode_video")

# Celery Client
celery_app = Celery('uploader', broker=CELERY_BROKER_URL)

@app.post("/upload")
async def upload_video(file: UploadFile = File(...), title: str = "Untitled", description: str = ""):
    # 1. Create metadata in Video Service
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{VIDEO_SERVICE_URL}/videos", json={
                "title": title,
                "description": description,
                "status": "uploading"
            })
            response.raise_for_status()
            video_data = response.json()
            video_id = video_data['id']
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create video metadata: {str(e)}")

    # 2. Save file to shared volume
    file_extension = os.path.splitext(file.filename)[1]
    raw_filename = f"{video_id}{file_extension}"
    raw_path = os.path.join(MEDIA_ROOT, raw_filename)
    
    # Ensure media root exists
    os.makedirs(MEDIA_ROOT, exist_ok=True)

    try:
        with open(raw_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        # Rollback metadata if possible (omitted for MVP)
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # 3. Trigger Transcoding Task
    task = celery_app.send_task(TRANSCODER_TASK_NAME, args=[video_id, raw_path])

    return {"message": "Upload successful, processing started", "video_id": video_id, "task_id": task.id}
