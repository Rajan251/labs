# Django & FastAPI Implementation Guide
## Complete Code-Level Changes for Queue-Based Microservices Architecture

This guide shows **exactly where to make changes** in your code for implementing a production-ready queue-based microservices system using either **Django** or **FastAPI**.

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [FastAPI Implementation (Your Current Setup)](#fastapi-implementation)
3. [Django Implementation (Alternative)](#django-implementation)
4. [Component-by-Component Comparison](#component-comparison)
5. [Step-by-Step Implementation](#step-by-step-implementation)
6. [Testing & Verification](#testing-verification)

---

## 🏗️ Architecture Overview

Both Django and FastAPI follow the same architectural pattern:

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Nginx (LB)     │  ← Rate limiting, load balancing
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  API Layer      │  ← Django/FastAPI (3+ replicas)
│  (Sync Routes)  │  ← Returns immediately
└──────┬──────────┘
       │
       ├─────────────┬──────────────┬──────────────┐
       ▼             ▼              ▼              ▼
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ MongoDB  │  │ RabbitMQ │  │  Redis   │  │  Celery  │
│          │  │  (Queue) │  │ (Cache)  │  │  Worker  │
└──────────┘  └──────────┘  └──────────┘  └──────────┘
                                                 │
                                                 ▼
                                          Heavy Processing
```

**Key Principle**: API returns task_id immediately → Workers process in background

---

## 🚀 FastAPI Implementation (Your Current Setup)

### File Structure
```
project/
├── app/
│   ├── __init__.py
│   ├── main.py              ← FastAPI app & routes
│   ├── models.py            ← Pydantic models
│   ├── database.py          ← MongoDB connection
│   ├── celery_app.py        ← Celery configuration
│   └── tasks.py             ← Background tasks
├── docker-compose.yml       ← All services
├── Dockerfile.app           ← App container
├── requirements.txt         ← Dependencies
└── nginx/
    └── nginx.conf           ← Load balancer config
```

### 1️⃣ **FastAPI Main Application** (`app/main.py`)

#### Where to Make Changes:

**A. Sync Endpoints (Direct Database Access)**
```python
# app/main.py - Lines 140-172

@app.get("/api/items", response_model=List[ItemResponse])
async def get_items(skip: int = 0, limit: int = 100):
    """
    ✅ SYNC ENDPOINT - Returns immediately
    Use for: Simple CRUD, queries, lightweight operations
    """
    collection = get_items_collection()
    cursor = collection.find().skip(skip).limit(limit)
    
    items = []
    for doc in cursor:
        items.append(ItemResponse(
            id=str(doc["_id"]),
            name=doc["name"],
            # ... other fields
        ))
    
    return items  # ← Returns immediately (fast)
```

**B. Async Endpoints (Queue-Based Processing)**
```python
# app/main.py - Lines 253-283

@app.post("/api/async/process", status_code=202)
async def submit_async_task(task_request: AsyncTaskRequest):
    """
    ✅ ASYNC ENDPOINT - Returns task_id immediately
    Use for: Heavy processing, long-running operations
    """
    # Enqueue task to RabbitMQ via Celery
    task = process_heavy_task.apply_async(
        kwargs={
            "data": task_request.data,
            "iterations": task_request.iterations
        },
        priority={"low": 3, "normal": 5, "high": 9}.get(task_request.priority, 5)
    )
    
    # Return immediately with task_id
    return AsyncTaskResponse(
        task_id=task.id,  # ← Client uses this to check status
        status="PENDING",
        message="Task submitted. Check /api/async/status/{task_id}"
    )
```

**C. Task Status Endpoint**
```python
# app/main.py - Lines 286-317

@app.get("/api/async/status/{task_id}")
async def get_task_status(task_id: str):
    """
    ✅ CHECK TASK STATUS
    Client polls this to get results
    """
    task_result = celery_app.AsyncResult(task_id)
    
    response = TaskStatusResponse(
        task_id=task_id,
        status=task_result.status  # PENDING, PROGRESS, SUCCESS, FAILURE
    )
    
    if task_result.successful():
        response.result = task_result.result  # ← Final result
    elif task_result.state == 'PROGRESS':
        response.progress = task_result.info  # ← Progress updates
    
    return response
```

### 2️⃣ **Celery Tasks** (`app/tasks.py`)

#### Where to Define Background Tasks:

```python
# app/tasks.py - Lines 34-148

@celery_app.task(
    bind=True,
    name="app.tasks.process_heavy_task",
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True
)
def process_heavy_task(self, data: str, iterations: int = 10):
    """
    ✅ BACKGROUND TASK - Runs in Celery worker
    This is where heavy processing happens
    """
    task_id = self.request.id
    
    # Heavy processing loop
    for i in range(iterations):
        # Do actual work here
        time.sleep(0.5)  # Simulate CPU work
        processed = f"{data.upper()}_ITERATION_{i+1}"
        
        # Update progress (visible in status endpoint)
        self.update_state(
            state='PROGRESS',
            meta={
                'current': i + 1,
                'total': iterations,
                'progress': int((i + 1) / iterations * 100)
            }
        )
    
    # Store result in MongoDB
    result = {
        "task_id": task_id,
        "status": "completed",
        "processed_items": processed_items
    }
    
    collection = get_task_results_collection()
    collection.insert_one(result)
    
    return result  # ← This becomes task_result.result
```

### 3️⃣ **Celery Configuration** (`app/celery_app.py`)

```python
# app/celery_app.py

from celery import Celery
import os

# Create Celery app
celery_app = Celery(
    "myapp",
    broker=os.getenv("CELERY_BROKER_URL", "amqp://guest@rabbitmq:5672//"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")
)

# Configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Performance settings
    worker_prefetch_multiplier=1,  # ← One task at a time
    worker_max_tasks_per_child=1000,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Task routing
    task_routes={
        'app.tasks.process_heavy_task': {'queue': 'default'},
        'app.tasks.scheduled_cleanup_task': {'queue': 'periodic'},
    }
)

# Auto-discover tasks
celery_app.autodiscover_tasks(['app'])
```

### 4️⃣ **Pydantic Models** (`app/models.py`)

```python
# app/models.py

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

# Request models
class AsyncTaskRequest(BaseModel):
    data: str = Field(..., description="Data to process")
    iterations: int = Field(default=10, ge=1, le=1000)
    priority: str = Field(default="normal", pattern="^(low|normal|high)$")

# Response models
class AsyncTaskResponse(BaseModel):
    task_id: str
    status: str
    message: str

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str  # PENDING, PROGRESS, SUCCESS, FAILURE
    result: Optional[Dict[str, Any]] = None
    progress: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
```

### 5️⃣ **Docker Compose** (`docker-compose.yml`)

```yaml
version: '3.8'

services:
  # API Service (3 replicas)
  api:
    build:
      context: .
      dockerfile: Dockerfile.app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
    deploy:
      replicas: 3
    environment:
      - MONGODB_URL=mongodb://mongodb:27017
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672//
    depends_on:
      - mongodb
      - redis
      - rabbitmq
  
  # Celery Worker (3 replicas)
  celery_worker:
    build:
      context: .
      dockerfile: Dockerfile.app
    command: celery -A app.celery_app worker --loglevel=info --concurrency=4
    deploy:
      replicas: 3
    environment:
      - MONGODB_URL=mongodb://mongodb:27017
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672//
    depends_on:
      - mongodb
      - redis
      - rabbitmq
  
  # Nginx Load Balancer
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - api
  
  # MongoDB
  mongodb:
    image: mongo:6
    volumes:
      - mongodb_data:/data/db
  
  # Redis
  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
  
  # RabbitMQ
  rabbitmq:
    image: rabbitmq:3-management-alpine
    ports:
      - "15672:15672"  # Management UI
    environment:
      - RABBITMQ_DEFAULT_USER=guest
      - RABBITMQ_DEFAULT_PASS=guest

volumes:
  mongodb_data:
```

---

## 🐍 Django Implementation (Alternative)

### File Structure
```
project/
├── myproject/
│   ├── __init__.py
│   ├── settings.py          ← Django settings
│   ├── urls.py              ← URL routing
│   ├── celery.py            ← Celery config
│   └── wsgi.py
├── api/
│   ├── __init__.py
│   ├── views.py             ← API views (routes)
│   ├── models.py            ← Django ORM models
│   ├── serializers.py       ← DRF serializers
│   ├── tasks.py             ← Celery tasks
│   └── urls.py              ← API URLs
├── manage.py
├── requirements.txt
└── docker-compose.yml
```

### 1️⃣ **Django Settings** (`myproject/settings.py`)

```python
# myproject/settings.py

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'rest_framework',  # ← Django REST Framework
    'api',  # ← Your API app
]

# Database (MongoDB via djongo)
DATABASES = {
    'default': {
        'ENGINE': 'djongo',
        'NAME': 'myapp',
        'CLIENT': {
            'host': os.getenv('MONGODB_URL', 'mongodb://localhost:27017'),
        }
    }
}

# Celery Configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'amqp://guest@rabbitmq:5672//')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
}

# Redis Cache
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

### 2️⃣ **Celery Configuration** (`myproject/celery.py`)

```python
# myproject/celery.py

from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

# Create Celery app
app = Celery('myproject')

# Load config from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# Configuration
app.conf.update(
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)
```

### 3️⃣ **Django Models** (`api/models.py`)

```python
# api/models.py

from djongo import models
from django.utils import timezone

class Item(models.Model):
    """Item model using MongoDB via djongo"""
    _id = models.ObjectIdField()
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'items'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class TaskResult(models.Model):
    """Store Celery task results in MongoDB"""
    _id = models.ObjectIdField()
    task_id = models.CharField(max_length=255, unique=True)
    result = models.JSONField()
    status = models.CharField(max_length=50)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'task_results'
```

### 4️⃣ **DRF Serializers** (`api/serializers.py`)

```python
# api/serializers.py

from rest_framework import serializers
from .models import Item

class ItemSerializer(serializers.ModelSerializer):
    """Serializer for Item model"""
    id = serializers.CharField(source='_id', read_only=True)
    
    class Meta:
        model = Item
        fields = ['id', 'name', 'description', 'metadata', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class AsyncTaskRequestSerializer(serializers.Serializer):
    """Request serializer for async tasks"""
    data = serializers.CharField(required=True)
    iterations = serializers.IntegerField(default=10, min_value=1, max_value=1000)
    priority = serializers.ChoiceField(
        choices=['low', 'normal', 'high'],
        default='normal'
    )


class AsyncTaskResponseSerializer(serializers.Serializer):
    """Response serializer for async tasks"""
    task_id = serializers.CharField()
    status = serializers.CharField()
    message = serializers.CharField()


class TaskStatusSerializer(serializers.Serializer):
    """Task status response"""
    task_id = serializers.CharField()
    status = serializers.CharField()
    result = serializers.JSONField(required=False, allow_null=True)
    progress = serializers.JSONField(required=False, allow_null=True)
    error = serializers.CharField(required=False, allow_null=True)
```

### 5️⃣ **Django Views (API Routes)** (`api/views.py`)

```python
# api/views.py

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.cache import cache
from celery.result import AsyncResult

from .models import Item, TaskResult
from .serializers import (
    ItemSerializer, AsyncTaskRequestSerializer,
    AsyncTaskResponseSerializer, TaskStatusSerializer
)
from .tasks import process_heavy_task

# ============================================================================
# SYNC ENDPOINTS (Direct Database Access)
# ============================================================================

@api_view(['GET', 'POST'])
def items_list(request):
    """
    GET: List all items (sync)
    POST: Create new item (sync)
    """
    if request.method == 'GET':
        # ✅ SYNC - Returns immediately
        items = Item.objects.all()[:100]  # Limit to 100
        serializer = ItemSerializer(items, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        # ✅ SYNC - Returns immediately
        serializer = ItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def item_detail(request, item_id):
    """Get single item by ID (sync)"""
    try:
        item = Item.objects.get(_id=item_id)
        serializer = ItemSerializer(item)
        return Response(serializer.data)
    except Item.DoesNotExist:
        return Response(
            {'error': f'Item {item_id} not found'},
            status=status.HTTP_404_NOT_FOUND
        )


# ============================================================================
# ASYNC ENDPOINTS (Queue-Based Processing)
# ============================================================================

@api_view(['POST'])
def submit_async_task(request):
    """
    ✅ ASYNC ENDPOINT - Returns task_id immediately
    Heavy processing happens in background worker
    """
    serializer = AsyncTaskRequestSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Enqueue task to RabbitMQ via Celery
    task = process_heavy_task.apply_async(
        kwargs={
            'data': serializer.validated_data['data'],
            'iterations': serializer.validated_data['iterations']
        },
        priority={
            'low': 3,
            'normal': 5,
            'high': 9
        }.get(serializer.validated_data['priority'], 5)
    )
    
    # Return immediately with task_id
    response_data = {
        'task_id': task.id,
        'status': 'PENDING',
        'message': f'Task submitted. Check /api/async/status/{task.id}'
    }
    
    return Response(response_data, status=status.HTTP_202_ACCEPTED)


@api_view(['GET'])
def get_task_status(request, task_id):
    """
    ✅ CHECK TASK STATUS
    Client polls this to get results
    """
    # Get task result from Celery
    task_result = AsyncResult(task_id)
    
    response_data = {
        'task_id': task_id,
        'status': task_result.status
    }
    
    if task_result.successful():
        response_data['result'] = task_result.result
    elif task_result.failed():
        response_data['error'] = str(task_result.info)
    elif task_result.state == 'PROGRESS':
        response_data['progress'] = task_result.info
    
    return Response(response_data)


@api_view(['GET'])
def health_check(request):
    """Health check endpoint"""
    from django.db import connection
    from myproject.celery import app as celery_app
    
    services = {}
    
    # Check MongoDB
    try:
        connection.ensure_connection()
        services['mongodb'] = 'connected'
    except Exception:
        services['mongodb'] = 'disconnected'
    
    # Check Redis
    try:
        cache.set('health_check', 'ok', 10)
        services['redis'] = 'connected' if cache.get('health_check') == 'ok' else 'disconnected'
    except Exception:
        services['redis'] = 'disconnected'
    
    # Check RabbitMQ
    try:
        celery_app.control.inspect().ping()
        services['rabbitmq'] = 'connected'
    except Exception:
        services['rabbitmq'] = 'disconnected'
    
    overall_status = 'healthy' if all(
        s == 'connected' for s in services.values()
    ) else 'degraded'
    
    return Response({
        'status': overall_status,
        'timestamp': timezone.now(),
        'services': services
    })
```

### 6️⃣ **Celery Tasks** (`api/tasks.py`)

```python
# api/tasks.py

from celery import Task
from celery.exceptions import SoftTimeLimitExceeded
from myproject.celery import app as celery_app
from .models import TaskResult
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class CallbackTask(Task):
    """Base task with callbacks"""
    
    def on_success(self, retval, task_id, args, kwargs):
        logger.info(f"Task {task_id} completed successfully")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Task {task_id} failed: {exc}")
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        logger.warning(f"Task {task_id} retrying: {exc}")


@celery_app.task(
    bind=True,
    base=CallbackTask,
    name="api.tasks.process_heavy_task",
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True
)
def process_heavy_task(self, data: str, iterations: int = 10):
    """
    ✅ BACKGROUND TASK - Runs in Celery worker
    This is where heavy processing happens
    """
    task_id = self.request.id
    logger.info(f"Starting heavy task {task_id}: data={data}, iterations={iterations}")
    
    try:
        processed_items = []
        
        # Heavy processing loop
        for i in range(iterations):
            # Simulate CPU work
            time.sleep(0.5)
            
            # Process data
            processed = f"{data.upper()}_ITERATION_{i+1}"
            processed_items.append(processed)
            
            # Update progress (visible in status endpoint)
            progress = int((i + 1) / iterations * 100)
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': i + 1,
                    'total': iterations,
                    'progress': progress,
                    'status': f'Processing iteration {i+1}/{iterations}'
                }
            )
            
            logger.debug(f"Task {task_id}: {progress}% complete")
        
        # Task completed successfully
        result = {
            "task_id": task_id,
            "input_data": data,
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
            "processed_items": processed_items,
            "total_processed": len(processed_items)
        }
        
        # Store result in MongoDB
        try:
            TaskResult.objects.create(
                task_id=task_id,
                result=result,
                status="completed"
            )
            logger.info(f"Task {task_id} result stored in MongoDB")
        except Exception as e:
            logger.error(f"Failed to store task result: {e}")
        
        logger.info(f"Task {task_id} completed: processed {len(processed_items)} items")
        
        return result
        
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}", exc_info=True)
        
        # Store error in MongoDB
        try:
            TaskResult.objects.create(
                task_id=task_id,
                result={"error": str(e)},
                status="failed"
            )
        except Exception as store_error:
            logger.error(f"Failed to store error: {store_error}")
        
        # Retry the task
        raise self.retry(exc=e, countdown=60)
```

### 7️⃣ **URL Configuration** (`api/urls.py`)

```python
# api/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Health check
    path('health', views.health_check, name='health'),
    
    # Sync endpoints
    path('api/items', views.items_list, name='items-list'),
    path('api/items/<str:item_id>', views.item_detail, name='item-detail'),
    
    # Async endpoints
    path('api/async/process', views.submit_async_task, name='async-process'),
    path('api/async/status/<str:task_id>', views.get_task_status, name='task-status'),
]
```

```python
# myproject/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('api.urls')),
]
```

### 8️⃣ **Django App Initialization** (`myproject/__init__.py`)

```python
# myproject/__init__.py

from __future__ import absolute_import, unicode_literals

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from .celery import app as celery_app

__all__ = ('celery_app',)
```

### 9️⃣ **Requirements** (`requirements.txt`)

```txt
# Django Requirements
Django==4.2.7
djangorestframework==3.14.0
djongo==1.3.6
pymongo==3.12.3
django-redis==5.4.0

# Celery
celery==5.3.4
redis==5.0.1

# AMQP (RabbitMQ)
amqp==5.2.0
kombu==5.3.4

# Server
gunicorn==21.2.0
uvicorn[standard]==0.24.0  # If using ASGI

# Utilities
python-dotenv==1.0.0
```

### 🔟 **Docker Configuration**

```dockerfile
# Dockerfile.django

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Collect static files (if needed)
RUN python manage.py collectstatic --noinput || true

# Run migrations (optional, can be done separately)
# RUN python manage.py migrate --noinput

EXPOSE 8000

# Default command (can be overridden in docker-compose)
CMD ["gunicorn", "myproject.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
```

```yaml
# docker-compose.yml for Django

version: '3.8'

services:
  # Django API Service (3 replicas)
  api:
    build:
      context: .
      dockerfile: Dockerfile.django
    command: gunicorn myproject.wsgi:application --bind 0.0.0.0:8000 --workers 4
    deploy:
      replicas: 3
    environment:
      - DJANGO_SETTINGS_MODULE=myproject.settings
      - MONGODB_URL=mongodb://mongodb:27017
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672//
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - mongodb
      - redis
      - rabbitmq
  
  # Celery Worker (3 replicas)
  celery_worker:
    build:
      context: .
      dockerfile: Dockerfile.django
    command: celery -A myproject worker --loglevel=info --concurrency=4
    deploy:
      replicas: 3
    environment:
      - DJANGO_SETTINGS_MODULE=myproject.settings
      - MONGODB_URL=mongodb://mongodb:27017
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672//
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - mongodb
      - redis
      - rabbitmq
  
  # Celery Beat (Scheduler for periodic tasks)
  celery_beat:
    build:
      context: .
      dockerfile: Dockerfile.django
    command: celery -A myproject beat --loglevel=info
    environment:
      - DJANGO_SETTINGS_MODULE=myproject.settings
      - MONGODB_URL=mongodb://mongodb:27017
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672//
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - mongodb
      - redis
      - rabbitmq
  
  # Nginx Load Balancer
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - api
  
  # MongoDB
  mongodb:
    image: mongo:6
    volumes:
      - mongodb_data:/data/db
  
  # Redis
  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
  
  # RabbitMQ
  rabbitmq:
    image: rabbitmq:3-management-alpine
    ports:
      - "15672:15672"
    environment:
      - RABBITMQ_DEFAULT_USER=guest
      - RABBITMQ_DEFAULT_PASS=guest

volumes:
  mongodb_data:
```

---

## 🔄 Component-by-Component Comparison

| Component | FastAPI | Django |
|-----------|---------|--------|
| **Web Framework** | FastAPI (ASGI) | Django + DRF (WSGI/ASGI) |
| **Server** | Uvicorn | Gunicorn |
| **Models** | Pydantic | Django ORM (djongo) |
| **Serialization** | Pydantic BaseModel | DRF Serializers |
| **Routes** | `@app.get()` decorators | `@api_view()` decorators |
| **Database** | PyMongo (direct) | djongo (ORM) |
| **Celery Config** | `celery_app.py` | `myproject/celery.py` |
| **Tasks** | `@celery_app.task()` | `@celery_app.task()` (same) |
| **Async Syntax** | `async def` (native) | `def` (sync by default) |
| **Validation** | Pydantic (automatic) | DRF Serializers (manual) |

---

## 📝 Step-by-Step Implementation

### For FastAPI (Your Current Setup)

#### Step 1: Define Your Heavy Task
```python
# app/tasks.py

@celery_app.task(bind=True, name="app.tasks.my_heavy_task")
def my_heavy_task(self, user_id: int, data: dict):
    """Your actual heavy processing logic"""
    # Example: Image processing, data analysis, report generation
    
    # Update progress
    self.update_state(state='PROGRESS', meta={'progress': 50})
    
    # Do work
    result = process_data(data)
    
    # Store in DB
    collection = get_results_collection()
    collection.insert_one({"user_id": user_id, "result": result})
    
    return result
```

#### Step 2: Create API Endpoint to Submit Task
```python
# app/main.py

@app.post("/api/submit-job")
async def submit_job(user_id: int, data: dict):
    """Submit heavy job to queue"""
    task = my_heavy_task.apply_async(
        kwargs={"user_id": user_id, "data": data}
    )
    
    return {"task_id": task.id, "status": "submitted"}
```

#### Step 3: Create Status Check Endpoint
```python
# app/main.py

@app.get("/api/job-status/{task_id}")
async def check_job_status(task_id: str):
    """Check job status"""
    result = celery_app.AsyncResult(task_id)
    
    if result.successful():
        return {"status": "completed", "result": result.result}
    elif result.state == 'PROGRESS':
        return {"status": "processing", "progress": result.info}
    else:
        return {"status": result.state}
```

#### Step 4: Run Services
```bash
# Build and start
docker compose up -d --build

# Check logs
docker compose logs -f api
docker compose logs -f celery_worker
```

### For Django

#### Step 1: Create Django Project
```bash
# Create project
django-admin startproject myproject
cd myproject
python manage.py startapp api

# Install dependencies
pip install django djangorestframework celery redis djongo
```

#### Step 2: Configure Settings
```python
# myproject/settings.py
# Add all the settings shown in Django section above
```

#### Step 3: Create Models, Serializers, Views
```python
# Follow the code examples in Django section above
# api/models.py - Define models
# api/serializers.py - Define serializers
# api/views.py - Define views
# api/tasks.py - Define Celery tasks
```

#### Step 4: Configure URLs
```python
# api/urls.py and myproject/urls.py
# Follow URL configuration shown above
```

#### Step 5: Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

#### Step 6: Run with Docker
```bash
# Use docker-compose.yml shown in Django section
docker compose up -d --build
```

---

## 🧪 Testing & Verification

### Test Sync Endpoint (Fast)
```bash
# Should return immediately
curl -X POST http://localhost/api/items \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Item", "description": "Quick test"}'
```

### Test Async Endpoint (Queue-Based)
```bash
# Submit task (returns immediately with task_id)
curl -X POST http://localhost/api/async/process \
  -H "Content-Type: application/json" \
  -d '{"data": "heavy task", "iterations": 100, "priority": "high"}'

# Response:
# {
#   "task_id": "abc-123-def",
#   "status": "PENDING",
#   "message": "Task submitted..."
# }

# Check status (poll this)
curl http://localhost/api/async/status/abc-123-def

# Response (in progress):
# {
#   "task_id": "abc-123-def",
#   "status": "PROGRESS",
#   "progress": {"current": 50, "total": 100, "progress": 50}
# }

# Response (completed):
# {
#   "task_id": "abc-123-def",
#   "status": "SUCCESS",
#   "result": {"processed_items": [...], "total_processed": 100}
# }
```

### Monitor Queue
```bash
# RabbitMQ Management UI
open http://localhost:15672
# Username: guest, Password: guest

# Check worker logs
docker compose logs -f celery_worker

# Check task in Redis
docker compose exec redis redis-cli
> KEYS celery-task-meta-*
> GET celery-task-meta-abc-123-def
```

### Load Test
```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test async endpoint (should not freeze)
ab -n 1000 -c 100 -p task.json -T application/json \
  http://localhost/api/async/process

# All requests should return immediately with task_id
```

---

## 🎯 Key Takeaways

### When to Use Sync vs Async

| Operation | Type | Why |
|-----------|------|-----|
| Get list of items | **SYNC** | Fast database query |
| Create/Update item | **SYNC** | Simple database write |
| Search/Filter | **SYNC** | Indexed queries are fast |
| Image processing | **ASYNC** | CPU-intensive |
| Video encoding | **ASYNC** | Long-running |
| Sending emails | **ASYNC** | External API calls |
| Report generation | **ASYNC** | Complex calculations |
| Batch imports | **ASYNC** | Large data processing |

### Architecture Benefits

✅ **API never freezes** - Returns task_id immediately  
✅ **Horizontal scaling** - Add more workers as needed  
✅ **Fault tolerance** - Failed tasks auto-retry  
✅ **Progress tracking** - Real-time status updates  
✅ **Priority queues** - High-priority tasks first  
✅ **Load balancing** - Nginx distributes requests  
✅ **Resource isolation** - Workers separate from API  

---

## 📚 Additional Resources

- **FastAPI**: https://fastapi.tiangolo.com/
- **Django REST Framework**: https://www.django-rest-framework.org/
- **Celery**: https://docs.celeryproject.org/
- **RabbitMQ**: https://www.rabbitmq.com/documentation.html
- **Redis**: https://redis.io/documentation
- **MongoDB**: https://docs.mongodb.com/

---

## 🆘 Common Issues & Solutions

### Issue: Tasks not processing
**Solution**: Check worker logs
```bash
docker compose logs celery_worker
docker compose restart celery_worker
```

### Issue: API returns 500 error
**Solution**: Check RabbitMQ connection
```bash
docker compose ps rabbitmq
docker compose logs rabbitmq
```

### Issue: Task status always PENDING
**Solution**: Check Redis backend
```bash
docker compose exec redis redis-cli ping
# Should return PONG
```

### Issue: High memory usage
**Solution**: Reduce worker concurrency
```yaml
# docker-compose.yml
command: celery -A app.celery_app worker --concurrency=2
```

---

**Need help?** Check the logs:
```bash
docker compose logs -f
```
