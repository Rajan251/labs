# Complete E-Commerce Platform - Kubernetes Deployment Guide

Comprehensive guide for deploying the e-commerce platform to Kubernetes.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                           │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Ingress Controller (nginx)                              │  │
│  │  ecommerce.example.com                                   │  │
│  └────────────────────┬─────────────────────────────────────┘  │
│                       │                                         │
│  ┌────────────────────▼─────────────────────────────────────┐  │
│  │  API Gateway (Nginx)                                     │  │
│  │  Routes: /catalog, /cart, /orders, /payments            │  │
│  └───┬────────┬────────┬────────┬────────┬────────┬─────────┘  │
│      │        │        │        │        │        │             │
│  ┌───▼───┐┌──▼───┐┌───▼───┐┌───▼───┐┌───▼───┐┌───▼───┐       │
│  │Catalog││ Cart ││ Order ││Payment││Invent.││ User  │       │
│  │Service││Service││Service││Service││Service││Service│       │
│  │3 pods ││2 pods││3 pods ││2 pods ││3 pods ││2 pods │       │
│  └───┬───┘└──┬───┘└───┬───┘└───┬───┘└───┬───┘└───┬───┘       │
│      │       │        │        │        │        │             │
│  ┌───▼───────▼────────▼────────▼────────▼────────▼─────────┐  │
│  │              Message Queue (RabbitMQ)                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ PostgreSQL   │  │    Redis     │  │   MongoDB    │        │
│  │ StatefulSet  │  │  Deployment  │  │ StatefulSet  │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Monitoring: Prometheus + Grafana                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Kubernetes cluster (v1.25+)
- kubectl configured
- Helm 3.x
- Docker registry access
- 16GB+ RAM, 8+ CPU cores

## Quick Deploy

```bash
# Clone repository
cd ecommerce

# Build all service images
./scripts/build-all.sh

# Deploy to development
kubectl apply -k k8s/overlays/dev

# Deploy to production
kubectl apply -k k8s/overlays/prod

# Verify deployment
kubectl get pods -n ecommerce
```

## Components

### 1. Namespace

All resources deployed in `ecommerce` namespace for isolation.

### 2. Databases

**PostgreSQL** (StatefulSet):
- Used by: Catalog, Order, Inventory, User services
- Replicas: 1 (can be scaled with replication)
- Storage: 20Gi PVC
- Backup: Daily snapshots

**Redis** (Deployment):
- Used by: Cart service, caching
- Replicas: 1 (can use Redis Cluster for HA)
- Persistence: AOF enabled

**MongoDB** (StatefulSet):
- Used by: Reviews, logs
- Replicas: 1 (can be scaled to replica set)
- Storage: 10Gi PVC

**RabbitMQ** (StatefulSet):
- Event bus for async communication
- Replicas: 3 (quorum queue)
- Management UI enabled

### 3. Microservices

Each service deployed as a Deployment with:
- **Replicas**: 2-5 (auto-scaling enabled)
- **Resources**: CPU/memory limits
- **Health checks**: Liveness and readiness probes
- **Config**: ConfigMaps and Secrets
- **Networking**: ClusterIP services

### 4. API Gateway

Nginx-based gateway for:
- Request routing
- Load balancing
- Rate limiting
- SSL termination

### 5. Monitoring Stack

**Prometheus**:
- Metrics collection
- Alert manager
- Service discovery

**Grafana**:
- Dashboards
- Visualization
- Alerting

## Step-by-Step Deployment

### Step 1: Create Namespace

```bash
kubectl create namespace ecommerce
```

### Step 2: Deploy Databases

```bash
# PostgreSQL
kubectl apply -f k8s/base/postgres.yaml

# Wait for PostgreSQL to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n ecommerce --timeout=300s

# Redis
kubectl apply -f k8s/base/redis.yaml

# MongoDB
kubectl apply -f k8s/base/mongodb.yaml

# RabbitMQ
kubectl apply -f k8s/base/rabbitmq.yaml
```

### Step 3: Initialize Databases

```bash
# PostgreSQL - Create databases
kubectl exec -it postgres-0 -n ecommerce -- psql -U admin -c "
CREATE DATABASE catalog;
CREATE DATABASE orders;
CREATE DATABASE inventory;
CREATE DATABASE users;
"

# Run migrations (if using Alembic)
kubectl apply -f k8s/jobs/db-migrations.yaml
```

### Step 4: Deploy ConfigMaps and Secrets

```bash
kubectl apply -f k8s/base/config.yaml
kubectl apply -f k8s/base/secrets.yaml
```

### Step 5: Deploy Microservices

```bash
# Deploy all services
kubectl apply -f k8s/base/catalog-service.yaml
kubectl apply -f k8s/base/cart-service.yaml
kubectl apply -f k8s/base/order-service.yaml
kubectl apply -f k8s/base/payment-service.yaml
kubectl apply -f k8s/base/inventory-service.yaml
kubectl apply -f k8s/base/user-service.yaml

# Wait for all services
kubectl wait --for=condition=ready pod -l tier=backend -n ecommerce --timeout=300s
```

### Step 6: Deploy API Gateway

```bash
kubectl apply -f k8s/base/api-gateway.yaml
```

### Step 7: Deploy Ingress

```bash
# Install nginx ingress controller (if not already installed)
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install nginx-ingress ingress-nginx/ingress-nginx

# Deploy ingress
kubectl apply -f k8s/base/ingress.yaml
```

### Step 8: Deploy Monitoring

```bash
# Prometheus
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack -n ecommerce

# Access Grafana
kubectl port-forward svc/prometheus-grafana 3000:80 -n ecommerce
```

## Using Kustomize

### Development Environment

