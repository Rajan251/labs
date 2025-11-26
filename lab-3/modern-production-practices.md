# Modern Production Terraform Practices (2024-2025)

## Overview

This document enhances the base Terraform guide with **modern production approaches** used by leading DevOps teams today. These patterns reflect current industry standards for security, automation, and operational excellence.

---

## 1. Modern Authentication: OIDC Instead of Static Keys

### Why OIDC?

**Traditional approach** (static keys) has security risks:
- Keys can be leaked in logs or code
- Long-lived credentials are high-risk
- Key rotation is manual and error-prone

**Modern approach** (OIDC) provides:
- ✅ Short-lived tokens (no long-term credentials)
- ✅ Automatic rotation
- ✅ Audit trail of who accessed what
- ✅ No secrets to manage in CI/CD

### GitHub Actions with OIDC (2024 Standard)

```yaml
name: Terraform Deploy (OIDC)

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  id-token: write   # Required for OIDC
  contents: read
  pull-requests: write

env:
  AWS_REGION: us-east-1
  TF_VERSION: 1.7.0

jobs:
  terraform:
    name: Terraform Plan & Apply
    runs-on: ubuntu-latest
    environment: production
    
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Configure AWS Credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsRole
          aws-region: ${{ env.AWS_REGION }}
          # No access keys needed!

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - name: Terraform Init
        run: terraform init
        working-directory: envs/prod

      - name: Terraform Plan
        id: plan
        run: terraform plan -no-color -out=tfplan
        working-directory: envs/prod
        continue-on-error: true

      - name: Post Plan to PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const plan = fs.readFileSync('envs/prod/tfplan.txt', 'utf8');
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `### Terraform Plan\n\`\`\`\n${plan}\n\`\`\``
            });

      - name: Terraform Apply
        if: github.ref == 'refs/heads/main' && github.event_name == 'push'
        run: terraform apply -auto-approve tfplan
        working-directory: envs/prod
```

### AWS IAM Setup for OIDC

```hcl
# Create OIDC provider for GitHub Actions
resource "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list = [
    "sts.amazonaws.com",
  ]

  thumbprint_list = [
    "6938fd4d98bab03faadb97b34396831e3780aea1",  # GitHub's thumbprint
    "1c58a3a8518e8759bf075b76b750d4f2df264fcd",  # Backup thumbprint
  ]

  tags = {
    Name = "GitHubActionsOIDC"
  }
}

# IAM role for GitHub Actions
resource "aws_iam_role" "github_actions" {
  name = "GitHubActionsRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.github.arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            "token.actions.githubusercontent.com:sub" = "repo:yourorg/yourrepo:*"
          }
        }
      }
    ]
  })
}

# Attach policies to the role
resource "aws_iam_role_policy_attachment" "github_actions_terraform" {
  role       = aws_iam_role.github_actions.name
  policy_arn = aws_iam_policy.terraform_permissions.arn
}
```

**Explanation**: 
- OIDC eliminates the need for storing AWS access keys in GitHub Secrets
- GitHub generates short-lived tokens that AWS trusts
- The IAM role is scoped to specific repositories
- Tokens expire automatically after the job completes

---

## 2. GitOps Workflow with Atlantis

### Why Atlantis?

Modern teams use **pull request-based workflows** for infrastructure changes:
- ✅ Code review before apply
- ✅ Automated plan on every PR
- ✅ Apply only after approval
- ✅ Audit trail in Git history
- ✅ Prevents manual terraform runs

### Atlantis Setup

```yaml
# atlantis.yaml
version: 3
automerge: false
delete_source_branch_on_merge: true
parallel_plan: true
parallel_apply: false

projects:
- name: dev
  dir: envs/dev
  workspace: default
  terraform_version: v1.7.0
  autoplan:
    when_modified: ["*.tf", "*.tfvars"]
    enabled: true
  apply_requirements: [approved, mergeable]
  workflow: default

- name: staging
  dir: envs/staging
  workspace: default
  terraform_version: v1.7.0
  autoplan:
    when_modified: ["*.tf", "*.tfvars"]
    enabled: true
  apply_requirements: [approved, mergeable]
  workflow: default

- name: prod
  dir: envs/prod
  workspace: default
  terraform_version: v1.7.0
  autoplan:
    when_modified: ["*.tf", "*.tfvars"]
    enabled: true
  apply_requirements: [approved, mergeable]
  workflow: prod

workflows:
  default:
    plan:
      steps:
      - init
      - plan
    apply:
      steps:
      - apply
  
  prod:
    plan:
      steps:
      - init
      - run: terraform fmt -check
      - run: tflint
      - run: checkov -d . --quiet --compact
      - plan
    apply:
      steps:
      - run: echo "Applying to production..."
      - apply
      - run: echo "Production deployment complete!"
