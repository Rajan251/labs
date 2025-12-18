# Infrastructure Architecture
**Document Control**
- **Version**: 1.0.0
- **Effective Date**: December 15, 2025
- **Document Owner**: IT Security Manager / Infrastructure Lead
- **Classification**: Internal - Technical

---

## 1. VAPT Infrastructure Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                  VAPT Program Infrastructure                          │
└──────────────────────────────────────────────────────────────────────┘

┌────────────────────────┐       ┌────────────────────────┐
│  Vulnerability         │       │  Penetration Testing   │
│  Management Server     │       │  Collaboration         │
│  (Nessus/Qualys)       │       │  Platform              │
│  - Weekly scans        │       │  (Faraday/Dradis)      │
│  - Policy management   │       │  - Multi-tester workspace│
└──────────┬─────────────┘       └──────────┬─────────────┘
           │                                 │
           ├─────────────────┬───────────────┤
           ↓                 ↓               ↓
┌──────────────────────────────────────────────────────────────────────┐
│                    Findings Database (PostgreSQL)                     │
│  - Centralized vulnerability repository                               │
│  - CVSS scoring, SLA tracking, audit trail                           │
└──────────┬───────────────────────────────────────────────────────────┘
           │
           ├─────────────────┬───────────────┬──────────────────┐
           ↓                 ↓               ↓                  ↓
