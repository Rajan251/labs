# 🏗️ AWS Tier-2 Architecture - Web UI Setup Guide

> **Production-Ready Two-Tier Architecture with NAT Gateway and Client VPN**

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Network Configuration](#network-configuration)
3. [Components](#components)
4. [Documentation](#documentation)
5. [Prerequisites](#prerequisites)
6. [Quick Start](#quick-start)

---

## 🎯 Architecture Overview

This is a **production-ready two-tier architecture** on AWS configured entirely through the **AWS Web Console (UI)**. The architecture includes:

- **Public Tier**: EC2 instances in public subnets with internet access via Internet Gateway
- **Private Tier**: EC2 instances in private subnets with outbound internet access via NAT Gateway
- **Secure Access**: AWS Client VPN for SSH access to private instances

```
┌─────────────────────────────────────────────────────────────────────┐
│                        VPC: 10.0.0.0/16                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                   Internet Gateway                          │    │
│  └────────────────────┬───────────────────────────────────────┘    │
│                       │                                              │
│  ┌────────────────────┴──────────────────────────────────────┐     │
│  │              PUBLIC SUBNETS                                │     │
│  ├────────────────────────────────────────────────────────────┤     │
│  │  AZ-a (us-east-1a)         AZ-b (us-east-1b)              │     │
│  │  10.0.1.0/24               10.0.2.0/24                     │     │
│  │  ┌──────────────┐          ┌──────────────┐               │     │
│  │  │ NAT Gateway  │          │              │               │     │
│  │  │ + Elastic IP │          │              │               │     │
│  │  └──────────────┘          └──────────────┘               │     │
│  └────────────────────┬──────────────────────────────────────┘     │
│                       │                                              │
│                       │ (NAT Gateway Route)                          │
│                       │                                              │
│  ┌────────────────────┴──────────────────────────────────────┐     │
│  │              PRIVATE SUBNETS                               │     │
│  ├────────────────────────────────────────────────────────────┤     │
│  │  AZ-a (us-east-1a)         AZ-b (us-east-1b)              │     │
│  │  10.0.3.0/24               10.0.4.0/24                     │     │
│  │  ┌──────────────┐          ┌──────────────┐               │     │
│  │  │ EC2 Instance │          │ EC2 Instance │               │     │
│  │  │ (Private)    │          │ (Private)    │               │     │
│  │  └──────────────┘          └──────────────┘               │     │
│  └────────────────────────────────────────────────────────────┘     │
│                       ▲                                              │
│                       │                                              │
│  ┌────────────────────┴──────────────────────────────────────┐     │
│  │              AWS Client VPN Endpoint                       │     │
│  │              (Secure SSH Access)                           │     │
│  └────────────────────────────────────────────────────────────┘     │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🌐 Network Configuration

| Component | CIDR Block | Availability Zone | Type | Purpose |
|-----------|------------|-------------------|------|---------|
| **VPC** | 10.0.0.0/16 | - | - | Main network |
| **Public Subnet 1** | 10.0.1.0/24 | us-east-1a | Public | NAT Gateway, Public resources |
| **Public Subnet 2** | 10.0.2.0/24 | us-east-1b | Public | High availability |
| **Private Subnet 1** | 10.0.3.0/24 | us-east-1a | Private | EC2 instances |
| **Private Subnet 2** | 10.0.4.0/24 | us-east-1b | Private | EC2 instances |

### IP Address Allocation

- **Total IPs**: 65,536 (10.0.0.0/16)
- **Public Subnet 1**: 251 usable IPs
- **Public Subnet 2**: 251 usable IPs
- **Private Subnet 1**: 251 usable IPs
- **Private Subnet 2**: 251 usable IPs

---

## 🧩 Components

### Network Infrastructure
- ✅ **VPC**: Isolated network environment (10.0.0.0/16)
- ✅ **Internet Gateway**: Internet access for public subnets
- ✅ **NAT Gateway**: Outbound internet for private subnets
- ✅ **Elastic IP**: Static IP for NAT Gateway
- ✅ **Route Tables**: Public and private routing

### Compute Resources
- ✅ **EC2 Instances**: Virtual machines in private subnets
- ✅ **Security Groups**: Firewall rules for instances

### Secure Access
- ✅ **AWS Client VPN**: Secure VPN access to private resources
- ✅ **VPN Certificates**: Mutual authentication

---

## 📚 Documentation

### Step-by-Step Web UI Guides

1. **[VPC Setup](./docs/01-VPC-SETUP.md)**
   - Create VPC with 10.0.0.0/16 CIDR
   - Enable DNS hostnames and resolution
   - Configure VPC settings

2. **[Subnet Configuration](./docs/02-SUBNET-CONFIGURATION.md)**
   - Create 2 public subnets (10.0.1.0/24, 10.0.2.0/24)
   - Create 2 private subnets (10.0.3.0/24, 10.0.4.0/24)
   - Configure availability zones
   - Enable auto-assign public IP

3. **[Internet Gateway & NAT Gateway](./docs/03-INTERNET-GATEWAY-NAT.md)**
   - Create and attach Internet Gateway
   - Allocate Elastic IP
   - Create NAT Gateway in Public Subnet 1

4. **[Route Tables](./docs/04-ROUTE-TABLES.md)**
   - Create public route table (IGW route)
   - Create private route table (NAT route)
   - Associate subnets with route tables

5. **[Security Groups](./docs/05-SECURITY-GROUPS.md)**
   - Create security groups for EC2 instances
   - Configure inbound/outbound rules
   - Security best practices

6. **[EC2 Deployment](./docs/06-EC2-DEPLOYMENT.md)**
   - Launch EC2 instances in private subnets
   - Configure instance settings
   - Key pair management

7. **[Client VPN Setup](./docs/07-CLIENT-VPN-SETUP.md)**
   - Generate VPN certificates
   - Create Client VPN endpoint
   - Configure authorization rules
   - Connect and test VPN

8. **[Testing & Verification](./docs/08-TESTING-VERIFICATION.md)**
   - Verify network connectivity
   - Test NAT Gateway
   - Test VPN access
   - Troubleshooting guide

### Load Balancing & Auto-Scaling Guides

9. **[Load Balancer Setup](./docs/09-LOAD-BALANCER-SETUP.md)**
   - Create Application Load Balancer
   - Configure Target Groups
   - Set up health checks
   - Test load balancing

10. **[Launch Template](./docs/10-LAUNCH-TEMPLATE.md)**
   - Create Launch Template
   - Configure user data
   - Set up auto-configuration
   - Version management

11. **[Auto Scaling Group](./docs/11-AUTO-SCALING-GROUP.md)**
   - Create Auto Scaling Group
   - Configure capacity (2-10 instances)
   - Multi-AZ distribution
   - Health check integration

12. **[Scaling Policies](./docs/12-SCALING-POLICIES.md)**
   - Target tracking policies
   - CPU-based scaling
   - Request-based scaling
   - Scheduled scaling

13. **[ALB & Auto Scaling Testing](./docs/13-ALB-AUTOSCALING-TESTING.md)**
   - Load balancer testing
   - Scale-out/scale-in testing
   - Load testing procedures
   - Performance validation

---

## 🔧 Prerequisites

### AWS Account Requirements
- ✅ Active AWS account
- ✅ IAM user with appropriate permissions
- ✅ Access to AWS Management Console

### Required Permissions
- EC2 full access
- VPC full access
- Certificate Manager access (for VPN)

### Local Tools (for VPN setup)
- OpenSSL (for certificate generation)
- AWS VPN Client (for connecting to VPN)

---

## 🚀 Quick Start

### Setup Time Estimate
⏱️ **Total Time**: 60-90 minutes

| Step | Time | Difficulty |
|------|------|------------|
| VPC & Subnets | 10 min | Easy |
| IGW & NAT Gateway | 10 min | Easy |
| Route Tables | 10 min | Easy |
| Security Groups | 10 min | Medium |
| EC2 Deployment | 15 min | Easy |
| Client VPN | 30 min | Medium |
| Testing | 10 min | Easy |

### Step-by-Step Process

1. **Start Here**: [VPC Setup](./docs/01-VPC-SETUP.md)
2. **Follow in Order**: Complete each guide sequentially
3. **Save Resource IDs**: Use the [Quick Reference](./QUICK_REFERENCE.md) to track IDs
4. **Test Each Step**: Verify before moving to next step

---

## 🔒 Security Features

- ✅ **Network Isolation**: Private subnets have no direct internet access
- ✅ **NAT Gateway**: Secure outbound internet for updates
- ✅ **Security Groups**: Least privilege firewall rules
- ✅ **Client VPN**: Encrypted VPN tunnel for SSH access
- ✅ **Multi-AZ**: High availability across availability zones
- ✅ **No Bastion Host**: VPN eliminates need for jump servers

---

## 💰 Cost Estimation

### Monthly Cost (us-east-1)

| Component | Quantity | Unit Cost | Total |
|-----------|----------|-----------|-------|
| NAT Gateway | 1 | $32/month | $32 |
| NAT Gateway Data | 100GB | $0.045/GB | $4.50 |
| Elastic IP | 1 | $3.60/month | $3.60 |
| **Application Load Balancer** | **1** | **$16/month** | **$16** |
| **ALB LCU Hours** | **Variable** | **$0.008/hour** | **~$6** |
| EC2 (t3.micro) | 2-10 | $7.50/month | $15-$75 |
| Client VPN Endpoint | 1 | $72/month | $72 |
| Client VPN Connections | 2 | $0.05/hour | $72 |
| EBS Storage (8GB) | 2-10 | $0.80/month | $1.60-$8 |
| **Total** | - | - | **~$222-$289/month** |

> **Note**: Costs vary based on usage, region, and data transfer. Client VPN is the most expensive component.

### Cost Optimization Tips
- 💡 Use VPN only when needed (hourly billing)
- 💡 Consider Session Manager instead of VPN for lower cost
- 💡 Use smaller instance types for testing
- 💡 Delete NAT Gateway when not in use (recreate when needed)

---

## 🎯 Key Features

- ✅ **Web UI Only**: No CLI or Terraform required
- ✅ **High Availability**: Multi-AZ deployment
- ✅ **Secure Access**: VPN-based SSH access
- ✅ **Internet Access**: NAT Gateway for private instances
- ✅ **Production Ready**: Best practices implemented
- ✅ **Well Documented**: Step-by-step screenshots and instructions

---

## 📖 Additional Resources

- [AWS VPC Documentation](https://docs.aws.amazon.com/vpc/)
- [AWS NAT Gateway Guide](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html)
- [AWS Client VPN Guide](https://docs.aws.amazon.com/vpn/latest/clientvpn-admin/)
- [Quick Reference Guide](./QUICK_REFERENCE.md)

---

## 🤝 Support

For issues or questions:
1. Check the [Testing & Verification Guide](./docs/08-TESTING-VERIFICATION.md)
2. Review the [Quick Reference](./QUICK_REFERENCE.md)
3. Verify security group rules and route tables

---

**Ready to start? Begin with [VPC Setup](./docs/01-VPC-SETUP.md)! 🚀**
