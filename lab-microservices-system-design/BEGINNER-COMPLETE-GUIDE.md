# 🎓 Complete Beginner's Guide to Queue-Based Microservices

## 📚 What You'll Learn

By the end of this guide, you'll understand:
- ✅ What microservices architecture is
- ✅ Why we use queues for background processing
- ✅ How FastAPI, Celery, RabbitMQ, Redis, and MongoDB work together
- ✅ How to implement this in your own project
- ✅ How to test and verify everything works

**Time Required:** 30-45 minutes  
**Difficulty:** Beginner-friendly (no prior experience needed)

---

## 🎯 Part 1: Understanding the Concepts

### What Problem Are We Solving?

**The Problem:**
```
User submits a request → API processes it (takes 10 seconds) → User waits 😴
                         ↓
                    API is BLOCKED
                    Other users can't use it!
```

**The Solution:**
```
User submits a request → API returns task_id (instant) → User gets response ✅
                         ↓
                    Task goes to queue
                         ↓
                    Worker processes in background
                         ↓
                    User checks status later
```

### Real-World Example

**Bad Approach (Without Queue):**
```python
@app.post("/generate-report")
def generate_report(user_id: int):
    # This takes 10 minutes!
    report = create_pdf_report(user_id)  # ← API is frozen for 10 minutes
    return report
```
❌ Problem: API is blocked, other users can't access it!

**Good Approach (With Queue):**
```python
@app.post("/generate-report")
def generate_report(user_id: int):
    # Send to queue and return immediately
    task = create_pdf_report_task.apply_async(kwargs={"user_id": user_id})
    return {"task_id": task.id, "status": "processing"}  # ← Returns in 0.1 seconds!
```
✅ Solution: API returns immediately, worker handles the heavy work!

---

## 🏗️ Part 2: Understanding the Architecture

### The Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         YOUR SYSTEM                             │
└─────────────────────────────────────────────────────────────────┘

1. CLIENT (Browser/Mobile App)
   ↓
2. NGINX (Load Balancer)
   ↓
3. FASTAPI (Your API - 3 copies running)
   ↓
4. RABBITMQ (Message Queue - like a to-do list)
   ↓
5. CELERY WORKER (Background processor - 3 copies running)
   ↓
6. MONGODB (Database - stores results)
   ↓
7. REDIS (Cache - stores task status)
```

### What Each Component Does

| Component | What It Does | Real-World Analogy |
|-----------|--------------|-------------------|
| **FastAPI** | Handles HTTP requests | Restaurant waiter (takes orders) |
| **RabbitMQ** | Stores tasks in queue | Kitchen order board |
| **Celery Worker** | Processes tasks | Chef (cooks the food) |
| **MongoDB** | Stores data | Storage room (keeps ingredients) |
| **Redis** | Caches results | Notepad (quick notes) |
| **Nginx** | Distributes traffic | Restaurant host (seats customers) |

---

## 📁 Part 3: Understanding Your Files

### Your Project Structure

```
/home/rk/Documents/labs/lab-microservices-system-design/
│
├── app/                          ← Your application code
│   ├── main.py                   ← API routes (waiter)
│   ├── tasks.py                  ← Background tasks (chef)
│   ├── celery_app.py             ← Celery configuration
│   ├── models.py                 ← Data structures
│   └── database.py               ← MongoDB connection
│
├── docker-compose.yml            ← Starts all services
├── Dockerfile.app                ← Builds your app container
├── requirements.txt              ← Python packages needed
│
└── nginx/
    └── nginx.conf                ← Load balancer settings
```

### What Each File Does

#### 1. `app/main.py` - Your API Routes

**Purpose:** Define HTTP endpoints that users can call

**Example:**
```python
@app.post("/api/async/process")
async def submit_task(data: str):
    """
    User calls this endpoint
    API returns immediately with task_id
    """
    task = process_heavy_task.apply_async(kwargs={"data": data})
    return {"task_id": task.id}  # ← Returns in milliseconds!
