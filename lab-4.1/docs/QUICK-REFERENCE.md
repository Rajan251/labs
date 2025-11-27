# GitHub Actions Quick Reference

## Common Workflow Patterns

### Basic Workflow Structure

```yaml
name: Workflow Name
on: [push, pull_request]
jobs:
  job-name:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo "Hello World"
```

### Triggers

```yaml
# Push to specific branches
on:
  push:
    branches: [main, develop]

# Pull requests
on:
  pull_request:
    types: [opened, synchronize]

# Tags
on:
  push:
    tags: ['v*']

# Schedule (cron)
on:
  schedule:
    - cron: '0 2 * * *'

# Manual trigger
on:
  workflow_dispatch:
    inputs:
      environment:
        type: choice
        options: [dev, staging, prod]

# Path filters
on:
  push:
    paths:
      - 'src/**'
      - '!docs/**'
```

### Environment Variables

```yaml
# Workflow level
env:
  NODE_ENV: production

jobs:
  build:
    # Job level
    env:
      API_URL: https://api.example.com
    steps:
      # Step level
      - name: Build
        env:
          BUILD_ID: ${{ github.run_number }}
        run: npm run build
      
      # Set for subsequent steps
      - run: echo "VERSION=1.0.0" >> $GITHUB_ENV
      - run: echo "Version is $VERSION"
```

### Secrets

```yaml
steps:
  - name: Use secret
    env:
      API_KEY: ${{ secrets.API_KEY }}
    run: ./deploy.sh
```

### Conditionals

```yaml
# Job level
jobs:
  deploy:
    if: github.ref == 'refs/heads/main'
    
# Step level
steps:
  - name: Deploy
    if: success()
  - name: Cleanup
    if: always()
  - name: Rollback
    if: failure()
```

### Matrix Builds

```yaml
strategy:
  matrix:
    node-version: [16, 18, 20]
    os: [ubuntu-latest, windows-latest]
  fail-fast: false

runs-on: ${{ matrix.os }}
steps:
  - uses: actions/setup-node@v4
    with:
      node-version: ${{ matrix.node-version }}
```

### Artifacts

```yaml
# Upload
- uses: actions/upload-artifact@v4
  with:
    name: build-output
    path: dist/

# Download
- uses: actions/download-artifact@v4
  with:
    name: build-output
    path: dist/
```

### Caching

```yaml
# NPM
- uses: actions/cache@v4
  with:
    path: ~/.npm
    key: ${{ runner.os }}-npm-${{ hashFiles('**/package-lock.json') }}

# Pip
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}

# Docker
- uses: docker/build-push-action@v5
  with:
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

## Essential Actions

### Checkout

```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 0  # Full history
    submodules: true  # Include submodules
```

### Setup Languages

```yaml
# Node.js
- uses: actions/setup-node@v4
  with:
    node-version: '20.x'
    cache: 'npm'

# Python
- uses: actions/setup-python@v5
  with:
    python-version: '3.12'
    cache: 'pip'

# Java
- uses: actions/setup-java@v4
  with:
    java-version: '17'
    distribution: 'temurin'
    cache: 'maven'
```

### Docker

```yaml
# Setup Buildx
- uses: docker/setup-buildx-action@v3

# Login
- uses: docker/login-action@v3
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}

# Build & Push
- uses: docker/build-push-action@v5
  with:
    context: .
    push: true
    tags: myapp:latest
```

### AWS

```yaml
# Configure credentials (OIDC)
- uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsRole
    aws-region: us-east-1

# ECR Login
- uses: aws-actions/amazon-ecr-login@v2
```

### Kubernetes

```yaml
- uses: azure/k8s-set-context@v3
  with:
    method: kubeconfig
    kubeconfig: ${{ secrets.KUBE_CONFIG }}

- run: kubectl apply -f k8s/
```

## Permissions

```yaml
permissions:
  contents: read
  packages: write
  pull-requests: write
  security-events: write
  id-token: write  # For OIDC
```

## Contexts

```yaml
# GitHub context
${{ github.sha }}
${{ github.ref }}
${{ github.actor }}
${{ github.repository }}
${{ github.event_name }}
${{ github.run_number }}

# Job context
${{ job.status }}

# Steps context
${{ steps.step-id.outputs.value }}

# Runner context
${{ runner.os }}
${{ runner.temp }}

# Env context
${{ env.MY_VAR }}

# Secrets context
${{ secrets.MY_SECRET }}
```

## Debugging

```yaml
# Enable debug logging (set in secrets)
ACTIONS_STEP_DEBUG: true
ACTIONS_RUNNER_DEBUG: true

# Print context
- run: echo '${{ toJSON(github) }}'

# SSH into runner
- uses: mxschmitt/action-tmate@v3
  if: failure()
```

## Common Commands

```bash
# Validate workflow syntax
yamllint .github/workflows/ci-cd.yml

# Test locally with act
act -j build

# View workflow runs
gh run list

# View specific run
gh run view <run-id>

# Download artifacts
gh run download <run-id>
```

## Best Practices

✅ **DO**
- Use specific action versions (`@v4` not `@main`)
- Cache dependencies
- Use OIDC for cloud authentication
- Set minimal permissions
- Use environment protection for production
- Add health checks and rollback logic
- Use secrets for sensitive data
- Enable branch protection

❌ **DON'T**
- Commit secrets to repository
- Use `@main` for actions (unstable)
- Log secrets
- Skip tests in CI
- Deploy without health checks
- Use long-lived credentials
- Ignore security scanning

## Troubleshooting Checklist

- [ ] Workflow file in `.github/workflows/`?
- [ ] Valid YAML syntax?
- [ ] Correct trigger configuration?
- [ ] Required secrets configured?
- [ ] Permissions set correctly?
- [ ] Branch protection not blocking?
- [ ] Workflow enabled in settings?
- [ ] Check Actions tab for errors

## Resources

- [Actions Marketplace](https://github.com/marketplace?type=actions)
- [Workflow Syntax](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [Events that trigger workflows](https://docs.github.com/en/actions/reference/events-that-trigger-workflows)
- [Context and expression syntax](https://docs.github.com/en/actions/reference/context-and-expression-syntax-for-github-actions)
