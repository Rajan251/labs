# Modern Production Terraform Practices - Part 2

## 7. Observability & Monitoring (Modern Stack)

### OpenTelemetry Integration

**Modern approach**: Unified observability with OpenTelemetry

```hcl
# modules/observability/main.tf
resource "aws_cloudwatch_log_group" "app" {
  name              = "/ecs/${var.environment}/app"
  retention_in_days = 30
  kms_key_id        = aws_kms_key.logs.arn

  tags = {
    Environment = var.environment
  }
}

# Modern: Structured logging with JSON
resource "aws_ecs_task_definition" "app" {
  container_definitions = jsonencode([
    {
      name  = "app"
      image = var.app_image
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.app.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "app"
          "mode"                  = "non-blocking"  # Modern: Don't block on logging
        }
      }
      
      # OpenTelemetry sidecar for metrics/traces
      dependsOn = [
        {
          containerName = "otel-collector"
          condition     = "START"
        }
      ]
    },
    {
      name  = "otel-collector"
      image = "public.ecr.aws/aws-observability/aws-otel-collector:latest"
      
      command = ["--config=/etc/ecs/otel-config.yaml"]
      
      environment = [
        {
          name  = "AWS_REGION"
          value = var.aws_region
        }
      ]
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.otel.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "otel"
        }
      }
    }
  ])
}

# CloudWatch Container Insights
resource "aws_ecs_cluster" "main" {
  name = "${var.environment}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# Modern: Composite alarms for better alerting
resource "aws_cloudwatch_composite_alarm" "app_health" {
  alarm_name          = "${var.environment}-app-health"
  alarm_description   = "Composite alarm for application health"
  actions_enabled     = true
  alarm_actions       = [aws_sns_topic.alerts.arn]
  
  alarm_rule = join(" OR ", [
    "ALARM(${aws_cloudwatch_metric_alarm.high_error_rate.alarm_name})",
    "ALARM(${aws_cloudwatch_metric_alarm.high_latency.alarm_name})",
    "ALARM(${aws_cloudwatch_metric_alarm.low_healthy_tasks.alarm_name})"
  ])
}

# Error rate alarm
resource "aws_cloudwatch_metric_alarm" "high_error_rate" {
  alarm_name          = "${var.environment}-high-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "5XXError"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  statistic           = "Sum"
  threshold           = 10
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = aws_lb.main.arn_suffix
  }
}

# Latency alarm (p99)
resource "aws_cloudwatch_metric_alarm" "high_latency" {
  alarm_name          = "${var.environment}-high-latency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  
  metric_query {
    id          = "m1"
    return_data = true
    
    metric {
      metric_name = "TargetResponseTime"
      namespace   = "AWS/ApplicationELB"
      period      = 60
      stat        = "p99"
      
      dimensions = {
        LoadBalancer = aws_lb.main.arn_suffix
      }
    }
  }
  
  threshold          = 1.0  # 1 second
  treat_missing_data = "notBreaching"
}
```

### Datadog Integration (Modern APM)

```hcl
# Datadog agent as sidecar
resource "aws_ecs_task_definition" "app_with_datadog" {
  family = "${var.environment}-app"
  
  container_definitions = jsonencode([
    {
      name  = "app"
      image = var.app_image
      
      environment = [
        {
          name  = "DD_AGENT_HOST"
          value = "localhost"
        },
        {
          name  = "DD_TRACE_AGENT_PORT"
          value = "8126"
        },
        {
          name  = "DD_ENV"
          value = var.environment
        },
        {
          name  = "DD_SERVICE"
          value = "my-app"
        },
        {
          name  = "DD_VERSION"
          value = var.app_version
        }
      ]
    },
    {
      name  = "datadog-agent"
      image = "public.ecr.aws/datadog/agent:latest"
      
      environment = [
        {
          name  = "DD_APM_ENABLED"
          value = "true"
        },
        {
          name  = "DD_APM_NON_LOCAL_TRAFFIC"
          value = "true"
        },
        {
          name  = "ECS_FARGATE"
          value = "true"
        }
      ]
      
      secrets = [
        {
          name      = "DD_API_KEY"
          valueFrom = aws_secretsmanager_secret.datadog_api_key.arn
        }
      ]
    }
  ])
}
```