```

**When user calls this:**
```bash
curl -X POST http://localhost/api/async/process -d '{"data": "hello"}'
```

**They get back:**
```json
{
  "task_id": "abc-123-def",
  "status": "PENDING"
}
```

---

#### 2. `app/tasks.py` - Background Tasks

**Purpose:** Define heavy processing that runs in workers

**Example:**
```python
@celery_app.task(bind=True)
def process_heavy_task(self, data: str):
    """
    This runs in a WORKER (not in API)
    Can take as long as needed
    """
    # Heavy processing
    time.sleep(10)  # Simulate 10 seconds of work
    
    # Update progress
    self.update_state(state='PROGRESS', meta={'progress': 50})
    
    # More work
    result = do_complex_calculation(data)
    
    return result  # ← Stored in Redis
```

**This runs in the background while API handles other requests!**

---

#### 3. `app/celery_app.py` - Celery Configuration

**Purpose:** Configure how Celery connects to RabbitMQ and Redis

**Example:**
```python
celery_app = Celery(
    "tasks",
    broker="amqp://guest@rabbitmq:5672//",  # ← RabbitMQ (queue)
    backend="redis://redis:6379/0"           # ← Redis (results)
)
```

**What this does:**
- Connects to RabbitMQ to get tasks
- Connects to Redis to store results
- Configures retry policies, timeouts, etc.

---

#### 4. `app/models.py` - Data Structures

**Purpose:** Define what data looks like (validation)

**Example:**
```python
class AsyncTaskRequest(BaseModel):
    data: str                    # Required field
    iterations: int = 10         # Optional, default 10
    priority: str = "normal"     # Optional, default "normal"
```

**This ensures users send correct data:**
```python
# ✅ Valid
{"data": "hello", "iterations": 5}

# ❌ Invalid (missing 'data')
{"iterations": 5}
```

---

#### 5. `docker-compose.yml` - Service Configuration

**Purpose:** Start all services (API, workers, databases)

**Example:**
```yaml
services:
  api:                    # FastAPI (3 copies)
    build: .
    command: uvicorn app.main:app
    deploy:
      replicas: 3
  
  celery_worker:          # Workers (3 copies)
    build: .
    command: celery -A app.celery_app worker
    deploy:
      replicas: 3
  
  mongodb:                # Database
    image: mongo:6
  
  redis:                  # Cache
    image: redis:7
  
  rabbitmq:               # Queue
    image: rabbitmq:3
```

---

## 🚀 Part 4: Step-by-Step Implementation

### Prerequisites

Before starting, make sure you have:
```bash
# Check Docker
docker --version
# Should show: Docker version 20.10+ or higher

# Check Docker Compose
docker compose version
# Should show: Docker Compose version 2.0+ or higher
```

**Don't have Docker?** Follow: `DEPLOY-02-DOCKER-INSTALL.md`

---

### Step 1: Navigate to Your Project

```bash
cd /home/rk/Documents/labs/lab-microservices-system-design
```

**What this does:** Changes to your project directory

---

### Step 2: Check Your Files

```bash
ls -la app/
```

**You should see:**
```
app/
├── __init__.py
├── main.py          ✅ API routes
├── tasks.py         ✅ Background tasks
├── celery_app.py    ✅ Celery config
├── models.py        ✅ Data models
└── database.py      ✅ Database connection
```

**All files exist?** ✅ Great! Continue to Step 3.

---

### Step 3: Understand the Flow

Let's trace what happens when a user submits a task:

```
1. User sends request
   ↓
   curl -X POST http://localhost/api/async/process -d '{"data": "hello"}'

2. Nginx receives it
   ↓
   nginx/nginx.conf → Forwards to one of 3 API instances

3. FastAPI receives it
   ↓
   app/main.py → @app.post("/api/async/process")
   
4. API enqueues task
   ↓
   task = process_heavy_task.apply_async(...)
   ↓
   Task sent to RabbitMQ queue
   
5. API returns immediately
   ↓
   return {"task_id": "abc-123", "status": "PENDING"}
   ↓
   User gets response in 0.1 seconds! ✅

6. Worker picks up task (in background)
   ↓
   Celery worker gets task from RabbitMQ
   ↓
   app/tasks.py → def process_heavy_task(...)
   
