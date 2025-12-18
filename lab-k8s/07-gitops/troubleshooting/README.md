# GitOps Troubleshooting Guide

## 🔍 Common Issues and Solutions

This guide covers the most common issues you'll encounter when working with GitOps and ArgoCD, along with their solutions.

---

## 🚨 ArgoCD Installation Issues

### Issue 1: Pods Not Starting (ImagePullBackOff)

**Symptoms:**
```bash
kubectl get pods -n argocd
# NAME                                  READY   STATUS             RESTARTS   AGE
# argocd-server-xxx                     0/1     ImagePullBackOff   0          2m
```

**Diagnosis:**
```bash
kubectl describe pod argocd-server-xxx -n argocd
# Look for: "Failed to pull image" or "rate limit exceeded"
```

**Solutions:**

1. **Docker Hub Rate Limiting:**
```bash
# Login to Docker Hub
docker login

# Create Docker registry secret
kubectl create secret docker-registry dockerhub \
  --docker-server=https://index.docker.io/v1/ \
  --docker-username=YOUR_USERNAME \
  --docker-password=YOUR_PASSWORD \
  --docker-email=YOUR_EMAIL \
  -n argocd

# Patch service accounts to use the secret
kubectl patch serviceaccount default -n argocd \
  -p '{"imagePullSecrets": [{"name": "dockerhub"}]}'
```

2. **Network Issues:**
```bash
# Test connectivity
kubectl run test --image=busybox --rm -it  --restart=Never -- wget -O- https://quay.io

# If fails, check cluster networking/DNS
```

### Issue 2: CrashLoopBackOff

**Symptoms:**
```bash
kubectl get pods -n argocd
# argocd-application-controller-0       0/1     CrashLoopBackOff   5          5m
```

**Diagnosis:**
```bash
# Check logs
kubectl logs -n argocd argocd-application-controller-0 --previous

# Common errors:
# - Out of memory
# - Permission denied
# - Connection refused to Redis
```

**Solutions:**

1. **Insufficient Resources:**
```bash
# Check node resources
kubectl top nodes

# Increase cluster resources
minikube delete
minikube start --cpus=4 --memory=10240

# Or for Kind, recreate with more resources
```

2. **Redis Connection Issues:**
```bash
# Check Redis is running
kubectl get pods -n argocd | grep redis

# Test Redis connection
kubectl run -it --rm redis-test --image=redis:alpine --restart=Never -n argocd -- redis-cli -h argocd-redis ping
```

---

## 🔄 Application Sync Issues

### Issue 3: Application Stuck in "OutOfSync"

**Symptoms:**
```bash
argocd app get myapp
# Status:         OutOfSync
# Sync Status:    OutOfSync from TARGET (abc123)
```

**Diagnosis:**
```bash
# Get detailed diff
argocd app diff myapp

# Check sync status
argocd app get myapp --refresh
```

**Solutions:**

1. **Force Refresh:**
```bash
# Hard refresh (bypass cache)
argocd app get myapp --hard-refresh

# Manual sync
argocd app sync myapp
```

2. **Prune Resources:**
```bash
# Sync with prune
argocd app sync myapp --prune

# Or update Application to enable auto-prune
kubectl patch application myapp -n argocd --type=merge \
  -p '{"spec":{"syncPolicy":{"automated":{"prune":true}}}}'
```

3. **Ignore Specific Differences:**
```yaml
# Add to Application spec
spec:
  ignoreDifferences:
    - group: apps
      kind: Deployment
      jsonPointers:
        - /spec/replicas  # If HPA manages this
```

### Issue 4: Sync Fails with "Permission Denied"

**Symptoms:**
```
FATA[0000] rpc error: code = PermissionDenied desc = permission denied
```

**Diagnosis:**
```bash
# Check ArgoCD has access to namespace
kubectl auth can-i create deployments --namespace=myapp --as=system:serviceaccount:argocd:argocd-application-controller
```

**Solutions:**

```bash
# Create necessary RBAC permissions
cat <<EOF | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind:RoleBinding
metadata:
  name: argocd-application-controller
  namespace: myapp
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: admin
subjects:
- kind: ServiceAccount
  name: argocd-application-controller
  namespace: argocd
EOF
```

### Issue 5: Git Repository Authentication Failed

**Symptoms:**
```
Failed to fetch: authentication required
```

**Solutions:**

1. **For Public Repositories:**
```bash
# Ensure repo URL is correct and public
argocd repo add https://github.com/user/repo.git
```

2. **For Private Repositories (HTTPS):**
```bash
# Add repository with credentials
argocd repo add https://github.com/user/repo.git \
  --username YOUR_USERNAME \
  --password YOUR_PASSWORD_OR_TOKEN
```

3. **For Private Repositories (SSH):**
```bash
# Add SSH key
argocd repo add git@github.com:user/repo.git \
  --ssh-private-key-path ~/.ssh/id_rsa
```

---

## 🐛 Application Health Issues

### Issue 6: Application Shows "Degraded" Health

**Symptoms:**
```bash
argocd app get myapp
# Health Status:  Degraded
```

**Diagnosis:**
```bash
# Check pod status
kubectl get pods -n myapp-namespace

# Describe problematic pod
kubectl describe pod pod-name -n myapp-namespace

# Check logs
kubectl logs pod-name -n myapp-namespace
```

**Common Causes & Solutions:**

1. **Pod CrashLoopBackOff:**
```bash
# Check logs for errors
kubectl logs pod-name --previous -n myapp-namespace

# Common fixes:
# - Fix application code
# - Adjust resource limits
# - Fix configuration/environment variables
```

