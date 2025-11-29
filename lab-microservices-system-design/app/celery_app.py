"""
Celery application configuration
Message broker: RabbitMQ
Result backend: Redis
"""
import os
from celery import Celery
from celery.schedules import crontab

# Celery configuration
broker_url = os.getenv("CELERY_BROKER_URL", "amqp://guest:guest@localhost:5672//")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

# Create Celery app
celery_app = Celery(
    "tasks",
    broker=broker_url,
    backend=result_backend,
    include=["app.tasks"]
)

# Celery configuration
celery_app.conf.update(
    # Task serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    
    # Timezone
    timezone="UTC",
    enable_utc=True,
    
    # Task execution
    task_acks_late=True,  # Acknowledge task after completion (not before)
    task_reject_on_worker_lost=True,  # Retry if worker crashes
    worker_prefetch_multiplier=1,  # Fair task distribution (one task at a time)
    
    # Task time limits (in seconds)
    task_time_limit=300,  # Hard timeout: 5 minutes
    task_soft_time_limit=270,  # Soft timeout: 4.5 minutes
    
    # Task retry configuration
    task_default_retry_delay=60,  # Retry after 60 seconds
    task_max_retries=3,  # Maximum 3 retries
    
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_persistent=True,  # Persist results to disk
    
    # Worker settings
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks (prevent memory leaks)
    worker_disable_rate_limits=False,
    
    # Broker settings
    broker_connection_retry=True,
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=10,
    
    # Task routing (optional - for advanced use)
    task_routes={
        "app.tasks.process_heavy_task": {"queue": "heavy"},
        "app.tasks.scheduled_cleanup_task": {"queue": "scheduled"},
    },
    
    # Beat schedule for periodic tasks
    beat_schedule={
        "cleanup-old-results": {
            "task": "app.tasks.scheduled_cleanup_task",
            "schedule": crontab(hour=2, minute=0),  # Run at 2 AM daily
        },
    },
)

# Optional: Configure logging
celery_app.conf.update(
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s",
)
