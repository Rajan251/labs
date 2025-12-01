# 🚀 Quick Reference Cheat Sheet

## 📋 Essential Commands

### Start/Stop Services
```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# Restart after code changes
docker compose down && docker compose up -d --build

# View logs
docker compose logs -f

# Check status
docker compose ps
```

---

## 🔍 Testing Endpoints

### Health Check
```bash
curl http://localhost/health
```

### Create Item (Sync - Fast)
```bash
curl -X POST http://localhost/api/items \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "description": "Test item"}'
```

### Submit Async Task
```bash
curl -X POST http://localhost/api/async/process \
  -H "Content-Type: application/json" \
  -d '{"data": "test", "iterations": 10, "priority": "high"}'
```

### Check Task Status
```bash
# Replace {task_id} with actual ID
curl http://localhost/api/async/status/{task_id}
```

---

## 📁 File Locations

| What | Where |
|------|-------|
| API Routes | `app/main.py` |
| Background Tasks | `app/tasks.py` |
| Celery Config | `app/celery_app.py` |
| Data Models | `app/models.py` |
| Database | `app/database.py` |
| Services Config | `docker-compose.yml` |

---

## 🎯 Adding Custom Task

### 1. Add Task (`app/tasks.py`)
```python
@celery_app.task(bind=True, name="app.tasks.my_task")
def my_task(self, data: str):
    # Your logic here
    return {"result": "done"}
```

### 2. Add Route (`app/main.py`)
```python
from app.tasks import my_task

@app.post("/api/my-endpoint")
async def my_endpoint(data: str):
    task = my_task.apply_async(kwargs={"data": data})
    return {"task_id": task.id}
```

### 3. Restart
```bash
docker compose down && docker compose up -d --build
```

---

## 🔧 Debugging

### Check Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f api
docker compose logs -f celery_worker
docker compose logs -f mongodb
docker compose logs -f redis
docker compose logs -f rabbitmq
```

### Check Container Stats
```bash
docker stats
```

### Access MongoDB
```bash
docker compose exec mongodb mongosh
> use myapp
> db.items.find().pretty()
```

### Access Redis
```bash
docker compose exec redis redis-cli
> KEYS *
> GET celery-task-meta-{task_id}
```

### RabbitMQ UI
```
http://localhost:15672
Username: guest
Password: guest
```

---

## 🎨 API Documentation
```
http://localhost/docs       # Swagger UI
http://localhost/redoc      # ReDoc
```

---

## ⚡ Performance Tips

### Scale Services
```bash
# Scale API to 5 instances
docker compose up -d --scale api=5

# Scale workers to 5 instances
docker compose up -d --scale celery_worker=5
```

### Reduce Worker Concurrency
```yaml
# docker-compose.yml
celery_worker:
  command: celery -A app.celery_app worker --concurrency=2
```

---

## 🆘 Common Issues

### Task Not Processing
```bash
# Restart worker
docker compose restart celery_worker

# Check worker logs
docker compose logs celery_worker
```

### API Returns 500
```bash
# Check health
curl http://localhost/health

# Check API logs
docker compose logs api
```

### High Memory
```bash
# Check stats
docker stats

# Reduce concurrency in docker-compose.yml
```

---

## 📊 Monitoring

### View Queue Status
```
http://localhost:15672 → Queues tab
```

### Check Task Progress
```bash
curl http://localhost/api/async/status/{task_id}
```

### Database Stats
```bash
docker compose exec mongodb mongosh
> use myapp
> db.stats()
> db.items.countDocuments()
```

---

## 🎓 When to Use What

| Use Case | Endpoint Type |
|----------|--------------|
| Get data | SYNC |
| Create/Update | SYNC |
| Search | SYNC |
| Send email | ASYNC |
| Process image | ASYNC |
| Generate PDF | ASYNC |
| Import CSV | ASYNC |
| Video encoding | ASYNC |

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `BEGINNER-COMPLETE-GUIDE.md` | **START HERE** - Complete tutorial |
| `START-HERE.md` | Quick overview |
| `SIMPLE-ANSWER.md` | Which files you need |
| `FASTAPI-FILES-EXPLAINED.md` | What each file does |
| `README.md` | Project overview |
| `QUICKSTART.md` | Quick setup |
| `TROUBLESHOOTING.md` | Common issues |
| `TUNING.md` | Performance tuning |

---

## 🚀 Quick Start (3 Steps)

```bash
# 1. Navigate to project
cd /home/rk/Documents/labs/lab-microservices-system-design

# 2. Start services
docker compose up -d

# 3. Test
curl http://localhost/health
```

**Done!** 🎉

---

## 💡 Pro Tips

1. **Always check logs** when debugging
2. **Use async for heavy tasks** (>1 second)
3. **Monitor RabbitMQ** to see queue length
4. **Scale workers** if queue is growing
5. **Add retries** to all tasks
6. **Update progress** in long tasks
7. **Store results** in MongoDB for persistence

---

## 🔗 Useful URLs

```
http://localhost              # API (via Nginx)
http://localhost/docs         # API Documentation
http://localhost/health       # Health Check
http://localhost:15672        # RabbitMQ Management
```

---

## 📞 Getting Help

1. Read `BEGINNER-COMPLETE-GUIDE.md`
2. Check `TROUBLESHOOTING.md`
3. View logs: `docker compose logs -f`
4. Check service status: `docker compose ps`
5. Restart: `docker compose down && docker compose up -d`
