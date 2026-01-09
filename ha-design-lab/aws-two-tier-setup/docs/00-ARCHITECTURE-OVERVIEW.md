# 🎯 Architecture Overview - Two-Tier AWS Setup

> **Understanding the Two-Tier Architecture Design and Traffic Flow**

---

## 📋 What is a Two-Tier Architecture?

A **two-tier architecture** separates your application into two distinct layers:

1. **Tier 1: Presentation + Application Layer** (Combined)
   - Web server (NGINX)
   - Application logic (Node.js/Python)
   - User interface
   - Business logic

2. **Tier 2: Data Layer**
   - Database (MongoDB)
   - Data storage
   - Data replication

---

## 🏗️ Architecture Components

### High-Level Architecture with IP Details

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          INTERNET (0.0.0.0/0)                            │
│                                   │                                       │
│                                   ▼                                       │
│                        ┌──────────────────────┐                          │
│                        │  Route 53 (DNS)      │                          │
│                        │  www.example.com     │                          │
│                        │  → ALB Public IP     │                          │
│                        └──────────┬───────────┘                          │
│                                   │                                       │
│                                   ▼                                       │
│              ┌────────────────────────────────────────┐                  │
│              │  Application Load Balancer (ALB)       │                  │
│              │  Public IP: 54.x.x.x (Auto-assigned)   │                  │
│              │  DNS: xxx.us-east-1.elb.amazonaws.com  │                  │
│              │  Ports: 80 (HTTP), 443 (HTTPS)         │                  │
│              └────────────┬───────────────────────────┘                  │
│                           │                                               │
│          ┌────────────────┴────────────────┐                             │
│          │                                  │                             │
│          ▼                                  ▼                             │
│  ┌───────────────────────┐        ┌───────────────────────┐             │
│  │ PUBLIC SUBNET 1       │        │ PUBLIC SUBNET 2       │             │
│  │ 10.0.1.0/24           │        │ 10.0.2.0/24           │             │
│  │ AZ: us-east-1a        │        │ AZ: us-east-1b        │             │
│  │ Internet Gateway: ✓   │        │ Internet Gateway: ✓   │             │
│  ├───────────────────────┤        ├───────────────────────┤             │
│  │ ┌─────────────────┐   │        │ ┌─────────────────┐   │             │
│  │ │ Web/App Server  │   │        │ │ Web/App Server  │   │             │
│  │ │ Private: 10.0.1.10│  │        │ │ Private: 10.0.2.10│  │             │
│  │ │ Public: 54.x.x.1  │  │        │ │ Public: 54.x.x.2  │  │             │
│  │ │                   │  │        │ │                   │  │             │
│  │ │ ┌─────────────┐   │  │        │ │ ┌─────────────┐   │  │             │
│  │ │ │ NGINX:80    │   │  │        │ │ │ NGINX:80    │   │  │             │
│  │ │ └──────┬──────┘   │  │        │ │ └──────┬──────┘   │  │             │
│  │ │ ┌──────▼──────┐   │  │        │ │ ┌──────▼──────┐   │  │             │
│  │ │ │ Node.js:3000│   │  │        │ │ │ Node.js:3000│   │  │             │
│  │ │ └─────────────┘   │  │        │ │ └─────────────┘   │  │             │
│  │ └─────────┬─────────┘  │        │ └─────────┬─────────┘  │             │
│  └───────────┼────────────┘        └───────────┼────────────┘             │
│              │                                  │                          │
│              └──────────────┬───────────────────┘                          │
│                             │                                              │
│                             ▼                                              │
│              ┌──────────────────────────────────┐                         │
│              │  MongoDB Connection (Port 27017) │                         │
│              └──────────────┬───────────────────┘                         │
│                             │                                              │
│          ┌──────────────────┴──────────────────┐                          │
│          │                                      │                          │
│          ▼                                      ▼                          │
│  ┌───────────────────────┐        ┌───────────────────────┐              │
│  │ PRIVATE SUBNET 1      │        │ PRIVATE SUBNET 2      │              │
│  │ 10.0.11.0/24          │        │ 10.0.12.0/24          │              │
│  │ AZ: us-east-1a        │        │ AZ: us-east-1b        │              │
│  │ Internet: ✗ (Isolated)│        │ Internet: ✗ (Isolated)│              │
│  ├───────────────────────┤        ├───────────────────────┤              │
│  │ ┌─────────────────┐   │        │ ┌─────────────────┐   │              │
│  │ │ MongoDB PRIMARY │   │        │ │ MongoDB SECONDARY│  │              │
│  │ │ IP: 10.0.11.10  │◄──┼────────┼─►│ IP: 10.0.12.10  │   │              │
│  │ │ Port: 27017     │   │        │ │ Port: 27017     │   │              │
│  │ │ Role: Primary   │   │        │ │ Role: Secondary │   │              │
│  │ │ Replica Set: rs0│   │        │ │ Replica Set: rs0│   │              │
│  │ └─────────────────┘   │        │ └─────────────────┘   │              │
│  └───────────────────────┘        └───────────────────────┘              │
│                                                                            │
│  VPC: 10.0.0.0/16 (65,536 IP addresses)                                  │
│  Region: us-east-1 (N. Virginia)                                         │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Traffic Flow

