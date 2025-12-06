# Deployment Guide

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+ (for local development)
- Kubernetes 1.24+ (for production)
- kubectl configured
- Helm 3.0+ (optional, for easier K8s deployment)

## Local Development Deployment

### Using Docker Compose

1. **Navigate to docker directory**
```bash
cd infrastructure/docker
```

2. **Start all services**
```bash
docker-compose up -d
```

3. **Check service status**
```bash
docker-compose ps
```

4. **View logs**
```bash
docker-compose logs -f config-service
```

5. **Stop services**
```bash
docker-compose down
```

6. **Clean up volumes (WARNING: deletes all data)**
```bash
docker-compose down -v
```

### Accessing Services

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health
- **Metrics**: http://localhost:8000/metrics
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)
- **PostgreSQL**: localhost:5432 (config_user/config_pass)
- **Redis**: localhost:6379

## Production Deployment (Kubernetes)

### Step 1: Build and Push Docker Image

```bash
# Build image
docker build -t your-registry/config-service:v1.0.0 -f infrastructure/docker/Dockerfile .

# Push to registry
docker push your-registry/config-service:v1.0.0
```

### Step 2: Update Kubernetes Manifests

Edit `infrastructure/kubernetes/deployment.yaml`:
```yaml
spec:
  template:
    spec:
      containers:
      - name: config-service
        image: your-registry/config-service:v1.0.0  # Update this
```

### Step 3: Update Secrets

**IMPORTANT**: Change all default passwords!

Edit `infrastructure/kubernetes/secrets.yaml`:
```yaml
stringData:
  DATABASE_URL: "postgresql+asyncpg://config_user:YOUR_STRONG_PASSWORD@postgres:5432/config_db"
  SECRET_KEY: "YOUR_SECRET_KEY_HERE"
  ENCRYPTION_KEY: "YOUR_ENCRYPTION_KEY_HERE"
```

Also update:
- `postgres-statefulset.yaml` - PostgreSQL password
- `rabbitmq-deployment.yaml` - RabbitMQ password

### Step 4: Deploy to Kubernetes

```bash
# Create namespace
kubectl apply -f infrastructure/kubernetes/namespace.yaml

# Deploy database and dependencies
kubectl apply -f infrastructure/kubernetes/postgres-statefulset.yaml
kubectl apply -f infrastructure/kubernetes/redis-deployment.yaml
kubectl apply -f infrastructure/kubernetes/rabbitmq-deployment.yaml

# Wait for databases to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n config-management --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis -n config-management --timeout=300s
kubectl wait --for=condition=ready pod -l app=rabbitmq -n config-management --timeout=300s

# Deploy config service
kubectl apply -f infrastructure/kubernetes/configmap.yaml
kubectl apply -f infrastructure/kubernetes/secrets.yaml
kubectl apply -f infrastructure/kubernetes/deployment.yaml
kubectl apply -f infrastructure/kubernetes/service.yaml

# Deploy ingress (optional)
kubectl apply -f infrastructure/kubernetes/ingress.yaml
```

### Step 5: Verify Deployment

```bash
# Check pods
kubectl get pods -n config-management

# Check services
kubectl get svc -n config-management

# View logs
kubectl logs -f deployment/config-service -n config-management

# Check health
kubectl port-forward svc/config-service 8000:80 -n config-management
curl http://localhost:8000/api/v1/health/ready
```

## Environment-Specific Deployments

### Development Environment

```bash
kubectl apply -f infrastructure/kubernetes/environments/dev/
```

### Staging Environment

```bash
kubectl apply -f infrastructure/kubernetes/environments/staging/
```

### Production Environment

```bash
kubectl apply -f infrastructure/kubernetes/environments/prod/
```

## Database Migrations

### Initial Setup

```bash
# Port-forward to PostgreSQL
kubectl port-forward svc/postgres 5432:5432 -n config-management

# Run migrations (from project root)
alembic upgrade head
```

### Creating New Migrations

```bash
# Generate migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head
```

## Scaling

