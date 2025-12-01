# FastAPI Files You Already Have ✅

## Your Current Setup (No Need to Create Anything!)

```
📁 /home/rk/Documents/labs/lab-microservices-system-design/
│
├── 📁 app/                          ← Your FastAPI application
│   ├── __init__.py                  ✅ EXISTS
│   ├── main.py                      ✅ EXISTS - FastAPI routes (sync & async endpoints)
│   ├── models.py                    ✅ EXISTS - Pydantic models (request/response)
│   ├── database.py                  ✅ EXISTS - MongoDB connection
│   ├── celery_app.py                ✅ EXISTS - Celery configuration
│   └── tasks.py                     ✅ EXISTS - Background tasks (Celery)
│
├── docker-compose.yml               ✅ EXISTS - All services (API, Workers, MongoDB, Redis, RabbitMQ)
├── Dockerfile.app                   ✅ EXISTS - Container definition
├── requirements.txt                 ✅ EXISTS - Python dependencies
│
└── 📁 nginx/
    └── nginx.conf                   ✅ EXISTS - Load balancer config
```

---

## How Your Files Work Together

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT REQUEST                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  nginx/nginx.conf          ← Load balancer                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  app/main.py               ← FastAPI routes                     │
│                                                                  │
│  @app.post("/api/async/process")  ← Async endpoint              │
│      ↓                                                           │
│      Enqueues task to RabbitMQ                                  │
│      Returns task_id immediately ✅                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  app/celery_app.py         ← Celery configuration               │
│                            ← Connects to RabbitMQ & Redis       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  app/tasks.py              ← Background tasks                   │
│                                                                  │
│  @celery_app.task()                                             │
│  def process_heavy_task():  ← Runs in worker                    │
│      # Heavy processing here                                    │
│      # Updates progress                                         │
│      # Returns result                                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## What Each File Does

### 1. `app/main.py` - Your API Routes
**Purpose:** Define HTTP endpoints (routes)

**What it does:**
- ✅ Handles incoming HTTP requests
- ✅ Sync endpoints: Direct database operations (fast)
- ✅ Async endpoints: Enqueue tasks to RabbitMQ (returns immediately)
- ✅ Status endpoints: Check task progress

**Example:**
```python
@app.post("/api/async/process")  # ← Route
async def submit_task(data: str):
    task = process_heavy_task.apply_async(kwargs={"data": data})
    return {"task_id": task.id}  # ← Returns immediately
```

---

### 2. `app/tasks.py` - Your Background Tasks
**Purpose:** Define heavy processing tasks that run in workers

**What it does:**
- ✅ Contains all background task functions
- ✅ Tasks run in Celery workers (separate from API)
- ✅ Can update progress
- ✅ Can retry on failure

**Example:**
```python
@celery_app.task(bind=True)
def process_heavy_task(self, data: str):
    # Heavy processing here
    time.sleep(10)  # Simulate work
    return {"result": "done"}
```

---

### 3. `app/celery_app.py` - Celery Configuration
**Purpose:** Configure Celery (task queue system)

**What it does:**
- ✅ Connects to RabbitMQ (message broker)
- ✅ Connects to Redis (result backend)
- ✅ Sets retry policies
- ✅ Sets timeouts
- ✅ Configures task routing

**Example:**
```python
celery_app = Celery(
    "tasks",
    broker="amqp://guest@rabbitmq:5672//",  # RabbitMQ
    backend="redis://redis:6379/0"           # Redis
)
```

---

### 4. `app/models.py` - Data Models
**Purpose:** Define request/response data structures

**What it does:**
- ✅ Validates incoming data
- ✅ Defines response format
- ✅ Auto-generates API documentation

**Example:**
```python
class AsyncTaskRequest(BaseModel):
    data: str
    iterations: int = 10
    priority: str = "normal"
```

---

### 5. `app/database.py` - Database Connection
**Purpose:** Connect to MongoDB

**What it does:**
- ✅ Manages MongoDB connection
- ✅ Provides database collections
- ✅ Connection pooling

**Example:**
```python
def get_items_collection():
    return db.get_collection("items")
```

---

### 6. `docker-compose.yml` - Services Configuration
**Purpose:** Define all services (API, workers, databases)

**What it does:**
- ✅ Starts API (3 replicas)
- ✅ Starts Celery workers (3 replicas)
- ✅ Starts MongoDB, Redis, RabbitMQ
- ✅ Starts Nginx load balancer

**Example:**
```yaml
services:
  api:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0
    deploy:
      replicas: 3
  
  celery_worker:
    build: .
    command: celery -A app.celery_app worker
    deploy:
      replicas: 3
```

---

## Quick Reference: Where to Edit

| What You Want to Do | File to Edit |
|---------------------|--------------|
| Add new API endpoint | `app/main.py` |
| Add new background task | `app/tasks.py` |
| Change Celery settings | `app/celery_app.py` |
| Add new data model | `app/models.py` |
| Change database logic | `app/database.py` |
| Add/remove services | `docker-compose.yml` |
| Change load balancer | `nginx/nginx.conf` |

---

## Example: Adding a New Custom Task

### Step 1: Add Task to `app/tasks.py`
```python
@celery_app.task(bind=True, name="app.tasks.send_email")
def send_email(self, to: str, subject: str, body: str):
    """Send email in background"""
    # Your email sending logic
    import smtplib
    # ... email code ...
    return {"status": "sent", "to": to}
```

### Step 2: Add Route to `app/main.py`
```python
from app.tasks import send_email

@app.post("/api/send-email")
async def trigger_email(to: str, subject: str, body: str):
    """Trigger email sending"""
    task = send_email.apply_async(
        kwargs={"to": to, "subject": subject, "body": body}
    )
    return {"task_id": task.id, "status": "queued"}
```

### Step 3: Restart
```bash
docker compose up -d --build
```

### Step 4: Test
```bash
curl -X POST http://localhost/api/send-email \
  -H "Content-Type: application/json" \
  -d '{"to": "user@example.com", "subject": "Test", "body": "Hello"}'
```

---

## ❌ Files You DON'T Need (Django Only)

These files are ONLY for Django framework:

```
❌ myproject/celery.py       ← Django Celery config (you have app/celery_app.py)
❌ myproject/settings.py     ← Django settings (you have .env)
❌ api/serializers.py        ← Django REST Framework (you have app/models.py)
❌ api/views.py              ← Django views (you have app/main.py)
❌ manage.py                 ← Django management (you have docker-compose)
```

**Don't create these!** They're for a completely different framework.

---

## Summary

✅ **You already have all the files you need!**

Your FastAPI setup is complete with:
- `app/main.py` - API routes
- `app/tasks.py` - Background tasks
- `app/celery_app.py` - Celery config
- `app/models.py` - Data models
- `app/database.py` - Database connection
- `docker-compose.yml` - Services

❌ **You don't need to create:**
- Django files (`myproject/celery.py`, `api/serializers.py`, etc.)
- These are only for Django framework

🚀 **To add custom tasks:**
1. Edit `app/tasks.py` - Add your task function
2. Edit `app/main.py` - Add API endpoint
3. Run `docker compose up -d --build`