**Explanation**:
- OpenTelemetry provides vendor-neutral observability
- Container Insights gives ECS-specific metrics
- Composite alarms reduce alert fatigue
- Datadog provides full APM (traces, metrics, logs)

---

## 8. Secrets Management (Modern Approach)

### AWS Secrets Manager with Rotation

```hcl
# modules/secrets/main.tf

# Database password with automatic rotation
resource "aws_secretsmanager_secret" "db_password" {
  name                    = "${var.environment}/db/password"
  description             = "Database master password"
  recovery_window_in_days = 7
  
  # Modern: Enable automatic rotation
  rotation_rules {
    automatically_after_days = 30
  }
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id = aws_secretsmanager_secret.db_password.id
  secret_string = jsonencode({
    username = "admin"
    password = random_password.db_password.result
  })
}

# Lambda function for rotation
resource "aws_secretsmanager_secret_rotation" "db_password" {
  secret_id           = aws_secretsmanager_secret.db_password.id
  rotation_lambda_arn = aws_lambda_function.rotate_secret.arn

  rotation_rules {
    automatically_after_days = 30
  }
}

# Modern: Use Secrets Manager for all sensitive data
resource "aws_ecs_task_definition" "app" {
  container_definitions = jsonencode([
    {
      name  = "app"
      image = var.app_image
      
      # No environment variables with secrets!
      secrets = [
        {
          name      = "DATABASE_URL"
          valueFrom = "${aws_secretsmanager_secret.db_password.arn}:url::"
        },
        {
          name      = "API_KEY"
          valueFrom = "${aws_secretsmanager_secret.api_key.arn}::"
        },
        {
          name      = "JWT_SECRET"
          valueFrom = "${aws_secretsmanager_secret.jwt_secret.arn}::"
        }
      ]
    }
  ])
}

# IAM policy for ECS task to read secrets
resource "aws_iam_role_policy" "ecs_secrets" {
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          aws_secretsmanager_secret.db_password.arn,
          aws_secretsmanager_secret.api_key.arn,
          aws_secretsmanager_secret.jwt_secret.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt"
        ]
        Resource = aws_kms_key.secrets.arn
      }
    ]
  })
}
```

### HashiCorp Vault Integration (Enterprise)

```hcl
# For organizations using Vault
data "vault_generic_secret" "db_credentials" {
  path = "secret/data/${var.environment}/database"
}

resource "aws_db_instance" "main" {
  username = data.vault_generic_secret.db_credentials.data["username"]
  password = data.vault_generic_secret.db_credentials.data["password"]
}
```

**Explanation**:
- Secrets Manager provides automatic rotation
- Secrets are encrypted with KMS
- ECS tasks fetch secrets at runtime (not in code)
- Vault provides centralized secret management for multi-cloud

---

## 9. Multi-Region & Disaster Recovery

### Active-Active Multi-Region Setup

