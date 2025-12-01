# Which Files Do I Need? 🤔

## Quick Answer

You are using **FastAPI** (not Django), so you need these files:

### ✅ Files You ALREADY HAVE (FastAPI)
```
✅ app/main.py              ← Your FastAPI routes (ALREADY EXISTS)
✅ app/tasks.py             ← Your Celery tasks (ALREADY EXISTS)
✅ app/celery_app.py        ← Your Celery config (ALREADY EXISTS)
✅ app/models.py            ← Your Pydantic models (ALREADY EXISTS)
✅ app/database.py          ← Your MongoDB connection (ALREADY EXISTS)
✅ docker-compose.yml       ← Your services config (ALREADY EXISTS)
```

### ❌ Files You DON'T NEED (Django Only)
```
❌ myproject/celery.py      ← Only for Django (IGNORE THIS)
❌ api/serializers.py       ← Only for Django (IGNORE THIS)
❌ api/views.py             ← Only for Django (IGNORE THIS)
❌ myproject/settings.py    ← Only for Django (IGNORE THIS)
```

---

## 📂 Your Current FastAPI Structure

```
/home/rk/Documents/labs/lab-microservices-system-design/
├── app/
│   ├── __init__.py          ✅ EXISTS
│   ├── main.py              ✅ EXISTS (FastAPI app & routes)
│   ├── models.py            ✅ EXISTS (Pydantic models)
│   ├── database.py          ✅ EXISTS (MongoDB connection)
│   ├── celery_app.py        ✅ EXISTS (Celery configuration)
│   └── tasks.py             ✅ EXISTS (Background tasks)
├── docker-compose.yml       ✅ EXISTS
├── Dockerfile.app           ✅ EXISTS
├── requirements.txt         ✅ EXISTS
└── nginx/
    └── nginx.conf           ✅ EXISTS
```

**You already have everything you need for FastAPI!** 🎉

---

## 🚀 What You Should Do Now

Since you already have all the FastAPI files, here's what you need to do:

### Option 1: Use Your Existing FastAPI Setup (Recommended)

**You don't need to create any new files!** Your current setup already has:

1. ✅ **app/celery_app.py** - Celery configuration
2. ✅ **app/tasks.py** - Background tasks
3. ✅ **app/main.py** - API routes

**Just use your existing files!** They're already set up correctly.

---

### Option 2: Add a New Custom Task (If You Want)

If you want to add your own custom background task, here's how:

#### Step 1: Add Your Task to `app/tasks.py`

Open your existing `app/tasks.py` and add a new task:

```python
# app/tasks.py (ADD THIS TO YOUR EXISTING FILE)

@celery_app.task(
    bind=True,
    name="app.tasks.my_custom_task",  # ← Your task name
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True
)
def my_custom_task(self, user_id: int, data: dict):
    """
    Your custom background task
    Example: Send email, process image, generate report, etc.
    """
    task_id = self.request.id
    logger.info(f"Starting custom task {task_id} for user {user_id}")
    
    try:
        # YOUR CUSTOM LOGIC HERE
        # Example: Send email
        # send_email(user_id, data['email'], data['subject'])
        
        # Example: Process image
        # processed_image = process_image(data['image_url'])
        
        # Example: Generate report
        # report = generate_report(user_id, data['report_type'])
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'progress': 50, 'status': 'Processing...'}
        )
        
        # Simulate work
        import time
        time.sleep(2)
        
        # Complete
        result = {
            "task_id": task_id,
            "user_id": user_id,
            "status": "completed",
            "message": "Task completed successfully"
        }
        
        logger.info(f"Task {task_id} completed")
        return result
        
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        raise self.retry(exc=e, countdown=60)
```

#### Step 2: Add API Endpoint to `app/main.py`

Open your existing `app/main.py` and add a new route:

```python
# app/main.py (ADD THIS TO YOUR EXISTING FILE)

from app.tasks import my_custom_task  # ← Import your task

@app.post("/api/my-custom-job", status_code=202)
async def submit_custom_job(user_id: int, data: dict):
    """
    Submit your custom job to the queue
    Returns immediately with task_id
    """
    # Enqueue task
    task = my_custom_task.apply_async(
        kwargs={"user_id": user_id, "data": data}
    )
    
    return {
        "task_id": task.id,
        "status": "PENDING",
        "message": f"Job submitted. Check /api/async/status/{task.id}"
    }
```