2. **Readiness Probe Failing:**
```yaml
# Adjust readiness probe settings
readinessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30  # Increase if app needs more startup time
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3  # Allow more failures before marking unhealthy
```

3. **Image Pull Errors:**
```bash
# Check image exists
docker pull your-image:tag

# Verify image pull secret
kubectl get secret image-pull-secret -n myapp-namespace
```

### Issue 7: Service/Ingress Not Working

**Symptoms:**
- Application deployed but not accessible
- Connection refused

**Diagnosis:**
```bash
# Check service exists and has endpoints
kubectl get svc -n myapp-namespace
kubectl get endpoints -n myapp-namespace

# Test from within cluster
kubectl run test --image=curlimages/curl --rm -it --restart=Never -- curl http://myapp-service
```

**Solutions:**

1. **Service Selector Mismatch:**
```yaml
# Ensure service selector matches pod labels
# Service:
selector:
  app: myapp
  
# Deployment:
template:
  metadata:
    labels:
      app: myapp  # Must match
```

2. **Port Configuration:**
```yaml
# Ensure ports are correctly configured
spec:
  ports:
    - port: 80          # Service port
      targetPort: 8080  # Container port (must match container)
```

---

## ⚡ Performance Issues

### Issue 8: Slow Sync Operations

**Symptoms:**
- Sync takes > 5 minutes
- ArgoCD UI slow

**Solutions:**

1. **Increase Controller Resources:**
```bash
kubectl edit deployment argocd-application-controller -n argocd

# Increase:
resources:
  requests:
    cpu: "1000m"
    memory: "1Gi"
  limits:
    cpu: "2000m"
    memory: "2Gi"
```

2. **Reduce Sync Frequency:**
```yaml
# In Application spec
spec:
  source:
    repoURL: https://github.com/user/repo
    targetRevision: HEAD
    # Add:
  syncPolicy:
    automated:
      prune: true
    # Reduce refresh interval (default: 3m)
```

3. **Use Server-Side Apply:**
```yaml
syncOptions:
  - ServerSideApply=true  # Faster for large applications
```

---

## 🔐 Security & Access Issues

### Issue 9: Cannot Access ArgoCD UI

**Symptoms:**
- Browser can't connect to localhost:8080
- Connection refused

**Solutions:**

1. **Check Port-Forward:**
```bash
# Check if running
ps aux | grep port-forward

# Start if not running
kubectl port-forward svc/argocd-server -n argocd 8080:443 &

# Test connection
curl -k https://localhost:8080
```

2. **Check ArgoCD Server Pod:**
```bash
kubectl get pods -n argocd | grep argocd-server

# If not running, check logs
kubectl logs -n argocd deployment/argocd-server
```

###Issue 10: Forgot Admin Password

**Solutions:**

```bash
# Retrieve initial password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# If secret was deleted, reset password:
# 1. Get current password hash
kubectl -n argocd get secret argocd-secret -o jsonpath="{.data['admin\.password']}" | base64 -d

# 2. Generate new password hash
# Use bcrypt online tool or:
argocd account bcrypt --password "new-password"

# 3. Update secret
kubectl -n argocd patch secret argocd-secret \
  -p '{"stringData": {"admin.password": "$2a$10$..."}}'
```

---

## 🔍 Diagnostic Commands

### General Diagnostics

```bash
# ArgoCD Status
kubectl get all -n argocd
argocd version
argocd cluster list

# Application Status
argocd app list
argocd app get <app-name>
argocd app history <app-name>
argocd app resources <app-name>

# Detailed Application Info
argocd app get <app-name> --refresh
argocd app diff <app-name>
argocd app manifests <app-name>

# Logs
kubectl logs -n argocd deployment/argocd-application-controller
kubectl logs -n argocd deployment/argocd-server
kubectl logs -n argocd deployment/argocd-repo-server

# Events
kubectl get events -n argocd --sort-by='.lastTimestamp'
kubectl get events -n <app-namespace> --sort-by='.lastTimestamp'

# Resource Usage
kubectl top nodes
kubectl top pods -n argocd
kubectl top pods -n <app-namespace>
```

---

## 🚑 Emergency Procedures

### Emergency: Application Down in Production

1. **Quick Rollback:**
```bash
# View history
argocd app history myapp-prod

# Rollback to last known good version
argocd app rollback myapp-prod <REVISION_ID>
```

2. **Manual Override (Last Resort):**
```bash
# Temporarily disable auto-sync
argocd app set myapp-prod --sync-policy none

# Make manual fix
kubectl edit deployment myapp -n production

# Re-enable auto-sync after fix is in Git
argocd app set myapp-prod --sync-policy automated
```

### Emergency: ArgoCD Down

```bash
# Applications keep running! ArgoCD is just the control plane

# Restart ArgoCD components
kubectl rollout restart deployment -n argocd

# Or delete and recreate pods
kubectl delete pods --all -n argocd
```

---

## 📚 Additional Resources

- [ArgoCD Troubleshooting Guide](https://argo-cd.readthedocs.io/en/stable/user-guide/troubleshooting/)
- [Kubernetes Debugging](https://kubernetes.io/docs/tasks/debug/)
- [ArgoCD GitHub Issues](https://github.com/argoproj/argo-cd/issues)

---

**Pro Tip**: Always check ArgoCD and application logs first. They usually contain the exact error message pointing to the issue! 🔍
