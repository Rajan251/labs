# GitHub Actions CI/CD Guide - Part 6: Problems & Solutions

## Common CI/CD Pipeline Issues

This section covers the most common problems encountered in GitHub Actions workflows and their solutions.

## Workflow Trigger Issues

### Problem 1: Workflow Not Triggering

**Symptom**: Push to branch doesn't trigger workflow

**Causes & Solutions**:

```yaml
# ❌ WRONG - Syntax error in trigger
on:
  push:
    branch: main  # Should be 'branches'

# ✅ CORRECT
on:
  push:
    branches: [main]
```

**Other causes**:
- Workflow file not in `.github/workflows/` directory
- YAML syntax errors (use YAML validator)
- Branch protection rules blocking workflow
- Workflow disabled in repository settings

**Debug steps**:
```bash
# Validate YAML syntax
yamllint .github/workflows/ci-cd.yml

# Check workflow is enabled
# Go to: Actions → Select workflow → Enable workflow
```

### Problem 2: Workflow Triggers on Wrong Events

**Symptom**: Workflow runs when it shouldn't

**Solution**:
```yaml
# Use path filters to run only when specific files change
on:
  push:
    branches: [main]
    paths:
      - 'src/**'
      - 'package.json'
      - '!docs/**'  # Exclude docs changes

# Use conditional execution
jobs:
  build:
    if: "!contains(github.event.head_commit.message, '[skip ci]')"
    runs-on: ubuntu-latest
```

### Problem 3: Scheduled Workflow Not Running

**Symptom**: Cron schedule doesn't trigger workflow

**Solution**:
```yaml
# ❌ WRONG - Invalid cron syntax
on:
  schedule:
    - cron: '0 0 * * *'  # Might not run in inactive repos

# ✅ CORRECT - Add manual trigger as backup
on:
  schedule:
    - cron: '0 2 * * *'  # 2 AM UTC
  workflow_dispatch:  # Manual trigger option

# Note: Scheduled workflows may be disabled in inactive repos
# GitHub disables them after 60 days of no activity
```

## Permission Issues

### Problem 4: Permission Denied Errors

**Symptom**: `Resource not accessible by integration` error

**Solution**:
```yaml
# Add required permissions
permissions:
  contents: write      # For pushing commits
  packages: write      # For pushing Docker images
  pull-requests: write # For commenting on PRs
  security-events: write # For uploading SARIF

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
```

### Problem 5: Can't Push to Protected Branch

**Symptom**: Push fails on protected branch

**Solution**:
```yaml
# Use a PAT with appropriate permissions
- uses: actions/checkout@v4
  with:
    token: ${{ secrets.PAT_TOKEN }}  # Personal Access Token

# Or use GitHub App token
- uses: actions/create-github-app-token@v1
  id: app-token
  with:
    app-id: ${{ secrets.APP_ID }}
    private-key: ${{ secrets.APP_PRIVATE_KEY }}

- uses: actions/checkout@v4
  with:
    token: ${{ steps.app-token.outputs.token }}
```

## Docker Build Issues

### Problem 6: Docker Build Fails with OOM

**Symptom**: Docker build crashes with out of memory error

**Solution**:
```yaml
# Use BuildKit with better memory management
- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v3

- name: Build with memory limits
  uses: docker/build-push-action@v5
  with:
    context: .
    push: false
    # Use multi-stage builds to reduce memory usage
    cache-from: type=gha
    cache-to: type=gha,mode=max

# Or use larger runner
jobs:
  build:
    runs-on: ubuntu-latest-8-cores  # Larger runner
```

### Problem 7: Docker Rate Limit Exceeded

**Symptom**: `toomanyrequests: You have reached your pull rate limit`

**Solution**:
```yaml
# Always authenticate to Docker Hub
- name: Login to Docker Hub
  uses: docker/login-action@v3
  with:
    username: ${{ secrets.DOCKERHUB_USERNAME }}
    password: ${{ secrets.DOCKERHUB_TOKEN }}

# Or use GitHub Container Registry
- name: Login to GHCR
  uses: docker/login-action@v3
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}

# Use GHCR for base images
FROM ghcr.io/myorg/base-image:latest
```

