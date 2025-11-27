## 3. DR Tiers & RPO/RTO Design

### Understanding RPO and RTO

**Recovery Point Objective (RPO):**
- Maximum acceptable amount of data loss measured in time
- Example: RPO of 15 minutes means you can lose up to 15 minutes of data
- Determines backup frequency and replication strategy

**Recovery Time Objective (RTO):**
- Maximum acceptable downtime before systems must be restored
- Example: RTO of 1 hour means systems must be operational within 60 minutes
- Determines infrastructure readiness and automation level

### DR Tier Classification

#### Tier 1: Mission-Critical (RPO: <5 min, RTO: <15 min)
**Components:**
- Payment processing systems
- Real-time trading platforms
- Authentication services
- Core API gateways

**Strategy:**
- **Active-Active** deployment across all clouds
- Synchronous replication where possible
- Automated failover with health checks
- Pre-warmed standby instances

**Implementation:**
```
Primary (AWS)          Secondary (Azure)       Tertiary (GCP)
     │                       │                       │
     ├─ Write ──────────────►├─ Sync Replica        │
     ├─ Read ◄──────────────►├─ Read                │
     └─ Failover ◄──────────►└─ Standby (Hot)       │
```

#### Tier 2: Business-Critical (RPO: 15 min, RTO: 1 hour)
**Components:**
- Customer-facing web applications
- Order management systems
- Inventory databases
- Email services

**Strategy:**
- **Active-Passive** with warm standby
- Asynchronous replication (15-minute intervals)
- Semi-automated failover (requires approval)
- Standby instances running at reduced capacity

**Implementation:**
```
Primary (AWS)          Secondary (Azure)       Tertiary (GCP)
     │                       │                       │
     ├─ Write               ├─ Async Replica (15min) │
     ├─ Read                ├─ Standby (Warm)        │
     └─ Failover ──────────►└─ Activate ────────────►└─ Cold Backup
```

#### Tier 3: Important (RPO: 4 hours, RTO: 8 hours)
**Components:**
- Analytics platforms
- Reporting systems
- Internal tools
- Development environments

**Strategy:**
- **Pilot Light** approach
- Periodic snapshots (every 4 hours)
- Manual failover process
- Minimal standby infrastructure

**Implementation:**
```
Primary (AWS)          Secondary (Azure)       Tertiary (GCP)
     │                       │                       │
     ├─ Write               ├─ Snapshot (4hr)        │
     ├─ Read                ├─ Pilot Light           │
     └─ Failover ──────────►└─ Provision & Restore ─►└─ Archive Storage
```

#### Tier 4: Non-Critical (RPO: 24 hours, RTO: 72 hours)
**Components:**
- Archive data
- Historical logs
- Test environments
- Documentation systems

**Strategy:**
- **Backup & Restore**
- Daily backups
- Manual restoration
- No standby infrastructure

### Component-Level RPO/RTO Mapping

| Component | Tier | RPO | RTO | Replication Type | Standby State |
|-----------|------|-----|-----|------------------|---------------|
| **Databases** |
| Payment DB (PostgreSQL) | 1 | 0 min | 5 min | Synchronous | Active-Active |
| User DB (PostgreSQL) | 2 | 15 min | 1 hour | Async (15min) | Warm Standby |
| Analytics DB (Redshift) | 3 | 4 hours | 8 hours | Snapshot | Pilot Light |
| Archive DB | 4 | 24 hours | 72 hours | Daily Backup | Cold |
| **NoSQL Databases** |
| Session Store (DynamoDB) | 1 | 0 min | 5 min | Global Tables | Active-Active |
| Product Catalog (Cosmos) | 2 | 15 min | 1 hour | Multi-region | Warm Standby |
| Logs (Firestore) | 3 | 4 hours | 8 hours | Snapshot | Pilot Light |
| **Cache** |
| Redis (Session) | 1 | 5 min | 10 min | Async | Hot Standby |
| Redis (Application) | 2 | 15 min | 1 hour | Snapshot | Warm Standby |
| **Storage** |
| User Uploads (S3) | 2 | 15 min | 1 hour | CRR (15min) | Replicated |
| Application Assets | 2 | 1 hour | 2 hours | CRR (1hr) | Replicated |
| Backups | 3 | 24 hours | 8 hours | Daily Sync | Archive |
| Logs | 4 | 24 hours | 72 hours | Weekly Sync | Archive |
| **Compute** |
| API Servers (EKS/AKS/GKE) | 1 | N/A | 10 min | N/A | Active-Active |
| Web Servers (EC2/VM/GCE) | 2 | N/A | 1 hour | AMI/Image | Warm Pool |
| Batch Jobs (Lambda/Functions) | 3 | N/A | 4 hours | Code Deploy | On-Demand |
| **Kubernetes** |
| Production Clusters | 1 | 15 min | 15 min | Velero (15min) | Active-Active |
| Staging Clusters | 3 | 4 hours | 8 hours | Velero (4hr) | Pilot Light |
| **Networking** |
| DNS (Route53/Traffic Mgr) | 1 | 0 min | 2 min | Multi-provider | Active-Active |
| Load Balancers | 1 | N/A | 5 min | IaC | Pre-provisioned |
| VPN/Interconnect | 2 | N/A | 1 hour | IaC | Warm Standby |
| **Identity** |
| IAM/Azure AD | 1 | 0 min | 5 min | Federated | Active-Active |
| Secrets (Vault) | 1 | 5 min | 10 min | Raft Replication | Active-Active |

