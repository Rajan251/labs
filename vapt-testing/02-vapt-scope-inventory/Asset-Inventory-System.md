# Asset Inventory System
**Document Control**
- **Version**: 1.0.0
- **Effective Date**: December 15, 2025
- **Document Owner**: IT Security Manager
- **Review Cycle**: Quarterly (inventory updates continuous)
- **Classification**: Internal - Technical

---

## 1. Purpose and Scope

This document defines the system for maintaining a **dynamic, comprehensive asset inventory** that serves as the foundation for all VAPT activities.

**Objectives**:
1. **Complete Visibility**: Maintain accurate, up-to-date register of all in-scope assets subject to security testing
2. **Risk-Based Prioritization**: Classify assets by criticality to drive testing frequency and depth
3. **Test Coverage**: Ensure no critical asset goes untested within policy-defined intervals
4. **Compliance**: Satisfy ISO/IEC 27001:2022 Annex A.8.1 (Asset Management) requirements

**Principle**: **"If it's not in the inventory, it doesn't get tested. If it's not tested, it's a blind spot."**

---

## 2. Asset Classification Taxonomy

### 2.1 Asset Categories

All organizational IT assets are grouped into the following categories for VAPT purposes:

#### A. External-Facing Assets (Public Attack Surface)

**Definition**: Systems accessible from the Internet without VPN/corporate network access

| Asset Type | Examples | Primary Risk | Testing Priority |
|------------|----------|--------------|------------------|
| **Web Applications** | Corporate website, customer portals, SaaS products | Data breach, defacement, service disruption | **High** |
| **APIs (RESTful/SOAP)** | Public APIs, mobile backend services, partner integrations | Data exfiltration, unauthorized access | **High** |
| **Mobile Applications** | iOS/Android apps (company-published) | Data leakage, insecure storage, API abuse | **High** |
| **Email/Messaging Gateways** | MX records, webmail interfaces | Phishing relay, spam, email spoofing | **Medium** |
| **Network Perimeter** | External firewall interfaces, VPN gateways, load balancers | Unauthorized network access, DDoS | **High** |
| **DNS Infrastructure** | Authoritative nameservers | DNS hijacking, zone poisoning | **Medium** |

---

#### B. Cloud Infrastructure (IaaS/PaaS/SaaS)

**Definition**: Assets hosted in cloud environments (hybrid cloud model)

| Cloud Provider | Asset Types | Example Services | Security Concerns |
|----------------|-------------|------------------|-------------------|
| **Amazon Web Services (AWS)** | EC2, S3, RDS, Lambda, EKS, IAM | Production app servers, data lakes | Misconfigured S3 buckets, overly permissive IAM, unpatched EC2 |
| **Microsoft Azure** | Virtual Machines, Azure SQL, App Services, AKS, Entra ID | Enterprise applications | Public blob storage, weak RBAC, credential exposure |
| **Google Cloud Platform (GCP)** | Compute Engine, Cloud Storage, GKE, Cloud SQL | Analytics platforms | Publicly exposed storage, service account abuse |
| **Multi/Hybrid** | Kubernetes clusters, container registries, CI/CD pipelines | DevOps infrastructure | Container escapes, secrets in images, supply chain |

**Testing Focus**: 
- **Configuration Review**: CIS Benchmarks for cloud, AWS Security Hub, Azure Defender, GCP Security Command Center
- **Penetration Testing**: Simulated breach scenarios (compromised credentials, lateral movement)

---

#### C. Internal Network Assets

**Definition**: Systems accessible only from corporate network or VPN

| Category | Asset Types | Examples | Testing Frequency |
|----------|-------------|----------|-------------------|
| **Servers - Windows** | AD domain controllers, file servers, SQL Server, Exchange | DC01.corp.local, FileServer-A | Quarterly (authenticated scans), Annual (pentest) |
| **Servers - Linux** | Web servers, database servers (MySQL, PostgreSQL), application servers | app-server-01, db-prod-mysql-01 | Quarterly |
| **Servers - Virtualization** | VMware ESXi hosts, Hyper-V servers, vCenter | vcenter.corp.local, esx-host-03 | Bi-annual |
| **Database Servers** | Oracle, MS SQL, MySQL, PostgreSQL, MongoDB | customer-db-01, analytics-mongodb | Bi-annual (high priority due to sensitive data) |
| **Network Devices** | Core routers, switches (L2/L3), firewalls, IDS/IPS | cisco-core-switch-01, palo-alto-fw-dmz | Annual |
| **Wireless Infrastructure** | Wireless controllers, access points | wlc-01, ap-floor2-east | Annual (includes wireless pentest) |
| **Storage Systems** | SAN, NAS, backup appliances | netapp-nas-01, veeam-backup | Annual |

