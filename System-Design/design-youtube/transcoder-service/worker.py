import os
import subprocess
from celery import Celery
import requests

# Configuration
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
MEDIA_ROOT = os.getenv("MEDIA_ROOT", "/var/www/media")
VIDEO_SERVICE_URL = os.getenv("VIDEO_SERVICE_URL", "http://video-service:8000")

app = Celery('transcoder', broker=CELERY_BROKER_URL)

@app.task(name='worker.transcode_video')
def transcode_video(video_id, input_path):
    print(f"Starting transcoding for video {video_id}")
    
    # Update status to processing (redundant but good for logging)
    requests.put(f"{VIDEO_SERVICE_URL}/videos/{video_id}/status", params={"status": "processing"})

    output_dir = os.path.join(MEDIA_ROOT, video_id)
    os.makedirs(output_dir, exist_ok=True)
    
    output_playlist = os.path.join(output_dir, "playlist.m3u8")

    # FFmpeg command for HLS
    # This is a simple command. For production, you'd want multi-bitrate.
    cmd = [
        "ffmpeg",
        "-i", input_path,
        "-profile:v", "baseline", # Baseline profile for compatibility
        "-level", "3.0",
        "-start_number", "0",
        "-hls_time", "10", # 10 second segments
        "-hls_list_size", "0", # Keep all segments in playlist
        "-f", "hls",
        output_playlist
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        
        # Construct HLS URL (relative to Nginx root)
        hls_url = f"/media/{video_id}/playlist.m3u8"
        
        # Update Video Service with success
        requests.put(f"{VIDEO_SERVICE_URL}/videos/{video_id}/status", params={
            "status": "ready",
            "hls_url": hls_url
        })
        print(f"Transcoding complete for {video_id}")
        
        # Cleanup raw file (optional, keeping for now)
        # os.remove(input_path)

    except subprocess.CalledProcessError as e:
        print(f"Transcoding failed: {e.stderr}")
        requests.put(f"{VIDEO_SERVICE_URL}/videos/{video_id}/status", params={"status": "failed"})
        raise e
