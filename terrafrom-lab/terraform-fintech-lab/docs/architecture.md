# Architecture Overview: PayFlow Solutions Infrastructure

## High-Level Architecture

This document provides detailed architecture diagrams and explanations for the PayFlow Solutions payment processing platform infrastructure.

## Network Architecture

### Complete Infrastructure Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Internet / Users                               │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   Route 53 (DNS)        │
                    │   payflow.example.com   │
                    └────────────┬────────────┘
                                 │
┌────────────────────────────────▼─────────────────────────────────────────────┐
│                         AWS Region: us-east-1                                │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                    VPC: 10.0.0.0/16                                    │ │
│  │                                                                        │ │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │ │
│  │  │              Public Subnets (Internet-facing)                    │ │ │
│  │  │                                                                  │ │ │
│  │  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │ │ │
│  │  │  │   AZ-1a         │  │   AZ-1b         │  │   AZ-1c         │ │ │ │
│  │  │  │  10.0.1.0/24    │  │  10.0.2.0/24    │  │  10.0.3.0/24    │ │ │ │
│  │  │  │                 │  │                 │  │                 │ │ │ │
│  │  │  │  ┌───────────┐  │  │  ┌───────────┐  │  │  ┌───────────┐  │ │ │ │
│  │  │  │  │    ALB    │◄─┼──┼──┤    ALB    │◄─┼──┼──┤    ALB    │  │ │ │ │
│  │  │  │  │ (Target)  │  │  │  │ (Target)  │  │  │  │ (Target)  │  │ │ │ │
│  │  │  │  └───────────┘  │  │  └───────────┘  │  │  └───────────┘  │ │ │ │
│  │  │  │                 │  │                 │  │                 │ │ │ │
│  │  │  │  ┌───────────┐  │  │  ┌───────────┐  │  │  ┌───────────┐  │ │ │ │
│  │  │  │  │    NAT    │  │  │  │    NAT    │  │  │  │    NAT    │  │ │ │ │
│  │  │  │  │  Gateway  │  │  │  │  Gateway  │  │  │  │  Gateway  │  │ │ │ │
│  │  │  │  └─────┬─────┘  │  │  └─────┬─────┘  │  │  └─────┬─────┘  │ │ │ │
│  │  │  │        │        │  │        │        │  │        │        │ │ │ │
│  │  │  │  ┌─────┴─────┐  │  │                 │  │                 │ │ │ │
│  │  │  │  │  Bastion  │  │  │                 │  │                 │ │ │ │
│  │  │  │  │   Host    │  │  │                 │  │                 │ │ │ │
│  │  │  │  └───────────┘  │  │                 │  │                 │ │ │ │
│  │  │  └─────────────────┘  └─────────────────┘  └─────────────────┘ │ │ │
│  │  └──────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                        │ │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │ │
│  │  │              Private Subnets (Application Tier)                 │ │ │
│  │  │                                                                  │ │ │
│  │  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │ │ │
│  │  │  │   AZ-1a         │  │   AZ-1b         │  │   AZ-1c         │ │ │ │
│  │  │  │  10.0.11.0/24   │  │  10.0.12.0/24   │  │  10.0.13.0/24   │ │ │ │
│  │  │  │                 │  │                 │  │                 │ │ │ │
│  │  │  │  ┌───────────┐  │  │  ┌───────────┐  │  │  ┌───────────┐  │ │ │ │
│  │  │  │  │   EC2     │  │  │  │   EC2     │  │  │  │   EC2     │  │ │ │ │
│  │  │  │  │ Instance  │  │  │  │ Instance  │  │  │  │ Instance  │  │ │ │ │
│  │  │  │  │  (ASG)    │  │  │  │  (ASG)    │  │  │  │  (ASG)    │  │ │ │ │
│  │  │  │  │           │  │  │  │           │  │  │  │           │  │ │ │ │
│  │  │  │  │ Payment   │  │  │  │ Payment   │  │  │  │ Payment   │  │ │ │ │
│  │  │  │  │ API App   │  │  │  │ API App   │  │  │  │ API App   │  │ │ │ │
│  │  │  │  └─────┬─────┘  │  │  └─────┬─────┘  │  │  └─────┬─────┘  │ │ │ │
│  │  │  │        │        │  │        │        │  │        │        │ │ │ │
│  │  │  └────────┼────────┘  └────────┼────────┘  └────────┼────────┘ │ │ │
│  │  └───────────┼──────────────────────┼──────────────────┼──────────┘ │ │
│  │              │                      │                  │            │ │
│  │  ┌───────────┼──────────────────────┼──────────────────┼──────────┐ │ │
│  │  │           │   Database Subnets (Data Tier)          │          │ │ │
│  │  │           │                      │                  │          │ │ │
│  │  │  ┌────────▼────────┐  ┌─────────▼────────┐  ┌──────▼────────┐ │ │ │
│  │  │  │   AZ-1a         │  │   AZ-1b          │  │   AZ-1c       │ │ │ │
│  │  │  │  10.0.21.0/24   │  │  10.0.22.0/24    │  │  10.0.23.0/24 │ │ │ │
│  │  │  │                 │  │                  │  │               │ │ │ │
│  │  │  │  ┌───────────┐  │  │  ┌────────────┐  │  │               │ │ │ │
│  │  │  │  │    RDS    │  │  │  │    RDS     │  │  │               │ │ │ │
│  │  │  │  │  Primary  │◄─┼──┼─►│  Standby   │  │  │               │ │ │ │
│  │  │  │  │ PostgreSQL│  │  │  │ (Multi-AZ) │  │  │               │ │ │ │
│  │  │  │  └───────────┘  │  │  └────────────┘  │  │               │ │ │ │
│  │  │  └─────────────────┘  └──────────────────┘  └───────────────┘ │ │ │
│  │  └──────────────────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                      Supporting AWS Services                           │ │
│  │                                                                        │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐             │ │
│  │  │    S3    │  │CloudWatch│  │   SNS    │  │   IAM    │             │ │
│  │  │  Buckets │  │Monitoring│  │  Alerts  │  │  Roles   │             │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘             │ │
│  │                                                                        │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐                            │ │
│  │  │ Secrets  │  │   VPC    │  │CloudTrail│                            │ │
│  │  │ Manager  │  │Flow Logs │  │  Audit   │                            │ │
│  │  └──────────┘  └──────────┘  └──────────┘                            │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Network Flow Diagrams