### Horizontal Scaling

```bash
# Scale config service
kubectl scale deployment config-service --replicas=5 -n config-management

# Auto-scaling
kubectl autoscale deployment config-service \
  --min=3 --max=10 \
  --cpu-percent=70 \
  -n config-management
```

### Vertical Scaling

Edit `deployment.yaml`:
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

## Monitoring Setup

### Deploy Prometheus

```bash
# Using Helm
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace \
  -f monitoring/prometheus/values.yaml
```

### Deploy Grafana Dashboards

```bash
kubectl create configmap grafana-dashboards \
  --from-file=monitoring/grafana/ \
  -n monitoring
```

## Backup and Restore

### Backup PostgreSQL

```bash
# Create backup
kubectl exec -n config-management postgres-0 -- \
  pg_dump -U config_user config_db > backup-$(date +%Y%m%d).sql

# Upload to S3 (example)
aws s3 cp backup-$(date +%Y%m%d).sql s3://your-bucket/backups/
```

### Restore PostgreSQL

```bash
# Download from S3
aws s3 cp s3://your-bucket/backups/backup-20240101.sql .

# Restore
kubectl exec -i -n config-management postgres-0 -- \
  psql -U config_user config_db < backup-20240101.sql
```

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n config-management

# Check logs
kubectl logs <pod-name> -n config-management

# Check events
kubectl get events -n config-management --sort-by='.lastTimestamp'
```

### Database Connection Issues

```bash
# Test database connectivity
kubectl run -it --rm debug --image=postgres:15-alpine \
  --restart=Never -n config-management -- \
  psql -h postgres -U config_user -d config_db
```

### Service Not Accessible

```bash
# Check service endpoints
kubectl get endpoints -n config-management

# Test internal connectivity
kubectl run -it --rm debug --image=curlimages/curl \
  --restart=Never -n config-management -- \
  curl http://config-service/api/v1/health
```

## Rolling Updates

```bash
# Update image
kubectl set image deployment/config-service \
  config-service=your-registry/config-service:v1.1.0 \
  -n config-management

# Check rollout status
kubectl rollout status deployment/config-service -n config-management

# Rollback if needed
kubectl rollout undo deployment/config-service -n config-management
```

## Security Hardening

1. **Use Kubernetes Secrets** - Never commit secrets to Git
2. **Enable RBAC** - Restrict access to resources
3. **Network Policies** - Limit pod-to-pod communication
4. **Pod Security Policies** - Enforce security standards
5. **TLS Everywhere** - Use TLS for all communications
6. **Regular Updates** - Keep dependencies updated
7. **Vulnerability Scanning** - Scan images regularly

## Performance Tuning

### Database Optimization

```sql
-- Add indexes for common queries
CREATE INDEX idx_config_app_env ON configs(app_id, environment, is_active);
CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp DESC);

-- Analyze tables
ANALYZE configs;
ANALYZE audit_logs;
```

### Redis Optimization

```bash
# Increase max memory
kubectl edit deployment redis -n config-management

# Add to container args:
args:
  - --maxmemory 512mb
  - --maxmemory-policy allkeys-lru
```

### Application Tuning

Edit `configmap.yaml`:
```yaml
data:
  DATABASE_POOL_SIZE: "50"  # Increase pool size
  REDIS_MAX_CONNECTIONS: "100"  # Increase Redis connections
  REDIS_CACHE_TTL: "600"  # Increase cache TTL
```

## Maintenance

### Regular Tasks

- **Daily**: Check logs for errors
- **Weekly**: Review metrics and alerts
- **Monthly**: Update dependencies
- **Quarterly**: Security audit
- **Yearly**: Disaster recovery drill

### Updating Dependencies

```bash
# Update Python packages
pip list --outdated
pip install --upgrade <package>

# Rebuild and redeploy
docker build -t your-registry/config-service:v1.1.0 .
docker push your-registry/config-service:v1.1.0
kubectl set image deployment/config-service config-service=your-registry/config-service:v1.1.0 -n config-management
```