### Problem 8: Docker Layer Cache Not Working

**Symptom**: Docker builds don't use cache, always rebuild

**Solution**:
```yaml
- name: Build with proper caching
  uses: docker/build-push-action@v5
  with:
    context: .
    push: true
    tags: myapp:latest
    cache-from: type=gha
    cache-to: type=gha,mode=max  # Important: mode=max
    
# Ensure Dockerfile is optimized
# ❌ BAD - Cache invalidated on any file change
COPY . /app

# ✅ GOOD - Copy dependencies first
COPY package*.json /app/
RUN npm ci
COPY . /app
```

## Kubernetes Deployment Issues

### Problem 9: kubectl Authentication Fails

**Symptom**: `error: You must be logged in to the server (Unauthorized)`

**Solution**:
```yaml
# Ensure kubeconfig is properly formatted and base64 encoded
- name: Configure kubectl
  run: |
    mkdir -p $HOME/.kube
    echo "${{ secrets.KUBE_CONFIG }}" | base64 -d > $HOME/.kube/config
    chmod 600 $HOME/.kube/config
    kubectl cluster-info

# Or use service account token
- name: Set kubectl context
  run: |
    kubectl config set-cluster mycluster \
      --server=${{ secrets.K8S_SERVER }} \
      --certificate-authority=<(echo "${{ secrets.K8S_CA }}" | base64 -d)
    kubectl config set-credentials github \
      --token=${{ secrets.K8S_TOKEN }}
    kubectl config set-context default \
      --cluster=mycluster \
      --user=github
    kubectl config use-context default
```

### Problem 10: Deployment Timeout

**Symptom**: `kubectl rollout status` times out

**Solution**:
```yaml
- name: Deploy with proper timeout and rollback
  run: |
    kubectl apply -f k8s/
    kubectl rollout status deployment/myapp \
      --timeout=10m \
      --namespace=production || \
    (kubectl rollout undo deployment/myapp -n production && exit 1)

# Check pod events for issues
- name: Debug deployment
  if: failure()
  run: |
    kubectl get pods -n production
    kubectl describe deployment myapp -n production
    kubectl logs -l app=myapp -n production --tail=100
```

### Problem 11: Image Pull Errors

**Symptom**: `ImagePullBackOff` or `ErrImagePull`

**Solution**:
```yaml
# Create image pull secret
- name: Create Docker registry secret
  run: |
    kubectl create secret docker-registry regcred \
      --docker-server=ghcr.io \
      --docker-username=${{ github.actor }} \
      --docker-password=${{ secrets.GITHUB_TOKEN }} \
      --namespace=production \
      --dry-run=client -o yaml | kubectl apply -f -

# Reference in deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  template:
    spec:
      imagePullSecrets:
        - name: regcred
      containers:
        - name: myapp
          image: ghcr.io/myorg/myapp:latest
```

## Cache Issues

### Problem 12: Cache Not Restoring

**Symptom**: Dependencies reinstall every time

**Solution**:
```yaml
# Ensure cache key includes dependency file hash
- name: Cache dependencies
  uses: actions/cache@v4
  with:
    path: ~/.npm
    key: ${{ runner.os }}-npm-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-npm-

# For multiple package managers
- name: Cache all dependencies
  uses: actions/cache@v4
  with:
    path: |
      ~/.npm
      ~/.cache/pip
      ~/.m2/repository
    key: ${{ runner.os }}-deps-${{ hashFiles('**/package-lock.json', '**/requirements.txt', '**/pom.xml') }}
```

### Problem 13: Cache Size Too Large

**Symptom**: Cache save/restore takes too long