```bash
# Preview
kubectl kustomize k8s/overlays/dev

# Apply
kubectl apply -k k8s/overlays/dev

# Verify
kubectl get pods -n ecommerce
```

### Production Environment

```bash
# Preview
kubectl kustomize k8s/overlays/prod

# Apply
kubectl apply -k k8s/overlays/prod

# Verify
kubectl get all -n ecommerce
```

## Scaling

### Manual Scaling

```bash
# Scale catalog service to 5 replicas
kubectl scale deployment catalog-service --replicas=5 -n ecommerce
```

### Auto-Scaling (HPA)

Each service has HPA configured:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: catalog-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: catalog-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

Check HPA status:
```bash
kubectl get hpa -n ecommerce
```

## Monitoring

### View Metrics

```bash
# Pod metrics
kubectl top pods -n ecommerce

# Service metrics
kubectl top nodes
```

### Access Dashboards

```bash
# Grafana
kubectl port-forward svc/prometheus-grafana 3000:80 -n ecommerce
# Open http://localhost:3000

# Prometheus
kubectl port-forward svc/prometheus-kube-prometheus-prometheus 9090:9090 -n ecommerce
# Open http://localhost:9090

# RabbitMQ Management
kubectl port-forward svc/rabbitmq 15672:15672 -n ecommerce
# Open http://localhost:15672
```

## Troubleshooting

### Pod Not Starting

```bash
# Describe pod
kubectl describe pod <pod-name> -n ecommerce

# Check logs
kubectl logs <pod-name> -n ecommerce

# Check events
kubectl get events -n ecommerce --sort-by='.lastTimestamp'
```

### Database Connection Issues

```bash
# Test PostgreSQL connection
kubectl exec -it deployment/catalog-service -n ecommerce -- sh
nc -zv postgres-service 5432

# Test Redis connection
kubectl exec -it deployment/cart-service -n ecommerce -- sh
redis-cli -h redis-service ping
```

### Service Communication Issues

```bash
# Test service DNS
kubectl exec -it deployment/catalog-service -n ecommerce -- sh
nslookup cart-service.ecommerce.svc.cluster.local

# Test HTTP connectivity
curl http://cart-service.ecommerce.svc.cluster.local:8002/health
```

## Updating Services

### Rolling Update

```bash
# Update image
kubectl set image deployment/catalog-service catalog=your-registry/catalog:v2.0.0 -n ecommerce

# Watch rollout
kubectl rollout status deployment/catalog-service -n ecommerce

# Rollback if needed
kubectl rollout undo deployment/catalog-service -n ecommerce
```

### Blue-Green Deployment

```bash
# Deploy new version (green)
kubectl apply -f k8s/deployments/catalog-service-v2.yaml

# Switch traffic
kubectl patch service catalog-service -p '{"spec":{"selector":{"version":"v2"}}}'

# Remove old version (blue)
kubectl delete deployment catalog-service-v1
```

## Backup and Recovery

### Database Backups

```bash
# PostgreSQL backup
kubectl exec postgres-0 -n ecommerce -- pg_dumpall -U admin > backup.sql

# Restore
kubectl exec -i postgres-0 -n ecommerce -- psql -U admin < backup.sql
```

### Persistent Volume Snapshots

```bash
# Create snapshot
kubectl apply -f k8s/snapshots/postgres-snapshot.yaml

# Restore from snapshot
kubectl apply -f k8s/restore/postgres-restore.yaml
```

## Security

### Network Policies

```bash
# Apply network policies
kubectl apply -f k8s/network-policies/

# Verify
kubectl get networkpolicies -n ecommerce
```

### Secrets Management

```bash
# Create secrets from files
kubectl create secret generic stripe-keys \
  --from-file=api-key=stripe-api-key.txt \
  -n ecommerce

# Use external secrets (recommended for production)
kubectl apply -f k8s/external-secrets/
```

## Performance Tuning

### Resource Limits

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### Connection Pooling

```python
# PostgreSQL connection pool
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True
)
```

### Caching Strategy

```python
# Redis caching
@cache(ttl=300)  # 5 minutes
async def get_product(product_id):
    return await db.fetch_one(...)
```

## Production Checklist

- [ ] Update all secrets with strong passwords
- [ ] Configure persistent volumes with backup
- [ ] Set up database replication
- [ ] Enable TLS/SSL for all services
- [ ] Configure resource limits appropriately
- [ ] Set up monitoring and alerting
- [ ] Configure log aggregation (ELK/Loki)
- [ ] Enable network policies
- [ ] Set up CI/CD pipeline
- [ ] Configure auto-scaling policies
- [ ] Test disaster recovery procedures
- [ ] Set up rate limiting
- [ ] Configure CORS policies
- [ ] Enable audit logging
- [ ] Set up backup automation

## Cost Optimization

### Right-Sizing

```bash
# Analyze resource usage
kubectl top pods -n ecommerce --containers

# Adjust resource requests/limits based on actual usage
```

### Spot Instances

```yaml
# Use node affinity for non-critical workloads
affinity:
  nodeAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 1
      preference:
        matchExpressions:
        - key: node.kubernetes.io/instance-type
          operator: In
          values:
          - spot
```

### Pod Disruption Budgets

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: catalog-pdb
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: catalog-service
```

## Cleanup

```bash
# Delete everything
kubectl delete namespace ecommerce

# Or delete specific resources
kubectl delete -k k8s/overlays/dev
kubectl delete -k k8s/overlays/prod
```

## Additional Resources

- [API Documentation](API_DOCUMENTATION.md)
- [Flow Documentation](FLOW_DOCUMENTATION.md)
- [Architecture Guide](ARCHITECTURE.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)

## Support

For issues and questions:
- GitHub Issues
- Slack: #ecommerce-platform
- Email: devops@example.com