### Traffic Flow: Client Request to Application

```
┌──────────┐
│  Client  │
└────┬─────┘
     │ 1. HTTPS Request
     │    (payflow.example.com)
     ▼
┌─────────────┐
│  Route 53   │
│    (DNS)    │
└────┬────────┘
     │ 2. Resolves to ALB DNS
     ▼
┌──────────────────────┐
│ Application Load     │
│ Balancer (ALB)       │
│ Public Subnets       │
│ - Health Checks      │
│ - SSL Termination    │
└────┬─────────────────┘
     │ 3. Routes to healthy target
     │    (Round-robin / Least outstanding)
     ▼
┌──────────────────────┐
│ EC2 Instance         │
│ Private Subnet       │
│ Auto Scaling Group   │
│ - Payment API        │
│ - Port 8080          │
└────┬─────────────────┘
     │ 4. Database query
     │    (via private subnet routing)
     ▼
┌──────────────────────┐
│ RDS PostgreSQL       │
│ Database Subnet      │
│ Multi-AZ             │
│ - Port 5432          │
└──────────────────────┘
```

### Outbound Internet Access (from Private Subnet)

```
┌──────────────────────┐
│ EC2 Instance         │
│ Private Subnet       │
│ 10.0.11.5            │
└────┬─────────────────┘
     │ 1. Outbound request
     │    (e.g., API call, software update)
     ▼
┌──────────────────────┐
│ Route Table          │
│ Private Subnet       │
│ 0.0.0.0/0 → NAT-GW   │
└────┬─────────────────┘
     │ 2. Routes to NAT Gateway
     ▼
┌──────────────────────┐
│ NAT Gateway          │
│ Public Subnet        │
│ Elastic IP attached  │
└────┬─────────────────┘
     │ 3. Source NAT translation
     ▼
┌──────────────────────┐
│ Internet Gateway     │
│ VPC-level            │
└────┬─────────────────┘
     │ 4. To Internet
     ▼
   Internet
```

## Component Details

### 1. VPC Configuration

| Component | Configuration | Purpose |
|-----------|--------------|---------|
| **VPC CIDR** | 10.0.0.0/16 | 65,536 IP addresses |
| **Public Subnets** | 10.0.1.0/24, 10.0.2.0/24, 10.0.3.0/24 | Internet-facing resources |
| **Private Subnets** | 10.0.11.0/24, 10.0.12.0/24, 10.0.13.0/24 | Application servers |
| **Database Subnets** | 10.0.21.0/24, 10.0.22.0/24, 10.0.23.0/24 | Database instances |
| **Availability Zones** | us-east-1a, us-east-1b, us-east-1c | Multi-AZ for HA |

### 2. Compute Layer