### 1. User Request Flow

```
User Browser
    │
    ├─► 1. DNS Resolution (Route 53)
    │      www.example.com → ALB IP
    │
    ├─► 2. HTTPS Request to ALB
    │      - SSL/TLS Termination
    │      - Health Check Validation
    │
    ├─► 3. Load Balancer Routing
    │      - Round-robin distribution
    │      - Sticky sessions (optional)
    │
    ├─► 4. Web/App Instance
    │      ┌─────────────────────┐
    │      │ NGINX (Port 80/443) │
    │      │   ↓                  │
    │      │ Reverse Proxy        │
    │      │   ↓                  │
    │      │ Node.js (Port 3000)  │
    │      │   ↓                  │
    │      │ Business Logic       │
    │      └─────────────────────┘
    │
    ├─► 5. Database Query
    │      - MongoDB connection
    │      - Read/Write operations
    │      - Replica set handling
    │
    └─► 6. Response Back to User
           - JSON/HTML response
           - Static assets (cached)
```

### 2. Database Replication Flow

```
┌─────────────────────────────────────────────────────────┐
│                                                           │
│  Application Writes                                      │
│         │                                                 │
│         ▼                                                 │
│  ┌──────────────┐                                        │
│  │  MongoDB     │                                        │
│  │  PRIMARY     │                                        │
│  │  (AZ-1)      │                                        │
│  └──────┬───────┘                                        │
│         │                                                 │
│         │ Oplog Replication                              │
│         │ (Asynchronous)                                 │
│         │                                                 │
│         ▼                                                 │
│  ┌──────────────┐                                        │
│  │  MongoDB     │                                        │
│  │  SECONDARY   │                                        │
│  │  (AZ-2)      │                                        │
│  └──────────────┘                                        │
│         │                                                 │
│         ▼                                                 │
│  Application Reads (Optional)                            │
│  - Read preference: primaryPreferred                     │
│  - Automatic failover on primary failure                 │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

---

## 🌐 Network Architecture (Detailed)

### VPC Layout with IP Ranges

```
┌─────────────────────────────────────────────────────────────────┐
│  VPC: 10.0.0.0/16                                               │
│  Total IPs: 65,536 addresses                                    │
│  Region: us-east-1                                              │
│  DNS Hostnames: Enabled                                         │
│  DNS Resolution: Enabled                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  PUBLIC SUBNETS (Internet-facing)                        │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │                                                           │  │
│  │  📍 Subnet 1: 10.0.1.0/24                                │  │
│  │     ├─ Availability Zone: us-east-1a                     │  │
│  │     ├─ Total IPs: 256 (251 usable)                       │  │
│  │     ├─ IP Range: 10.0.1.0 - 10.0.1.255                   │  │
│  │     ├─ Gateway: 10.0.1.1 (AWS reserved)                  │  │
│  │     ├─ Broadcast: 10.0.1.255 (AWS reserved)              │  │
│  │     ├─ Route: 0.0.0.0/0 → Internet Gateway               │  │
│  │     └─ Auto-assign Public IP: ✓ Enabled                  │  │
│  │                                                           │  │
│  │     Example IPs:                                          │  │
│  │     • Web/App Server 1: 10.0.1.10 (+ Public IP)          │  │
│  │     • Web/App Server 2: 10.0.1.11 (+ Public IP)          │  │
│  │     • Available: 10.0.1.12 - 10.0.1.254                  │  │
│  │                                                           │  │
│  │  📍 Subnet 2: 10.0.2.0/24                                │  │
│  │     ├─ Availability Zone: us-east-1b                     │  │
│  │     ├─ Total IPs: 256 (251 usable)                       │  │
│  │     ├─ IP Range: 10.0.2.0 - 10.0.2.255                   │  │
│  │     ├─ Gateway: 10.0.2.1 (AWS reserved)                  │  │
│  │     ├─ Broadcast: 10.0.2.255 (AWS reserved)              │  │
│  │     ├─ Route: 0.0.0.0/0 → Internet Gateway               │  │
│  │     └─ Auto-assign Public IP: ✓ Enabled                  │  │
│  │                                                           │  │
│  │     Example IPs:                                          │  │
│  │     • Web/App Server 3: 10.0.2.10 (+ Public IP)          │  │
│  │     • Web/App Server 4: 10.0.2.11 (+ Public IP)          │  │
│  │     • Available: 10.0.2.12 - 10.0.2.254                  │  │
│  │                                                           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  PRIVATE SUBNETS (Isolated - No Internet)                │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │                                                           │  │
│  │  🔒 Subnet 1: 10.0.11.0/24                               │  │
│  │     ├─ Availability Zone: us-east-1a                     │  │
│  │     ├─ Total IPs: 256 (251 usable)                       │  │
│  │     ├─ IP Range: 10.0.11.0 - 10.0.11.255                 │  │
│  │     ├─ Gateway: 10.0.11.1 (AWS reserved)                 │  │
│  │     ├─ Broadcast: 10.0.11.255 (AWS reserved)             │  │
│  │     ├─ Route: 10.0.0.0/16 → local ONLY                   │  │
│  │     └─ Internet Access: ✗ Disabled (Isolated)            │  │
│  │                                                           │  │
│  │     Example IPs:                                          │  │
│  │     • MongoDB Primary: 10.0.11.10                        │  │
│  │     • MongoDB Arbiter: 10.0.11.11 (optional)             │  │
│  │     • Available: 10.0.11.12 - 10.0.11.254                │  │
│  │                                                           │  │
│  │  🔒 Subnet 2: 10.0.12.0/24                               │  │
│  │     ├─ Availability Zone: us-east-1b                     │  │
│  │     ├─ Total IPs: 256 (251 usable)                       │  │
│  │     ├─ IP Range: 10.0.12.0 - 10.0.12.255                 │  │
│  │     ├─ Gateway: 10.0.12.1 (AWS reserved)                 │  │
│  │     ├─ Broadcast: 10.0.12.255 (AWS reserved)             │  │
│  │     ├─ Route: 10.0.0.0/16 → local ONLY                   │  │
│  │     └─ Internet Access: ✗ Disabled (Isolated)            │  │
│  │                                                           │  │
│  │     Example IPs:                                          │  │
│  │     • MongoDB Secondary: 10.0.12.10                      │  │
│  │     • MongoDB Backup: 10.0.12.11 (optional)              │  │
│  │     • Available: 10.0.12.12 - 10.0.12.254                │  │
│  │                                                           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Routing Tables (Detailed)

