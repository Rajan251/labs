# 🏗️ AWS Two-Tier Architecture - Complete Guide

> **Production-Ready Two-Tier Application Architecture with Auto-Scaling**

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Components](#components)
3. [Documentation](#documentation)
4. [Quick Start](#quick-start)
5. [Deployment Options](#deployment-options)

---

## 🎯 Architecture Overview

This is a **production-ready two-tier architecture** on AWS that combines the web and application layers into a single tier, with a separate database tier.

│  │  │  │ MongoDB      │◄─────────┼─►│ MongoDB      │         │ │
│  │  │  │ PRIMARY      │  Replica │  │ SECONDARY    │         │ │
│  │  │  │              │   Set    │  │              │         │ │
│  │  │  └──────────────┘          │  └──────────────┘         │ │
│  │  │                             │                           │ │
│  │  └─────────────────────────────┴───────────────────────── │ │
│  │                                                             │ │
│  └─────────────────────────────────────────────────────────── │ │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

---

## 🧩 Components

### Tier 1: Web/Application Tier
- **Load Balancer**: Application Load Balancer (ALB) for traffic distribution
- **Auto-Scaling Group**: 2-10 instances based on CPU/memory metrics
- **Web Server**: NGINX for static content and reverse proxy
- **Application**: Node.js/Python backend application
- **Subnets**: Public subnets in 2 Availability Zones
- **Security**: Security groups, SSL/TLS termination

### Tier 2: Database Tier
- **Database**: MongoDB Replica Set (1 Primary + 1 Secondary)
- **High Availability**: Multi-AZ deployment
- **Subnets**: Private subnets (no internet access)
- **Security**: Restricted access from app tier only
- **Backup**: Automated backups and point-in-time recovery

---

## 📚 Documentation

### Step-by-Step Guides

1. **[Architecture Overview](./docs/00-ARCHITECTURE-OVERVIEW.md)**
   - Detailed architecture explanation
   - Traffic flow diagrams
   - Component interactions

2. **[Infrastructure Setup](./docs/01-INFRASTRUCTURE-SETUP.md)**
   - VPC creation
   - Subnets and routing
   - Security groups
   - Load balancer setup

3. **[Database Tier Setup](./docs/02-DATABASE-TIER-SETUP.md)**
   - MongoDB installation
   - Replica set configuration
   - Security hardening
   - Backup configuration

4. **[Web/App Tier Setup](./docs/03-WEBAPP-TIER-SETUP.md)**
   - NGINX configuration
   - Application deployment
   - Auto-scaling setup
   - Health checks

5. **[Auto-Scaling Configuration](./docs/04-AUTOSCALING-SETUP.md)**
   - Scaling policies
   - CloudWatch alarms
   - Launch templates
   - Testing auto-scaling

6. **[Web UI Setup Steps](./docs/05-WEB-UI-STEPS.md)**
   - AWS Console step-by-step guide
   - Screenshots and explanations
   - Configuration details

7. **[Testing & Verification](./docs/06-TESTING-VERIFICATION.md)**
   - Load testing
   - Failover testing
   - Monitoring setup
   - Performance validation

---

## 🚀 Quick Start

### Option 1: Terraform (Recommended)

```bash
# Navigate to terraform directory
cd terraform/environments/dev

# Initialize Terraform
terraform init

# Review the plan
terraform plan

# Deploy infrastructure
terraform apply

# Get outputs
terraform output
```

### Option 2: Manual Setup via AWS CLI

```bash
# Run the setup script
./scripts/deploy-infrastructure.sh

# Deploy database
./scripts/setup-mongodb.sh

# Deploy application
./scripts/deploy-application.sh
```

### Option 3: AWS Console (Web UI)

Follow the detailed guide: [Web UI Setup Steps](./docs/05-WEB-UI-STEPS.md)

---

## 🛠️ Deployment Options

| Method | Time | Complexity | Best For |
|--------|------|------------|----------|
| **Terraform** | 15-20 min | Medium | Production, IaC, Automation |
| **AWS CLI** | 30-40 min | Medium | Learning, Custom setups |
| **Web Console** | 45-60 min | Low | Beginners, Visual learners |

---

## 📊 Architecture Specifications

### Network Configuration

| Component | CIDR Block | Type | Purpose |
|-----------|------------|------|---------|
| VPC | 10.0.0.0/16 | - | Main network |
| Public Subnet 1 | 10.0.1.0/24 | Public | Web/App AZ-1 |
| Public Subnet 2 | 10.0.2.0/24 | Public | Web/App AZ-2 |
| Private Subnet 1 | 10.0.11.0/24 | Private | Database AZ-1 |
| Private Subnet 2 | 10.0.12.0/24 | Private | Database AZ-2 |

### Instance Specifications

| Tier | Instance Type | Min | Max | Desired |
|------|---------------|-----|-----|---------|
| Web/App | t3.medium | 2 | 10 | 2 |
| Database | t3.large | 2 | 2 | 2 |

### Auto-Scaling Triggers

| Metric | Scale Out | Scale In |
|--------|-----------|----------|
| CPU Utilization | > 70% | < 30% |
| Memory Utilization | > 75% | < 35% |
| Request Count | > 1000/min | < 200/min |

---

## 🔒 Security Features

- ✅ VPC isolation
- ✅ Security groups with least privilege
- ✅ Private database tier (no internet access)
- ✅ SSL/TLS encryption
- ✅ Encrypted EBS volumes
- ✅ IAM roles and policies
- ✅ CloudWatch logging
- ✅ AWS WAF integration (optional)

---

## 📈 Monitoring & Alerts

- **CloudWatch Metrics**: CPU, Memory, Network, Disk
- **CloudWatch Alarms**: Auto-scaling triggers, health checks
- **CloudWatch Logs**: Application logs, access logs, error logs
- **CloudWatch Dashboards**: Real-time monitoring

---

## 💰 Cost Estimation

### Monthly Cost (us-east-1)

| Component | Quantity | Unit Cost | Total |
|-----------|----------|-----------|-------|
| EC2 (t3.medium) | 2-10 | $30/month | $60-$300 |
| EC2 (t3.large) | 2 | $60/month | $120 |
| ALB | 1 | $16/month | $16 |
| EBS (100GB) | 12 | $10/month | $120 |
| Data Transfer | ~100GB | $9/month | $9 |
| **Total** | - | - | **$325-$565** |

> **Note**: Costs vary based on usage, region, and scaling

---

## 🎯 Key Features

- ✅ **High Availability**: Multi-AZ deployment
- ✅ **Auto-Scaling**: Automatic capacity adjustment
- ✅ **Load Balancing**: Even traffic distribution
- ✅ **Database Replication**: MongoDB replica set
- ✅ **Security**: Multi-layer security controls
- ✅ **Monitoring**: Comprehensive CloudWatch integration
- ✅ **Infrastructure as Code**: Terraform modules
- ✅ **Cost-Optimized**: Right-sized instances

---

## 📖 Additional Resources

- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [MongoDB Production Notes](https://docs.mongodb.com/manual/administration/production-notes/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)

---

## 🤝 Support

For issues or questions:
1. Check the [Troubleshooting Guide](./docs/06-TESTING-VERIFICATION.md#troubleshooting)
2. Review CloudWatch logs
3. Verify security group rules

---

**Ready to deploy? Start with [Infrastructure Setup](./docs/01-INFRASTRUCTURE-SETUP.md)! 🚀**