7. Worker processes task
   ↓
   Does heavy work (10 seconds, 10 minutes, doesn't matter!)
   ↓
   Updates progress in Redis
   
8. Worker stores result
   ↓
   Saves to MongoDB
   ↓
   Updates status in Redis to "SUCCESS"

9. User checks status
   ↓
   curl http://localhost/api/async/status/abc-123
   ↓
   Gets: {"status": "SUCCESS", "result": {...}}
```

---

### Step 4: Start the Services

```bash
# Build Docker images
docker compose build

# Start all services
docker compose up -d

# Check status
docker compose ps
```

**What this does:**
- Builds your FastAPI app into a Docker image
- Starts 3 API instances
- Starts 3 Celery workers
- Starts MongoDB, Redis, RabbitMQ, Nginx

**Expected output:**
```
NAME                    STATUS
api-1                   Up
api-2                   Up
api-3                   Up
celery_worker-1         Up
celery_worker-2         Up
celery_worker-3         Up
mongodb                 Up
redis                   Up
rabbitmq                Up
nginx                   Up
```

---

### Step 5: Verify Services Are Running

```bash
# Check health endpoint
curl http://localhost/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "services": {
    "mongodb": "connected",
    "redis": "connected",
    "rabbitmq": "connected"
  }
}
```

✅ All services connected? Great! Continue to Step 6.

❌ Some services disconnected? Check logs:
```bash
docker compose logs mongodb
docker compose logs redis
docker compose logs rabbitmq
```

---

### Step 6: Test Sync Endpoint (Fast)

**What is a sync endpoint?**
- Processes request immediately
- Returns result right away
- Use for: Simple database queries, CRUD operations

**Test it:**
```bash
# Create an item
curl -X POST http://localhost/api/items \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Item",
    "description": "My first item",
    "metadata": {"category": "test"}
  }'
```

**Expected response (immediate):**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "name": "Test Item",
  "description": "My first item",
  "metadata": {"category": "test"},
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**What happened:**
1. Request → Nginx → FastAPI
2. FastAPI → MongoDB (insert)
3. FastAPI → Returns result
4. Total time: ~50ms ⚡

---

### Step 7: Test Async Endpoint (Queue-Based)

**What is an async endpoint?**
- Enqueues task to RabbitMQ
- Returns task_id immediately
- Worker processes in background
- Use for: Heavy processing, long-running tasks

**Test it:**
```bash
# Submit async task
curl -X POST http://localhost/api/async/process \
  -H "Content-Type: application/json" \
  -d '{
    "data": "heavy processing task",
    "iterations": 100,
    "priority": "high"
  }'
```

**Expected response (immediate):**
```json
{
  "task_id": "a7f8c9d0-1234-5678-9abc-def012345678",
  "status": "PENDING",
  "message": "Task submitted successfully. Use /api/async/status/{task_id} to check progress."
}
```

**What happened:**
1. Request → Nginx → FastAPI
2. FastAPI → Enqueues to RabbitMQ
3. FastAPI → Returns task_id
4. Total time: ~10ms ⚡ (super fast!)

**Meanwhile (in background):**
5. Worker → Gets task from RabbitMQ
6. Worker → Processes task (takes 50 seconds)
7. Worker → Stores result in MongoDB
8. Worker → Updates status in Redis

---

### Step 8: Check Task Status

**Copy the task_id from Step 7 and check status:**

```bash
# Replace {task_id} with your actual task_id
curl http://localhost/api/async/status/a7f8c9d0-1234-5678-9abc-def012345678
```

**Response (while processing):**
```json
{
  "task_id": "a7f8c9d0-1234-5678-9abc-def012345678",
  "status": "PROGRESS",
  "progress": {
    "current": 50,
    "total": 100,
    "progress": 50,
    "status": "Processing iteration 50/100"
  }
}
```

**Response (when completed):**
```json
{
  "task_id": "a7f8c9d0-1234-5678-9abc-def012345678",
  "status": "SUCCESS",
  "result": {
    "task_id": "a7f8c9d0-1234-5678-9abc-def012345678",
    "status": "completed",
    "processed_items": ["HEAVY PROCESSING TASK_ITERATION_1", "..."],
    "total_processed": 100,
    "completed_at": "2024-01-01T00:01:00Z"
  }
}
```

---

### Step 9: Monitor the System

#### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f api
docker compose logs -f celery_worker
docker compose logs -f rabbitmq
```