---

#### D. End-User Devices

**Definition**: Employee workstations and mobile devices

| Type | Asset Examples | Testing Approach |
|------|----------------|------------------|
| **Corporate Workstations** | Windows 10/11 laptops, MacBooks | **Sampled**: Vulnerability scans on representative sample (SOE - Standard Operating Environment) |
| **Corporate Mobile (MDM-Managed)** | Enrolled iPhones, Android devices | Configuration compliance checks (MDM policy enforcement) |
| **BYOD (Limited)** | Personal devices accessing corporate email | Network Access Control (NAC) validation only |

**Rationale**: Full testing of every endpoint is impractical; focus on **gold image** validation and policy enforcement.

---

#### E. Development & Non-Production

**Definition**: Pre-production environments

| Environment | Purpose | Testing Requirement |
|-------------|---------|---------------------|
| **Development (DEV)** | Coding, feature development | SAST/DAST in CI/CD (not in annual pentest scope, but scanned for credential leaks) |
| **Quality Assurance (QA/UAT)** | Pre-release testing | Full pentest required before production promotion |
| **Staging** | Production mirror | Configuration parity review with production |

**Rule**: Staging environments must be tested **before** production deployments (shift-left security).

---

#### F. Specialized & Emerging Technologies

| Asset Type | Examples | Unique Testing Considerations |
|------------|----------|-------------------------------|
| **IoT Devices** | Smart building systems (HVAC, lighting), IP cameras, badge readers | Firmware analysis, default credentials, unencrypted protocols |
| **OT/ICS/SCADA** (if applicable) | Industrial control systems, PLCs, RTUs | **Requires specialized OT security testing (coordination with operations to avoid disruption)** |
| **Containerized Apps** | Docker containers, Kubernetes pods | Image vulnerability scanning (Trivy), runtime security (Falco), K8s RBAC |
| **Serverless Functions** | AWS Lambda, Azure Functions | IAM permissions, function code review, API Gateway security |

---

## 3. Asset Inventory Data Model

### 3.1 Core Asset Attributes

Every asset in the inventory must have the following fields:

| Field | Type | Description | Example | Required |
|-------|------|-------------|---------|----------|
| **Asset ID** | UUID | Unique identifier | `AST-2025-04523` | ✅ Yes |
| **Asset Name** | String | Descriptive name | `Customer Portal - Production` | ✅ Yes |
| **Asset Type** | Enum | From taxonomy above | `Web Application` | ✅ Yes |
| **Hostname/URL** | String | Network identifier | `portal.example.com` or `192.168.1.50` | ✅ Yes |
| **IP Address(es)** | Array | IPv4/IPv6 addresses | `[203.0.113.10, 2001:db8::1]` | Conditional (N/A for SaaS) |
| **Environment** | Enum | `Production / Staging / QA / Dev` | `Production` | ✅ Yes |
| **Owner** | String | Business unit or individual | `Engineering Team - John Doe` | ✅ Yes |
| **Technical Contact** | String | DevOps/admin responsible | `jane.admin@example.com` | ✅ Yes |
| **Criticality Tier** | Enum | `Tier 1 / Tier 2 / Tier 3` (see § 3.2) | `Tier 1` | ✅ Yes |
| **Data Classification** | Enum | `Restricted / Confidential / Internal / Public` | `Restricted (PII)` | ✅ Yes |
| **Compliance Scope** | Array | Applicable regulations | `[PCI-DSS, GDPR, ISO 27001]` | ✅ Yes |

---

### 3.2 Testing Metadata

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| **Last Test Date** | Date | Most recent VAPT activity | `2025-09-15` |
| **Last Test Type** | Enum | `Vulnerability Scan / Pentest / Config Review` | `Penetration Test` |
| **Next Test Due** | Date | Auto-calculated based on policy frequency | `2026-03-15` (bi-annual for Tier 1 web app) |
| **Test Frequency** | Enum | Policy-defined cadence | `Bi-annual` |
| **Open Vulnerabilities** | Integer | Count of unresolved findings | `3 (1 High, 2 Medium)` |
| **Test Status** | Enum | `Compliant / Overdue / Upcoming` | `Compliant` |

---

### 3.3 Asset Criticality Tiering

