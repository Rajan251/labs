import redis
import json
import time
import requests
import os

# Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
VLLM_URL = os.getenv("VLLM_URL", "http://vllm-service:8000/v1/completions")

r = redis.Redis(host=REDIS_HOST, port=6379, db=0)

def process_task(task):
    print(f"Processing task: {task['id']}")
    
    payload = {
        "model": "meta-llama/Llama-2-7b-chat-hf",
        "prompt": task['message'],
        "max_tokens": task.get('max_tokens', 200),
        "temperature": 0.7
    }
    
    try:
        response = requests.post(VLLM_URL, json=payload)
        response.raise_for_status()
        result = response.json()
        
        # Store result
        output = {
            "id": task['id'],
            "status": "completed",
            "response": result['choices'][0]['text']
        }
        r.set(f"result:{task['id']}", json.dumps(output), ex=3600) # Expire in 1 hour
        print(f"Task {task['id']} completed.")
        
    except Exception as e:
        print(f"Error processing task {task['id']}: {e}")
        error_output = {
            "id": task['id'],
            "status": "failed",
            "error": str(e)
        }
        r.set(f"result:{task['id']}", json.dumps(error_output), ex=3600)

def main():
    print("Worker started. Waiting for tasks...")
    while True:
        # Blocking pop from queue
        item = r.blpop("chat_queue", timeout=5)
        if item:
            queue_name, task_data = item
            task = json.loads(task_data)
            process_task(task)
        else:
            # No tasks, just loop
            pass

if __name__ == "__main__":
    main()
