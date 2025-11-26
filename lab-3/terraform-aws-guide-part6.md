# Terraform AWS Infrastructure Guide - Part 6 (Final)

## 20. Cleanup & Destroy

### Safe Destroy Process

```bash
# 1. Review what will be destroyed
terraform plan -destroy

# 2. Destroy specific environment (with confirmation)
cd envs/dev
terraform destroy

# You will be prompted:
# Do you really want to destroy all resources?
# Enter 'yes' to confirm

# 3. Destroy without confirmation (CI/CD)
terraform destroy -auto-approve

# 4. Destroy specific resources only
terraform destroy -target=aws_instance.bastion

# 5. Destroy everything except specific resource
terraform state rm aws_s3_bucket.important
terraform destroy
```

### Prevent Accidental Destruction

```hcl
# Add lifecycle prevent_destroy to critical resources
resource "aws_s3_bucket" "critical_data" {
  bucket = "critical-data-bucket"
  
  lifecycle {
    prevent_destroy = true
  }
}

# Enable deletion protection on ALB
resource "aws_lb" "main" {
  name                       = "prod-alb"
  enable_deletion_protection = true
}

# Use workspaces for environment isolation
# terraform workspace new prod
# terraform workspace select prod
```

### Cleanup Checklist

- [ ] Backup important data from S3 buckets
- [ ] Export any logs or metrics
- [ ] Document any manual changes made
- [ ] Notify team members
- [ ] Remove DNS records pointing to resources
- [ ] Delete CloudWatch alarms
- [ ] Clean up S3 state bucket (if removing everything)
- [ ] Delete DynamoDB lock table (if removing everything)

---

## 21. Deliverables & File List

### Complete Repository Structure

```
terraform-aws-infrastructure/
├── README.md                          # Main documentation
├── .gitignore                         # Git ignore rules
├── .pre-commit-config.yaml           # Pre-commit hooks
├── modules/
│   ├── vpc/
│   │   ├── main.tf                   # VPC resources
│   │   ├── variables.tf              # VPC inputs
│   │   ├── outputs.tf                # VPC outputs
│   │   ├── security_groups.tf        # Security groups
│   │   └── README.md                 # VPC module docs
│   ├── ec2-asg/
│   │   ├── main.tf                   # ASG resources
│   │   ├── variables.tf              # ASG inputs
│   │   ├── outputs.tf                # ASG outputs
│   │   ├── user_data.sh              # Bootstrap script
│   │   └── README.md                 # ASG module docs
│   ├── alb/
│   │   ├── main.tf                   # ALB resources
│   │   ├── variables.tf              # ALB inputs
│   │   ├── outputs.tf                # ALB outputs
│   │   └── README.md                 # ALB module docs
│   └── s3/
│       ├── main.tf                   # S3 resources
│       ├── variables.tf              # S3 inputs
│       ├── outputs.tf                # S3 outputs
│       └── README.md                 # S3 module docs
├── envs/
│   ├── dev/
│   │   ├── main.tf                   # Dev environment main
│   │   ├── variables.tf              # Dev variables
│   │   ├── outputs.tf                # Dev outputs
│   │   ├── terraform.tfvars          # Dev values (gitignored)
│   │   ├── terraform.tfvars.example  # Example values
│   │   └── backend.tf                # Dev backend config
│   ├── staging/
│   │   └── ...                       # Same structure as dev
│   └── prod/
│       └── ...                       # Same structure as dev
├── scripts/
│   ├── create-backend.sh             # Create S3/DynamoDB backend
│   ├── init.sh                       # Initialize environment
│   ├── plan.sh                       # Run terraform plan
│   ├── apply.sh                      # Run terraform apply
│   └── destroy.sh                    # Run terraform destroy
├── .github/
│   └── workflows/
│       └── terraform.yml             # GitHub Actions CI/CD
└── docs/
    ├── architecture.md               # Architecture documentation
    ├── runbook.md                    # Operations runbook
    └── troubleshooting.md            # Troubleshooting guide
```

### Sample README.md

```markdown
# AWS Infrastructure with Terraform

Production-ready AWS infrastructure using Terraform: VPC, EC2, ALB, S3.

## Prerequisites

- Terraform >= 1.6.0
- AWS CLI configured
- AWS account with appropriate permissions

## Quick Start

```bash
# 1. Create backend
./scripts/create-backend.sh

# 2. Initialize dev environment
cd envs/dev
terraform init

# 3. Copy and edit variables
cp terraform.tfvars.example terraform.tfvars
vim terraform.tfvars

# 4. Deploy
terraform plan -out=tfplan
terraform apply tfplan
```

## Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `aws_region` | AWS region | `us-east-1` |
| `environment` | Environment name | `dev` |
| `project_name` | Project name | `myapp` |
| `vpc_cidr` | VPC CIDR block | `10.0.0.0/16` |
| `instance_type` | EC2 instance type | `t3.small` |

## Required IAM Permissions

See [docs/iam-policy.json](docs/iam-policy.json) for complete policy.

Minimum required:
- EC2: Full access
- VPC: Full access
- ELB: Full access
- S3: Create/manage buckets
- IAM: Create roles and policies

## Outputs

- `alb_dns_name`: Load balancer DNS
- `vpc_id`: VPC identifier
- `bucket_name`: S3 bucket name

## Support

See [docs/troubleshooting.md](docs/troubleshooting.md)
```

---

## 22. Advanced Topics

### Blue/Green Deployments