```
┌─────────────────────────────────────────────────────┐
│           Auto Scaling Group (ASG)                  │
│                                                     │
│  Configuration:                                     │
│  • Min Size: 2 instances                           │
│  • Desired: 3 instances                            │
│  • Max Size: 10 instances                          │
│                                                     │
│  Launch Template:                                   │
│  • AMI: Amazon Linux 2023                          │
│  • Instance Type: t3.small (prod), t3.micro (dev)  │
│  • User Data: Bootstrap script                     │
│  • IAM Role: EC2-PaymentAPI-Role                   │
│  • Security Group: app-sg                          │
│                                                     │
│  Scaling Policies:                                  │
│  • Target Tracking: CPU 70%                        │
│  • Step Scaling: Rapid scale-out on high load     │
│  • Scheduled: Scale up before peak hours           │
└─────────────────────────────────────────────────────┘
```

### 3. Load Balancing

```
┌─────────────────────────────────────────────────────┐
│      Application Load Balancer (ALB)                │
│                                                     │
│  Listeners:                                         │
│  • Port 80 (HTTP) → Redirect to 443                │
│  • Port 443 (HTTPS) → Target Group                 │
│                                                     │
│  Target Group:                                      │
│  • Protocol: HTTP                                   │
│  • Port: 8080                                       │
│  • Health Check: /health                           │
│    - Interval: 30s                                  │
│    - Timeout: 5s                                    │
│    - Healthy threshold: 2                          │
│    - Unhealthy threshold: 3                        │
│                                                     │
│  Features:                                          │
│  • Cross-zone load balancing: Enabled              │
│  • Connection draining: 300s                       │
│  • Sticky sessions: Disabled (stateless API)       │
└─────────────────────────────────────────────────────┘
```

### 4. Database Layer

```
┌─────────────────────────────────────────────────────┐
│         RDS PostgreSQL Multi-AZ                     │
│                                                     │
│  Configuration:                                     │
│  • Engine: PostgreSQL 15.x                         │
│  • Instance Class: db.t3.small                     │
│  • Storage: 100 GB gp3 (encrypted)                 │
│  • Multi-AZ: Enabled                               │
│                                                     │
│  High Availability:                                 │
│  • Primary: us-east-1a                             │
│  • Standby: us-east-1b (synchronous replication)   │
│  • Automatic failover: ~60-120 seconds             │
│                                                     │
│  Backup:                                            │
│  • Automated backups: 7 days retention             │
│  • Backup window: 03:00-04:00 UTC                  │
│  • Maintenance window: Sun 04:00-05:00 UTC         │
│                                                     │
│  Security:                                          │
│  • Encryption at rest: AWS KMS                     │
│  • Encryption in transit: SSL/TLS required         │
│  • Network: Private subnets only                   │
└─────────────────────────────────────────────────────┘
```

### 5. Security Architecture

```
┌─────────────────────────────────────────────────────┐
│              Security Layers                        │
│                                                     │
│  Layer 1: Network ACLs (Stateless)                 │
│  ┌───────────────────────────────────────────────┐ │
│  │ Public Subnet NACL:                           │ │
│  │ • Inbound: 80, 443, 1024-65535                │ │
│  │ • Outbound: All                               │ │
│  └───────────────────────────────────────────────┘ │
│                                                     │
│  Layer 2: Security Groups (Stateful)               │
│  ┌───────────────────────────────────────────────┐ │
│  │ ALB Security Group:                           │ │
│  │ • Inbound: 80, 443 from 0.0.0.0/0             │ │
│  │ • Outbound: 8080 to app-sg                    │ │
│  └───────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────┐ │
│  │ Application Security Group:                   │ │
│  │ • Inbound: 8080 from alb-sg                   │ │
│  │ • Inbound: 22 from bastion-sg                 │ │
│  │ • Outbound: 5432 to db-sg, 443 to 0.0.0.0/0   │ │
│  └───────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────┐ │
│  │ Database Security Group:                      │ │
│  │ • Inbound: 5432 from app-sg only              │ │
│  │ • Outbound: None                              │ │
│  └───────────────────────────────────────────────┘ │
│                                                     │
│  Layer 3: IAM Roles (Least Privilege)             │
│  ┌───────────────────────────────────────────────┐ │
│  │ EC2 Instance Role:                            │ │
│  │ • CloudWatch Logs: Write                      │ │
│  │ • S3: Read (config), Write (logs)             │ │
│  │ • Secrets Manager: Read (DB credentials)      │ │
│  │ • SSM: Session Manager access                 │ │
│  └───────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

## High Availability Design

### Failure Scenarios and Recovery

| Failure Type | Impact | Recovery | RTO | RPO |
|-------------|--------|----------|-----|-----|
| **Single EC2 Instance** | No impact (ALB routes to healthy) | ASG launches replacement | 2-3 min | 0 |
| **Availability Zone** | Reduced capacity | Traffic to other AZs | Immediate | 0 |
| **RDS Primary** | Brief connection errors | Auto-failover to standby | 60-120s | 0 |
| **NAT Gateway** | No outbound from that AZ | Traffic uses other NAT GWs | Immediate | 0 |
| **ALB** | Service unavailable | Route53 health check failover | 60s | 0 |

### Auto Scaling Behavior

```
Scaling Out (Add Instances):
─────────────────────────────────────────────────────
Time    CPU%   Instances   Action
0:00    50%    3           Normal operation
0:05    75%    3           Alarm: CPU > 70% for 2 min
0:07    80%    3           Trigger scale-out
0:09    80%    4           New instance launching
0:11    70%    5           Another instance launching
0:13    60%    5           CPU normalizing
0:15    55%    5           Stable