┌────────────────┐  ┌────────────────┐  ┌──────────────┐  ┌──────────────┐
│ GRC/Ticketing  │  │ SIEM           │  │ Dashboards   │  │ Evidence     │
│ (Jira/SNOW)    │  │ (Splunk/ELK)   │  │ (Grafana/    │  │ Repository   │
│ - Remediation  │  │ - Alerts       │  │  Power BI)   │  │ (SharePoint) │
│   tracking     │  │ - Correlation  │  │ - KPI metrics│  │ - 7yr retain │
└────────────────┘  └────────────────┘  └──────────────┘  └──────────────┘
```

---

## 2. Component Specifications

### 2.1 Vulnerability Management Server

**Purpose**: Automated vulnerability scanning platform

**Platform Options**:
- **Option 1**: Tenable Nessus Professional
- **Option 2**: Qualys VMDR (Cloud-based)
- **Option 3**: Rapid7 Nexpose/InsightVM

**Recommended**: Nessus Professional (on-premise control + cost-effective)

**Hardware/VM Specifications**:
| Component | Specification |
|-----------|---------------|
| **CPU** | 8 vCPUs (Intel Xeon or equivalent) |
| **RAM** | 16 GB |
| **Storage** | 500 GB SSD (for scan results, plugins) |
| **Network** | Dedicated management VLAN, access to all subnets for scanning |
| **OS** | Ubuntu 22.04 LTS or Red Hat Enterprise Linux 9 |

**Configuration**:
- **Scan Policies**: Separate policies for Windows, Linux, Network Devices, Web Apps
- **Credentials**: Encrypted credential vault for authenticated scans
- **Scan Schedule**: Automated weekly scans (Sunday 02:00-06:00)
- **Plugin Updates**: Automated daily updates
- **Integration**: API-enabled for findings export to PostgreSQL database

**Hardening** (CIS Benchmark Level 1):
- Disable unnecessary services
- Enable host-based firewall (UFW/firewalld) - allow only HTTPS (8834) from security team IPs
- Multi-factor authentication (MFA) required for all users
- SSL/TLS enforced (disable HTTP)
- Regular OS patching (monthly)

**Backup**:
- Daily encrypted backups of scan databases and configurations
- Backup destination: AWS S3 (encrypted at rest, versioning enabled)
- Retention: 90 days

---

### 2.2 Penetration Testing Collaboration Platform

**Purpose**: Centralized workspace for penetration testers to collaborate and aggregate findings

**Platform Options**:
- **Option 1**: Faraday Platform (Open Source)
- **Option 2**: Dradis CE (Community Edition)
- **Option 3**: PlexTrac (Commercial)

**Recommended**: Faraday (feature-rich open source)

**Hardware/VM Specifications**:
| Component | Specification |
|-----------|---------------|
| **CPU** | 4 vCPUs |
| **RAM** | 8 GB |
| **Storage** | 250 GB SSD |
| **Network** | Isolated penetration testing VLAN (no direct internet access for opsec) |
| **OS** | Ubuntu 22.04 LTS |

**Features**:
- Multi-user workspaces (concurrent testers on same engagement)
- Tool integration: Import results from Nmap, Metasploit, Burp Suite, etc.
- Report generation (HTML, PDF, CSV export)
- API for findings export

**Security**:
- TLS 1.3 enforced
- OAuth 2.0 or SAML SSO integration (corporate Active Directory)
- Role-based access control (RBAC): Tester, Lead, Viewer
- Audit logging: All actions logged

---

### 2.3 Findings Database (PostgreSQL)

**Purpose**: Central repository for all vulnerability data (see [Findings Database Schema](./Findings-Database-Schema.md))

**Hardware/VM Specifications**:
| Component | Specification |
|-----------|---------------|
| **CPU** | 4 vCPUs |
| **RAM** | 16 GB |
| **Storage** | 1 TB SSD (for 7-year retention) |
| **Database** | PostgreSQL 15+ |
| **OS** | Ubuntu 22.04 LTS |

**High Availability** (for mission-critical deployments):
- PostgreSQL replication (primary + standby replica)
- Automated failover (Patroni + Consul)
- Load balancing (HAProxy)

**Backup & Disaster Recovery**:
- Automated daily backups (pg_dump + WAL archiving)
- Point-in-time recovery (PITR) capability
- Backup encryption (GPG or native PostgreSQL encryption)
- Offsite backup storage (AWS S3 cross-region replication)
- RTO (Recovery Time Objective): 4 hours
- RPO (Recovery Point Objective): 24 hours

**Security**:
- Network isolation (database server accessible only from application tier)
-SSL/TLS connections enforced (`sslmode=require`)
- Row-level security (RLS) for multi-tenancy (if needed)
- Database user roles (read-only, analyst, admin per schema)

---

### 2.4 GRC/Ticketing Integration

**Purpose**: Track vulnerability remediation through to closure

**Platform Options**:
- **Jira Service Management** (Atlassian)
- **ServiceNow Security Operations (SecOps)**
- **Linear** (for startups)

**Recommended**: Jira or ServiceNow (widely adopted, strong API)

**Integration Method**: REST API

**Workflow**:
1. Critical/High finding created in findings database
2. Webhook triggers API call to Jira/ServiceNow
3. Ticket auto-created with details (title, description, CVSS, due date)
4. Assigned to asset owner (from CMDB lookup)
5. Ticket status synced back to findings database:
   - "In Progress" → Finding status updated
   - "Resolved" → Finding status = "Pending Verification"
   - Re-test passed → Finding status = "Remediated", Ticket closed

**Example API Payload** (Jira):
```json
POST /rest/api/3/issue
{
  "fields": {
    "project": { "key": "SEC" },
    "summary": "[Critical] SQL Injection in Customer Portal",
    "description": "Vulnerability ID: finding-uuid-12345\nCVSS: 9.8\nAsset: portal.example.com\nDue Date: 2025-12-22\nFull details: https://vapt-portal/findings/finding-uuid-12345",
    "issuetype": { "name": "Security Vulnerability" },
    "priority": { "name": "Highest" },
    "assignee": { "name": "john.doe" },
    "duedate": "2025-12-22",
    "labels": ["vapt", "sql-injection", "critical"]
  }
}
```

---

### 2.5 SIEM Integration

**Purpose**: Real-time alerting and correlation of vulnerabilities with security events

**SIEM Platforms**:
- Splunk Enterprise / Splunk Cloud
- Elastic Stack (ELK)
- Microsoft Sentinel (Azure cloud)

**Integration**:
- **Syslog**: Forward vulnerability findings as syslog events
- **HTTP Event Collector** (Splunk HEC): JSON payload push
- **API**: Periodic sync of findings

**Use Cases**:
1. **Alert on Critical Finding**: When Critical vulnerability discovered in production → trigger SIEM alert → page on-call team
2. **Correlation**: Cross-reference vulnerability findings with exploitation attempts
   - Example: "SQL injection found in /api/users" + "SIEM detects SQLi payloads in /api/users logs" = Active exploitation

**Sample SIEM Alert** (Splunk):
```spl
sourcetype=vapt:finding severity=Critical status=New
| eval alert_message="Critical vulnerability discovered: ".vulnerability_title." on ".asset_name
| sendemail to="security-oncall@example.com" subject="CRITICAL VAPT Finding"
```

---

### 2.6 Metrics & Reporting Dashboard

**Purpose**: Real-time KPI visualization for management and operational teams

**Platform Options**:
- **Grafana** (Open Source, integrates with PostgreSQL)
- **Power BI** (Microsoft, enterprise reporting)
- **Tableau** (Advanced analytics)

**Recommended**: Grafana (real-time, cost-effective)

**Data Source**: PostgreSQL findings database

**Key Dashboards**:

#### Executive Dashboard
- Total open vulnerabilities (gauge chart: Critical, High, Medium, Low)
- SLA compliance percentage (line chart over time)
- Mean time to remediate (bar chart by severity)
- Top 10 most vulnerable assets

#### Operational Dashboard  
- Overdue vulnerabilities (table with countdown to breach)
- Vulnerabilities by status (pie chart: New, In Progress, Pending Verification)
- Remediation velocity (trend: vulnerabilities closed per week)
- Asset coverage (% of assets tested in last 90 days)

**Grafana Configuration**:
```yaml
# grafana-datasource.yml
apiVersion: 1
datasources:
  - name: VAPT Findings DB
    type: postgres
    url: findings-db.internal:5432
    database: vapt
    user: grafana_readonly
    secureJsonData:
      password: ${POSTGRES_PASSWORD}
    jsonData:
      sslmode: require
      postgresVersion: 1500