```hcl
# Create two target groups
resource "aws_lb_target_group" "blue" {
  name     = "${var.environment}-blue-tg"
  port     = 80
  protocol = "HTTP"
  vpc_id   = var.vpc_id
}

resource "aws_lb_target_group" "green" {
  name     = "${var.environment}-green-tg"
  port     = 80
  protocol = "HTTP"
  vpc_id   = var.vpc_id
}

# Use variable to control active target group
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"
  
  default_action {
    type             = "forward"
    target_group_arn = var.active_color == "blue" ? 
                       aws_lb_target_group.blue.arn : 
                       aws_lb_target_group.green.arn
  }
}

# Switch traffic by changing variable
# active_color = "green"
```

### Terraform Cloud / Enterprise

```hcl
terraform {
  cloud {
    organization = "my-org"
    
    workspaces {
      name = "aws-infrastructure-dev"
    }
  }
}
```

### Cross-Account Deployments

```hcl
# Assume role in different account
provider "aws" {
  alias  = "prod_account"
  region = "us-east-1"
  
  assume_role {
    role_arn = "arn:aws:iam::123456789012:role/TerraformRole"
  }
}

# Use aliased provider
resource "aws_vpc" "prod" {
  provider   = aws.prod_account
  cidr_block = "10.1.0.0/16"
}
```

### Atlantis for PR-Based Workflows

```yaml
# atlantis.yaml
version: 3
projects:
- name: dev
  dir: envs/dev
  workflow: default
  autoplan:
    when_modified: ["*.tf", "*.tfvars"]
    enabled: true
  
- name: prod
  dir: envs/prod
  workflow: prod
  autoplan:
    when_modified: ["*.tf"]
    enabled: true

workflows:
  prod:
    plan:
      steps:
      - init
      - plan
    apply:
      steps:
      - apply
```

---

## 23. Best Practices Checklist

### Code Quality
- [ ] Use consistent naming conventions
- [ ] Run `terraform fmt` before committing
- [ ] Use `terraform validate` in CI/CD
- [ ] Implement pre-commit hooks
- [ ] Add comments for complex logic
- [ ] Use meaningful variable names
- [ ] Keep modules focused and reusable

### State Management
- [ ] Use remote state (S3 + DynamoDB)
- [ ] Enable state encryption
- [ ] Enable S3 versioning
- [ ] Implement state locking
- [ ] Never commit state files to git
- [ ] Use separate state per environment

### Security
- [ ] Never hardcode credentials
- [ ] Use IAM roles over access keys
- [ ] Enable encryption at rest
- [ ] Enable encryption in transit
- [ ] Implement least privilege IAM
- [ ] Use security scanning tools
- [ ] Enable MFA for privileged accounts
- [ ] Regular security audits

### Infrastructure
- [ ] Use multiple AZs for HA
- [ ] Implement auto-scaling
- [ ] Configure health checks
- [ ] Enable monitoring and logging
- [ ] Use private subnets for apps
- [ ] Implement bastion for SSH access
- [ ] Tag all resources consistently

### Operations
- [ ] Document architecture
- [ ] Create runbooks
- [ ] Implement CI/CD pipelines
- [ ] Test disaster recovery
- [ ] Monitor costs
- [ ] Regular backups
- [ ] Change management process

### Development Workflow
- [ ] Use feature branches
- [ ] Require code reviews
- [ ] Test in dev before prod
- [ ] Use workspaces or separate state
- [ ] Plan before apply
- [ ] Review plans carefully
- [ ] Gradual rollouts for prod

---

## Summary & Next Steps

### What You've Learned

This guide covered:
1. ✅ Complete Ubuntu server setup for Terraform
2. ✅ Production-ready project structure
3. ✅ Remote state with S3 and DynamoDB
4. ✅ VPC with public/private subnets across AZs
5. ✅ Security groups following least privilege
6. ✅ EC2 instances with Auto Scaling
7. ✅ Application Load Balancer configuration
8. ✅ S3 buckets with encryption and lifecycle
9. ✅ Secrets management best practices
10. ✅ Reusable modules
11. ✅ CI/CD integration
12. ✅ Testing and validation
13. ✅ Change management and rollback
14. ✅ Cost optimization strategies
15. ✅ Comprehensive troubleshooting
16. ✅ End-to-end working examples

### Next Steps

1. **Deploy the Example**
   - Clone the code examples
   - Customize for your use case
   - Deploy to dev environment
   - Test thoroughly

2. **Expand Infrastructure**
   - Add RDS database
   - Implement CloudFront CDN
   - Add Route53 DNS
   - Implement WAF rules
   - Add monitoring (CloudWatch, Prometheus)

3. **Improve Operations**
   - Set up Atlantis or Terraform Cloud
   - Implement automated testing (Terratest)
   - Create disaster recovery plan
   - Document incident response

4. **Learn More**
   - Terraform Registry modules
   - AWS Well-Architected Framework
   - Infrastructure as Code best practices
   - GitOps workflows

### Additional Resources

- **Terraform Documentation**: https://www.terraform.io/docs
- **AWS Provider Docs**: https://registry.terraform.io/providers/hashicorp/aws
- **Terraform Best Practices**: https://www.terraform-best-practices.com
- **AWS Well-Architected**: https://aws.amazon.com/architecture/well-architected

### Support & Community

- Terraform Community Forum: https://discuss.hashicorp.com
- AWS Forums: https://forums.aws.amazon.com
- Stack Overflow: Tag `terraform` and `amazon-web-services`

---

**Congratulations!** You now have a complete, production-ready guide for provisioning AWS infrastructure with Terraform. Start small, test thoroughly, and scale confidently.
