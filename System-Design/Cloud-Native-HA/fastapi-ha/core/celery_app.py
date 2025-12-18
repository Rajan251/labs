from celery import Celery
from .config import settings

celery_app = Celery(
    "worker", 
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Worker autoscaling
    worker_autoscale='10,3', # Max 10, min 3
)

@celery_app.task
def process_background_job(data: dict):
    # Simulate work
    import time
    time.sleep(5)
    return {"status": "completed", "data": data}