**What to look for:**
```
celery_worker-1  | [2024-01-01 00:00:00] Task app.tasks.process_heavy_task[abc-123] received
celery_worker-1  | [2024-01-01 00:00:10] Task app.tasks.process_heavy_task[abc-123] succeeded
```

#### RabbitMQ Management UI

```bash
# Open in browser
http://localhost:15672

# Login:
# Username: guest
# Password: guest
```

**What you'll see:**
- Queues tab → See tasks waiting
- Connections tab → See workers connected
- Channels tab → See active processing

#### Container Stats

```bash
# Real-time resource usage
docker stats
```

**Output:**
```
NAME              CPU %    MEM USAGE
api-1             5%       150MB
api-2             3%       145MB
api-3             4%       148MB
celery_worker-1   25%      200MB  ← Processing task
celery_worker-2   2%       120MB
celery_worker-3   1%       118MB
mongodb           10%      300MB
redis             1%       50MB
rabbitmq          5%       150MB
nginx             1%       20MB
```

---

## 🎨 Part 5: Adding Your Own Custom Task

Now let's add your own background task!

### Scenario: Send Welcome Email

Let's create a task that sends a welcome email to new users.

#### Step 1: Add Task to `app/tasks.py`

```bash
# Open the file
nano app/tasks.py
# or use your favorite editor
```

**Add this at the bottom:**

```python
@celery_app.task(
    bind=True,
    name="app.tasks.send_welcome_email",
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True
)
def send_welcome_email(self, user_email: str, user_name: str):
    """
    Send welcome email to new user
    This runs in background worker
    """
    task_id = self.request.id
    logger.info(f"Sending welcome email to {user_email}")
    
    try:
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'progress': 25, 'status': 'Preparing email...'}
        )
        
        # Simulate email preparation
        import time
        time.sleep(2)
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'progress': 50, 'status': 'Connecting to email server...'}
        )
        
        # Simulate sending email
        time.sleep(2)
        
        # In real app, you would do:
        # import smtplib
        # server = smtplib.SMTP('smtp.gmail.com', 587)
        # server.sendmail(from_addr, user_email, message)
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'progress': 75, 'status': 'Sending email...'}
        )
        
        time.sleep(2)
        
        # Complete
        result = {
            "task_id": task_id,
            "user_email": user_email,
            "user_name": user_name,
            "status": "sent",
            "sent_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Welcome email sent to {user_email}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to send email to {user_email}: {e}")
        raise self.retry(exc=e, countdown=60)
```

**Save and close the file** (Ctrl+X, then Y, then Enter)

---

#### Step 2: Add API Endpoint to `app/main.py`

```bash
# Open the file
nano app/main.py
```

**Add this import at the top:**

```python
from app.tasks import process_heavy_task, send_welcome_email  # ← Add send_welcome_email
```

**Add this endpoint before the error handlers section:**

```python
@app.post("/api/send-welcome-email", response_model=AsyncTaskResponse, status_code=status.HTTP_202_ACCEPTED, tags=["Email"])
async def send_welcome_email_endpoint(user_email: str, user_name: str):
    """
    Send welcome email to new user (async operation)
    Returns immediately with task_id
    Email is sent in background
    """
    try:
        # Enqueue email task
        task = send_welcome_email.apply_async(
            kwargs={
                "user_email": user_email,
                "user_name": user_name
            }
        )
        
        logger.info(f"Welcome email task queued: {task.id}")
        
        return AsyncTaskResponse(
            task_id=task.id,
            status="PENDING",
            message=f"Email queued for {user_email}. Check /api/async/status/{task.id}"
        )
        
    except Exception as e:
        logger.error(f"Error queueing email task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue email: {str(e)}"
        )
```

**Save and close the file**

---

#### Step 3: Rebuild and Restart

```bash
# Stop services
docker compose down

# Rebuild with new code
docker compose build

# Start services
docker compose up -d

# Check logs
docker compose logs -f celery_worker
```

---

#### Step 4: Test Your New Endpoint

```bash
# Send welcome email
curl -X POST "http://localhost/api/send-welcome-email?user_email=john@example.com&user_name=John" \
  -H "Content-Type: application/json"
```

