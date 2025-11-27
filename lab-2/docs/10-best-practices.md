# 10. Best Practices

## Jenkins Best Practices

### Pipeline as Code

✅ **Store Jenkinsfile in SCM**
- Version control your pipelines
- Review changes through pull requests
- Rollback easily if needed

```groovy
// Good: Jenkinsfile in repository root
pipeline {
    agent any
    stages {
        // ...
    }
}
```

### Use Shared Libraries

✅ **Create reusable pipeline code**

```groovy
// vars/buildDockerImage.groovy
def call(String imageName, String tag) {
    sh "docker build -t ${imageName}:${tag} ."
}

// In Jenkinsfile
@Library('my-shared-library') _
buildDockerImage('myapp', env.BUILD_NUMBER)
```

### Security

✅ **Use Credentials Plugin**
- Never hardcode secrets
- Use Jenkins credentials store
- Rotate credentials regularly

```groovy
withCredentials([string(credentialsId: 'api-key', variable: 'API_KEY')]) {
    sh 'curl -H "Authorization: Bearer $API_KEY" ...'
}
```

✅ **Enable CSRF Protection**
- Manage Jenkins → Configure Global Security
- Enable "Prevent Cross Site Request Forgery exploits"

✅ **Implement RBAC**
- Use Matrix Authorization Strategy
- Limit access based on roles
- Regular audit of permissions

### Performance

✅ **Limit Build History**
- Configure "Discard old builds"
- Keep last 10-20 builds
- Saves disk space

✅ **Use Parallel Stages**
```groovy
stage('Tests') {
    parallel {
        stage('Unit Tests') { steps { sh 'npm run test:unit' } }
        stage('Integration Tests') { steps { sh 'npm run test:integration' } }
    }
}
```

✅ **Clean Workspace**
```groovy
post {
    always {
        cleanWs()
    }
}
```

### Monitoring

✅ **Regular Backups**
```bash
# Automated backup script
tar -czf jenkins-backup-$(date +%Y%m%d).tar.gz /var/lib/jenkins/
```

✅ **Monitor Build Metrics**
- Build success rate
- Build duration trends
- Queue length

## Docker Best Practices

### Dockerfile Optimization

✅ **Use Multi-Stage Builds**
```dockerfile
# Build stage
FROM node:18 AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Production stage
FROM node:18-alpine
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
CMD ["node", "dist/server.js"]
```

✅ **Use Specific Tags**
```dockerfile
# Bad
FROM node:latest

# Good
FROM node:18.17.0-alpine
```

✅ **Minimize Layers**
```dockerfile
# Bad - 3 layers
RUN apt-get update
RUN apt-get install -y package1
RUN apt-get install -y package2

# Good - 1 layer
RUN apt-get update && apt-get install -y \
    package1 \
    package2 \
    && rm -rf /var/lib/apt/lists/*
```

✅ **Use .dockerignore**
```
node_modules
.git
.env
*.md
.vscode
```

### Security

✅ **Run as Non-Root User**
```dockerfile
RUN useradd -m -u 1000 appuser
USER appuser
```

✅ **Scan Images for Vulnerabilities**
```bash
# Using Trivy
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    aquasec/trivy image myapp:latest
```

✅ **Use Minimal Base Images**
```dockerfile
# Prefer alpine or distroless
FROM node:18-alpine
# or
FROM gcr.io/distroless/nodejs:18
```

### Image Management

✅ **Tag Properly**
```bash
# Include version and commit
docker tag myapp:latest myapp:v1.2.3
docker tag myapp:latest myapp:git-abc123
```

✅ **Regular Cleanup**
```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Complete cleanup
docker system prune -a --volumes
```

## Kubernetes Best Practices

### Resource Management

✅ **Define Resource Requests and Limits**
```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

✅ **Use Horizontal Pod Autoscaler**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: myapp-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: myapp
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### High Availability

✅ **Multiple Replicas**
```yaml
spec:
  replicas: 3  # Minimum for HA
```

✅ **Pod Disruption Budgets**
```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: myapp-pdb
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: myapp
```

✅ **Anti-Affinity Rules**
```yaml
affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      podAffinityTerm:
        labelSelector:
          matchExpressions:
          - key: app
            operator: In
            values:
            - myapp
        topologyKey: kubernetes.io/hostname
```

### Health Checks

✅ **Liveness and Readiness Probes**
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 3000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /ready
    port: 3000
  initialDelaySeconds: 5
  periodSeconds: 5
```

### Configuration Management

✅ **Use ConfigMaps for Configuration**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: myapp-config
data:
  database_url: "postgres://db:5432/mydb"
  log_level: "info"