```

---

### 2.7 Secure Evidence Repository

**Purpose**: Centralized storage for all VAPT artifacts (reports, RoEs, remediation proofs) with strict access controls

**Platform Options**:
- **SharePoint Online** (Microsoft 365 E5) with DLP
- **On-Premise File Server** (Windows Server with NTFS ACLs)
- **Box.com** (with governance features)

**Recommended**: SharePoint Online (compliance features, DLP, audit logging)

**Directory Structure**:
```
/VAPT_Evidence/
├── /Policies/
│   ├── VAPT-Policy-v1.0-Signed.pdf
│   └── Methodology-Framework-v1.0.pdf
├── /2024/
│   ├── /Q1-2024-External-Pentest/
│   │   ├── RoE-Signed-2024-01-15.pdf
│   │   ├── Final-Report-2024-02-10.pdf
│   │   ├── Executive-Summary-2024-02-10.pdf
│   │   └── /Supporting_Evidence/
│   │       ├── screenshot_sql_injection_001.png
│   │       └── burp_traffic_capture.pcap (encrypted)
│   └── /Q2-2024-Cloud-Security-Assessment/
│       └── ...
├── /2025/
│   └── /Q1-2025-Internal-Infratest/
│       └── ...
├── /Risk_Acceptances/
│   ├── /2024/
│   │   └── RA-2024-003-Legacy-Server.pdf (signed waiver)
│   └── /2025/
└── /Remediation_Proofs/
    ├── /2024/
    └── /2025/
```

**Security Controls**:
| Control | Implementation |
|---------|----------------|
| **Access Control** | CISO: Full, Security Manager: Modify, SOC: Read-only, Auditors: Time-limited read during audits |
| **Encryption at Rest** | AES-256 (SharePoint native or BitLocker for file servers) |
| **Encryption in Transit** | TLS 1.3 |
| **Data Loss Prevention (DLP)** | Block downloads containing PII/credit card patterns (SharePoint DLP policies) |
| **Audit Logging** | All access logged (who, what file, when) - retained 7 years |
| **Versioning** | Enabled (documents immutable once finalized - version history preserved) |
| **Retention** | 7 years (ISO requirement), then secure deletion |
| **Backup** | Daily backups to separate geo-redundant location |

**Access Request Workflow**:
- Auditors request time-limited access via ticket
- Security Manager grants access (24-hour token or specific folder access for audit duration)
- Automated revocation after audit completion

---

## 3. Network Architecture

### 3.1 Network Segmentation (VLANs)

```
┌────────────────────────────────────────────────────────────────────┐
│                          Corporate Network                          │
└────────────────────────────────────────────────────────────────────┘

VLAN 10: Management Network (10.0.10.0/24)
  - Nessus Server, Faraday Server, Findings DB
  - Access: Security team only (MFA required)

VLAN 20: Production Network (10.0.20.0/24)
  - Production workloads being scanned
  - Nessus scans FROM VLAN 10 INTO VLAN 20 (firewall rule: Allow 8834/tcp from Nessus IP)

