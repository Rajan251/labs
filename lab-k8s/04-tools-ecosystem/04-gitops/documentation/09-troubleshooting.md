# Troubleshooting GitOps Issues

## Common ArgoCD Issues

### 1. Application OutOfSync

**Symptoms:**
- Application shows "OutOfSync" status in UI
- Resources in cluster don't match Git

**Diagnosis:**
```bash
# Check application status
argocd app get <app-name>

# View diff between Git and cluster
argocd app diff <app-name>

# Check sync status details
kubectl describe application <app-name> -n argocd
```

**Common Causes & Solutions:**

#### Manual Changes to Cluster
```bash
# Someone ran kubectl commands directly
# Solution: Enable self-heal or manually sync

argocd app sync <app-name>

# Or enable self-heal
argocd app set <app-name> --self-heal
```

#### Git Not Updated
```bash
# CI pipeline didn't update manifests
# Solution: Check CI logs, manually update Git

# Verify latest commit
git log -1

# Check if ArgoCD is tracking correct revision
argocd app get <app-name> | grep "Target Revision"
```

#### Kustomize Build Errors
```bash
# Kustomize can't build manifests
# Solution: Test kustomize build locally

kustomize build path/to/overlay
```

### 2. Application Degraded/Unhealthy

**Symptoms:**
- Health status shows "Degraded"
- Pods are CrashLoopBackOff or ImagePullBackOff

**Diagnosis:**
```bash
# Check resource health
argocd app get <app-name> --show-operation

# View resource tree
argocd app resources <app-name>

# Check pod status
kubectl get pods -n <namespace>

# Describe failed pod
kubectl describe pod <pod-name> -n <namespace>

# View pod logs
kubectl logs <pod-name> -n <namespace>
```

**Common Issues:**

#### ImagePullBackOff
```bash
# Can't pull container image
# Causes:
# - Image doesn't exist
# - Wrong image tag
# - Registry authentication failure

# Solutions:
# 1. Verify image exists
docker pull <image>:<tag>

# 2. Check image pull secrets
kubectl get secrets -n <namespace>

# 3. Create image pull secret if needed
kubectl create secret docker-registry regcred \
  --docker-server=<registry> \
  --docker-username=<username> \
  --docker-password=<password> \
  -n <namespace>

# 4. Add to deployment
kubectl patch serviceaccount default \
  -p '{"imagePullSecrets": [{"name": "regcred"}]}' \
  -n <namespace>
```

#### CrashLoop BackOff
```bash
# Container keeps crashing
# Check logs for errors
kubectl logs <pod-name> -n <namespace>

# Check previous container logs
kubectl logs <pod-name> -n <namespace> --previous

# Common fixes:
# - Increase memory/CPU limits
# - Fix application configuration
# - Check environment variables
# - Verify dependencies (database, API)
```

### 3. Sync Failures

**Symptoms:**
- Sync operation fails
- Error messages in ArgoCD UI

**Diagnosis:**
```bash
# View sync history
argocd app history <app-name>

# Check latest sync result
argocd app get <app-name>

# View detailed sync errors
kubectl get application <app-name> -n argocd -o yaml
```

**Common Issues:**

#### Permission Errors
```bash
# ArgoCD doesn't have permission to create resources
# Error: "forbidden: User ... cannot create resource ..."

# Solution: Check RBAC permissions
kubectl auth can-i create deployment --as=system:serviceaccount:argocd:argocd-application-controller -n <namespace>

# Grant permissions if needed (create Role/RoleBinding)
```

#### Resource Quota Exceeded
```bash
# Namespace has resource quotas
# Error: "exceeded quota"

# Check quota
kubectl get resourcequota -n <namespace>

# View usage
kubectl describe resourcequota -n <namespace>

# Solutions:
# - Increase quota
# - Reduce resource requests
# - Clean up unused resources
```

#### Schema Validation Errors
```bash
# Invalid YAML or API version
# Error: "error validating data"

# Solution: Validate manifests locally
kubectl apply --dry-run=client -f manifest.yaml

# Or use kustomize
kustomize build . | kubectl apply --dry-run=client -f -
```

### 4. Git Connection Issues

**Symptoms:**
- Can't fetch from Git repository
- "failed to get Git client" errors

**Diagnosis:**
```bash
# List repositories
argocd repo list

# Test repository connection
argocd repo get <repo-url>

# View repo server logs
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-repo-server
```

**Common Issues:**

