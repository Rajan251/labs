from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

app = FastAPI()

# Database Connection
MONGO_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "videodb")
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Models
class Video(BaseModel):
    id: Optional[str] = None
    title: str
    description: str
    status: str = "processing" # processing, ready, failed
    hls_url: Optional[str] = None
    thumbnail_url: Optional[str] = None

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

# Routes
@app.get("/videos", response_model=List[Video])
async def list_videos():
    videos = []
    cursor = db.videos.find()
    async for document in cursor:
        document['id'] = str(document['_id'])
        videos.append(document)
    return videos

@app.get("/videos/{video_id}", response_model=Video)
async def get_video(video_id: str):
    video = await db.videos.find_one({"_id": ObjectId(video_id)})
    if video:
        video['id'] = str(video['_id'])
        return video
    raise HTTPException(status_code=404, detail="Video not found")

@app.post("/videos", response_model=Video)
async def create_video_metadata(video: Video):
    video_dict = video.dict(exclude={'id'})
    result = await db.videos.insert_one(video_dict)
    video.id = str(result.inserted_id)
    return video

@app.put("/videos/{video_id}/status")
async def update_video_status(video_id: str, status: str, hls_url: str = None):
    update_data = {"status": status}
    if hls_url:
        update_data["hls_url"] = hls_url
    
    result = await db.videos.update_one(
        {"_id": ObjectId(video_id)},
        {"$set": update_data}
    )
    if result.modified_count == 1:
        return {"message": "Status updated"}
    raise HTTPException(status_code=404, detail="Video not found")