**Solution**:
```yaml
# Cache only necessary directories
- name: Cache node_modules
  uses: actions/cache@v4
  with:
    path: node_modules  # Not ~/.npm
    key: ${{ runner.os }}-modules-${{ hashFiles('**/package-lock.json') }}

# Exclude large unnecessary files
- name: Cache with exclusions
  uses: actions/cache@v4
  with:
    path: |
      ~/.cache/pip
      !~/.cache/pip/http
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
```

## Artifact Issues

### Problem 14: Artifacts Not Found

**Symptom**: `Error: Unable to find any artifacts`

**Solution**:
```yaml
- name: Upload artifacts
  uses: actions/upload-artifact@v4
  with:
    name: build-output
    path: dist/
    if-no-files-found: error  # Fail if no files found

# Ensure path is correct
- name: Debug artifact path
  run: |
    ls -la dist/
    find . -name "*.js" -type f

# Download in another job
- name: Download artifacts
  uses: actions/download-artifact@v4
  with:
    name: build-output
    path: dist/
```

## Environment Variable Issues

### Problem 15: Environment Variables Not Set

**Symptom**: Variables are empty or undefined

**Solution**:
```yaml
# Set at workflow level
env:
  NODE_ENV: production

jobs:
  build:
    # Set at job level
    env:
      API_URL: https://api.example.com
    
    steps:
      # Set at step level
      - name: Build
        env:
          BUILD_NUMBER: ${{ github.run_number }}
        run: npm run build

      # Set for subsequent steps
      - name: Set env var
        run: echo "VERSION=1.0.0" >> $GITHUB_ENV
      
      - name: Use env var
        run: echo "Version is $VERSION"
```

## Timeout Issues

### Problem 16: Job Timeout

**Symptom**: Job cancelled after 6 hours (default timeout)

**Solution**:
```yaml
jobs:
  long-running:
    runs-on: ubuntu-latest
    timeout-minutes: 120  # 2 hours
    steps:
      - name: Long task
        timeout-minutes: 30  # Step-level timeout
        run: ./long-script.sh
```

## Concurrency Issues

### Problem 17: Multiple Workflows Running Simultaneously

**Symptom**: Deployments conflict with each other

**Solution**:
```yaml
# Limit concurrency
concurrency:
  group: production-deployment
  cancel-in-progress: false  # Don't cancel running deployments

# Or per-branch concurrency
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true  # Cancel old runs
```

## Matrix Build Issues

### Problem 18: Matrix Build Failures

**Symptom**: One version fails, need to continue others

**Solution**:
```yaml
strategy:
  matrix:
    node-version: [16, 18, 20]
    os: [ubuntu-latest, windows-latest]
  fail-fast: false  # Continue other builds
  max-parallel: 4   # Limit concurrent jobs

jobs:
  test:
    runs-on: ${{ matrix.os }}
    continue-on-error: ${{ matrix.node-version == '16' }}  # Allow Node 16 to fail
```

## Debugging Tips

### Enable Debug Logging

```yaml
# Set secrets in repository:
# ACTIONS_STEP_DEBUG = true
# ACTIONS_RUNNER_DEBUG = true

# Or add to workflow
- name: Enable debug
  run: |
    echo "ACTIONS_STEP_DEBUG=true" >> $GITHUB_ENV
    echo "ACTIONS_RUNNER_DEBUG=true" >> $GITHUB_ENV
```

### SSH into Runner

```yaml
- name: Setup tmate session
  if: failure()
  uses: mxschmitt/action-tmate@v3
  timeout-minutes: 30
```

### Inspect Runner Environment

```yaml
- name: Debug environment
  run: |
    echo "GitHub Context:"
    echo "${{ toJSON(github) }}"
    echo "Environment Variables:"
    env | sort
    echo "Disk Space:"
    df -h
    echo "Memory:"
    free -h
```

---

> [!TIP]
> When debugging workflow issues, start by checking the Actions tab for detailed logs. Enable debug logging for more verbose output, and use `if: failure()` steps to capture diagnostic information.
