# Kubernetes Deployment Guide

Complete guide for deploying the inventory system to Kubernetes.

## Prerequisites

- Kubernetes cluster (1.25+)
- kubectl configured
- Docker registry access
- Kustomize (built into kubectl)

## Quick Deploy

```bash
# Build and push Docker image
docker build -t your-registry/inventory-api:latest .
docker push your-registry/inventory-api:latest

# Deploy to development
kubectl apply -k k8s/overlays/dev

# Deploy to production
kubectl apply -k k8s/overlays/prod
```

## Architecture

```
┌─────────────────────────────────────────────┐
│           Kubernetes Cluster                │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │  Ingress (nginx)                     │  │
│  │  inventory.example.com               │  │
│  └────────────┬─────────────────────────┘  │
│               │                             │
│  ┌────────────▼─────────────────────────┐  │
│  │  Service: inventory-api-service      │  │
│  │  Type: LoadBalancer                  │  │
│  └────────────┬─────────────────────────┘  │
│               │                             │
│  ┌────────────▼─────────────────────────┐  │
│  │  Deployment: inventory-api           │  │
│  │  Replicas: 3-10 (HPA)                │  │
│  │  ┌─────┐ ┌─────┐ ┌─────┐             │  │
│  │  │ Pod │ │ Pod │ │ Pod │             │  │
│  │  └─────┘ └─────┘ └─────┘             │  │
│  └──────────────────────────────────────┘  │
│                                             │
│  ┌──────────────┐    ┌──────────────┐     │
│  │ StatefulSet  │    │ Deployment   │     │
│  │  PostgreSQL  │    │    Redis     │     │
│  │  (1 replica) │    │  (1 replica) │     │
│  └──────────────┘    └──────────────┘     │
│                                             │
└─────────────────────────────────────────────┘
```

## Components

### 1. Namespace

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: inventory-system
```

All resources deployed in `inventory-system` namespace.

### 2. ConfigMap & Secrets

**ConfigMap** - Non-sensitive configuration:
- Database host, port, name
- Redis host, port

**Secrets** - Sensitive data:
- Database credentials
- JWT secret

### 3. PostgreSQL StatefulSet

- **Replicas**: 1 (single instance)
- **Storage**: 10Gi PersistentVolume
- **Resources**: 256Mi-512Mi memory, 250m-500m CPU
- **Probes**: Liveness and readiness checks

### 4. Redis Deployment

- **Replicas**: 1
- **Persistence**: AOF enabled
- **Resources**: 128Mi-256Mi memory, 100m-200m CPU

### 5. Inventory API Deployment

- **Replicas**: 3-10 (auto-scaling)
- **Image**: inventory-api:latest
- **Resources**: 256Mi-512Mi memory, 250m-500m CPU
- **HPA**: Scales based on CPU (70%) and memory (80%)

### 6. Services

- **postgres-service**: ClusterIP (headless)
- **redis-service**: ClusterIP
- **inventory-api-service**: LoadBalancer

### 7. Ingress

- **Host**: inventory.example.com
- **TLS**: Let's Encrypt certificate
- **Controller**: nginx

## Deployment Steps

### Step 1: Prepare Docker Image

```bash
# Build image
docker build -t your-registry/inventory-api:v1.0.0 .

# Tag as latest
docker tag your-registry/inventory-api:v1.0.0 your-registry/inventory-api:latest

# Push to registry
docker push your-registry/inventory-api:v1.0.0
docker push your-registry/inventory-api:latest
```

### Step 2: Update Image Reference

Edit `k8s/base/inventory-api.yaml`:
```yaml
spec:
  template:
    spec:
      containers:
      - name: inventory-api
        image: your-registry/inventory-api:v1.0.0  # Update this
```

### Step 3: Deploy Base Resources

```bash
# Create namespace
kubectl apply -f k8s/base/namespace.yaml

# Deploy config and secrets
kubectl apply -f k8s/base/config.yaml

# Deploy databases
kubectl apply -f k8s/base/postgres.yaml
kubectl apply -f k8s/base/redis.yaml

# Wait for databases to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n inventory-system --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis -n inventory-system --timeout=60s
```

### Step 4: Initialize Database

```bash
# Get PostgreSQL pod name
POD=$(kubectl get pod -l app=postgres -n inventory-system -o jsonpath='{.items[0].metadata.name}')