#### Authentication Failures
```bash
# Private repository without credentials

# For HTTPS with token:
argocd repo add https://github.com/user/repo \
  --username user \
  --password <github-token>

# For SSH:
argocd repo add git@github.com:user/repo.git \
  --ssh-private-key-path ~/.ssh/id_rsa
```

#### Webhook Not Working
```bash
# ArgoCD not notified of Git changes
# Must manually sync or wait for polling

# Configure webhook in GitHub/GitLab:
# URL: https://argocd.example.com/api/webhook
# Secret: <webhook-secret>

# Get webhook secret
kubectl get secret argocd-secret -n argocd -o jsonpath="{.data.webhook\.github\.secret}" | base64 -d
```

### 5. Performance Issues

**Symptoms:**
- Slow sync operations
- ArgoCD UI slow or unresponsive
- High CPU/memory usage

**Diagnosis:**
```bash
# Check ArgoCD pod resources
kubectl top pods -n argocd

# View controller logs
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-application-controller --tail=100

# Check application count
argocd app list | wc -l
```

**Solutions:**

```bash
# Increase controller resources
kubectl edit deployment argocd-application-controller -n argocd
# Update resources.limits and resources.requests

# Adjust sync timeout
argocd app set <app-name> --sync-option Timeout=5m

# Reduce polling frequency
kubectl edit configmap argocd-cm -n argocd
# Add: timeout.reconciliation: 600 (10 minutes)
```

## Debug Commands Reference

### Application Commands
```bash
# Get application details
argocd app get <app-name>

# View application history
argocd app history <app-name>

# Show resource differences
argocd app diff <app-name>

# View resource tree
argocd app resources <app-name>

# Manual sync
argocd app sync <app-name>

# Force sync (ignore errors)
argocd app sync <app-name> --force

# Delete and recreate resource
argocd app sync <app-name> --resource apps:Deployment:<name>
```

### Logs
```bash
# Application controller logs (sync logic)
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-application-controller

# Repo server logs (Git operations)
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-repo-server

# Server logs (API/UI)
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-server

# All ArgoCD logs
kubectl logs -n argocd --all-containers=true
```

### Events
```bash
# Check Kubernetes events
kubectl get events -n <namespace> --sort-by='.lastTimestamp'

# Watch events
kubectl get events -n <namespace> -w

# Application events
kubectl describe application <app-name> -n argocd | grep Events -A 10
```

## Prevention Best Practices

### 1. Pre-Deployment Validation
```bash
# Always build and test locally first
kustomize build overlays/dev | kubectl apply --dry-run=client -f -

# Validate YAML syntax
yamllint manifests/

# Use pre-commit hooks for validation
```

### 2. Gradual Rollouts
```bash
# Test in dev first
argocd app sync myapp-dev

# Then staging
argocd app sync myapp-staging

# Finally production (with manual approval)
argocd app sync myapp-prod
```

### 3. Monitoring
```bash
# Set up alerts for OutOfSync apps
# Use Prometheus + ArgoCD metrics
# Create Grafana dashboards
```

### 4. Documentation
```bash
# Document all manual interventions
# Maintain runbooks for common issues
# Keep Git commit messages clear
```

## Emergency Procedures

### Quick Rollback
```bash
# Method 1: Git revert
git revert <bad-commit>
git push

# ArgoCD will auto-sync to previous state

# Method 2: Sync to specific revision
argocd app sync <app-name> --revision <good-commit-sha>

# Method 3: Rollback in ArgoCD
argocd app rollback <app-name> <history-id>
```

### Force Delete Stuck Resources
```bash
# Remove finalizers if resource won't delete
kubectl patch <resource> <name> -p '{"metadata":{"finalizers":[]}}' --type=merge -n <namespace>

# Force delete
kubectl delete <resource> <name> --force --grace-period=0 -n <namespace>
```

### Reset ArgoCD Application
```bash
# Delete and recreate application
argocd app delete <app-name>
kubectl apply -f argocd-apps/<app-name>.yaml
```

## Get Help

If you're still stuck:

1. **Check ArgoCD Documentation**: https://argo-cd.readthedocs.io/
2. **ArgoCD GitHub Issues**: https://github.com/argoproj/argo-cd/issues
3. **Slack Community**: https://argoproj.github.io/community/join-slack
4. **Stack Overflow**: Tag questions with `argocd`

## Next Steps

- [GitOps Concepts](04-gitops-concepts.md)
- [CI/CD Integration](06-cicd-integration.md)
- [Monitoring Setup](07-monitoring-observability.md)
