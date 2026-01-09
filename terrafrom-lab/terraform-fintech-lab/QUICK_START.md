# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites
```bash
# Check Terraform version
terraform --version  # Should be >= 1.6.0

# Check AWS CLI
aws --version
aws sts get-caller-identity  # Verify AWS credentials
```

### Step 1: Navigate to Lab 01
```bash
cd /home/rk/Documents/labs/terrafrom-lab/terraform-fintech-lab/labs/01-vpc-networking
```

### Step 2: Deploy VPC Infrastructure
```bash
# Initialize Terraform
terraform init

# Review what will be created
terraform plan

# Deploy infrastructure
terraform apply
# Type 'yes' when prompted
```

### Step 3: Verify Deployment
```bash
# Check VPC
aws ec2 describe-vpcs \
  --filters "Name=tag:Project,Values=payflow-platform" \
  --query 'Vpcs[*].[VpcId,CidrBlock]' \
  --output table

# Check subnets
terraform output public_subnet_ids
terraform output private_subnet_ids
```

### Step 4: Clean Up (When Done)
```bash
terraform destroy
# Type 'yes' when prompted
```

## 📚 Learning Path

### Beginner (Start Here)
1. Read [README.md](README.md) - Understand the scenario
2. Review [docs/architecture.md](docs/architecture.md) - Visualize infrastructure
3. Complete [Lab 01](labs/01-vpc-networking/README.md) - Deploy VPC

### Intermediate
4. Study [docs/security-best-practices.md](docs/security-best-practices.md)
5. Review [TERRAFORM_MODULES.md](TERRAFORM_MODULES.md) - Module patterns
6. Practice [docs/use-cases.md](docs/use-cases.md) - Operational scenarios

### Advanced
7. Implement remaining labs (02-07)
8. Customize modules for your needs
9. Add CI/CD pipeline
10. Deploy to production

## 📖 Documentation Index

| Document | Purpose | Time to Read |
|----------|---------|--------------|
| [README.md](README.md) | Lab overview & quick start | 10 min |
| [docs/architecture.md](docs/architecture.md) | Architecture diagrams | 15 min |
| [docs/business-requirements.md](docs/business-requirements.md) | Business context | 20 min |
| [docs/security-best-practices.md](docs/security-best-practices.md) | Security guide | 30 min |
| [docs/troubleshooting.md](docs/troubleshooting.md) | Troubleshooting | 20 min |
| [docs/use-cases.md](docs/use-cases.md) | Operational scenarios | 30 min |
| [TERRAFORM_MODULES.md](TERRAFORM_MODULES.md) | Module reference | 45 min |
| [labs/01-vpc-networking/README.md](labs/01-vpc-networking/README.md) | Lab 01 guide | 30 min |

## 💰 Cost Estimates

### Development Environment
- **NAT Gateway**: $32/month (single)
- **EC2 Instances**: Free tier eligible
- **RDS**: $15/month (single-AZ)
- **Total**: ~$50/month

### Production Environment
- **NAT Gateways**: $96/month (3 AZs)
- **EC2 Instances**: $90/month (3 instances)
- **RDS**: $60/month (Multi-AZ)
- **ALB**: $16/month
- **Total**: ~$260/month

### Cost Optimization Tips
✅ Use single NAT GW in dev (save $64/month)  
✅ Schedule scaling for off-hours (save 40%)  
✅ Use Reserved Instances (save 30%)  
✅ Destroy resources when not in use  

## 🆘 Common Issues

### "VPC Limit Exceeded"
```bash
# Check current VPC count
aws ec2 describe-vpcs --query 'length(Vpcs)'

# Request limit increase
aws service-quotas request-service-quota-increase \
  --service-code vpc \
  --quota-code L-F678F1CE \
  --desired-value 10
```

### "State Lock Error"
```bash
# Force unlock (use with caution)
terraform force-unlock <LOCK_ID>
```

### "Permission Denied"
```bash
# Check IAM permissions
aws sts get-caller-identity
aws iam get-user
```

## 🎯 Learning Objectives

By completing this lab, you will:

✅ Deploy production-grade VPC infrastructure  
✅ Implement multi-AZ high availability  
✅ Configure auto-scaling and load balancing  
✅ Secure infrastructure with defense-in-depth  
✅ Monitor infrastructure health  
✅ Troubleshoot common issues  
✅ Optimize costs  

## 📞 Getting Help

- **Documentation**: Check [docs/troubleshooting.md](docs/troubleshooting.md)
- **AWS Docs**: https://docs.aws.amazon.com/vpc/
- **Terraform Docs**: https://registry.terraform.io/providers/hashicorp/aws/

## 🎓 Next Steps

After Lab 01, continue with:
- **Lab 02**: Security Groups and NACLs
- **Lab 03**: EC2 Auto Scaling
- **Lab 04**: Application Load Balancer
- **Lab 05**: RDS Database
- **Lab 06**: CloudWatch Monitoring
- **Lab 07**: Multi-Environment Deployment

---

**Ready to begin?** Start with [Lab 01: VPC Networking](labs/01-vpc-networking/README.md) 🚀
