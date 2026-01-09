# AWS Three-Tier Architecture with MongoDB Replica Set

## 🏗️ Complete Deployment Guide

> **Production-ready three-tier application on AWS with MongoDB high availability**

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Infrastructure Setup](#infrastructure-setup)
4. [Database Tier Setup](#database-tier-setup)
5. [Application Tier Setup](#application-tier-setup)
6. [Web Tier Setup](#web-tier-setup)
7. [Load Balancer Configuration](#load-balancer-configuration)
8. [Security Configuration](#security-configuration)
9. [Monitoring & Logging](#monitoring--logging)
10. [Testing & Validation](#testing--validation)

---

## Architecture Overview

### 🎯 Three-Tier Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           AWS CLOUD (VPC)                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │                    🌐 WEB TIER (Public Subnet)                  │    │
│  ├────────────────────────────────────────────────────────────────┤    │
│  │                                                                 │    │
│  │  ┌──────────────────┐                                          │    │
│  │  │ Application Load │  ← HTTPS (443)                           │    │
│  │  │    Balancer      │  ← HTTP (80) → Redirect to HTTPS         │    │
│  │  └────────┬─────────┘                                          │    │
│  │           │                                                     │    │
│  │           ├──────────┬──────────┬──────────┐                   │    │
│  │           ▼          ▼          ▼          ▼                   │    │
│  │     ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │    │
│  │     │ NGINX 1 │ │ NGINX 2 │ │ NGINX 3 │ │ NGINX 4 │          │    │
│  │     │  (AZ-1) │ │  (AZ-2) │ │  (AZ-1) │ │  (AZ-2) │          │    │
│  │     │ Web UI  │ │ Web UI  │ │ Web UI  │ │ Web UI  │          │    │
│  │     └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘          │    │
│  │          │           │           │           │                 │    │
│  └──────────┼───────────┼───────────┼───────────┼─────────────────┘    │
│             │           │           │           │                      │
│  ┌──────────┼───────────┼───────────┼───────────┼─────────────────┐    │
│  │          │           │           │           │                 │    │
│  │    🔧 APPLICATION TIER (Private Subnet)                        │    │
│  ├────────────────────────────────────────────────────────────────┤    │
│  │          │           │           │           │                 │    │
│  │          ▼           ▼           ▼           ▼                 │    │
│  │     ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │    │
│  │     │ App     │ │ App     │ │ App     │ │ App     │          │    │
│  │     │ Server  │ │ Server  │ │ Server  │ │ Server  │          │    │
│  │     │  (AZ-1) │ │  (AZ-2) │ │  (AZ-1) │ │  (AZ-2) │          │    │
│  │     │ Node.js │ │ Node.js │ │ Node.js │ │ Node.js │          │    │
│  │     │ Python  │ │ Python  │ │ Python  │ │ Python  │          │    │
│  │     └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘          │    │
│  │          │           │           │           │                 │    │
│  └──────────┼───────────┼───────────┼───────────┼─────────────────┘    │
│             │           │           │           │                      │
│  ┌──────────┼───────────┼───────────┼───────────┼─────────────────┐    │
│  │          │           │           │           │                 │    │
│  │    💾 DATABASE TIER (Private Subnet - Isolated)               │    │
│  ├────────────────────────────────────────────────────────────────┤    │
│  │          │           │           │           │                 │    │
│  │          └───────────┴───────────┴───────────┘                 │    │
│  │                      │                                         │    │
│  │                      ▼                                         │    │
│  │          ┌───────────────────────┐                            │    │
│  │          │  MongoDB Replica Set  │                            │    │
│  │          └───────────────────────┘                            │    │
│  │                      │                                         │    │
│  │          ┌───────────┼───────────┐                            │    │
│  │          ▼           ▼           ▼                            │    │
│  │     ┌─────────┐ ┌─────────┐ ┌─────────┐                      │    │
│  │     │ PRIMARY │ │SECONDARY│ │SECONDARY│                      │    │
│  │     │ mongo-1 │ │ mongo-2 │ │ mongo-3 │                      │    │
│  │     │  (AZ-1) │ │  (AZ-2) │ │  (AZ-1) │                      │    │
│  │     │ t3.large│ │ t3.large│ │ t3.large│                      │    │
│  │     │ 100GB   │ │ 100GB   │ │ 100GB   │                      │    │
│  │     │ EBS SSD │ │ EBS SSD │ │ EBS SSD │                      │    │
│  │     └─────────┘ └─────────┘ └─────────┘                      │    │
│  │                                                                │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │                    🔐 SECURITY & MONITORING                     │    │
│  ├────────────────────────────────────────────────────────────────┤    │
│  │  • Security Groups (Firewall Rules)                            │    │
│  │  • Network ACLs                                                │    │
│  │  • AWS Certificate Manager (SSL/TLS)                           │    │
│  │  • CloudWatch (Monitoring & Logs)                              │    │
│  │  • AWS Backup (Automated Backups)                              │    │
│  │  • Route 53 (DNS)                                              │    │
│  │  • NAT Gateway (Outbound Internet for Private Subnets)         │    │
│  │  • Bastion Host (SSH Access)                                   │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Architecture Components

### **Tier 1: Web Tier (Public Subnet)**
- **Purpose**: Serve static content, handle HTTPS, reverse proxy
- **Components**:
  - Application Load Balancer (ALB)
  - 4x NGINX servers (2 per AZ)
  - Auto Scaling Group
  - CloudFront CDN (optional)
- **Availability Zones**: 2 (us-east-1a, us-east-1b)

### **Tier 2: Application Tier (Private Subnet)**
- **Purpose**: Business logic, API endpoints, data processing
- **Components**:
  - 4x Application servers (Node.js/Python)
  - Auto Scaling Group
  - Internal Load Balancer
- **Availability Zones**: 2 (us-east-1a, us-east-1b)

### **Tier 3: Database Tier (Private Subnet - Isolated)**
- **Purpose**: Data persistence with high availability
- **Components**:
  - 3x MongoDB replica set (PRIMARY + 2 SECONDARYs)
  - EBS volumes (gp3 SSD)
  - Automated backups to S3
- **Availability Zones**: 2 (us-east-1a, us-east-1b)

---

## Prerequisites

### ✅ AWS Account Requirements

- [ ] AWS Account with admin access
- [ ] AWS CLI installed and configured
- [ ] SSH key pair created
- [ ] Domain name (optional, for custom domain)
- [ ] AWS Budget alert configured (recommended)

### ✅ Local Tools Required

```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Verify installation
aws --version

# Configure AWS CLI
aws configure
# AWS Access Key ID: YOUR_ACCESS_KEY
# AWS Secret Access Key: YOUR_SECRET_KEY
# Default region name: us-east-1
# Default output format: json

# Install Terraform (optional, for IaC)
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/

# Verify Terraform
terraform --version
```

### ✅ Estimated AWS Costs

| Component | Instance Type | Quantity | Monthly Cost (USD) |
|-----------|--------------|----------|-------------------|
| **Web Tier** | t3.small | 4 | ~$60 |
| **App Tier** | t3.medium | 4 | ~$120 |
| **Database Tier** | t3.large | 3 | ~$180 |
| **Load Balancer** | ALB | 1 | ~$25 |
| **EBS Storage** | gp3 100GB | 3 | ~$30 |
| **Data Transfer** | - | - | ~$50 |
| **NAT Gateway** | - | 2 | ~$60 |
| **Backups (S3)** | - | - | ~$20 |
| **Total** | | | **~$545/month** |

> 💡 **Cost Optimization**: Use Reserved Instances for 40-60% savings, or Spot Instances for non-production.

---

## 📁 Project Structure

```
aws-three-tier-setup/
├── infrastructure/
│   ├── terraform/              # Infrastructure as Code
│   │   ├── main.tf
│   │   ├── vpc.tf
│   │   ├── security-groups.tf
│   │   ├── ec2.tf
│   │   └── outputs.tf
│   └── cloudformation/         # Alternative IaC
│       └── stack.yaml
├── scripts/
│   ├── setup-vpc.sh           # VPC creation script
│   ├── setup-database.sh      # MongoDB setup
│   ├── setup-application.sh   # App server setup
│   ├── setup-web.sh           # Web server setup
│   └── deploy.sh              # Complete deployment
├── database/
│   ├── mongod.conf            # MongoDB configuration
│   ├── init-replica-set.js    # Replica set initialization
│   └── backup.sh              # Backup script
├── application/
│   ├── app.js                 # Node.js application
│   ├── requirements.txt       # Python dependencies
│   ├── .env.production        # Environment variables
│   └── ecosystem.config.js    # PM2 configuration
├── web-ui/
│   ├── index.html             # Main page
│   ├── css/
│   ├── js/
│   └── nginx.conf             # NGINX configuration
└── docs/
    ├── README.md              # This file
    ├── SETUP_GUIDE.md         # Step-by-step setup
    ├── ARCHITECTURE.md        # Detailed architecture
    └── TROUBLESHOOTING.md     # Common issues
```

---

## 🚀 Quick Start

### Option 1: Automated Deployment (Recommended)

```bash
# Clone repository
cd /home/rk/Documents/labs/ha-design-lab/aws-three-tier-setup

# Run automated deployment
./scripts/deploy.sh

# Follow prompts:
# - AWS Region: us-east-1
# - Environment: production
# - Domain: example.com (optional)
```

### Option 2: Manual Step-by-Step

Follow the detailed guides in order:

1. **[Infrastructure Setup](./docs/01-INFRASTRUCTURE-SETUP.md)** - VPC, Subnets, Security Groups
2. **[Database Tier Setup](./docs/02-DATABASE-TIER-SETUP.md)** - MongoDB Replica Set
3. **[Application Tier Setup](./docs/03-APPLICATION-TIER-SETUP.md)** - Node.js/Python Servers
4. **[Web Tier Setup](./docs/04-WEB-TIER-SETUP.md)** - NGINX + Load Balancer
5. **[Security Configuration](./docs/05-SECURITY-CONFIGURATION.md)** - SSL, Firewall, IAM
6. **[Monitoring Setup](./docs/06-MONITORING-SETUP.md)** - CloudWatch, Alarms
7. **[Testing & Validation](./docs/07-TESTING-VALIDATION.md)** - End-to-end tests

---

## 🎯 Key Features

✅ **High Availability**: Multi-AZ deployment, survives AZ failure  
✅ **Auto Scaling**: Scales based on CPU/memory usage  
✅ **Load Balancing**: Distributes traffic across instances  
✅ **Security**: Private subnets, security groups, SSL/TLS  
✅ **Monitoring**: CloudWatch metrics, alarms, logs  
✅ **Backup**: Automated daily backups to S3  
✅ **Disaster Recovery**: Cross-region replication (optional)  
✅ **Cost Optimized**: Right-sized instances, reserved pricing  

---

## 📊 Traffic Flow

```
User Request
    ↓
Route 53 (DNS)
    ↓
CloudFront (CDN - Optional)
    ↓
Application Load Balancer (HTTPS)
    ↓
NGINX Web Servers (Static Content + Reverse Proxy)
    ↓
Application Servers (API + Business Logic)
    ↓
MongoDB Replica Set (Data Persistence)
    ↓
Response back to User
```

---

## 🔐 Security Layers

1. **Network Security**
   - VPC with public/private subnets
   - Security groups (stateful firewall)
   - Network ACLs (stateless firewall)
   - NAT Gateway for outbound traffic

2. **Application Security**
   - SSL/TLS encryption (HTTPS)
   - MongoDB authentication
   - Environment variables for secrets
   - AWS Secrets Manager integration

3. **Access Control**
   - IAM roles and policies
   - Bastion host for SSH access
   - No direct internet access to app/db tiers
   - MFA for AWS console

4. **Data Security**
   - Encrypted EBS volumes
   - Encrypted backups in S3
   - MongoDB encryption at rest (optional)
   - VPC Flow Logs

---

## 📈 Monitoring & Alerts

### CloudWatch Metrics

- **Web Tier**: Request count, latency, error rate
- **App Tier**: CPU, memory, disk usage
- **Database Tier**: Replication lag, connections, disk I/O

### Alarms

- High CPU (> 80% for 5 minutes)
- High memory (> 85%)
- Replication lag (> 10 seconds)
- Disk space (< 20% free)
- Failed health checks

---

## 🧪 Testing Checklist

- [ ] VPC and subnets created
- [ ] Security groups configured
- [ ] MongoDB replica set initialized
- [ ] Application servers deployed
- [ ] Web servers deployed
- [ ] Load balancer configured
- [ ] SSL certificate installed
- [ ] DNS configured
- [ ] Auto scaling tested
- [ ] Failover tested (kill PRIMARY)
- [ ] Backup and restore tested
- [ ] Monitoring alarms tested
- [ ] Load testing completed

---

## 📚 Next Steps

1. **Read the detailed setup guides** in `docs/` directory
2. **Review the Terraform configuration** in `infrastructure/terraform/`
3. **Customize the application** in `application/` directory
4. **Deploy the infrastructure** using automated scripts
5. **Configure monitoring** and set up alerts
6. **Test failover scenarios**
7. **Set up CI/CD pipeline** (optional)

---

## 🆘 Support & Troubleshooting

- **Setup Issues**: See [TROUBLESHOOTING.md](./docs/TROUBLESHOOTING.md)
- **Architecture Questions**: See [ARCHITECTURE.md](./docs/ARCHITECTURE.md)
- **AWS Documentation**: https://docs.aws.amazon.com/
- **MongoDB on AWS**: https://docs.mongodb.com/manual/administration/install-on-linux/

---

## 📝 Summary

This three-tier architecture provides:

- **Scalability**: Auto-scales based on demand
- **Reliability**: Multi-AZ deployment with 99.99% uptime
- **Security**: Multiple layers of security controls
- **Performance**: Load balanced with CDN support
- **Maintainability**: Infrastructure as Code, automated deployments
- **Cost-Effective**: Optimized instance sizing and reserved pricing

**Ready to deploy? Start with the [Infrastructure Setup Guide](./docs/01-INFRASTRUCTURE-SETUP.md)!**

---

**Created**: 2025-12-23  
**AWS Region**: us-east-1  
**Estimated Setup Time**: 2-3 hours  
**Difficulty**: Intermediate to Advanced