#### Public Route Table (rtb-public)
```
┌─────────────────────────────────────────────────────────────┐
│  Route Table: Public Subnets                                │
├─────────────────────────────────────────────────────────────┤
│  Destination         Target                  Status         │
├─────────────────────────────────────────────────────────────┤
│  10.0.0.0/16        local                   Active         │
│  (VPC internal)     (VPC router)            (Always)       │
│                                                              │
│  0.0.0.0/0          igw-xxxxxxxxx           Active         │
│  (Internet)         (Internet Gateway)      (Always)       │
└─────────────────────────────────────────────────────────────┘

Associated Subnets:
  • 10.0.1.0/24 (public-subnet-1, us-east-1a)
  • 10.0.2.0/24 (public-subnet-2, us-east-1b)

Traffic Flow:
  • Internal (10.0.x.x) → VPC local routing
  • External (Internet) → Internet Gateway → Internet
```

#### Private Route Table (rtb-private)
```
┌─────────────────────────────────────────────────────────────┐
│  Route Table: Private Subnets (Database Tier)              │
├─────────────────────────────────────────────────────────────┤
│  Destination         Target                  Status         │
├─────────────────────────────────────────────────────────────┤
│  10.0.0.0/16        local                   Active         │
│  (VPC internal)     (VPC router)            (Always)       │
│                                                              │
│  (No internet route - fully isolated for security)          │
└─────────────────────────────────────────────────────────────┘

Associated Subnets:
  • 10.0.11.0/24 (private-db-subnet-1, us-east-1a)
  • 10.0.12.0/24 (private-db-subnet-2, us-east-1b)

Traffic Flow:
  • Internal (10.0.x.x) → VPC local routing ONLY
  • External (Internet) → ✗ BLOCKED (No route)
  • Can communicate with web/app tier via VPC routing
```