**Expected response:**
```json
{
  "task_id": "xyz-789-abc",
  "status": "PENDING",
  "message": "Email queued for john@example.com. Check /api/async/status/xyz-789-abc"
}
```

**Check status:**
```bash
curl http://localhost/api/async/status/xyz-789-abc
```

**Response (processing):**
```json
{
  "task_id": "xyz-789-abc",
  "status": "PROGRESS",
  "progress": {
    "progress": 50,
    "status": "Connecting to email server..."
  }
}
```

**Response (completed):**
```json
{
  "task_id": "xyz-789-abc",
  "status": "SUCCESS",
  "result": {
    "task_id": "xyz-789-abc",
    "user_email": "john@example.com",
    "user_name": "John",
    "status": "sent",
    "sent_at": "2024-01-01T00:05:00Z"
  }
}
```

**Check worker logs:**
```bash
docker compose logs celery_worker | grep "welcome email"
```

**You should see:**
```
celery_worker-1  | Sending welcome email to john@example.com
celery_worker-1  | Welcome email sent to john@example.com
```

---

## 🎯 Part 6: Common Use Cases

### Use Case 1: Image Processing

```python
# app/tasks.py
@celery_app.task(bind=True)
def process_image(self, image_url: str, user_id: int):
    """Resize, compress, add watermark"""
    # Download image
    image = download_image(image_url)
    
    # Resize
    self.update_state(state='PROGRESS', meta={'progress': 33})
    resized = resize_image(image, width=800)
    
    # Compress
    self.update_state(state='PROGRESS', meta={'progress': 66})
    compressed = compress_image(resized, quality=85)
    
    # Add watermark
    self.update_state(state='PROGRESS', meta={'progress': 90})
    watermarked = add_watermark(compressed)
    
    # Upload to S3
    url = upload_to_s3(watermarked)
    
    return {"processed_url": url}
```

---

### Use Case 2: Report Generation

```python
# app/tasks.py
@celery_app.task(bind=True)
def generate_monthly_report(self, user_id: int, month: str):
    """Generate PDF report with charts"""
    # Fetch data
    self.update_state(state='PROGRESS', meta={'progress': 20})
    data = fetch_user_data(user_id, month)
    
    # Generate charts
    self.update_state(state='PROGRESS', meta={'progress': 40})
    charts = create_charts(data)
    
    # Create PDF
    self.update_state(state='PROGRESS', meta={'progress': 70})
    pdf = generate_pdf(data, charts)
    
    # Send email
    self.update_state(state='PROGRESS', meta={'progress': 90})
    send_email_with_attachment(user_id, pdf)
    
    return {"report_url": pdf_url, "sent_to": user_email}
```

---

### Use Case 3: Batch Data Import

```python
# app/tasks.py
@celery_app.task(bind=True)
def import_csv_data(self, file_url: str):
    """Import 10,000 rows from CSV"""
    # Download CSV
    csv_data = download_csv(file_url)
    
    total_rows = len(csv_data)
    imported = 0
    
    # Process in batches
    for batch in chunk_list(csv_data, size=100):
        # Import batch
        import_batch_to_db(batch)
        imported += len(batch)
        
        # Update progress
        progress = int(imported / total_rows * 100)
        self.update_state(
            state='PROGRESS',
            meta={
                'progress': progress,
                'imported': imported,
                'total': total_rows
            }
        )
    
    return {"imported": imported, "total": total_rows}
```

---

## 🔍 Part 7: Debugging & Troubleshooting

### Problem 1: Task Not Processing

**Symptoms:**
- Task status stays "PENDING"
- Nothing in worker logs

**Check:**
```bash
# 1. Is worker running?
docker compose ps celery_worker

# 2. Check worker logs
docker compose logs celery_worker

# 3. Check RabbitMQ
docker compose logs rabbitmq

# 4. Restart worker
docker compose restart celery_worker
```

---

### Problem 2: Task Fails

**Symptoms:**
- Task status shows "FAILURE"
- Error in result

**Check:**
```bash
# Check worker logs for error
docker compose logs celery_worker | grep ERROR

# Check task status
curl http://localhost/api/async/status/{task_id}
```

**Common errors:**
- Import error: Missing package in `requirements.txt`
- Connection error: MongoDB/Redis not reachable
- Timeout: Task takes too long (increase `task_time_limit`)