Scaling In (Remove Instances):
─────────────────────────────────────────────────────
Time    CPU%   Instances   Action
0:00    30%    5           Low utilization
0:15    25%    5           Alarm: CPU < 30% for 15 min
0:17    25%    5           Trigger scale-in
0:19    25%    4           Instance terminating (drain)
0:24    30%    4           Stable
```

## Monitoring Architecture

```
┌─────────────────────────────────────────────────────┐
│              CloudWatch Monitoring                  │
│                                                     │
│  Metrics Collected:                                 │
│  ┌───────────────────────────────────────────────┐ │
│  │ EC2 Instances:                                │ │
│  │ • CPU Utilization                             │ │
│  │ • Network In/Out                              │ │
│  │ • Disk Read/Write                             │ │
│  │ • Status Checks                               │ │
│  │ • Custom: Memory, Disk Space                  │ │
│  └───────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────┐ │
│  │ ALB:                                          │ │
│  │ • Request Count                               │ │
│  │ • Target Response Time                        │ │
│  │ • Healthy/Unhealthy Host Count                │ │
│  │ • HTTP 4xx/5xx Errors                         │ │
│  └───────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────┐ │
│  │ RDS:                                          │ │
│  │ • CPU Utilization                             │ │
│  │ • Database Connections                        │ │
│  │ • Read/Write IOPS                             │ │
│  │ • Replication Lag                             │ │
│  └───────────────────────────────────────────────┘ │
│                                                     │
│  Alarms → SNS Topics → Email/SMS                   │
└─────────────────────────────────────────────────────┘
```

## Cost Optimization Architecture

### Resource Tagging Strategy

```
All resources tagged with:
┌─────────────────────────────────────┐
│ Environment: dev/staging/prod       │
│ Project: payflow-platform           │
│ ManagedBy: terraform                │
│ CostCenter: engineering             │
│ Owner: devops-team                  │
│ Compliance: pci-dss                 │
└─────────────────────────────────────┘
```

### Environment-Specific Sizing

| Resource | Dev | Staging | Production |
|----------|-----|---------|------------|
| **EC2 Type** | t3.micro | t3.small | t3.large |
| **RDS Type** | db.t3.micro | db.t3.small | db.t3.large |
| **RDS Multi-AZ** | No | Yes | Yes |
| **NAT Gateways** | 1 | 3 | 3 |
| **ASG Min** | 1 | 2 | 3 |
| **ASG Max** | 3 | 6 | 10 |

## Deployment Workflow

```
┌──────────────┐
│  Developer   │
│  Workstation │
└──────┬───────┘
       │
       │ 1. terraform plan
       ▼
┌──────────────┐
│   Terraform  │
│   Validates  │
│   & Plans    │
└──────┬───────┘
       │
       │ 2. Shows changes
       ▼
┌──────────────┐
│   Review &   │
│   Approve    │
└──────┬───────┘
       │
       │ 3. terraform apply
       ▼
┌──────────────────────────────────┐
│   AWS API                        │
│   Creates/Updates Resources      │
└──────┬───────────────────────────┘
       │
       │ 4. Resources provisioned
       ▼
┌──────────────────────────────────┐
│   State File                     │
│   S3: terraform-state-bucket     │
│   DynamoDB: terraform-lock-table │
└──────────────────────────────────┘
```

## Next Steps

- Review [Business Requirements](business-requirements.md)
- Study [Security Best Practices](security-best-practices.md)
- Start with [Lab 01: VPC Networking](../labs/01-vpc-networking/README.md)