VLAN 30: Penetration Testing VLAN (10.0.30.0/24)
  - Kali Linux workstations for pentesters
  - Isolated from production (except during active engagement per RoE)
  - Internet access restricted (prevent data exfiltration)

VLAN 100: DMZ (externally accessible, scanned from internet and internally)
```

**Firewall Rules** (Simplified):
```
VLAN 10 (Management) → VLAN 20 (Production):
  Allow: TCP/445 (SMB), TCP/22 (SSH), TCP/3389 (RDP) for credentialed scans
  Source: Nessus Server IP only

VLAN 30 (Pentest) → VLAN 20 (Production):
  Deny by default (must request firewall exception per RoE, auto-expire after engagement)

VLAN 10 (Management) → Internet:
  Allow: HTTPS to Nessus plugin updates, CVE feed APIs
```

---

### 3.2 Cloud Integration

**For AWS/Azure/GCP Scanning**:

**AWS**:
- IAM Role: `VAPTSecurityAudit` (read-only, based on AWS `SecurityAudit` managed policy)
- Tools: Prowler, ScoutSuite, AWS Security Hub integration
- Trigger: Automated daily AWS Config snapshots exported to S3 → analyzed by Prowler → findings imported to database

**Azure**:
- Service Principal with `Security Reader` role
- Tools: ScoutSuite, Azure Defender integration

**GCP**:
- Service Account with `Security Reviewer` role
- Tools: ScoutSuite, GCP Security Command Center

---

## 4. Deployment Architecture

### 4.1 On-Premise Deployment

**Advantages**: Full control, sensitive data stays on-prem

**Infrastructure**: VMware vSphere or Hyper-V cluster

**Components**:
- 4 VMs (Nessus, Faraday, PostgreSQL, Grafana)
- 1 file server (Evidence Repository)
- Backup appliance (Veeam or Commvault)

**Total Resources**: 20 vCPUs, 48 GB RAM, 2 TB storage

---

### 4.2 Hybrid Cloud Deployment

**Advantages**: Scalability, disaster recovery

**Architecture**:
- **On-Premise**: Nessus (for internal scans), Evidence Repository (compliance)
- **Cloud (AWS/Azure)**: Findings Database (RDS/Azure SQL), Grafana (EKS/AKS), Backup (S3/Blob Storage)

**Benefits**:
- Managed database (automated backups, patching)
- Global accessibility for distributed teams
- Cost optimization (scale down non-business hours)

---

## 5. Budget Estimate

| Component | Annual Cost (Estimate) |
|-----------|------------------------|
| **Tenable Nessus Professional** (for 256 IPs) | $3,000 - $5,000 |
| **Faraday Platform** (Open Source - self-hosted) | $0 (or $5,000/year for Faraday Pro support) |
| **PostgreSQL** (self-hosted on VM or AWS RDS Small) | $0 (VM) or $2,000/year (RDS) |
| **Grafana** (Open Source) | $0 |
| **SharePoint Online** (included in M365 E5, or standalone E3: $8/user/month × 20 users) | $1,920/year |
| **VM Hosting** (on-prem) or **Cloud Compute** | $3,000 - $10,000/year |
| **Data retention/backup storage** (1TB × 7 years cloud storage) | $500 - $1,500/year |
| **Total Infrastructure** | **$10,420 - $25,420/year** |

*(Excludes labor costs, external pentest services)*

---

## 6. Disaster Recovery

| Scenario | Recovery Procedure | RTO | RPO |
|----------|-------------------|-----|-----|
| **Nessus Server Failure** | Restore from backup, redploy VM, reimport scan policies | 4 hours | 24 hours |
| **Database Corruption** | Point-in-time recovery from WAL archives | 2 hours | 1 hour |
| **Evidence Repository Loss** | Restore from geo-redundant backup (S3 cross-region) | 6 hours | 24 hours |
| **Complete Datacenter Loss** | Failover to cloud-based replicas (if hybrid deployment) | 24 hours | 24 hours |

---

## 7. Related Documents

- [VAPT Policy](../01-policy-governance/VAPT-Policy.md)
- [Findings Database Schema](./Findings-Database-Schema.md)
- [ISO 27001 Mapping](../03-compliance-integration/ISO-27001-Mapping.md)

---

**Document Control Log**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-15 | Infrastructure / Security Team | Initial infrastructure architecture |

---

*Internal - Technical*