```hcl
# modules/multi-region/main.tf

# Primary region
provider "aws" {
  alias  = "primary"
  region = "us-east-1"
}

# Secondary region
provider "aws" {
  alias  = "secondary"
  region = "us-west-2"
}

# Deploy to both regions
module "infrastructure_primary" {
  source = "../../modules/infrastructure"
  
  providers = {
    aws = aws.primary
  }
  
  region      = "us-east-1"
  environment = var.environment
}

module "infrastructure_secondary" {
  source = "../../modules/infrastructure"
  
  providers = {
    aws = aws.secondary
  }
  
  region      = "us-west-2"
  environment = var.environment
}

# Route53 health checks and failover
resource "aws_route53_health_check" "primary" {
  fqdn              = module.infrastructure_primary.alb_dns_name
  port              = 443
  type              = "HTTPS"
  resource_path     = "/health"
  failure_threshold = 3
  request_interval  = 30

  tags = {
    Name = "${var.environment}-primary-health"
  }
}

resource "aws_route53_health_check" "secondary" {
  fqdn              = module.infrastructure_secondary.alb_dns_name
  port              = 443
  type              = "HTTPS"
  resource_path     = "/health"
  failure_threshold = 3
  request_interval  = 30

  tags = {
    Name = "${var.environment}-secondary-health"
  }
}

# Route53 with failover
resource "aws_route53_record" "app_primary" {
  zone_id = var.route53_zone_id
  name    = "app.${var.domain_name}"
  type    = "A"

  set_identifier = "primary"
  
  failover_routing_policy {
    type = "PRIMARY"
  }

  alias {
    name                   = module.infrastructure_primary.alb_dns_name
    zone_id                = module.infrastructure_primary.alb_zone_id
    evaluate_target_health = true
  }

  health_check_id = aws_route53_health_check.primary.id
}

resource "aws_route53_record" "app_secondary" {
  zone_id = var.route53_zone_id
  name    = "app.${var.domain_name}"
  type    = "A"

  set_identifier = "secondary"
  
  failover_routing_policy {
    type = "SECONDARY"
  }

  alias {
    name                   = module.infrastructure_secondary.alb_dns_name
    zone_id                = module.infrastructure_secondary.alb_zone_id
    evaluate_target_health = true
  }

  health_check_id = aws_route53_health_check.secondary.id
}

# Cross-region DynamoDB replication
resource "aws_dynamodb_table" "app_data" {
  provider = aws.primary
  
  name             = "${var.environment}-app-data"
  billing_mode     = "PAY_PER_REQUEST"
  hash_key         = "id"
  stream_enabled   = true
  stream_view_type = "NEW_AND_OLD_IMAGES"

  replica {
    region_name = "us-west-2"
  }

  attribute {
    name = "id"
    type = "S"
  }
}

# S3 cross-region replication
resource "aws_s3_bucket" "primary" {
  provider = aws.primary
  bucket   = "${var.environment}-data-primary"
}

resource "aws_s3_bucket_versioning" "primary" {
  provider = aws.primary
  bucket   = aws_s3_bucket.primary.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_replication_configuration" "primary" {
  provider = aws.primary
  
  role   = aws_iam_role.replication.arn
  bucket = aws_s3_bucket.primary.id

  rule {
    id     = "replicate-all"
    status = "Enabled"

    destination {
      bucket        = aws_s3_bucket.secondary.arn
      storage_class = "STANDARD"
    }
  }
}
```

**Explanation**:
- Active-active setup in two regions
- Route53 automatic failover based on health checks
- DynamoDB global tables for data replication
- S3 cross-region replication for objects
- RTO (Recovery Time Objective) < 1 minute

---

## 10. Drift Detection & Remediation

### Automated Drift Detection with Driftctl

```yaml
# .github/workflows/drift-detection.yml
name: Drift Detection

on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
  workflow_dispatch:

jobs:
  detect-drift:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: us-east-1

      - name: Install Driftctl
        run: |
          curl -L https://github.com/snyk/driftctl/releases/latest/download/driftctl_linux_amd64 -o driftctl
          chmod +x driftctl
          sudo mv driftctl /usr/local/bin/

      - name: Scan for Drift
        run: |
          driftctl scan \
            --from tfstate+s3://my-terraform-state/envs/prod/terraform.tfstate \
            --output json://drift-report.json

      - name: Check for Drift
        run: |
          if [ $(jq '.summary.total_unmanaged' drift-report.json) -gt 0 ]; then
            echo "⚠️ Drift detected!"
            jq '.unmanaged' drift-report.json
            exit 1
          else
            echo "✅ No drift detected"
          fi

      - name: Post to Slack
        if: failure()
        uses: slackapi/slack-github-action@v1
        with:
          webhook-url: ${{ secrets.SLACK_WEBHOOK }}
          payload: |
            {
              "text": "🚨 Infrastructure drift detected in production!",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "Infrastructure drift detected. Check GitHub Actions for details."
                  }
                }
              ]
            }
```

