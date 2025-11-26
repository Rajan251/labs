# GitLab CI/CD Troubleshooting Guide

Comprehensive troubleshooting guide for common GitLab CI/CD issues with exact error messages, diagnostic steps, and solutions.

## Table of Contents

1. [Runner Issues](#runner-issues)
2. [Docker & Container Issues](#docker--container-issues)
3. [Security Scanning Issues](#security-scanning-issues)
4. [Registry & Image Push Issues](#registry--image-push-issues)
5. [Kubernetes Deployment Issues](#kubernetes-deployment-issues)
6. [Performance Issues](#performance-issues)
7. [Permission & RBAC Issues](#permission--rbac-issues)
8. [Cache & Artifact Issues](#cache--artifact-issues)

---

## Runner Issues

### Problem: Runner Not Picking Up Jobs

**Error Message:**
```
This job is stuck because the project doesn't have any runners online assigned to it.
```

**Cause:**
- No runners registered
- Runner tags don't match job tags
- Runner is paused
- Runner offline

**Diagnostic Steps:**
```bash
# Check runner status
sudo gitlab-runner status

# List runners
sudo gitlab-runner list

# Verify runner
sudo gitlab-runner verify

# Check runner logs
sudo journalctl -u gitlab-runner -f
```

**Solution:**
1. Register a runner if none exists
2. Check job tags match runner tags in `.gitlab-ci.yml`
3. Ensure runner is active in GitLab UI (Settings > CI/CD > Runners)
4. Restart runner: `sudo gitlab-runner restart`

---

### Problem: Runner Fails to Start

**Error Message:**
```
ERROR: Failed to load config stat /etc/gitlab-runner/config.toml: no such file or directory
```

**Cause:**
- Missing or corrupted config.toml
- Wrong file permissions

**Solution:**
```bash
# Check if config file exists
ls -la /etc/gitlab-runner/config.toml

# Fix permissions
sudo chmod 600 /etc/gitlab-runner/config.toml
sudo chown gitlab-runner:gitlab-runner /etc/gitlab-runner/config.toml

# Re-register runner if config is missing
sudo gitlab-runner register
```

---

## Docker & Container Issues

### Problem: `docker: command not found`

**Error Message:**
```
/bin/sh: docker: command not found
ERROR: Job failed: exit code 127
```

**Cause:**
- Using shell executor instead of docker executor
- Docker not installed on runner host

**Solution:**

**Option 1:** Use Docker executor
```bash
# Re-register runner with docker executor
sudo gitlab-runner register --executor docker
```

**Option 2:** Install Docker on shell executor
```bash
# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker gitlab-runner
sudo gitlab-runner restart
```

---

### Problem: Docker Build Fails - Permission Denied

**Error Message:**
```
Got permission denied while trying to connect to the Docker daemon socket
```

**Cause:**
- gitlab-runner user not in docker group
- Docker socket permissions

**Solution:**
```bash
# Add gitlab-runner to docker group
sudo usermod -aG docker gitlab-runner

# Restart runner
sudo gitlab-runner restart

# Verify
sudo -u gitlab-runner docker ps
```

---

### Problem: Docker Build Fails - No Space Left on Device

**Error Message:**
```
ERROR: failed to solve: write /var/lib/docker/tmp/...: no space left on device
```

**Cause:**
- Disk full from Docker images/containers

**Diagnostic Steps:**
```bash
# Check disk space
df -h

# Check Docker disk usage
docker system df
```

**Solution:**
```bash
# Clean up Docker
docker system prune -a --volumes

# Remove unused images
docker image prune -a

# Remove stopped containers
docker container prune

# Set up automatic cleanup (add to cron)
0 2 * * * docker system prune -af --filter "until=24h"
```

---

### Problem: Docker-in-Docker Not Working

**Error Message:**
```
Cannot connect to the Docker daemon at unix:///var/run/docker.sock
```

**Cause:**
- Privileged mode not enabled
- Missing DinD service

**Solution:**

In `.gitlab-ci.yml`:
```yaml
build:
  image: docker:24.0
  services:
    - docker:24.0-dind  # Add DinD service
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
  script:
    - docker build -t myimage .
```

In `config.toml`:
```toml
[[runners]]
  [runners.docker]
    privileged = true  # Enable privileged mode
```

---

## Security Scanning Issues

### Problem: SAST Job Times Out

**Error Message:**
```
ERROR: Job failed (system failure): execution took longer than 1h0m0s seconds
```

**Cause:**
- Large codebase
- Slow analyzer
- Too many files

**Solution:**

Increase timeout:
```yaml
sast:
  timeout: 2h  # Increase timeout
```

Exclude paths:
```yaml
variables:
  SAST_EXCLUDED_PATHS: "spec, test, tests, tmp, node_modules, vendor, dist"
```

Disable specific analyzers:
```yaml
variables:
  SAST_EXCLUDED_ANALYZERS: "eslint"  # Disable slow analyzers
```

---

### Problem: Dependency Scanning Fails on Private Registry

**Error Message:**
```
ERROR: Failed to fetch dependencies from private registry
```

**Cause:**
- Missing authentication for private npm/pip/maven registry

**Solution:**

For npm:
```yaml
dependency_scanning:
  before_script:
    - echo "//registry.npmjs.org/:_authToken=${NPM_TOKEN}" > .npmrc
```

For pip:
```yaml
dependency_scanning:
  variables:
    PIP_INDEX_URL: "https://${PYPI_USER}:${PYPI_PASSWORD}@pypi.example.com/simple"
```

---

### Problem: Container Scanning Fails - Image Not Found

**Error Message:**
```
ERROR: Cannot pull image: registry.gitlab.com/group/project:tag
```

**Cause:**
- Image not built yet
- Wrong image tag
- Missing `needs` dependency

**Solution:**
```yaml
container_scanning:
  needs: [docker-build]  # Ensure image is built first
  variables:
    CS_IMAGE: "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"  # Use correct tag
```

---

## Registry & Image Push Issues

### Problem: Cannot Push to GitLab Registry

**Error Message:**
```
denied: access forbidden
ERROR: Job failed: exit code 1
```

**Cause:**
- Insufficient permissions
- CI_JOB_TOKEN expired
- Registry disabled

**Diagnostic Steps:**
```bash
# Test registry login
echo "$CI_REGISTRY_PASSWORD" | docker login -u "$CI_REGISTRY_USER" --password-stdin "$CI_REGISTRY"
```

**Solution:**

1. Check project permissions (Maintainer role required)
2. Enable Container Registry: Settings > General > Visibility > Container Registry
3. Use deploy token instead of CI_JOB_TOKEN:

```yaml
docker-build:
  before_script:
    - echo "$DEPLOY_TOKEN" | docker login -u "$DEPLOY_USER" --password-stdin "$CI_REGISTRY"
```

---

### Problem: Image Push Fails - Layer Already Exists

**Error Message:**
```
layer already exists but with different content
```

**Cause:**
- Tag reuse with different content
- Registry corruption

**Solution:**
```bash
# Use unique tags (commit SHA)
docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA .

# Or force push
docker push --force $CI_REGISTRY_IMAGE:tag
```

---

## Kubernetes Deployment Issues

### Problem: Unauthorized - Cannot Access Kubernetes API

**Error Message:**
```
Error from server (Forbidden): deployments.apps is forbidden: User "system:serviceaccount:gitlab-runner:default" cannot create resource "deployments"
```

**Cause:**
- Missing RBAC permissions
- Invalid kubeconfig
- Expired service account token

**Diagnostic Steps:**
```bash
# Test kubectl access
kubectl auth can-i create deployment --namespace=production

# Check service account
kubectl get serviceaccount gitlab -n gitlab-runner
kubectl describe serviceaccount gitlab -n gitlab-runner
```

**Solution:**

Create RBAC role and binding:
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: gitlab-deploy
  namespace: production
rules:
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "create", "update", "patch", "delete"]
- apiGroups: [""]
  resources: ["services", "pods"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: gitlab-deploy
  namespace: production
subjects:
- kind: ServiceAccount
  name: gitlab
  namespace: gitlab-runner
roleRef:
  kind: Role
  name: gitlab-deploy
  apiGroup: rbac.authorization.k8s.io
```

Apply:
```bash
kubectl apply -f rbac.yaml
```

---

### Problem: Deployment Fails - ImagePullBackOff

**Error Message:**
```
Failed to pull image "registry.gitlab.com/group/project:tag": rpc error: code = Unknown desc = Error response from daemon: pull access denied
```

**Cause:**
- Missing image pull secret
- Wrong image tag
- Image doesn't exist

**Diagnostic Steps:**
```bash
# Check pod events
kubectl describe pod <pod-name> -n <namespace>

# Check if image exists
docker pull registry.gitlab.com/group/project:tag
```

**Solution:**

Create image pull secret:
```bash
kubectl create secret docker-registry gitlab-registry \
  --docker-server=registry.gitlab.com \
  --docker-username=$CI_REGISTRY_USER \
  --docker-password=$CI_REGISTRY_PASSWORD \
  --namespace=production
```

Reference in deployment:
```yaml
spec:
  imagePullSecrets:
  - name: gitlab-registry
```

---

### Problem: Helm Upgrade Fails - Release Not Found

**Error Message:**
```
Error: release: not found
```

**Cause:**
- First deployment (release doesn't exist yet)
- Wrong release name

**Solution:**

Use `--install` flag:
```bash
helm upgrade --install myapp ./helm \
  --namespace production \
  --create-namespace
```

---

## Performance Issues

### Problem: Slow Pipeline Execution

**Cause:**
- Sequential stages
- No caching
- Large artifacts
- Slow tests

**Diagnostic Steps:**
```bash
# Check pipeline duration in GitLab UI
# Analyze which jobs take longest
```

**Solution:**

1. **Use `needs` for DAG**:
```yaml
test:
  needs: [build]  # Don't wait for entire stage
```

2. **Enable caching**:
```yaml
cache:
  key: ${CI_COMMIT_REF_SLUG}
  paths:
    - node_modules/
```

3. **Parallelize jobs**:
```yaml
test:
  parallel: 5
```

4. **Set artifact expiration**:
```yaml
artifacts:
  expire_in: 1 week
```

---

### Problem: Cache Not Working

**Error Message:**
```
WARNING: node_modules/: no matching files
```

**Cause:**
- Wrong cache key
- Different runners (no shared cache)
- Cache policy mismatch

**Solution:**

1. **Use consistent cache key**:
```yaml
cache:
  key: ${CI_COMMIT_REF_SLUG}
  paths:
    - node_modules/
```

2. **Configure shared cache (S3)**:
```toml
[[runners]]
  [runners.cache]
    Type = "s3"
    Shared = true
```

3. **Check cache policy**:
```yaml
build:
  cache:
    policy: pull-push  # Download and upload

test:
  cache:
    policy: pull  # Only download
```

---

## Permission & RBAC Issues

### Problem: Cannot Access CI/CD Variables

**Error Message:**
```
WARNING: DATABASE_PASSWORD: variable is not defined
```

**Cause:**
- Variable not set
- Protected variable on non-protected branch
- Variable masked incorrectly

**Solution:**

1. Check variable exists: Settings > CI/CD > Variables
2. For protected variables, ensure branch is protected
3. Verify variable key matches exactly (case-sensitive)
4. Check variable scope (environment-specific)

---

### Problem: Cannot Deploy to Protected Environment

**Error Message:**
```
This job is creating a deployment to production and is waiting for approval
```

**Cause:**
- Environment is protected
- User doesn't have deploy permission

**Solution:**

1. Settings > CI/CD > Protected Environments
2. Add user/role to "Allowed to deploy"
3. Or approve deployment manually in GitLab UI

---

## Cache & Artifact Issues

### Problem: Artifacts Fill Up Storage

**Error Message:**
```
ERROR: Uploading artifacts to coordinator... too large
```

**Cause:**
- No expiration set
- Large build outputs

**Solution:**

1. **Set expiration**:
```yaml
artifacts:
  expire_in: 1 week
```

2. **Reduce artifact size**:
```yaml
artifacts:
  paths:
    - dist/  # Only necessary files
  exclude:
    - dist/**/*.map  # Exclude source maps
```

3. **Configure project retention**: Settings > CI/CD > Artifacts

---

## Quick Reference Commands

```bash
# Runner diagnostics
sudo gitlab-runner status
sudo gitlab-runner verify
sudo gitlab-runner list
sudo journalctl -u gitlab-runner -f

# Docker cleanup
docker system prune -a --volumes
docker system df

# Kubernetes diagnostics
kubectl get pods -n <namespace>
kubectl describe pod <pod-name> -n <namespace>
kubectl logs <pod-name> -n <namespace>
kubectl auth can-i create deployment

# GitLab API
curl --header "PRIVATE-TOKEN: <token>" "https://gitlab.com/api/v4/projects/:id/pipelines"
```

---

## Getting Help

- **GitLab Forum**: https://forum.gitlab.com/
- **GitLab Issues**: https://gitlab.com/gitlab-org/gitlab/-/issues
- **Stack Overflow**: Tag `gitlab-ci`
- **GitLab Docs**: https://docs.gitlab.com/ee/ci/