#### Step 3: Restart Services

```bash
# Rebuild and restart
docker compose down
docker compose up -d --build

# Check logs
docker compose logs -f celery_worker
```

#### Step 4: Test Your New Task

```bash
# Submit job
curl -X POST http://localhost/api/my-custom-job \
  -H "Content-Type: application/json" \
  -d '{"user_id": 123, "data": {"key": "value"}}'

# Response:
# {
#   "task_id": "abc-123-def",
#   "status": "PENDING",
#   "message": "Job submitted. Check /api/async/status/abc-123-def"
# }

# Check status
curl http://localhost/api/async/status/abc-123-def
```

---

## 🐍 What If You Want to Use Django Instead?

**Only do this if you want to completely switch from FastAPI to Django!**

If you want to use Django, you would need to:

1. **Create a new Django project** (separate from your current FastAPI project)
2. **Create these NEW files:**
   ```
   myproject/
   ├── __init__.py
   ├── settings.py          ← Django settings
   ├── urls.py              ← URL routing
   ├── celery.py            ← Celery config for Django
   └── wsgi.py
   
   api/
   ├── __init__.py
   ├── views.py             ← Django REST Framework views
   ├── models.py            ← Django ORM models
   ├── serializers.py       ← DRF serializers
   ├── tasks.py             ← Celery tasks
   └── urls.py
   ```

**But you don't need to do this!** Your FastAPI setup is already working.

---

## 📊 Comparison: What You Have vs What Django Would Need

| File | FastAPI (You Have) | Django (You Don't Need) |
|------|-------------------|------------------------|
| **Web Framework** | `app/main.py` ✅ | `api/views.py` ❌ |
| **Models** | `app/models.py` (Pydantic) ✅ | `api/models.py` (Django ORM) ❌ |
| **Serializers** | Built into Pydantic ✅ | `api/serializers.py` ❌ |
| **Celery Config** | `app/celery_app.py` ✅ | `myproject/celery.py` ❌ |
| **Tasks** | `app/tasks.py` ✅ | `api/tasks.py` ❌ |
| **Settings** | `.env` file ✅ | `myproject/settings.py` ❌ |

---

## 🎯 Summary

### What You Should Do:

1. **✅ Keep using your existing FastAPI files** - They're already set up correctly!
2. **✅ Your files are:**
   - `app/main.py` - API routes
   - `app/tasks.py` - Background tasks
   - `app/celery_app.py` - Celery config
   - `app/models.py` - Data models
   - `app/database.py` - MongoDB connection

3. **❌ Ignore Django files** - You don't need them:
   - `myproject/celery.py` - Only for Django
   - `api/serializers.py` - Only for Django
   - `api/views.py` - Only for Django

### If You Want to Add Custom Tasks:

Just edit your existing files:
1. Add task to `app/tasks.py`
2. Add route to `app/main.py`
3. Restart: `docker compose up -d --build`

---

## 🆘 Still Confused?

**Question:** "Do I need to create `myproject/celery.py`?"  
**Answer:** ❌ NO! That's only for Django. You already have `app/celery_app.py` for FastAPI.

**Question:** "Do I need to create `api/serializers.py`?"  
**Answer:** ❌ NO! That's only for Django. FastAPI uses Pydantic models in `app/models.py`.

**Question:** "What files do I need to create?"  
**Answer:** ✅ NONE! You already have everything for FastAPI.

**Question:** "How do I add a new background task?"  
**Answer:** ✅ Edit your existing `app/tasks.py` and `app/main.py` (see Option 2 above).

---

## 📞 Need Help?

If you want to:
- ✅ Add a new custom task → Edit `app/tasks.py` and `app/main.py`
- ✅ Modify existing tasks → Edit `app/tasks.py`
- ✅ Add new API routes → Edit `app/main.py`
- ✅ Change Celery config → Edit `app/celery_app.py`

**You don't need to create any new files!** Just edit your existing ones.
