# Complete Terraform AWS Infrastructure Guide

## 📚 Guide Overview

This is a **complete, production-ready guide** for provisioning AWS infrastructure using Terraform from an Ubuntu server. It covers VPCs, subnets, security groups, EC2 instances, Application Load Balancers (ALB), S3 buckets, and more.

### 🆕 Modern Production Practices (2024-2025)

**NEW!** We've added comprehensive guides on modern production approaches:

- **[Modern Production Practices](modern-production-practices.md)** - OIDC auth, GitOps, Policy as Code, advanced security
- **[Modern Production Practices Part 2](modern-production-practices-part2.md)** - Observability, secrets management, multi-region, testing
- **[Modern vs Traditional Comparison](modern-vs-traditional.md)** - See what's changed and why it matters

**Key Modern Enhancements:**
- ✅ OIDC authentication (no static AWS keys)
- ✅ GitOps with Atlantis (PR-based workflows)
- ✅ Policy as Code (OPA/Sentinel)
- ✅ Advanced security scanning (tfsec, Checkov, Terrascan, Trivy)
- ✅ Cost management (Infracost in PRs)
- ✅ ECS Fargate (serverless containers)
- ✅ OpenTelemetry + Datadog APM
- ✅ Secrets Manager with rotation
- ✅ Multi-region active-active
- ✅ Automated drift detection
- ✅ Infrastructure testing (Terratest)

## 📖 Documentation Structure

The guide is split into 6 comprehensive parts:

### [Part 1: Foundations](terraform-aws-guide.md)
1. **Project Overview** - Architecture diagram and use cases
2. **Prerequisites** - Ubuntu server setup, AWS CLI, Terraform installation
3. **Project Layout** - Recommended directory structure
4. **Remote State** - S3 backend and DynamoDB locking
5. **Provider Configuration** - AWS authentication methods

### [Part 2: Core Infrastructure](terraform-aws-guide-part2.md)
6. **Networking** - Complete VPC module with subnets, NAT, IGW
7. **Security Groups & IAM** - Least privilege examples
8. **EC2 Instances** - Bastion hosts, Launch Templates, Auto Scaling

### [Part 3: Application Layer](terraform-aws-guide-part3.md)
9. **Application Load Balancer** - ALB with target groups and health checks
10. **S3 Buckets** - Encryption, versioning, lifecycle policies
11. **Variables & Outputs** - Secrets handling best practices
12. **Modules** - Creating and using reusable modules

### [Part 4: Operations](terraform-aws-guide-part4.md)
13. **CI/CD** - GitHub Actions and GitLab CI examples
14. **Testing & Validation** - terraform fmt, validate, checkov, tflint
15. **Change Management** - Safe updates and rollback strategies
16. **Cost & Security** - Optimization tips and security checklist

### [Part 5: Troubleshooting & Examples](terraform-aws-guide-part5.md)
17. **Troubleshooting** - Common problems with detailed solutions
18. **End-to-End Examples** - Complete working code
19. **Step-by-Step Runbook** - Exact commands to deploy

### [Part 6: Advanced Topics](terraform-aws-guide-part6.md)
20. **Cleanup & Destroy** - Safe destruction procedures
21. **Deliverables** - Complete file structure
22. **Advanced Topics** - Blue/green deployments, Terraform Cloud
23. **Best Practices** - Comprehensive checklist

## 🚀 Quick Start

### 1. Prerequisites

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install tools
sudo apt install -y curl wget unzip git jq

# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Install Terraform
wget -O- https://apt.releases.hashicorp.com/gpg | \
  gpg --dearmor | \
  sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] \
  https://apt.releases.hashicorp.com $(lsb_release -cs) main" | \
  sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install -y terraform

