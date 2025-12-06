# Deployment Guide

Complete guide for deploying the Webhook Delivery Platform in various environments.

## Table of Contents

1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Production Deployment](#production-deployment)
4. [Environment Configuration](#environment-configuration)
5. [Database Migrations](#database-migrations)
6. [Scaling](#scaling)
7. [Troubleshooting](#troubleshooting)

---

## Local Development

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- RabbitMQ 3+

### Setup Steps

1. **Clone Repository**:
```bash
git clone <repository-url>
cd webhook-lab
```

2. **Create Virtual Environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

4. **Start Infrastructure Services**:
```bash
# PostgreSQL
docker run -d --name postgres \
  -e POSTGRES_USER=webhook_user \
  -e POSTGRES_PASSWORD=webhook_pass \
  -e POSTGRES_DB=webhook_db \
  -p 5432:5432 \
  postgres:15-alpine

# Redis
docker run -d --name redis \
  -p 6379:6379 \
  redis:7-alpine

# RabbitMQ
docker run -d --name rabbitmq \
  -e RABBITMQ_DEFAULT_USER=webhook_user \
  -e RABBITMQ_DEFAULT_PASS=webhook_pass \
  -p 5672:5672 \
  -p 15672:15672 \
  rabbitmq:3-management-alpine
```

5. **Configure Environment**:
```bash
cp .env.example .env
# Edit .env with your local settings
```

6. **Initialize Database**:
```bash
# Create tables
python -c "from app.database import init_db; init_db()"
```

7. **Start API Server**:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

8. **Start Celery Worker** (in new terminal):
```bash
celery -A app.workers.delivery_worker worker --loglevel=info --concurrency=4
```

9. **Access Application**:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- RabbitMQ Management: http://localhost:15672

---

## Docker Deployment

### Quick Start

1. **Clone and Configure**:
```bash
git clone <repository-url>
cd webhook-lab
cp .env.example .env
```

2. **Start All Services**:
```bash
docker-compose up -d
```

3. **Check Status**:
```bash
docker-compose ps
```

4. **View Logs**:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f worker
```

5. **Stop Services**:
```bash
docker-compose down

# With volume cleanup
docker-compose down -v
```

### Service URLs

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Metrics**: http://localhost:8000/metrics
- **RabbitMQ**: http://localhost:15672
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000

---

## Production Deployment

### Architecture

```
Internet → Load Balancer → API Servers (N instances)
                              ↓
                         Message Queue
                              ↓
                         Workers (M instances)
                              ↓
                         Tenant Endpoints
```

### Prerequisites

- Kubernetes cluster (or Docker Swarm)
- PostgreSQL managed service (RDS, Cloud SQL, etc.)
- Redis managed service (ElastiCache, MemoryStore, etc.)
- RabbitMQ managed service (CloudAMQP, Amazon MQ, etc.)
- Load balancer (ALB, GCP Load Balancer, etc.)
- SSL/TLS certificates
- Monitoring infrastructure (Prometheus, Grafana)

### Deployment Steps

#### 1. Prepare Infrastructure

**Database (PostgreSQL)**:
```sql
CREATE DATABASE webhook_db;
CREATE USER webhook_user WITH PASSWORD 'strong_password';
GRANT ALL PRIVILEGES ON DATABASE webhook_db TO webhook_user;
```

**Redis Configuration**:
- Enable persistence (RDB snapshots)
- Set maxmemory policy: `allkeys-lru`
- Configure max connections: 1000+

**RabbitMQ Configuration**:
- Enable management plugin
- Create vhost: `/webhooks`
- Set up user with permissions
- Configure queue durability

#### 2. Build Docker Image

```bash
# Build
docker build -t webhook-platform:1.0.0 .

# Tag for registry
docker tag webhook-platform:1.0.0 your-registry.com/webhook-platform:1.0.0

# Push
docker push your-registry.com/webhook-platform:1.0.0
```

#### 3. Configure Environment

Create production `.env`:
```bash
# Application
APP_NAME=webhook-platform
APP_VERSION=1.0.0
DEBUG=false
LOG_LEVEL=INFO

# Database (use managed service)
DATABASE_URL=postgresql://user:pass@db-host:5432/webhook_db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis (use managed service)
REDIS_URL=redis://redis-host:6379/0
REDIS_MAX_CONNECTIONS=100

# RabbitMQ (use managed service)
RABBITMQ_URL=amqp://user:pass@rabbitmq-host:5672/webhooks
CELERY_BROKER_URL=amqp://user:pass@rabbitmq-host:5672/webhooks
CELERY_RESULT_BACKEND=redis://redis-host:6379/1

# Security
SECRET_KEY=<generate-strong-random-key>

# Rate Limiting
RATE_LIMIT_PER_TENANT=100
RATE_LIMIT_WINDOW=60

# Webhook Delivery
MAX_RETRY_ATTEMPTS=6
INITIAL_RETRY_DELAY=1
MAX_RETRY_DELAY=32
WEBHOOK_TIMEOUT=30
```

#### 4. Deploy API Servers

**Kubernetes Deployment**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webhook-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: webhook-api
  template:
    metadata:
      labels:
        app: webhook-api
    spec:
      containers:
      - name: api
        image: your-registry.com/webhook-platform:1.0.0
        command: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: webhook-secrets
              key: database-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

#### 5. Deploy Workers

**Kubernetes Deployment**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webhook-worker
spec:
  replicas: 5
  selector:
    matchLabels:
      app: webhook-worker
  template:
    metadata:
      labels:
        app: webhook-worker
    spec:
      containers:
      - name: worker
        image: your-registry.com/webhook-platform:1.0.0
        command: ["celery", "-A", "app.workers.delivery_worker", "worker", "--loglevel=info", "--concurrency=4"]
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: webhook-secrets
              key: database-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

#### 6. Configure Load Balancer

**Kubernetes Service**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: webhook-api-service
spec:
  type: LoadBalancer
  selector:
    app: webhook-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
```

#### 7. Set Up SSL/TLS

```bash
# Using cert-manager in Kubernetes
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create certificate
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: webhook-platform-cert
spec:
  secretName: webhook-platform-tls
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - webhooks.yourdomain.com
```

---

## Environment Configuration

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `REDIS_URL` | Redis connection string | `redis://host:6379/0` |
| `CELERY_BROKER_URL` | RabbitMQ broker URL | `amqp://user:pass@host:5672/` |
| `SECRET_KEY` | Application secret key | `<random-256-bit-key>` |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `false` | Enable debug mode |
| `LOG_LEVEL` | `INFO` | Logging level |
| `RATE_LIMIT_PER_TENANT` | `100` | Events per minute per tenant |
| `MAX_RETRY_ATTEMPTS` | `6` | Maximum delivery retries |
| `WEBHOOK_TIMEOUT` | `30` | Webhook request timeout (seconds) |

### Generating Secret Key

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Database Migrations

### Using Alembic

1. **Initialize Alembic** (already done):
```bash
alembic init alembic
```

2. **Create Migration**:
```bash
alembic revision --autogenerate -m "Add new column"
```

3. **Apply Migrations**:
```bash
# Upgrade to latest
alembic upgrade head

# Upgrade to specific version
alembic upgrade <revision>

# Downgrade
alembic downgrade -1
```

4. **View Migration History**:
```bash
alembic history
alembic current
```

---

## Scaling

### Horizontal Scaling

**API Servers**:
```bash
# Kubernetes
kubectl scale deployment webhook-api --replicas=10

# Docker Compose
docker-compose up -d --scale api=5
```

**Workers**:
```bash
# Kubernetes
kubectl scale deployment webhook-worker --replicas=20

# Docker Compose
docker-compose up -d --scale worker=10
```

### Vertical Scaling

Update resource limits in deployment configuration:
```yaml
resources:
  requests:
    memory: "1Gi"
    cpu: "1000m"
  limits:
    memory: "2Gi"
    cpu: "2000m"
```

### Auto-Scaling

**Horizontal Pod Autoscaler (HPA)**:
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: webhook-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: webhook-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Errors

**Symptom**: `FATAL: password authentication failed`

**Solution**:
- Verify `DATABASE_URL` is correct
- Check database user permissions
- Ensure database is accessible from application

#### 2. Worker Not Processing Tasks

**Symptom**: Events stuck in `pending` status

**Solution**:
```bash
# Check worker logs
docker-compose logs worker

# Verify RabbitMQ connection
docker-compose exec worker celery -A app.workers.delivery_worker inspect active

# Check queue depth
docker-compose exec rabbitmq rabbitmqctl list_queues
```

#### 3. High Memory Usage

**Symptom**: Workers consuming excessive memory

**Solution**:
- Reduce worker concurrency
- Set `worker_max_tasks_per_child` lower
- Increase worker replicas with lower concurrency

#### 4. Rate Limit Not Working

**Symptom**: Rate limits not enforced

**Solution**:
- Verify Redis connection
- Check Redis logs for errors
- Ensure Redis has sufficient memory

#### 5. Webhooks Not Delivered

**Symptom**: Events in DLQ

**Solution**:
```bash
# Check delivery attempts
curl -H "X-API-Key: <key>" http://localhost:8000/api/v1/events/<event_id>/attempts

# View DLQ entries
curl http://localhost:8000/api/v1/dlq

# Check worker logs for errors
docker-compose logs worker | grep ERROR
```

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Database connection
docker-compose exec postgres pg_isready

# Redis connection
docker-compose exec redis redis-cli ping

# RabbitMQ connection
docker-compose exec rabbitmq rabbitmq-diagnostics ping
```

### Performance Monitoring

```bash
# Database connections
docker-compose exec postgres psql -U webhook_user -d webhook_db -c "SELECT count(*) FROM pg_stat_activity;"

# Redis memory usage
docker-compose exec redis redis-cli INFO memory

# RabbitMQ queue depth
docker-compose exec rabbitmq rabbitmqctl list_queues name messages
```

---

## Backup and Recovery

### Database Backup

```bash
# Backup
docker-compose exec postgres pg_dump -U webhook_user webhook_db > backup.sql

# Restore
docker-compose exec -T postgres psql -U webhook_user webhook_db < backup.sql
```

### Redis Backup

```bash
# Trigger save
docker-compose exec redis redis-cli SAVE

# Copy RDB file
docker cp webhook-redis:/data/dump.rdb ./redis-backup.rdb
```

---

## Security Checklist

- [ ] Change all default passwords
- [ ] Use strong `SECRET_KEY`
- [ ] Enable HTTPS/TLS
- [ ] Restrict database access by IP
- [ ] Use managed services for production
- [ ] Enable Redis authentication
- [ ] Configure RabbitMQ SSL
- [ ] Set up firewall rules
- [ ] Enable audit logging
- [ ] Implement API key rotation
- [ ] Regular security updates
- [ ] Monitor for vulnerabilities

---

## Monitoring Setup

See [MONITORING.md](MONITORING.md) for detailed monitoring configuration.
