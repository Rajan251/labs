# Quick Reference - Terraform AWS Infrastructure

## 🚀 Quick Start Commands

```bash
# 1. Setup (one-time)
./scripts/create-backend.sh

# 2. Deploy
cd envs/dev
terraform init
terraform plan -out=tfplan
terraform apply tfplan

# 3. Verify
terraform output
curl $(terraform output -raw alb_url)

# 4. Cleanup
terraform destroy
```

## 📝 Common Commands

| Task | Command |
|------|---------|
| **Format code** | `terraform fmt -recursive` |
| **Validate** | `terraform validate` |
| **Plan** | `terraform plan -out=tfplan` |
| **Apply** | `terraform apply tfplan` |
| **Destroy** | `terraform destroy` |
| **View outputs** | `terraform output` |
| **List resources** | `terraform state list` |
| **Show resource** | `terraform state show <resource>` |
| **Refresh state** | `terraform refresh` |

## 🔧 Helper Scripts

```bash
./scripts/init.sh <env>      # Initialize environment
./scripts/plan.sh <env>      # Create plan
./scripts/apply.sh <env>     # Apply changes
./scripts/destroy.sh <env>   # Destroy resources
```

## 📊 Resource Overview

| Resource | Count | Purpose |
|----------|-------|---------|
| VPC | 1 | Network isolation |
| Subnets | 4 | 2 public + 2 private |
| NAT Gateway | 1 | Outbound internet for private subnets |
| ALB | 1 | Load balancing |
| Auto Scaling Group | 1 | Auto-scaling EC2 instances |
| Security Groups | 2 | ALB + App security |

## 💰 Cost Estimate

| Resource | Monthly Cost |
|----------|--------------|
| 2x t3.micro EC2 | ~$15 |
| 1x NAT Gateway | ~$32 |
| 1x ALB | ~$22 |
| **Total** | **~$69/month** |

## 🔍 Verification Commands

```bash
# Check VPC
aws ec2 describe-vpcs --filters "Name=tag:Name,Values=dev-vpc"

# Check instances
aws ec2 describe-instances --filters "Name=tag:Name,Values=dev-app-asg"

# Check ALB
aws elbv2 describe-load-balancers --names dev-alb

# Check target health
aws elbv2 describe-target-health --target-group-arn <ARN>
```

## 🐛 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| State lock stuck | `terraform force-unlock <LOCK_ID>` |
| Health checks failing | Wait 2-3 min, check security groups |
| Bucket exists error | Use unique bucket name |
| Capacity error | Change AZ or instance type |

## 📚 Documentation

- **[README.md](README.md)** - Main guide overview
- **[EXECUTION-GUIDE.md](EXECUTION-GUIDE.md)** - Step-by-step walkthrough
- **[modern-production-practices.md](modern-production-practices.md)** - Modern DevOps patterns
- **[modern-vs-traditional.md](modern-vs-traditional.md)** - Comparison guide

## 🎯 Production Checklist

Before deploying to production:

- [ ] Review and customize variables
- [ ] Set up OIDC authentication
- [ ] Enable security scanning (tfsec, Checkov)
- [ ] Add Infracost for cost visibility
- [ ] Implement GitOps workflow (Atlantis)
- [ ] Set up monitoring and alerting
- [ ] Configure multi-region for DR
- [ ] Enable secrets rotation
- [ ] Add automated testing
- [ ] Document runbooks

## 🔐 Security Best Practices

- ✅ Use OIDC instead of static AWS keys
- ✅ Enable encryption at rest and in transit
- ✅ Use private subnets for applications
- ✅ Implement least privilege IAM
- ✅ Enable MFA on AWS accounts
- ✅ Use Secrets Manager for sensitive data
- ✅ Run security scans before deployment
- ✅ Enable CloudTrail and VPC Flow Logs

## 📞 Support

- **Troubleshooting**: See [EXECUTION-GUIDE.md](EXECUTION-GUIDE.md#troubleshooting)
- **Modern Practices**: See [modern-production-practices.md](modern-production-practices.md)
- **AWS Docs**: https://docs.aws.amazon.com/
- **Terraform Docs**: https://www.terraform.io/docs