# Create tables (run migrations)
kubectl exec -it $POD -n inventory-system -- psql -U admin -d inventory -c "
CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";
-- Add your schema here or use Alembic
"
```

### Step 5: Deploy API

```bash
# Deploy API
kubectl apply -f k8s/base/inventory-api.yaml

# Wait for rollout
kubectl rollout status deployment/inventory-api -n inventory-system
```

### Step 6: Deploy Ingress

```bash
# Install nginx ingress controller (if not already installed)
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml

# Deploy ingress
kubectl apply -f k8s/base/ingress.yaml
```

### Step 7: Verify Deployment

```bash
# Check all pods
kubectl get pods -n inventory-system

# Check services
kubectl get svc -n inventory-system

# Check ingress
kubectl get ingress -n inventory-system

# View logs
kubectl logs -f deployment/inventory-api -n inventory-system

# Test API
kubectl port-forward svc/inventory-api-service 8000:80 -n inventory-system
curl http://localhost:8000/health
```

## Using Kustomize

### Development Environment

```bash
# Preview changes
kubectl kustomize k8s/overlays/dev

# Apply
kubectl apply -k k8s/overlays/dev

# Verify
kubectl get pods -n inventory-system -l app=dev-inventory-api
```

### Production Environment

```bash
# Preview
kubectl kustomize k8s/overlays/prod

# Apply
kubectl apply -k k8s/overlays/prod

# Verify
kubectl get pods -n inventory-system -l app=prod-inventory-api
```

## Scaling

### Manual Scaling

```bash
# Scale to 5 replicas
kubectl scale deployment inventory-api --replicas=5 -n inventory-system
```

### Auto-Scaling (HPA)

HPA automatically scales based on:
- CPU utilization > 70%
- Memory utilization > 80%

```bash
# Check HPA status
kubectl get hpa -n inventory-system

# Describe HPA
kubectl describe hpa inventory-api-hpa -n inventory-system
```

## Monitoring

### View Metrics

```bash
# Pod metrics
kubectl top pods -n inventory-system

# Node metrics
kubectl top nodes
```

### Logs

```bash
# Stream logs
kubectl logs -f deployment/inventory-api -n inventory-system

# Last 100 lines
kubectl logs --tail=100 deployment/inventory-api -n inventory-system

# All pods
kubectl logs -l app=inventory-api -n inventory-system
```

## Troubleshooting

### Pod Not Starting

```bash
# Describe pod
kubectl describe pod <pod-name> -n inventory-system

# Check events
kubectl get events -n inventory-system --sort-by='.lastTimestamp'

# Check logs
kubectl logs <pod-name> -n inventory-system
```

### Database Connection Issues

```bash
# Test database connectivity
kubectl exec -it deployment/inventory-api -n inventory-system -- sh
# Inside pod:
nc -zv postgres-service 5432
```

### Redis Connection Issues

```bash
# Test Redis
kubectl exec -it deployment/inventory-api -n inventory-system -- sh
# Inside pod:
redis-cli -h redis-service ping
```

## Updating

### Rolling Update

```bash
# Update image
kubectl set image deployment/inventory-api inventory-api=your-registry/inventory-api:v1.1.0 -n inventory-system

# Watch rollout
kubectl rollout status deployment/inventory-api -n inventory-system

# Rollback if needed
kubectl rollout undo deployment/inventory-api -n inventory-system
```

## Cleanup

```bash
# Delete everything
kubectl delete namespace inventory-system

# Or delete specific resources
kubectl delete -k k8s/overlays/dev
kubectl delete -k k8s/overlays/prod
```

## Production Checklist

- [ ] Update secrets with strong passwords
- [ ] Configure persistent volumes for production
- [ ] Set up database backups
- [ ] Configure monitoring (Prometheus/Grafana)
- [ ] Set up logging (ELK/Loki)
- [ ] Configure TLS certificates
- [ ] Set resource limits appropriately
- [ ] Enable network policies
- [ ] Configure pod security policies
- [ ] Set up CI/CD pipeline
- [ ] Test disaster recovery

## Best Practices

1. **Use Kustomize overlays** for environment-specific configs
2. **Tag images** with version numbers, not just `latest`
3. **Set resource limits** to prevent resource exhaustion
4. **Use health checks** for liveness and readiness
5. **Enable auto-scaling** for variable load
6. **Monitor metrics** and set up alerts
7. **Regular backups** of PostgreSQL data
8. **Use secrets** for sensitive data
9. **Network policies** to restrict traffic
10. **Regular updates** and security patches