# Configure AWS
aws configure
```

### 2. Create Backend Resources

```bash
chmod +x scripts/*.sh
./scripts/create-backend.sh
```

### 3. Deploy Infrastructure

```bash
# Initialize
./scripts/init.sh dev

# Plan
./scripts/plan.sh dev

# Apply
./scripts/apply.sh dev
```

## 📋 Step-by-Step Execution Guide

**NEW!** For detailed step-by-step instructions with explanations, see:

👉 **[EXECUTION-GUIDE.md](EXECUTION-GUIDE.md)** - Complete walkthrough with:
- ✅ Prerequisites checklist
- ✅ Environment setup (15-20 min)
- ✅ Project setup (10 min)
- ✅ Infrastructure deployment (10-15 min)
- ✅ Verification steps
- ✅ Troubleshooting guide
- ✅ Cost estimates
- ✅ Production workflow

**Perfect for first-time users!**

## 📁 Repository Structure

```
terraform-aws-infrastructure/
├── README.md                          # This file
├── terraform-aws-guide.md             # Part 1: Foundations
├── terraform-aws-guide-part2.md       # Part 2: Core Infrastructure
├── terraform-aws-guide-part3.md       # Part 3: Application Layer
├── terraform-aws-guide-part4.md       # Part 4: Operations
├── terraform-aws-guide-part5.md       # Part 5: Troubleshooting
├── terraform-aws-guide-part6.md       # Part 6: Advanced Topics
├── scripts/
│   ├── create-backend.sh              # Create S3/DynamoDB backend
│   ├── init.sh                        # Initialize Terraform
│   ├── plan.sh                        # Plan changes
│   ├── apply.sh                       # Apply changes
│   └── destroy.sh                     # Destroy resources
└── [Additional module/env directories as needed]
```

## 🎯 What's Included

### Infrastructure Components
- ✅ VPC with public and private subnets across multiple AZs
- ✅ Internet Gateway and NAT Gateway
- ✅ Route tables and associations
- ✅ Security groups following least privilege
- ✅ Bastion host for secure SSH access
- ✅ EC2 Auto Scaling Groups with Launch Templates
- ✅ Application Load Balancer with health checks
- ✅ S3 buckets with encryption and versioning
- ✅ IAM roles and instance profiles
- ✅ CloudWatch alarms for auto-scaling

### Operational Excellence
- ✅ Remote state with S3 and DynamoDB locking
- ✅ Reusable modules for VPC, EC2, ALB, S3
- ✅ CI/CD examples (GitHub Actions, GitLab CI)
- ✅ Automated scripts for common operations
- ✅ Comprehensive troubleshooting guide
- ✅ Security best practices
- ✅ Cost optimization strategies

## 🔧 Helper Scripts

| Script | Purpose |
|--------|---------|
| `create-backend.sh` | Create S3 bucket and DynamoDB table for state |
| `init.sh <env>` | Initialize Terraform for environment |
| `plan.sh <env>` | Create execution plan |
| `apply.sh <env>` | Apply changes |
| `destroy.sh <env>` | Destroy resources (with confirmation) |

## 📊 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                          AWS Region                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    VPC (10.0.0.0/16)                      │  │
│  │                                                           │  │
│  │  ┌──────────────────────┐  ┌──────────────────────┐     │  │
│  │  │  Public Subnet AZ-A  │  │  Public Subnet AZ-B  │     │  │
│  │  │    (10.0.1.0/24)     │  │    (10.0.2.0/24)     │     │  │
│  │  │                      │  │                      │     │  │
│  │  │  ┌──────────────┐    │  │    ┌──────────────┐ │     │  │
│  │  │  │   Bastion    │    │  │    │     ALB      │ │     │  │
│  │  │  │    Host      │    │  │    │  (Public)    │ │     │  │
│  │  │  └──────────────┘    │  │    └──────┬───────┘ │     │  │
│  │  │  ┌──────────────┐    │  │           │         │     │  │
│  │  │  │ NAT Gateway  │    │  │           │         │     │  │
│  │  │  └──────┬───────┘    │  │           │         │     │  │
│  │  └─────────┼────────────┘  └───────────┼─────────┘     │  │
│  │            │                            │               │  │
│  │            │  Internet Gateway          │               │  │
│  │            │         ▲                  │               │  │
│  │  ┌─────────┼─────────┼──────────────────┼─────────┐     │  │
│  │  │         │         │                  │         │     │  │
│  │  │  Private Subnet AZ-A    Private Subnet AZ-B    │     │  │
│  │  │    (10.0.11.0/24)         (10.0.12.0/24)       │     │  │
│  │  │                                                 │     │  │
│  │  │  ┌──────────────┐       ┌──────────────┐       │     │  │
│  │  │  │  App Server  │       │  App Server  │       │     │  │
│  │  │  │   EC2 (ASG)  │       │   EC2 (ASG)  │       │     │  │
│  │  │  └──────┬───────┘       └──────┬───────┘       │     │  │
│  │  │         │                      │               │     │  │
│  │  │         └──────────┬───────────┘               │     │  │
│  │  │                    │                           │     │  │
│  │  └────────────────────┼───────────────────────────┘     │  │
│  │                       │                                 │  │
│  └───────────────────────┼─────────────────────────────────┘  │
│                          │                                    │
│                          ▼                                    │
│                   ┌─────────────┐                             │
│                   │  S3 Buckets │                             │
│                   │  - State    │                             │
│                   │  - Artifacts│                             │
│                   │  - Storage  │                             │
│                   └─────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
```

## 🔍 Key Features

### Security
- Encryption at rest and in transit
- Least privilege IAM policies
- Private subnets for application servers
- Bastion host for secure access
- Security group rules with minimal exposure
- Secrets management best practices

### High Availability
- Multi-AZ deployment
- Auto Scaling Groups
- Application Load Balancer
- Health checks and automatic recovery

### Operational
- Remote state with locking
- Modular, reusable code
- CI/CD ready
- Comprehensive logging
- Cost optimization strategies

## 📝 Common Commands

```bash
# Format code
terraform fmt -recursive

# Validate
terraform validate

# Plan
terraform plan -out=tfplan

# Apply
terraform apply tfplan

# View outputs
terraform output

# Destroy
terraform destroy

# View state
terraform state list
terraform state show <resource>
```

## 🐛 Troubleshooting

See [Part 5](terraform-aws-guide-part5.md#17-troubleshooting) for detailed troubleshooting guide including:

- State locking issues
- ALB health check failures
- EC2 connectivity problems
- Terraform destroy failures
- IAM permission errors
- And more...

## 💰 Cost Estimate

Approximate monthly cost for dev environment (us-east-1):

| Resource | Cost |
|----------|------|
| 2x t3.small EC2 | ~$30 |
| 1x NAT Gateway | ~$32 |
| 1x ALB | ~$22 |
| S3 Storage | ~$2 |
| **Total** | **~$86/month** |

## ✅ Best Practices Checklist

- [ ] Use remote state with locking
- [ ] Enable encryption everywhere
- [ ] Implement least privilege IAM
- [ ] Deploy across multiple AZs
- [ ] Use modules for reusability
- [ ] Tag all resources
- [ ] Never hardcode secrets
- [ ] Run terraform fmt before commit
- [ ] Review plans before apply
- [ ] Test in dev before prod

## 📚 Additional Resources

- [Terraform Documentation](https://www.terraform.io/docs)
- [AWS Provider Docs](https://registry.terraform.io/providers/hashicorp/aws)
- [Terraform Best Practices](https://www.terraform-best-practices.com)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected)

## 🤝 Support

For issues or questions:
1. Check the [Troubleshooting Guide](terraform-aws-guide-part5.md#17-troubleshooting)
2. Review [Common Problems](terraform-aws-guide-part5.md#common-problems--solutions)
3. Consult Terraform/AWS documentation

## 📄 License

This guide is provided as-is for educational and production use.

---

**Ready to get started?** Begin with [Part 1: Foundations](terraform-aws-guide.md) or jump directly to the [Quick Start](#-quick-start) section above.
