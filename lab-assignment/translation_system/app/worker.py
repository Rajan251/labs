import time
import json
import redis
from .config import Config
import sys
import os

def process_job(job_data):
    job = json.loads(job_data)
    job_id = job.get("job_id")
    word_count = job.get("word_count", 0)
    priority = job.get("priority", False)
    
    print(f" [x] Received Job {job_id} | Priority: {priority} | Words: {word_count}")
    
    # Simulate processing time
    processing_time = (word_count / Config.WORDS_PER_MINUTE) * 60
    
    print(f" [>] Processing... (Simulated time: {processing_time:.2f}s)")
    time.sleep(processing_time)
    
    print(f" [v] Job {job_id} Completed")

def start_worker():
    print(" [*] Connecting to Redis...")
    r = redis.Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, db=0)
    
    print(" [*] Waiting for messages. To exit press CTRL+C")
    
    while True:
        # Strict Priority: Check Critical first
        result = r.blpop([Config.QUEUE_CRITICAL, Config.QUEUE_STANDARD], timeout=0)
        
        if result:
            queue_name, job_data = result
            process_job(job_data)

if __name__ == "__main__":
    try:
        start_worker()
    except KeyboardInterrupt:
        print("Interrupted")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