**Criticality determines testing depth, frequency, and remediation SLAs.**

#### Tier 1: Mission-Critical

**Definition**: Assets whose compromise would cause:
- **Severe Business Impact**: Direct revenue loss, regulatory penalties, major reputational damage
- **High Data Sensitivity**: Access to PII, PCI, PHI, intellectual property, authentication systems

**Examples**:
- Payment processing systems
- Customer-facing e-commerce platform
- Production databases containing PII
- Active Directory domain controllers
- CEO/CFO email accounts (high-value targets)

**Testing Requirements**:
- **Frequency**: Bi-annual penetration tests + weekly authenticated scans
- **Depth**: White-box or gray-box (most thorough)
- **Remediation SLA**: Critical=7 days, High=30 days
- **Third-Party Validation**: Annual external pentest mandatory

---

#### Tier 2: Important Business Systems

**Definition**: Assets that support critical operations but have some redundancy or limited public exposure

**Examples**:
- Internal business applications (CRM, ERP)
- Employee-facing portals (HR self-service, IT helpdesk)
- Backup/DR systems
- Internal file servers

**Testing Requirements**:
- **Frequency**: Annual penetration test + quarterly authenticated scans
- **Depth**: Gray-box testing
- **Remediation SLA**: Critical=7 days, High=30 days, Medium=90 days

---

#### Tier 3: Low-Impact Systems

**Definition**: Assets with minimal business impact if compromised or development/test systems

**Examples**:
- Development environments (with synthetic data)
- Archived legacy systems (read-only access)
- Internal documentation wikis
- Test lab infrastructure

**Testing Requirements**:
- **Frequency**: Annual vulnerability scan (authenticated), pentest only if high-risk findings emerge
- **Depth**: Automated scanning (black-box)
- **Remediation SLA**: Critical=30 days, High=90 days, Medium/Low=Next maintenance window

---

### 3.4 Data Classification Impact

| Data Classification | Types of Data | Impact on Asset Criticality |
|---------------------|---------------|----------------------------|
| **Restricted** | PII (names, SSNs, financial data), PCI (credit card numbers), PHI (medical records), Trade secrets | **Always Tier 1 or Tier 2** |
| **Confidential** | Internal communications, business plans, non-public financials | Tier 2 minimum |
| **Internal** | Employee directory, internal procedures | Tier 2 or Tier 3 |
| **Public** | Marketing materials, public website content | Tier 3 (unless public-facing production) |

---

## 4. Asset Discovery and Registration

### 4.1 Discovery Methods

**Automated Discovery**:

| Method | Frequency | Tools | Output |
|--------|-----------|-------|--------|
| **Network Scanning** | Weekly | Nmap, Masscan | All live IPs on corporate networks |
| **Cloud API Querying** | Daily | AWS Config, Azure Resource Graph, GCP Asset Inventory | All cloud resources in subscriptions |
| **CMDB Sync** | Real-time (via API) | ServiceNow, Jira Assets | Officially registered assets |
| **Active Directory Query** | Daily | PowerShell scripts | All domain-joined computers |
| **Certificate Transparency Logs** | Weekly | Certificate transparency monitors | Newly issued SSL certificates (identifies new subdomains) |

**Semi-Automated Discovery**:
- **CASB (Cloud Access Security Broker)**: Discover shadow IT (SaaS apps accessed by employees)
- **Agent-Based Reporting**: Endpoint detection and response (EDR) agents report installed software

**Manual Registration**:
- **New Project Intake Process**: All new applications must complete security questionnaire, which automatically creates asset record
- **Change Management Integration**: New production deployments trigger asset registration

---

### 4.2 Asset Registration Workflow

**Step 1: Discovery**
- Asset identified via automated scan or manual submission

**Step 2: Validation**
- IT Security team confirms asset is in-scope (not third-party or out-of-scope)
- Asset owner identified via CMDB or project documentation

**Step 3: Classification**
- Criticality tier assigned based on business impact assessment (questionnaire)
- Data classification determined (scan for PII, query data catalog)

**Step 4: Test Scheduling**
- Next test date auto-calculated based on asset type + criticality (per policy matrix)
- Added to master VAPT calendar

**Step 5: Notification**
- Asset owner notified via email: "Your asset [name] has been added to the VAPT inventory and is scheduled for testing on [date]"

---

### 4.3 Change Management Integration

**Trigger**: Any production deployment or infrastructure change

