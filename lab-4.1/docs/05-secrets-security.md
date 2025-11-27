# GitHub Actions CI/CD Guide - Part 5: Secrets & Security

## Overview

Proper secrets management is critical for secure CI/CD pipelines. This section covers GitHub Secrets, environment variables, permissions, and authentication best practices.

## GitHub Secrets

### Creating Secrets

**Repository Secrets** (Settings → Secrets and variables → Actions):
- Available to all workflows in the repository
- Use for API keys, tokens, passwords

**Environment Secrets** (Settings → Environments):
- Scoped to specific environments (production, staging)
- Can require manual approval
- Support protection rules

**Organization Secrets**:
- Shared across multiple repositories
- Managed at organization level

### Using Secrets in Workflows

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to production
        env:
          API_KEY: ${{ secrets.API_KEY }}
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: ./deploy.sh
```

### Secret Naming Conventions

```yaml
# Good naming practices
secrets.AWS_ACCESS_KEY_ID
secrets.AWS_SECRET_ACCESS_KEY
secrets.DOCKERHUB_USERNAME
secrets.DOCKERHUB_TOKEN
secrets.KUBE_CONFIG_PROD
secrets.SLACK_WEBHOOK_URL
```

## Encrypted Environment Variables

### Environment-Specific Secrets

```yaml
jobs:
  deploy-prod:
    runs-on: ubuntu-latest
    environment: production  # Uses production environment secrets
    steps:
      - name: Deploy
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}  # From production environment
        run: ./deploy.sh
  
  deploy-staging:
    runs-on: ubuntu-latest
    environment: staging  # Uses staging environment secrets
    steps:
      - name: Deploy
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}  # From staging environment
        run: ./deploy.sh
```

### Masking Sensitive Output

```yaml
- name: Set secret value
  run: |
    echo "::add-mask::${{ secrets.API_KEY }}"
    echo "API_KEY=${{ secrets.API_KEY }}" >> $GITHUB_ENV

# The secret will be masked in logs as ***
```

## Fine-Grained Permissions

### GITHUB_TOKEN Permissions

```yaml
name: Secure Workflow

on: [push]

permissions:
  contents: read        # Read repository contents
  packages: write       # Push to GitHub Packages
  pull-requests: write  # Comment on PRs
  security-events: write # Upload security scan results

jobs:
  build:
    runs-on: ubuntu-latest
    # Job-level permissions override workflow-level
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4
      - name: Build and push
        run: docker build -t myapp .
```

### Minimal Permissions Example

```yaml
# Default: no permissions
permissions: {}

jobs:
  read-only:
    runs-on: ubuntu-latest
    permissions:
      contents: read  # Only read access
    steps:
      - uses: actions/checkout@v4
      - run: npm test
```

### Common Permission Scopes

| Scope | Read | Write | Use Case |
|-------|------|-------|----------|
| `contents` | Clone repo | Push commits | Checkout code, push changes |
| `packages` | Pull images | Push images | Docker registry operations |
| `pull-requests` | Read PRs | Comment on PRs | PR automation |
| `security-events` | Read alerts | Upload SARIF | Security scanning |
| `deployments` | Read | Create | Deployment tracking |
| `issues` | Read | Create/edit | Issue automation |

## OIDC Authentication (AWS/GCP/Azure)

### AWS OIDC Setup

**1. Create IAM Role with OIDC Provider**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
          "token.actions.githubusercontent.com:sub": "repo:myorg/myrepo:ref:refs/heads/main"
        }
      }
    }
  ]
}
```

**2. Use in Workflow**

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write  # Required for OIDC
      contents: read
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsRole
          aws-region: us-east-1
          # No access keys needed!
      
      - name: Deploy to AWS
        run: |
          aws s3 sync dist/ s3://my-bucket
```

### Azure OIDC Setup

```yaml
- name: Azure Login
  uses: azure/login@v1
  with:
    client-id: ${{ secrets.AZURE_CLIENT_ID }}
    tenant-id: ${{ secrets.AZURE_TENANT_ID }}
    subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}

- name: Deploy to Azure
  run: |
    az webapp deploy --name myapp --resource-group mygroup
```

### GCP OIDC Setup

```yaml
- name: Authenticate to Google Cloud
  uses: google-github-actions/auth@v2
  with:
    workload_identity_provider: 'projects/123456789/locations/global/workloadIdentityPools/github/providers/github-provider'
    service_account: 'github-actions@myproject.iam.gserviceaccount.com'

- name: Deploy to GCP
  run: |
    gcloud app deploy