### IP Address Allocation Summary

| Subnet | CIDR | AZ | Type | Usable IPs | Purpose | Internet |
|--------|------|-------|------|------------|---------|----------|
| **Public-1** | 10.0.1.0/24 | us-east-1a | Public | 251 | Web/App | ✓ Yes |
| **Public-2** | 10.0.2.0/24 | us-east-1b | Public | 251 | Web/App | ✓ Yes |
| **Private-1** | 10.0.11.0/24 | us-east-1a | Private | 251 | Database | ✗ No |
| **Private-2** | 10.0.12.0/24 | us-east-1b | Private | 251 | Database | ✗ No |
| **Total** | 10.0.0.0/16 | Multi-AZ | Mixed | 1,004 | All tiers | Mixed |

---

## 🔒 Security Architecture

### Security Groups

#### 1. ALB Security Group
```yaml
Inbound Rules:
  - Port 80 (HTTP):   0.0.0.0/0
  - Port 443 (HTTPS): 0.0.0.0/0

Outbound Rules:
  - All traffic to Web/App Security Group
```

#### 2. Web/App Security Group
```yaml
Inbound Rules:
  - Port 80:   ALB Security Group
  - Port 443:  ALB Security Group
  - Port 3000: ALB Security Group (Node.js)
  - Port 22:   Bastion/Your IP (SSH)

Outbound Rules:
  - Port 27017: Database Security Group (MongoDB)
  - Port 443:   0.0.0.0/0 (HTTPS for updates)
```

#### 3. Database Security Group
```yaml
Inbound Rules:
  - Port 27017: Web/App Security Group (MongoDB)
  - Port 27017: Database Security Group (Replication)

Outbound Rules:
  - Port 27017: Database Security Group (Replication)
```

---

## 📊 Auto-Scaling Architecture

### Scaling Configuration

```
┌─────────────────────────────────────────────────────────┐
│  Auto-Scaling Group                                     │
│                                                           │
│  Minimum Capacity:  2 instances                         │
│  Maximum Capacity:  10 instances                        │
│  Desired Capacity:  2 instances                         │
│                                                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Scaling Policies                               │   │
│  ├─────────────────────────────────────────────────┤   │
│  │                                                  │   │
│  │  Scale Out (Add Instances):                     │   │
│  │  ✓ CPU > 70% for 2 minutes                      │   │
│  │  ✓ Memory > 75% for 2 minutes                   │   │
│  │  ✓ Request count > 1000/min                     │   │
│  │                                                  │   │
│  │  Scale In (Remove Instances):                   │   │
│  │  ✓ CPU < 30% for 5 minutes                      │   │
│  │  ✓ Memory < 35% for 5 minutes                   │   │
│  │  ✓ Request count < 200/min                      │   │
│  │                                                  │   │
│  └─────────────────────────────────────────────────┘   │
│                                                           │
│  Health Checks:                                          │
│  ✓ ELB Health Check (every 30s)                         │
│  ✓ EC2 Status Check (every 60s)                         │
│  ✓ Application Health Endpoint (/health)                │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

---

## 🎯 High Availability Design

### Multi-AZ Deployment

| Component | AZ-1 (us-east-1a) | AZ-2 (us-east-1b) | Failover |
|-----------|-------------------|-------------------|----------|
| **ALB** | ✅ Active | ✅ Active | Automatic |
| **Web/App** | ✅ Active | ✅ Active | Load balanced |
| **MongoDB** | ✅ Primary | ✅ Secondary | Automatic (30s) |

### Failure Scenarios

#### Scenario 1: Web/App Instance Failure
```
1. Health check fails (3 consecutive failures)
2. ALB stops routing traffic to failed instance
3. Auto-scaling detects unhealthy instance
4. New instance launched automatically
5. Health check passes, traffic resumes
Time to recover: ~3-5 minutes
```

#### Scenario 2: Database Primary Failure
```
1. MongoDB detects primary failure
2. Replica set election initiated
3. Secondary promoted to primary
4. Application reconnects automatically
5. Failed node can rejoin as secondary
Time to recover: ~30-60 seconds
```

#### Scenario 3: Availability Zone Failure
```
1. All resources in AZ-1 become unavailable
2. ALB routes all traffic to AZ-2
3. Auto-scaling launches instances in AZ-2
4. MongoDB secondary (AZ-2) becomes primary
5. System continues with reduced capacity
Time to recover: ~2-3 minutes
```

---

## 💾 Data Flow

### Write Operation
```
Client → ALB → Web/App → MongoDB Primary → Oplog → Secondary
                                  ↓
                            Write Confirmed
                                  ↓
                            Response to Client