### Terraform Cloud Drift Detection

```hcl
# terraform.tf
terraform {
  cloud {
    organization = "my-org"
    
    workspaces {
      name = "production"
    }
  }
}

# Terraform Cloud automatically detects drift
# and can trigger notifications
```

**Explanation**:
- Driftctl compares actual AWS state vs Terraform state
- Runs on schedule to catch manual changes
- Alerts team via Slack when drift detected
- Terraform Cloud provides built-in drift detection

---

## 11. Module Versioning & Private Registry

### Publishing Modules to Private Registry

```hcl
# modules/vpc/versions.tf
terraform {
  required_version = ">= 1.6.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Tag releases in Git: v1.0.0, v1.1.0, etc.
```

### Using Versioned Modules

```hcl
# envs/prod/main.tf

# Modern: Use versioned modules from private registry
module "vpc" {
  source  = "app.terraform.io/my-org/vpc/aws"
  version = "~> 2.0"  # Semantic versioning
  
  vpc_cidr    = "10.0.0.0/16"
  environment = "prod"
}

# Or from GitHub with version tags
module "vpc" {
  source = "github.com/my-org/terraform-aws-vpc?ref=v2.1.0"
  
  vpc_cidr    = "10.0.0.0/16"
  environment = "prod"
}

# Lock file ensures consistency
# .terraform.lock.hcl is committed to Git
```

**Explanation**:
- Modules are versioned using semantic versioning
- Private registry (Terraform Cloud/Enterprise) hosts modules
- Version constraints prevent breaking changes
- Lock file ensures reproducible builds

---

## 12. Testing Infrastructure Code

### Terratest (Go-based Testing)

```go
// test/vpc_test.go
package test

import (
    "testing"
    "github.com/gruntwork-io/terratest/modules/terraform"
    "github.com/gruntwork-io/terratest/modules/aws"
    "github.com/stretchr/testify/assert"
)

func TestVPCModule(t *testing.T) {
    t.Parallel()
    
    awsRegion := "us-east-1"
    
    terraformOptions := &terraform.Options{
        TerraformDir: "../modules/vpc",
        
        Vars: map[string]interface{}{
            "vpc_cidr":      "10.0.0.0/16",
            "environment":   "test",
            "aws_region":    awsRegion,
        },
        
        EnvVars: map[string]string{
            "AWS_DEFAULT_REGION": awsRegion,
        },
    }
    
    defer terraform.Destroy(t, terraformOptions)
    
    terraform.InitAndApply(t, terraformOptions)
    
    // Validate outputs
    vpcID := terraform.Output(t, terraformOptions, "vpc_id")
    assert.NotEmpty(t, vpcID)
    
    // Validate actual AWS resources
    vpc := aws.GetVpcById(t, vpcID, awsRegion)
    assert.Equal(t, "10.0.0.0/16", *vpc.CidrBlock)
    
    subnets := aws.GetSubnetsForVpc(t, vpcID, awsRegion)
    assert.Equal(t, 4, len(subnets))  // 2 public + 2 private
}

func TestECSService(t *testing.T) {
    t.Parallel()
    
    terraformOptions := &terraform.Options{
        TerraformDir: "../modules/ecs-service",
        
        Vars: map[string]interface{}{
            "environment":    "test",
            "desired_count":  2,
            "container_port": 8080,
        },
    }
    
    defer terraform.Destroy(t, terraformOptions)
    terraform.InitAndApply(t, terraformOptions)
    
    // Validate ECS service
    clusterName := terraform.Output(t, terraformOptions, "cluster_name")
    serviceName := terraform.Output(t, terraformOptions, "service_name")
    
    service := aws.GetEcsService(t, "us-east-1", clusterName, serviceName)
    assert.Equal(t, int64(2), *service.DesiredCount)
}
```