```

### Atlantis Deployment (ECS Fargate)

```hcl
# Modern approach: Run Atlantis on ECS Fargate (serverless)
resource "aws_ecs_cluster" "atlantis" {
  name = "atlantis-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_ecs_task_definition" "atlantis" {
  family                   = "atlantis"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.atlantis_task.arn

  container_definitions = jsonencode([
    {
      name  = "atlantis"
      image = "ghcr.io/runatlantis/atlantis:v0.27.0"
      
      environment = [
        {
          name  = "ATLANTIS_REPO_ALLOWLIST"
          value = "github.com/yourorg/*"
        },
        {
          name  = "ATLANTIS_GH_USER"
          value = "atlantis-bot"
        },
        {
          name  = "ATLANTIS_ATLANTIS_URL"
          value = "https://atlantis.yourdomain.com"
        }
      ]
      
      secrets = [
        {
          name      = "ATLANTIS_GH_TOKEN"
          valueFrom = aws_secretsmanager_secret.atlantis_github_token.arn
        },
        {
          name      = "ATLANTIS_GH_WEBHOOK_SECRET"
          valueFrom = aws_secretsmanager_secret.atlantis_webhook_secret.arn
        }
      ]
      
      portMappings = [
        {
          containerPort = 4141
          protocol      = "tcp"
        }
      ]
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.atlantis.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "atlantis"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "atlantis" {
  name            = "atlantis"
  cluster         = aws_ecs_cluster.atlantis.id
  task_definition = aws_ecs_task_definition.atlantis.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.atlantis.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.atlantis.arn
    container_name   = "atlantis"
    container_port   = 4141
  }
}
```

**Explanation**:
- Atlantis runs as a containerized service (ECS Fargate)
- Automatically comments on PRs with `terraform plan` output
- Team members review and approve changes
- Type `atlantis apply` in PR comment to deploy
- All changes are tracked in Git history

---

## 3. Policy as Code (OPA & Sentinel)

### Why Policy as Code?

Prevent misconfigurations **before** they reach production:
- ✅ Enforce security standards (no public S3, require encryption)
- ✅ Cost controls (block expensive instance types)
- ✅ Compliance (require specific tags, regions)
- ✅ Automated enforcement (no manual reviews needed)

### Open Policy Agent (OPA) Example

```rego
# policy/terraform.rego
package terraform

import input as tfplan

# Deny if S3 bucket is public
deny[msg] {
  resource := tfplan.resource_changes[_]
  resource.type == "aws_s3_bucket"
  resource.change.after.acl == "public-read"
  
  msg := sprintf("S3 bucket '%s' must not be public", [resource.address])
}

# Deny if EC2 instance is too large
deny[msg] {
  resource := tfplan.resource_changes[_]
  resource.type == "aws_instance"
  
  expensive_types := ["m5.8xlarge", "m5.12xlarge", "m5.16xlarge"]
  resource.change.after.instance_type == expensive_types[_]
  
  msg := sprintf("Instance type '%s' is too expensive for %s", 
    [resource.change.after.instance_type, resource.address])
}

# Require encryption for all EBS volumes
deny[msg] {
  resource := tfplan.resource_changes[_]
  resource.type == "aws_ebs_volume"
  not resource.change.after.encrypted
  
  msg := sprintf("EBS volume '%s' must be encrypted", [resource.address])
}

# Require specific tags
required_tags := ["Environment", "Owner", "CostCenter"]

deny[msg] {
  resource := tfplan.resource_changes[_]
  resource.type == "aws_instance"
  
  existing_tags := object.keys(resource.change.after.tags)
  missing_tags := [tag | tag := required_tags[_]; not tag in existing_tags]
  count(missing_tags) > 0
  
  msg := sprintf("Instance '%s' missing required tags: %v", 
    [resource.address, missing_tags])
}
```

### Integrate OPA in CI/CD

```yaml
# .github/workflows/terraform.yml
- name: Terraform Plan
  run: terraform plan -out=tfplan
  working-directory: envs/prod

- name: Convert plan to JSON
  run: terraform show -json tfplan > tfplan.json
  working-directory: envs/prod

- name: Run OPA Policy Check
  run: |
    opa eval --data policy/ --input envs/prod/tfplan.json \
      --format pretty "data.terraform.deny" > policy-results.txt
    
    if [ -s policy-results.txt ]; then
      echo "❌ Policy violations found:"
      cat policy-results.txt
      exit 1
    else
      echo "✅ All policies passed"
    fi
```

**Explanation**:
- OPA policies are written in Rego language
- Policies check the Terraform plan before apply
- Violations block the deployment automatically
- Centralized policy management across all projects

---

## 4. Advanced Security Scanning

### Modern Security Stack

```yaml
# .github/workflows/security.yml
name: Security Scanning

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # 1. tfsec - Fast security scanner
      - name: tfsec
        uses: aquasecurity/tfsec-action@v1.0.3
        with:
          soft_fail: false
          format: sarif
          output: tfsec.sarif

      # 2. Checkov - Comprehensive policy checks
      - name: Checkov
        uses: bridgecrewio/checkov-action@v12
        with:
          directory: .
          framework: terraform
          output_format: sarif
          output_file_path: checkov.sarif
          soft_fail: false

      # 3. Terrascan - Compliance scanning
      - name: Terrascan
        uses: tenable/terrascan-action@v1.4.0
        with:
          iac_type: 'terraform'
          iac_dir: '.'
          policy_type: 'aws'
          sarif_upload: true

      # 4. Trivy - Vulnerability scanning
      - name: Trivy IaC Scan
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'config'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy.sarif'

      # Upload all results to GitHub Security tab
      - name: Upload SARIF files
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: |
            tfsec.sarif
            checkov.sarif
            trivy.sarif
```

**Explanation**:
- **tfsec**: Fast, focused on AWS security best practices
- **Checkov**: Comprehensive, supports multiple clouds and compliance frameworks
- **Terrascan**: Policy-based, good for compliance (CIS, NIST)
- **Trivy**: Vulnerability scanning, detects misconfigurations
- Results appear in GitHub Security tab for easy tracking

---

## 5. Cost Management with Infracost

### Why Infracost?

**See cost impact before deployment**:
- ✅ Estimate costs in pull requests
- ✅ Prevent expensive mistakes
- ✅ Track cost trends over time
- ✅ Budget alerts

### Infracost Integration

```yaml
# .github/workflows/terraform.yml
- name: Setup Infracost
  uses: infracost/actions/setup@v2
  with:
    api-key: ${{ secrets.INFRACOST_API_KEY }}

- name: Generate Infracost JSON
  run: |
    infracost breakdown --path=envs/prod \
      --format=json \
      --out-file=/tmp/infracost.json

- name: Post Infracost Comment
  uses: infracost/actions/comment@v1
  with:
    path: /tmp/infracost.json
    behavior: update
```

### Example Infracost Output in PR

```
### Monthly Cost Estimate

| Resource | Baseline Cost | Planned Cost | Delta |
|----------|---------------|--------------|-------|
| aws_instance.app (t3.small) | $15.18 | $15.18 | $0.00 |
| aws_nat_gateway.main | $32.85 | $65.70 | +$32.85 ⚠️ |
| aws_lb.main | $22.27 | $22.27 | $0.00 |
| **Total** | **$70.30** | **$103.15** | **+$32.85** |

⚠️ **Warning**: This change will increase monthly costs by $32.85 (47%)
```

**Explanation**:
- Infracost analyzes Terraform plans
- Shows cost breakdown per resource
- Highlights cost increases in PRs
- Helps teams make informed decisions

---

## 6. Container-Based Deployments (ECS/EKS)

### Modern Approach: ECS Fargate

Instead of managing EC2 instances, use **serverless containers**:

```hcl
# modules/ecs-service/main.tf
resource "aws_ecs_cluster" "main" {
  name = "${var.environment}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"  # Modern: Always enable observability
  }

  configuration {
    execute_command_configuration {
      logging = "OVERRIDE"
      log_configuration {
        cloud_watch_log_group_name = aws_cloudwatch_log_group.ecs_exec.name
      }
    }
  }
}

resource "aws_ecs_task_definition" "app" {
  family                   = "${var.environment}-app"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.task_cpu
  memory                   = var.task_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name  = "app"
      image = "${var.ecr_repository_url}:${var.image_tag}"
      
      portMappings = [
        {
          containerPort = var.container_port
          protocol      = "tcp"
        }
      ]
      
      environment = [
        {
          name  = "ENVIRONMENT"
          value = var.environment
        },
        {
          name  = "AWS_REGION"
          value = var.aws_region
        }
      ]
      
      secrets = [
        {
          name      = "DATABASE_URL"
          valueFrom = "${aws_secretsmanager_secret.db_url.arn}:url::"
        },
        {
          name      = "API_KEY"
          valueFrom = "${aws_secretsmanager_secret.api_key.arn}::"
        }
      ]
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.app.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "app"
        }
      }
      
      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:${var.container_port}/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])
}

resource "aws_ecs_service" "app" {
  name            = "${var.environment}-app"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"
  
  # Modern: Enable ECS Exec for debugging
  enable_execute_command = true

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = var.target_group_arn
    container_name   = "app"
    container_port   = var.container_port
  }

  # Modern: Deployment circuit breaker
  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  # Modern: Faster deployments
  deployment_configuration {
    maximum_percent         = 200
    minimum_healthy_percent = 100
  }

  # Modern: Auto-scaling integration
  lifecycle {
    ignore_changes = [desired_count]
  }
}

# Modern: Application Auto Scaling
resource "aws_appautoscaling_target" "ecs" {
  max_capacity       = var.max_capacity
  min_capacity       = var.min_capacity
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.app.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "ecs_cpu" {
  name               = "${var.environment}-cpu-autoscaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = 70.0
  }
}
```

**Why ECS Fargate over EC2?**
- ✅ No server management (truly serverless)
- ✅ Pay only for container runtime
- ✅ Automatic scaling
- ✅ Built-in security (task isolation)
- ✅ Faster deployments
- ✅ Better resource utilization

---

*Continued in next section...*