### Replication Strategies Explained

#### Synchronous Replication
**When to Use:**
- Tier 1 mission-critical systems
- Zero data loss requirement (RPO = 0)
- Financial transactions, payment systems
- Compliance requirements (ACID transactions)

**How It Works:**
```
Application Write Request
         │
         ▼
    Primary DB
         │
         ├──────────────┐
         │              │
         ▼              ▼
   Local Commit    Sync to Secondary
         │              │
         └──────┬───────┘
                ▼
         Acknowledge to App
```

**Pros:**
- Zero data loss
- Immediate consistency
- Strong durability guarantees

**Cons:**
- Higher latency (network round-trip)
- Performance impact on writes
- Limited by network distance (typically <100ms RTT)

**Example Configuration:**
```sql
-- PostgreSQL Synchronous Replication
ALTER SYSTEM SET synchronous_commit = 'remote_apply';
ALTER SYSTEM SET synchronous_standby_names = 'secondary1,secondary2';
```

#### Asynchronous Replication
**When to Use:**
- Tier 2 business-critical systems
- Acceptable data loss window (RPO 5-60 minutes)
- Cross-region replication
- High-throughput systems

**How It Works:**
```
Application Write Request
         │
         ▼
    Primary DB
         │
         ▼
   Local Commit
         │
         ▼
   Acknowledge to App
         │
         ▼
   Async Replication Queue
         │
         ▼
   Secondary DB (delayed)
```

**Pros:**
- Low write latency
- No performance impact
- Works across long distances

**Cons:**
- Potential data loss (RPO > 0)
- Replication lag
- Eventual consistency

**Example Configuration:**
```yaml
# AWS RDS Cross-Region Read Replica
aws rds create-db-instance-read-replica \
  --db-instance-identifier mydb-replica-us-west \
  --source-db-instance-identifier mydb-us-east \
  --region us-west-2
```

#### Snapshot-Based Replication
**When to Use:**
- Tier 3 important systems
- Large datasets with infrequent changes
- Analytics and reporting databases
- Cost-sensitive workloads

**How It Works:**
```
Scheduled Snapshot (every 4 hours)
         │
         ▼
   Create Point-in-Time Copy
         │
         ▼
   Transfer to Secondary Region
         │
         ▼
   Store in Object Storage
         │
         ▼
   Restore on Failover
```

**Pros:**
- Cost-effective
- Low operational overhead
- Suitable for large datasets

**Cons:**
- High RPO (hours)
- Longer RTO (restoration time)
- Storage costs for snapshots

**Example Configuration:**
```bash
# Automated EBS Snapshot with AWS Backup
aws backup create-backup-plan \
  --backup-plan '{
    "BackupPlanName": "DailyBackups",
    "Rules": [{
      "RuleName": "Every4Hours",
      "ScheduleExpression": "cron(0 */4 * * ? *)",
      "TargetBackupVaultName": "Default",
      "Lifecycle": {
        "DeleteAfterDays": 30
      },
      "CopyActions": [{
        "DestinationBackupVaultArn": "arn:aws:backup:us-west-2:...",
        "Lifecycle": {
          "DeleteAfterDays": 90
        }
      }]
    }]
  }'
```

