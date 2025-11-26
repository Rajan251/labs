# Terraform AWS Infrastructure Guide - Part 4

## 13. CI/CD for Terraform

### GitHub Actions Example

**File: `.github/workflows/terraform.yml`**

```yaml
name: Terraform CI/CD

on:
  pull_request:
    branches: [main]
    paths:
      - 'envs/**'
      - 'modules/**'
  push:
    branches: [main]
    paths:
      - 'envs/**'
      - 'modules/**'

env:
  AWS_REGION: us-east-1
  TF_VERSION: 1.6.5

jobs:
  terraform-plan:
    name: Terraform Plan
    runs-on: ubuntu-latest
    strategy:
      matrix:
        environment: [dev, staging, prod]
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - name: Terraform Format Check
        run: terraform fmt -check -recursive
        continue-on-error: true

      - name: Terraform Init
        working-directory: envs/${{ matrix.environment }}
        run: terraform init

      - name: Terraform Validate
        working-directory: envs/${{ matrix.environment }}
        run: terraform validate

      - name: Terraform Plan
        working-directory: envs/${{ matrix.environment }}
        run: |
          terraform plan -out=tfplan -no-color | tee plan.txt
        
      - name: Upload Plan
        uses: actions/upload-artifact@v3
        with:
          name: ${{ matrix.environment }}-tfplan
          path: envs/${{ matrix.environment }}/tfplan

      - name: Comment PR with Plan
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const plan = fs.readFileSync('envs/${{ matrix.environment }}/plan.txt', 'utf8');
            const output = `### Terraform Plan - ${{ matrix.environment }}
            \`\`\`
            ${plan}
            \`\`\``;
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: output
            });

  terraform-apply:
    name: Terraform Apply
    runs-on: ubuntu-latest
    needs: terraform-plan
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    environment: production  # Requires manual approval
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - name: Terraform Init
        working-directory: envs/prod
        run: terraform init

      - name: Download Plan
        uses: actions/download-artifact@v3
        with:
          name: prod-tfplan
          path: envs/prod

      - name: Terraform Apply
        working-directory: envs/prod
        run: terraform apply -auto-approve tfplan
```

### GitLab CI Example

**File: `.gitlab-ci.yml`**

```yaml
image:
  name: hashicorp/terraform:1.6
  entrypoint: [""]

variables:
  AWS_DEFAULT_REGION: us-east-1
  TF_ROOT: ${CI_PROJECT_DIR}/envs/${CI_ENVIRONMENT_NAME}

cache:
  paths:
    - ${TF_ROOT}/.terraform

before_script:
  - cd ${TF_ROOT}
  - terraform --version
  - terraform init

stages:
  - validate
  - plan
  - apply

validate:
  stage: validate
  script:
    - terraform fmt -check
    - terraform validate
  only:
    - merge_requests
    - main

plan:dev:
  stage: plan
  environment:
    name: dev
  script:
    - terraform plan -out=tfplan
  artifacts:
    paths:
      - ${TF_ROOT}/tfplan
    expire_in: 1 week
  only:
    - merge_requests

apply:dev:
  stage: apply
  environment:
    name: dev
  script:
    - terraform apply -auto-approve tfplan
  dependencies:
    - plan:dev
  only:
    - main
  when: manual

plan:prod:
  stage: plan
  environment:
    name: prod
  script:
    - terraform plan -out=tfplan
  artifacts:
    paths:
      - ${TF_ROOT}/tfplan
    expire_in: 1 week
  only:
    - main

apply:prod:
  stage: apply
  environment:
    name: prod
  script:
    - terraform apply -auto-approve tfplan
  dependencies:
    - plan:prod
  only:
    - main
  when: manual
```

### Security Best Practices for CI/CD

- **Use OIDC** instead of long-lived credentials when possible
- **Store secrets** in GitHub Secrets / GitLab CI Variables
- **Require approvals** for production applies
- **Use separate** AWS accounts/roles per environment
- **Enable audit logging** for all Terraform operations

---

## 14. Testing & Validation

### Essential Terraform Commands

```bash
# Format code
terraform fmt -recursive

# Validate configuration
terraform validate

# Check for security issues (requires checkov)
checkov -d .

# Lint Terraform files (requires tflint)
tflint

# Generate documentation (requires terraform-docs)
terraform-docs markdown table . > README.md

# Plan with detailed output
terraform plan -out=tfplan

# Show plan in JSON
terraform show -json tfplan | jq

# Apply with plan file
terraform apply tfplan

# Targeted apply (specific resource)
terraform apply -target=module.vpc

# Destroy specific resource
terraform destroy -target=aws_instance.bastion

# Show current state
terraform show

# List resources in state
terraform state list

# Inspect specific resource
terraform state show aws_instance.bastion

# View outputs
terraform output

# View specific output
terraform output alb_dns_name

# Refresh state
terraform refresh

# Import existing resource
terraform import aws_instance.example i-1234567890abcdef0
```

### Pre-commit Hooks

**File: `.pre-commit-config.yaml`**

```yaml
repos:
  - repo: https://github.com/antonbabenko/pre-commit-terraform
    rev: v1.83.5
    hooks:
      - id: terraform_fmt
      - id: terraform_validate
      - id: terraform_docs
      - id: terraform_tflint
      - id: terraform_checkov