```

## Security Best Practices

### 1. Never Log Secrets

```yaml
# ❌ BAD - Secrets exposed in logs
- name: Deploy
  run: |
    echo "API Key: ${{ secrets.API_KEY }}"
    curl -H "Authorization: ${{ secrets.API_KEY }}" https://api.example.com

# ✅ GOOD - Secrets masked
- name: Deploy
  env:
    API_KEY: ${{ secrets.API_KEY }}
  run: |
    curl -H "Authorization: $API_KEY" https://api.example.com
```

### 2. Use Environment Protection

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: production
      # Requires manual approval
      # Limits which branches can deploy
    steps:
      - name: Deploy
        run: ./deploy.sh
```

### 3. Rotate Secrets Regularly

```yaml
# Use short-lived credentials with OIDC instead of long-lived secrets
- name: Get temporary credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsRole
    role-session-name: GitHubActions-${{ github.run_id }}
    aws-region: us-east-1
```

### 4. Limit Secret Scope

```yaml
# Use environment secrets instead of repository secrets
environment: production  # Only production secrets accessible
```

### 5. Audit Secret Usage

```yaml
- name: Log deployment
  run: |
    echo "Deployed by: ${{ github.actor }}"
    echo "Commit: ${{ github.sha }}"
    echo "Timestamp: $(date)"
```

## Secrets Management Tools

### HashiCorp Vault Integration

```yaml
- name: Import Secrets from Vault
  uses: hashicorp/vault-action@v2
  with:
    url: https://vault.example.com
    token: ${{ secrets.VAULT_TOKEN }}
    secrets: |
      secret/data/production database_url | DATABASE_URL ;
      secret/data/production api_key | API_KEY

- name: Use secrets
  env:
    DATABASE_URL: ${{ env.DATABASE_URL }}
    API_KEY: ${{ env.API_KEY }}
  run: ./deploy.sh
```

### AWS Secrets Manager

```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsRole
    aws-region: us-east-1

- name: Get secrets from AWS Secrets Manager
  run: |
    SECRET=$(aws secretsmanager get-secret-value --secret-id prod/api-key --query SecretString --output text)
    echo "::add-mask::$SECRET"
    echo "API_KEY=$SECRET" >> $GITHUB_ENV

- name: Use secret
  run: ./deploy.sh
```

## Common Security Issues & Solutions

### Problem 1: Secrets Exposed in Logs

**Symptom**: Secrets visible in workflow logs

**Solution**:
```yaml
# Always use environment variables, never echo secrets
- name: Deploy
  env:
    SECRET: ${{ secrets.MY_SECRET }}
  run: |
    # Secret is automatically masked
    ./deploy.sh
```

### Problem 2: Unauthorized Access

**Symptom**: Workflow can access secrets it shouldn't

**Solution**:
```yaml
# Use environment protection
environment:
  name: production
  # Configure in GitHub UI:
  # - Required reviewers
  # - Wait timer
  # - Deployment branches (only main)
```

### Problem 3: Expired Credentials

**Symptom**: Authentication fails with old credentials

**Solution**:
```yaml
# Use OIDC for automatic credential rotation
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsRole
    role-duration-seconds: 3600  # 1 hour
    aws-region: us-east-1
```

### Problem 4: Secret Sprawl

**Symptom**: Too many secrets, hard to manage

**Solution**:
```yaml
# Use a secrets manager
- name: Get all secrets from Vault
  uses: hashicorp/vault-action@v2
  with:
    url: ${{ secrets.VAULT_URL }}
    token: ${{ secrets.VAULT_TOKEN }}
    secrets: |
      secret/data/app/* | ;
```

### Problem 5: Secrets in Pull Requests

**Symptom**: Untrusted PRs can access secrets

**Solution**:
```yaml
# Use pull_request_target carefully
on:
  pull_request_target:  # Has access to secrets
    types: [labeled]

jobs:
  deploy:
    if: contains(github.event.pull_request.labels.*.name, 'safe-to-deploy')
    # Only run if PR is labeled by maintainer
```

## Security Checklist

- [ ] Use environment secrets for production
- [ ] Enable environment protection rules
- [ ] Require manual approval for production deployments
- [ ] Use OIDC instead of long-lived credentials
- [ ] Rotate secrets regularly
- [ ] Use minimal permissions for GITHUB_TOKEN
- [ ] Never log secrets
- [ ] Mask sensitive output
- [ ] Audit secret usage
- [ ] Use secrets manager for complex setups
- [ ] Restrict which branches can deploy
- [ ] Enable branch protection rules
- [ ] Use signed commits
- [ ] Scan for secrets in code (git-secrets, truffleHog)

---

> [!CAUTION]
> Never commit secrets to your repository, even in private repos. Use GitHub Secrets and consider using OIDC for cloud provider authentication to avoid long-lived credentials entirely.