### Multi-Cloud Replication Patterns

#### Pattern 1: Database Replication (PostgreSQL)
```
AWS RDS PostgreSQL (Primary)
         │
         ├─ Logical Replication (pglogical)
         │
         ▼
Azure PostgreSQL (Secondary)
         │
         ├─ Streaming Replication
         │
         ▼
GCP Cloud SQL (Tertiary)
```

**Implementation:**
```sql
-- On AWS RDS (Primary)
CREATE PUBLICATION my_publication FOR ALL TABLES;

-- On Azure PostgreSQL (Secondary)
CREATE SUBSCRIPTION my_subscription
  CONNECTION 'host=aws-rds.amazonaws.com port=5432 dbname=mydb user=repl_user'
  PUBLICATION my_publication;
```

#### Pattern 2: Object Storage Sync
```
AWS S3 (Primary)
         │
         ├─ S3 Cross-Region Replication
         │
         ▼
AWS S3 us-west-2
         │
         ├─ AWS DataSync
         │
         ▼
Azure Blob Storage
         │
         ├─ Rclone Sync
         │
         ▼
GCP Cloud Storage
```

**Implementation:**
```bash
# Rclone configuration for multi-cloud sync
rclone sync s3:my-bucket azure:my-container \
  --transfers 32 \
  --checkers 16 \
  --fast-list \
  --update \
  --use-server-modtime

rclone sync azure:my-container gcs:my-bucket \
  --transfers 32 \
  --fast-list
```

#### Pattern 3: Kubernetes Workload Backup
```
EKS Cluster (AWS)
         │
         ├─ Velero Backup (every 15 min)
         │
         ▼
S3 Bucket (Backup Storage)
         │
         ├─ Cross-Cloud Sync
         │
         ├──────────┬──────────┐
         ▼          ▼          ▼
   Azure Blob   GCS Bucket   On-Prem
         │          │          │
         ▼          ▼          ▼
   AKS Restore  GKE Restore  K8s Restore
```

**Implementation:**
```bash
# Velero backup schedule
velero schedule create daily-backup \
  --schedule="0 */6 * * *" \
  --include-namespaces production \
  --snapshot-volumes \
  --ttl 720h

# Restore to different cloud
velero restore create --from-backup daily-backup-20231127 \
  --namespace-mappings production:production-azure
```

### RPO/RTO Optimization Strategies

**Reduce RPO:**
1. Increase replication frequency
2. Use synchronous replication for critical data
3. Implement change data capture (CDC)
4. Enable continuous backup (AWS Backup, Azure Backup)
5. Use database transaction logs shipping

**Reduce RTO:**
1. Pre-provision standby infrastructure (warm/hot standby)
2. Automate failover procedures
3. Use infrastructure as code (Terraform, CloudFormation)
4. Implement health checks and monitoring
5. Regular DR drills to identify bottlenecks
6. Use managed services with built-in HA
7. Maintain runbooks and playbooks

**Cost vs. RPO/RTO Trade-offs:**
```
┌─────────────────────────────────────────────┐
│                                             │
│  High Cost                                  │
│      ▲                                      │
│      │                                      │
│      │    ┌──────────┐                      │
│      │    │ Active-  │                      │
│      │    │ Active   │                      │
│      │    └──────────┘                      │
│      │         ┌──────────┐                 │
│      │         │  Warm    │                 │
│      │         │ Standby  │                 │
│      │         └──────────┘                 │
│      │              ┌──────────┐            │
│      │              │  Pilot   │            │
│      │              │  Light   │            │
│      │              └──────────┘            │
│      │                   ┌──────────┐       │
│      │                   │ Backup & │       │
│      │                   │ Restore  │       │
│      │                   └──────────┘       │
│      │                                      │
│  Low Cost                                   │
│      └────────────────────────────────────► │
│         Low RTO/RPO          High RTO/RPO   │
│                                             │
└─────────────────────────────────────────────┘
```