---

### Problem 3: API Returns 500 Error

**Check:**
```bash
# Check API logs
docker compose logs api

# Check if services are connected
curl http://localhost/health
```

**Common causes:**
- MongoDB not running
- RabbitMQ not running
- Syntax error in code

---

### Problem 4: High Memory Usage

**Check:**
```bash
docker stats
```

**Solutions:**
```yaml
# docker-compose.yml
celery_worker:
  command: celery -A app.celery_app worker --concurrency=2  # Reduce from 4
```

---

## 📊 Part 8: Monitoring & Metrics

### View API Documentation

```bash
# Open in browser
http://localhost/docs
```

**You'll see:**
- All endpoints
- Request/response schemas
- Try it out feature

---

### RabbitMQ Dashboard

```bash
# Open in browser
http://localhost:15672
```

**Monitor:**
- Queue length (how many tasks waiting)
- Message rate (tasks/second)
- Consumer count (how many workers)

---

### Check Database

```bash
# Connect to MongoDB
docker compose exec mongodb mongosh

# Use database
use myapp

# View collections
show collections

# Query items
db.items.find().pretty()

# Query task results
db.task_results.find().pretty()

# Count documents
db.items.countDocuments()
```

---

## 🎓 Part 9: Best Practices

### When to Use Sync vs Async

| Operation | Type | Why |
|-----------|------|-----|
| Get user profile | **SYNC** | Fast database query |
| Create new user | **SYNC** | Simple database insert |
| Login | **SYNC** | Quick validation |
| Search products | **SYNC** | Indexed query |
| **Send email** | **ASYNC** | External API, can fail |
| **Process image** | **ASYNC** | CPU-intensive |
| **Generate PDF** | **ASYNC** | Takes time |
| **Import CSV** | **ASYNC** | Large dataset |
| **Video encoding** | **ASYNC** | Very slow |

### Task Design Tips

**✅ Good Task:**
```python
@celery_app.task(bind=True, max_retries=3)
def send_email(self, to: str, subject: str, body: str):
    """
    - Small, focused task
    - Clear parameters
    - Idempotent (can run multiple times safely)
    - Has retry logic
    """
    pass
```

**❌ Bad Task:**
```python
@celery_app.task()
def do_everything(data):
    """
    - Too broad
    - No retry logic
    - Unclear what 'data' is
    - Not idempotent
    """
    pass
```

---

## 🚀 Part 10: Next Steps

### What You've Learned

✅ How microservices architecture works  
✅ Why queues prevent API freezing  
✅ How FastAPI, Celery, RabbitMQ work together  
✅ How to add custom background tasks  
✅ How to test and monitor the system  

### What to Do Next

1. **Add your own tasks** - Think of heavy operations in your app
2. **Implement real logic** - Replace `time.sleep()` with actual work
3. **Add authentication** - Secure your API endpoints
4. **Deploy to production** - Follow `DEPLOY-00-MASTER-CHECKLIST.md`
5. **Monitor in production** - Add Prometheus + Grafana

---

## 📚 Additional Resources

### Documentation
- **FastAPI**: https://fastapi.tiangolo.com/
- **Celery**: https://docs.celeryproject.org/
- **RabbitMQ**: https://www.rabbitmq.com/documentation.html
- **Docker**: https://docs.docker.com/

### Your Project Files
- `README.md` - Project overview
- `QUICKSTART.md` - Quick setup guide
- `TUNING.md` - Performance tuning
- `TROUBLESHOOTING.md` - Common issues
- `DEPLOY-00-MASTER-CHECKLIST.md` - Deployment guide

---

## 🆘 Getting Help

### Check Logs
```bash
docker compose logs -f
```

### Check Service Status
```bash
docker compose ps
```

### Restart Everything
```bash
docker compose down
docker compose up -d --build
```

### Still Stuck?
1. Check `TROUBLESHOOTING.md`
2. Review error logs
3. Verify all services are running
4. Check network connectivity

---

## 🎉 Congratulations!

You now understand:
- ✅ Queue-based microservices architecture
- ✅ How to implement async background tasks
- ✅ How to test and monitor your system
- ✅ How to add custom functionality

**You're ready to build scalable, production-ready applications!** 🚀