```

Install:

```bash
pip install pre-commit
pre-commit install
```

### Terratest Example (Go)

```go
package test

import (
    "testing"
    "github.com/gruntwork-io/terratest/modules/terraform"
    "github.com/stretchr/testify/assert"
)

func TestVPCModule(t *testing.T) {
    terraformOptions := &terraform.Options{
        TerraformDir: "../modules/vpc",
        Vars: map[string]interface{}{
            "vpc_cidr":      "10.0.0.0/16",
            "environment":   "test",
        },
    }

    defer terraform.Destroy(t, terraformOptions)
    terraform.InitAndApply(t, terraformOptions)

    vpcID := terraform.Output(t, terraformOptions, "vpc_id")
    assert.NotEmpty(t, vpcID)
}
```

---

## 15. Change Management & Rollback

### Safe Update Process

```bash
# 1. Create feature branch
git checkout -b feature/add-monitoring

# 2. Make changes to Terraform code
# ... edit files ...

# 3. Format and validate
terraform fmt -recursive
terraform validate

# 4. Plan and review
cd envs/dev
terraform plan -out=tfplan

# 5. Review plan carefully
terraform show tfplan

# 6. Apply to dev first
terraform apply tfplan

# 7. Test changes in dev
# ... manual testing ...

# 8. If successful, plan for prod
cd ../prod
terraform plan -out=tfplan

# 9. Review prod plan
terraform show tfplan

# 10. Apply to prod (with approval)
terraform apply tfplan
```

### Handling Drift

```bash
# Detect drift
terraform plan -refresh-only

# Show what changed outside Terraform
terraform plan -refresh-only -out=drift.tfplan
terraform show drift.tfplan

# Option 1: Import manual changes into state
terraform apply -refresh-only

# Option 2: Revert manual changes
terraform apply
```

### Rollback Strategies

**Method 1: Revert Git Commit**

```bash
# Revert last commit
git revert HEAD

# Plan with reverted code
terraform plan -out=rollback.tfplan

# Apply rollback
terraform apply rollback.tfplan
```

**Method 2: Use Previous State**

```bash
# List state versions (S3 versioned bucket)
aws s3api list-object-versions \
  --bucket my-terraform-state \
  --prefix envs/prod/terraform.tfstate

# Download previous version
aws s3api get-object \
  --bucket my-terraform-state \
  --key envs/prod/terraform.tfstate \
  --version-id <VERSION_ID> \
  terraform.tfstate.backup

# Replace current state (DANGEROUS - backup first!)
cp terraform.tfstate terraform.tfstate.current
cp terraform.tfstate.backup terraform.tfstate

# Plan to see what will change
terraform plan
```

**Method 3: Targeted Destroy and Recreate**

```bash
# Destroy problematic resource
terraform destroy -target=module.alb

# Recreate with previous configuration
git checkout HEAD~1 -- modules/alb/
terraform apply -target=module.alb
```

---

## 16. Cost & Security Considerations

### Cost Estimation

| Resource | Typical Cost (us-east-1) | Notes |
|----------|-------------------------|-------|
| t3.small EC2 (2 instances) | ~$30/month | On-demand pricing |
| NAT Gateway (2 AZs) | ~$64/month | $0.045/hour + data transfer |
| ALB | ~$22/month | $0.0225/hour + LCU charges |
| S3 (100GB) | ~$2.30/month | Standard storage |
| EBS gp3 (40GB) | ~$3.20/month | 2 x 20GB volumes |
| **Total** | **~$121/month** | Approximate |

**Cost Optimization Tips:**

```hcl
# Use single NAT for dev (not production!)
single_nat_gateway = var.environment == "dev" ? true : false

# Use Spot instances for non-critical workloads
resource "aws_launch_template" "app" {
  instance_market_options {
    market_type = "spot"
    spot_options {
      max_price = "0.05"
    }
  }
}

# Use S3 Intelligent-Tiering
resource "aws_s3_bucket_intelligent_tiering_configuration" "example" {
  bucket = aws_s3_bucket.app_storage.id
  name   = "EntireBucket"

  tiering {
    access_tier = "DEEP_ARCHIVE_ACCESS"
    days        = 180
  }
}

# Schedule EC2 instances (dev environments)
# Use AWS Instance Scheduler or Lambda
```

### Tagging Policy

```hcl
locals {
  required_tags = {
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
    Owner       = var.owner
    CostCenter  = var.cost_center
    Compliance  = var.compliance_level
  }
}

# Apply to all resources via provider default_tags
provider "aws" {
  default_tags {
    tags = local.required_tags
  }
}
```

### Security Checklist

- [ ] Enable encryption at rest (EBS, S3, RDS)
- [ ] Enable encryption in transit (HTTPS, TLS)
- [ ] Use IMDSv2 for EC2 metadata
- [ ] Block S3 public access
- [ ] Restrict security groups (no 0.0.0.0/0 SSH)
- [ ] Enable VPC Flow Logs
- [ ] Enable CloudTrail logging
- [ ] Use AWS Secrets Manager for secrets
- [ ] Enable MFA for privileged accounts
- [ ] Regular security scanning (checkov, tfsec)
- [ ] Implement least privilege IAM
- [ ] Enable GuardDuty
- [ ] Use AWS Config for compliance
- [ ] Regular patching and updates

---

*Continued in next file...*