**Process**:
1. Change Request (CR) submitted via ServiceNow/Jira
2. Automated check: "Does this CR introduce a new asset or modify an existing tested asset?"
   - **Yes** → Security review required (asset inventory update)
   - **No** → Proceed with standard approval
3. Asset inventory updated with new version, last change date
4. If significant change (e.g., major code refactor, new network exposure): Trigger ad-hoc security test

**Example**:
> CR-2025-1234: "Migrate customer portal from on-prem to AWS"
> → Asset record updated: Environment changed to "AWS", New URL: `portal-new.example.com`
> → Trigger: Pre-migration pentest scheduled (ensures new environment is secure before cutover)

---

## 5. Asset Inventory Maintenance

### 5.1 Data Quality Standards

**Target Metrics**:
- **Accuracy**: >98% of registered assets are current and reachable
- **Completeness**: 100% of production assets cataloged
- **Freshness**: Inventory synchronized with reality within 24 hours of changes

**Quality Checks**:
- **Monthly Reconciliation**: Compare inventory against:
  - Network scan results (detect unregistered IPs)
  - Cloud resource exports (detect unregistered instances)
  - CMDB (identify discrepancies)
- **Quarterly Review**: Asset owners confirm their assets are still accurate (email campaign)

---

### 5.2 Decommissioning Process

**Asset End-of-Life Workflow**:
1. Asset owner submits decommissioning request
2. Final security scan performed (ensure data wiped, no residual exposure)
3. Asset status changed to **"Decommissioned"** (not deleted - retained for audit history)
4. Outstanding vulnerabilities auto-closed (reason: "Asset decommissioned")

**Retention**: Decommissioned asset records retained for 3 years (audit trail).

---

### 5.3 Orphaned Asset Management

**Definition**: Assets discovered in scans but not registered in CMDB (rogue IT)

**Process**:
1. **Identification**: Weekly scan reveals IP/host not in inventory
2. **Triage**: IT Security investigates (query DHCP logs, AD, cloud consoles)
3. **Action**:
   - **Legitimate**: Owner found → Add to inventory
   - **Shadow IT**: Unauthorized deployment → Escalate to IT management, potentially quarantine
   - **Abandoned**: No owner → Mark for decommissioning after 30-day grace period

**Risk**: Orphaned assets are highest risk—often unpatched and unmonitored.

---

## 6. Integration with VAPT Program

### 6.1 Automated Test Scheduling

**Integration Logic**:

```plaintext
IF (Asset.NextTestDue - TODAY) <= 7 days THEN
    Generate RoE template pre-filled with Asset details
    Notify IT Security Manager: "Asset [name] test due in [X] days"
    Create calendar event for testing team
    Email asset owner: "Please prepare for upcoming testing (review RoE)"
END IF

IF (Asset.NextTestDue < TODAY) THEN
    Set Asset.TestStatus = "OVERDUE"
    Escalate to CISO (weekly summary of overdue tests)
    Flag in ISO compliance dashboard (audit risk)
END IF
```

---

### 6.2 Finding Linkage

**Bi-Directional Relationship**:
- **Asset Record → Vulnerabilities**: View all findings for a specific asset
- **Vulnerability → Asset**: Trace finding back to affected system

**Dashboard View Example**:

```
Asset: Customer Portal (AST-2025-04523)
┌───────────────────────────────────────────────────────┐
│ Criticality: Tier 1 | Data: Restricted (PII)         │
│ Last Test: 2025-09-15 | Next Test: 2026-03-15        │
├───────────────────────────────────────────────────────┤
│ Open Vulnerabilities: 3                               │
│   🔴 Critical: 0                                      │
│   🟠 High: 1 (SQL Injection - Due: 2025-10-10) OVERDUE│
│   🟡 Medium: 2 (Missing Security Headers, SSL Config) │
├───────────────────────────────────────────────────────┤
│ Test History:                                         │
│   - 2025-09-15: Penetration Test (External)          │
│   - 2025-06-01: Vulnerability Scan                   │
│   - 2024-12-10: Code Review (Pre-deployment)         │
└───────────────────────────────────────────────────────┘
```

---

## 7. Reporting and Metrics

### 7.1 Asset Inventory Reports

**Weekly Operations Report**:
- Total assets by category
- New assets registered this week
- Assets with overdue tests
- Orphaned assets discovered

**Monthly Executive Summary**:
- Asset coverage percentage (% of production assets tested within policy frequency)
- Top 5 asset classes with highest vulnerability density
- Decommissioned assets (risk reduction)