```

✅ **Use Secrets for Sensitive Data**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: myapp-secrets
type: Opaque
data:
  db_password: cGFzc3dvcmQxMjM=  # base64 encoded
```

✅ **Never Hardcode Secrets**
```yaml
# Bad
env:
- name: DB_PASSWORD
  value: "password123"

# Good
env:
- name: DB_PASSWORD
  valueFrom:
    secretKeyRef:
      name: myapp-secrets
      key: db_password
```

### Namespace Organization

✅ **Use Namespaces for Isolation**
```bash
# Separate environments
kubectl create namespace development
kubectl create namespace staging
kubectl create namespace production
```

✅ **Resource Quotas**
```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
  namespace: development
spec:
  hard:
    requests.cpu: "10"
    requests.memory: 20Gi
    limits.cpu: "20"
    limits.memory: 40Gi
```

### Security

✅ **RBAC**
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
  namespace: production
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list"]
```

✅ **Network Policies**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: backend
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
```

✅ **Pod Security Standards**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: restricted
```

## CI/CD Best Practices

### Version Control

✅ **Semantic Versioning**
```
v1.2.3
 │ │ └─ Patch: Bug fixes
 │ └─── Minor: New features (backward compatible)
 └───── Major: Breaking changes
```

✅ **Git Flow**
- `main` - Production code
- `develop` - Development branch
- `feature/*` - Feature branches
- `hotfix/*` - Hotfix branches

### Testing

✅ **Test Pyramid**
```
        /\
       /  \      E2E Tests (Few)
      /────\
     /      \    Integration Tests (Some)
    /────────\
   /          \  Unit Tests (Many)
  /────────────\
```

✅ **Automated Testing in Pipeline**
```groovy
stage('Tests') {
    parallel {
        stage('Unit Tests') {
            steps { sh 'npm run test:unit' }
        }
        stage('Integration Tests') {
            steps { sh 'npm run test:integration' }
        }
        stage('Security Scan') {
            steps { sh 'npm audit' }
        }
    }
}
```

### Deployment Strategies

✅ **Rolling Updates** (Default)
- Gradual replacement of pods
- Zero downtime
- Easy rollback

✅ **Blue-Green Deployment**
- Two identical environments
- Instant switch
- Easy rollback

✅ **Canary Deployment**
- Gradual traffic shift
- Test with subset of users
- Minimize risk

### Monitoring and Observability

✅ **Three Pillars**
1. **Metrics** - Prometheus, Grafana
2. **Logs** - ELK, Loki
3. **Traces** - Jaeger, Zipkin

✅ **SLIs and SLOs**
- Service Level Indicators (SLIs)
- Service Level Objectives (SLOs)
- Service Level Agreements (SLAs)

### Documentation

✅ **Document Everything**
- Architecture diagrams
- Runbooks for common issues
- Deployment procedures
- Rollback procedures

✅ **Keep Documentation Updated**
- Review quarterly
- Update with changes
- Version control documentation

## Security Best Practices

### General Security

✅ **Principle of Least Privilege**
- Grant minimum necessary permissions
- Regular access reviews
- Remove unused accounts

✅ **Regular Updates**
```bash
# Update system
sudo apt update && sudo apt upgrade

# Update Docker
sudo apt install docker-ce docker-ce-cli

# Update Kubernetes
# Follow cluster-specific upgrade procedures
```

✅ **Secrets Management**
- Use HashiCorp Vault or AWS Secrets Manager
- Rotate secrets regularly
- Never commit secrets to Git

✅ **Network Security**
- Use TLS/SSL everywhere
- Implement network segmentation
- Use firewalls and security groups

### Compliance

✅ **Audit Logging**
- Enable audit logs
- Regular log reviews
- Retain logs per compliance requirements

✅ **Backup and Disaster Recovery**
- Regular automated backups
- Test restore procedures
- Document recovery time objectives (RTO)

## Performance Optimization

### Jenkins

- Use pipeline caching
- Limit concurrent builds
- Archive artifacts selectively
- Use agents for distributed builds

### Docker

- Layer caching
- Multi-stage builds
- Minimize image size
- Use BuildKit

### Kubernetes

- Right-size resources
- Use HPA for auto-scaling
- Implement caching strategies
- Optimize container startup time

## Summary

Following these best practices will help you:
- ✅ Build reliable CI/CD pipelines
- ✅ Maintain secure systems
- ✅ Optimize performance
- ✅ Scale efficiently
- ✅ Troubleshoot effectively

Remember: **Best practices evolve**. Stay updated with the latest recommendations from the community.