### Run Tests

```bash
# Install Go and Terratest
go mod init test
go get github.com/gruntwork-io/terratest/modules/terraform
go get github.com/stretchr/testify/assert

# Run tests
go test -v -timeout 30m
```

**Explanation**:
- Terratest validates infrastructure by deploying it
- Tests run in parallel for speed
- Actual AWS resources are created and validated
- Automatic cleanup with defer

---

## 13. Complete Modern CI/CD Pipeline

### GitHub Actions (Production-Ready)

```yaml
# .github/workflows/terraform-production.yml
name: Terraform Production Pipeline

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

permissions:
  id-token: write
  contents: read
  pull-requests: write
  security-events: write

env:
  AWS_REGION: us-east-1
  TF_VERSION: 1.7.0

jobs:
  validate:
    name: Validate & Lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - name: Terraform Format Check
        run: terraform fmt -check -recursive

      - name: Terraform Init
        run: terraform init -backend=false
        working-directory: envs/prod

      - name: Terraform Validate
        run: terraform validate
        working-directory: envs/prod

      - name: TFLint
        uses: terraform-linters/setup-tflint@v4
        with:
          tflint_version: latest

      - name: Run TFLint
        run: tflint --recursive

  security:
    name: Security Scanning
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: tfsec
        uses: aquasecurity/tfsec-action@v1.0.3

      - name: Checkov
        uses: bridgecrewio/checkov-action@v12
        with:
          framework: terraform

      - name: Trivy
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'config'

  cost:
    name: Cost Estimation
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v4

      - name: Setup Infracost
        uses: infracost/actions/setup@v2
        with:
          api-key: ${{ secrets.INFRACOST_API_KEY }}

      - name: Generate Cost Estimate
        run: |
          infracost breakdown --path=envs/prod \
            --format=json \
            --out-file=/tmp/infracost.json

      - name: Post Cost Comment
        uses: infracost/actions/comment@v1
        with:
          path: /tmp/infracost.json

  plan:
    name: Terraform Plan
    runs-on: ubuntu-latest
    needs: [validate, security]
    environment: production-plan
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - name: Terraform Init
        run: terraform init
        working-directory: envs/prod

      - name: Terraform Plan
        id: plan
        run: |
          terraform plan -no-color -out=tfplan | tee plan.txt
        working-directory: envs/prod

      - name: Upload Plan
        uses: actions/upload-artifact@v4
        with:
          name: tfplan
          path: envs/prod/tfplan
          retention-days: 5

      - name: Comment Plan on PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const plan = fs.readFileSync('envs/prod/plan.txt', 'utf8');
            
            const output = `### Terraform Plan
            <details><summary>Show Plan</summary>
            
            \`\`\`terraform
            ${plan}
            \`\`\`
            
            </details>`;
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: output
            });

  apply:
    name: Terraform Apply
    runs-on: ubuntu-latest
    needs: [plan]
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - name: Terraform Init
        run: terraform init
        working-directory: envs/prod

      - name: Download Plan
        uses: actions/download-artifact@v4
        with:
          name: tfplan
          path: envs/prod

      - name: Terraform Apply
        run: terraform apply -auto-approve tfplan
        working-directory: envs/prod

      - name: Post to Slack
        if: always()
        uses: slackapi/slack-github-action@v1
        with:
          webhook-url: ${{ secrets.SLACK_WEBHOOK }}
          payload: |
            {
              "text": "${{ job.status == 'success' && '✅' || '❌' }} Terraform Apply ${{ job.status }}",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "Terraform apply to production: *${{ job.status }}*\nCommit: ${{ github.sha }}\nActor: ${{ github.actor }}"
                  }
                }
              ]
            }
```

**Explanation**:
- Multi-stage pipeline: validate → security → cost → plan → apply
- OIDC authentication (no static keys)
- Security scanning with multiple tools
- Cost estimation on PRs
- Manual approval required for production
- Slack notifications for visibility

---

*Continued in summary...*