**Annual Audit Report** (for ISO certification):
- Complete asset inventory export (CSV/Excel)
- Evidence of regular inventory reviews (meeting minutes)
- Coverage attestation (all Tier 1 assets tested per policy)

---

### 7.2 Key Performance Indicators (KPIs)

| KPI | Target | Current | Trend |
|-----|--------|---------|-------|
| **Asset Coverage (Tier 1)** | 100% tested within policy frequency | [Calculate monthly] | [Improving/Stable/Degrading] |
| **Asset Coverage (All Tiers)** | >95% | | |
| **Inventory Accuracy** | >98% (reconciliation match rate) | | |
| **Mean Time to Register New Asset** | <48 hours from discovery | | |
| **Orphaned Assets** | <5 at any time | | |

---

## 8. Compliance Mapping

### 8.1 ISO/IEC 27001:2022 Annex A.8.1 (Asset Management)

**Control Requirement**: "Assets associated with information and information processing facilities shall be identified, and an inventory of these assets shall be drawn up and maintained."

**Implementation Evidence**:
- ✅ Comprehensive asset inventory (this system)
- ✅ Asset ownership assigned (Owner field)
- ✅ Acceptable use defined (testing policy applied to all assets)
- ✅ Return of assets process (decommissioning workflow)

**Audit Artifacts**:
- Asset inventory database export (as of audit date)
- Sample asset records showing all required fields populated
- Evidence of quarterly inventory reviews (meeting minutes, email confirmations)

---

### 8.2 ISO 9001:2015 (Operational Planning)

**Clause 8.1**: "The organization shall plan, implement, and control the processes needed to meet requirements for provision of products and services."

**Linkage**: Asset inventory is the input to VAPT planning (operational process). Without complete inventory, testing cannot be properly planned.

---

## 9. Tools and Technology

### 9.1 Recommended Platforms

**Asset Inventory Database**:
- **Option 1**: ServiceNow CMDB (Configuration Management Database) with custom VAPT fields
- **Option 2**: Jira Assets (formerly Insight) with asset schemas
- **Option 3**: Dedicated GRC platform (Archer, ServiceNow GRC, LogicGate)

**Integration Requirements**:
- API access for automated discovery tools to update inventory
- Integration with vulnerability management platform (Nessus, Qualys) to link findings
- Integration with ticketing system for remediation workflow

---

### 9.2 Discovery Tool Suite

| Tool | Purpose | Deployment |
|------|---------|------------|
| **Nmap/Masscan** | Internal network discovery | Scheduled scans from scan server |
| **AWS Config** | AWS resource inventory | Enabled on all AWS accounts |
| **Azure Resource Graph** | Azure resource inventory | Query via Azure CLI automation |
| **GCP Asset Inventory** | GCP resource inventory | API integration |
| **Shodan/Censys** | External attack surface monitoring | Weekly API queries for org domains |

---

## 10. Roles and Responsibilities

| Role | Responsibilities |
|------|------------------|
| **IT Security Manager** | Overall inventory accuracy, approval of asset classifications, quarterly review |
| **SOC Team** | Execute automated discovery scans, triage orphaned assets |
| **Asset Owners** | Validate asset details, confirm data classification, approve testing windows |
| **CMDB Administrators** | Maintain CMDB integration, data quality |
| **DevOps Teams** | Register new production deployments, update inventory on infrastructure changes |

---

## 11. Continuous Improvement

### 11.1 Lessons Learned Integration

**Example**:
> "2024-Q3 Pentest: Tester discovered production API subdomain `api-v2.example.com` not in inventory, leading to year-old unpatched vulnerabilities."
> 
> **Root Cause**: Certificate transparency monitoring only checked `*.example.com`, missed multi-level subdomains.
> 
> **Corrective Action**: Updated CT log monitoring script to detect all subdomains (regex: `.*\.example\.com`). Added alerting for any new TLS certificate issuance.
> 
> **Result**: 12 additional subdomains discovered and added to inventory within 2 weeks.

---

## 12. Related Documents

- [VAPT Policy](../01-policy-governance/VAPT-Policy.md)
- [Testing Schedule Matrix](./Testing-Schedule-Matrix.md)
- [Data Classification Handling](./Data-Classification-Handling.md)
- [ISO 27001 Mapping](../03-compliance-integration/ISO-27001-Mapping.md)

---

**Document Control Log**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-15 | IT Security Team | Initial asset inventory system design |

---

*This document is marked as **Internal - Technical**. Distribution limited to IT and security teams.*
