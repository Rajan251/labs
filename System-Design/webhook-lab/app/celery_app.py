"""
Celery configuration for webhook delivery workers.
"""
from celery import Celery
from app.config import settings

# Create Celery app
celery_app = Celery(
    "webhook_worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max
    task_soft_time_limit=240,  # 4 minutes soft limit
    worker_prefetch_multiplier=1,  # One task at a time per worker
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks
)
