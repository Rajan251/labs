# GitHub Actions CI/CD Project Requirements

## Overview

This document outlines the requirements and setup needed to implement the GitHub Actions CI/CD pipelines described in this guide.

## Prerequisites

### 1. GitHub Account & Repository

- GitHub account with repository access
- Repository with appropriate permissions
- Branch protection rules configured (recommended)

### 2. Development Environment

**Required Tools:**
- Git (2.x or higher)
- Text editor or IDE (VS Code, IntelliJ, etc.)
- YAML validator/linter

**Optional Tools:**
- [act](https://github.com/nektos/act) - Run workflows locally
- [GitHub CLI](https://cli.github.com/) - Manage workflows from terminal
- Docker Desktop - For local testing

### 3. Language-Specific Requirements

**Node.js Projects:**
- Node.js 16.x or higher
- npm or yarn package manager
- `package.json` with scripts defined

**Python Projects:**
- Python 3.9 or higher
- pip or Poetry for dependency management
- `requirements.txt` or `pyproject.toml`

**Java Projects:**
- JDK 11 or higher
- Maven or Gradle build tool
- `pom.xml` or `build.gradle`

## Repository Setup

### 1. Directory Structure

Create the following structure in your repository:

```
your-repo/
├── .github/
│   └── workflows/
│       └── ci-cd.yml
├── src/
│   └── (your application code)
├── tests/
│   └── (your test files)
├── Dockerfile
├── k8s-manifests/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── ingress.yaml
└── README.md
```

### 2. Required Files

**Minimum Required:**
- `.github/workflows/ci-cd.yml` - Main workflow file
- Application source code
- Dependency manifest (`package.json`, `requirements.txt`, etc.)

**Recommended:**
- `Dockerfile` - For containerized deployments
- `k8s-manifests/` - For Kubernetes deployments
- `.gitignore` - Exclude build artifacts
- `README.md` - Project documentation

## GitHub Configuration

### 1. Repository Secrets

Configure the following secrets based on your deployment targets:

**Docker Hub:**
```
DOCKERHUB_USERNAME
DOCKERHUB_TOKEN
```

**AWS:**
```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
# Or for OIDC (recommended):
AWS_ROLE_ARN
```

**Kubernetes:**
```
KUBE_CONFIG  # Base64 encoded kubeconfig
# Or:
K8S_SERVER
K8S_TOKEN
K8S_CA
```

**Notifications:**
```
SLACK_WEBHOOK_URL
```

**Security Scanning:**
```
SNYK_TOKEN
CODECOV_TOKEN
```

### 2. Environment Configuration

Create environments in GitHub:

**Development:**
- No protection rules
- Auto-deploy on `develop` branch

**Staging:**
- Optional: Wait timer (5 minutes)
- Auto-deploy on `main` branch

**Production:**
- Required reviewers (1-2 people)
- Deployment branches: `main` only
- Manual approval required

**To create environments:**
1. Go to **Settings** → **Environments**
2. Click **New environment**
3. Configure protection rules

### 3. Branch Protection Rules

Configure for `main` branch:

- ✅ Require pull request reviews (1-2 approvals)
- ✅ Require status checks to pass
  - Select: `build`, `test`, `lint`
- ✅ Require branches to be up to date
- ✅ Require signed commits (recommended)
- ✅ Include administrators

## Deployment Target Setup

### Kubernetes Cluster

**Requirements:**
- Kubernetes cluster (1.20+)
- `kubectl` access configured
- Namespace created (`production`, `staging`, `development`)
- Service account with deployment permissions

**Setup:**
```bash
# Create namespace
kubectl create namespace production

# Create service account
kubectl create serviceaccount github-actions -n production

# Create role binding
kubectl create rolebinding github-actions-deployer \
  --clusterrole=edit \
  --serviceaccount=production:github-actions \
  -n production

# Get token
kubectl create token github-actions -n production
```

### AWS Setup

**For OIDC (Recommended):**

1. Create OIDC provider in IAM
2. Create IAM role with trust policy
3. Attach required policies (ECR, ECS, S3, etc.)

**For Access Keys:**

1. Create IAM user
2. Attach policies
3. Generate access key
4. Store in GitHub Secrets

### Docker Registry

**GitHub Container Registry (GHCR):**
- No additional setup needed
- Uses `GITHUB_TOKEN` automatically

**Docker Hub:**
- Create account
- Generate access token
- Store in secrets

## Workflow Customization

### 1. Trigger Configuration

Modify triggers based on your workflow:

```yaml
on:
  push:
    branches: [main, develop]
    paths:
      - 'src/**'
      - 'package.json'
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 2 * * *'
```

### 2. Environment Variables

Set project-specific variables:

```yaml
env:
  NODE_VERSION: '20.x'
  PYTHON_VERSION: '3.12'
  DOCKER_REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}
```

### 3. Job Dependencies

Adjust job dependencies based on your pipeline:

```yaml
jobs:
  build:
    # ...
  
  test:
    needs: [build]
    # ...
  
  deploy:
    needs: [build, test]
    # ...
```

## Testing the Setup

### 1. Local Validation

```bash
# Validate YAML syntax
yamllint .github/workflows/ci-cd.yml

# Test locally with act
act -j build
```

### 2. Test Workflow

Create a simple test workflow first:

```yaml
name: Test Setup
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo "Setup successful!"
```

### 3. Gradual Rollout

1. Start with build and test jobs
2. Add security scanning
3. Add Docker build
4. Add deployment to dev
5. Add staging and production

## Monitoring & Maintenance

### 1. Workflow Monitoring

- Check **Actions** tab regularly
- Set up notifications for failures
- Review workflow run times
- Monitor artifact storage usage

### 2. Dependency Updates

Keep actions up to date:

```yaml
# Update regularly
- uses: actions/checkout@v4  # Check for v5
- uses: actions/setup-node@v4  # Check for updates
```

Use Dependabot:

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

### 3. Security

- Rotate secrets regularly
- Review permissions quarterly
- Audit workflow runs
- Enable security scanning
- Use OIDC instead of long-lived credentials

## Cost Considerations

### GitHub Actions Minutes

**Free Tier:**
- Public repos: Unlimited
- Private repos: 2,000 minutes/month

**Paid Plans:**
- Team: 3,000 minutes/month
- Enterprise: 50,000 minutes/month

**Optimization Tips:**
- Use caching to reduce build times
- Use `fail-fast: false` selectively
- Limit concurrent jobs
- Use path filters to skip unnecessary runs

### Storage

**Artifacts & Logs:**
- Free: 500 MB
- Retention: 90 days default

**Optimization:**
- Set shorter retention periods
- Clean up old artifacts
- Compress artifacts before upload

## Troubleshooting

### Common Setup Issues

1. **Workflow not triggering**
   - Check file location (`.github/workflows/`)
   - Validate YAML syntax
   - Check branch name in trigger

2. **Permission errors**
   - Add required permissions to workflow
   - Check repository settings
   - Verify secret names

3. **Secrets not accessible**
   - Verify secret names match exactly
   - Check environment configuration
   - Ensure secrets are set at correct level

## Next Steps

1. ✅ Complete prerequisites
2. ✅ Set up repository structure
3. ✅ Configure secrets and environments
4. ✅ Create initial workflow
5. ✅ Test with simple job
6. ✅ Gradually add complexity
7. ✅ Monitor and optimize

---

> [!TIP]
> Start simple and iterate. Don't try to implement everything at once. Test each component independently before combining into a complete pipeline.