```

### Read Operation
```
Client → ALB → Web/App → MongoDB (Primary or Secondary)
                                  ↓
                            Data Retrieved
                                  ↓
                            Response to Client
```

---

## 📈 Monitoring Architecture

### CloudWatch Metrics

```
┌─────────────────────────────────────────────────────────┐
│  CloudWatch Monitoring                                  │
│                                                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │  ALB Metrics                                    │   │
│  │  • Request Count                                │   │
│  │  • Target Response Time                         │   │
│  │  • HTTP 4xx/5xx Errors                          │   │
│  │  • Healthy/Unhealthy Host Count                 │   │
│  └─────────────────────────────────────────────────┘   │
│                                                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │  EC2 Metrics                                    │   │
│  │  • CPU Utilization                              │   │
│  │  • Network In/Out                               │   │
│  │  • Disk Read/Write                              │   │
│  │  • Status Checks                                │   │
│  └─────────────────────────────────────────────────┘   │
│                                                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Custom Application Metrics                     │   │
│  │  • Memory Utilization                           │   │
│  │  • Application Response Time                    │   │
│  │  • Database Connection Pool                     │   │
│  │  • Active Sessions                              │   │
│  └─────────────────────────────────────────────────┘   │
│                                                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Alarms                                         │   │
│  │  • High CPU (>70%)                              │   │
│  │  • High Memory (>75%)                           │   │
│  │  • Unhealthy Targets                            │   │
│  │  • Database Connection Failures                 │   │
│  └─────────────────────────────────────────────────┘   │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

---

## 🔄 Deployment Strategy

### Blue-Green Deployment

```
┌─────────────────────────────────────────────────────────┐
│                                                           │
│  Current (Blue) Environment                              │
│  ┌─────────────────────────────────────────────────┐   │
│  │  ALB → Target Group Blue                        │   │
│  │         ├─► Instance 1 (v1.0)                   │   │
│  │         └─► Instance 2 (v1.0)                   │   │
│  └─────────────────────────────────────────────────┘   │
│                                                           │
│  New (Green) Environment                                 │
│  ┌─────────────────────────────────────────────────┐   │
│  │  ALB → Target Group Green (0% traffic)          │   │
│  │         ├─► Instance 3 (v2.0)                   │   │
│  │         └─► Instance 4 (v2.0)                   │   │
│  └─────────────────────────────────────────────────┘   │
│                                                           │
│  Deployment Steps:                                       │
│  1. Deploy new version to Green                         │
│  2. Test Green environment                              │
│  3. Gradually shift traffic (10% → 50% → 100%)          │
│  4. Monitor metrics and errors                          │
│  5. Rollback to Blue if issues detected                 │
│  6. Terminate Blue after successful deployment          │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

---

## 🎯 Key Design Decisions

### Why Two-Tier Instead of Three-Tier?

| Aspect | Two-Tier | Three-Tier |
|--------|----------|------------|
| **Complexity** | Lower | Higher |
| **Cost** | Lower (fewer resources) | Higher |
| **Latency** | Lower (one less hop) | Slightly higher |
| **Scalability** | Good for small-medium apps | Better for large apps |
| **Maintenance** | Easier | More complex |

### When to Use Two-Tier?

✅ **Good for:**
- Small to medium applications
- Startups and MVPs
- Cost-sensitive projects
- Simple business logic
- Moderate traffic (< 10,000 req/min)

❌ **Not ideal for:**
- Complex microservices
- Very high traffic (> 100,000 req/min)
- Multiple independent services
- Complex business logic requiring isolation

---

## 📚 Next Steps

1. **[Infrastructure Setup](./01-INFRASTRUCTURE-SETUP.md)** - Create VPC, subnets, and networking
2. **[Database Tier Setup](./02-DATABASE-TIER-SETUP.md)** - Deploy MongoDB replica set
3. **[Web/App Tier Setup](./03-WEBAPP-TIER-SETUP.md)** - Deploy application servers
4. **[Auto-Scaling Setup](./04-AUTOSCALING-SETUP.md)** - Configure auto-scaling policies

---

**Architecture overview complete! Ready to build? 🚀**
