# ISO/IEC 27001:2022 Annex A Compliance Mapping
**Document Control**
- **Version**: 1.0.0
- **Effective Date**: December 15, 2025
- **Document Owner**: CISO / Information Security Manager
- **Classification**: Internal - Management

---

## 1. Purpose

Demonstrates how the VAPT program implements and provides evidence for ISO/IEC 27001:2022 Annex A controls, particularly those related to vulnerability management and security testing.

---

## 2. Key Annex A Controls Addressed by VAPT

### A.5.7: Threat Intelligence

**Control Statement**: "Information relating to information security threats shall be collected and analyzed to produce threat intelligence."

**VAPT Implementation**:
- **Threat Intelligence Sources**: CVE/NVD feeds, vendor advisories, CISA KEV, security mailing lists
- **Analysis**: Zero-day monitoring process evaluates applicability to organizational assets
- **Intelligence Integration**: VAPT findings feed into organizational threat model and risk assessments

**Evidence for Auditor**:
✅ [Zero-Day Response Process](../02 vapt-scope-inventory/Zero-Day-Response-Process.md) - threat intelligence integration
✅ Threat intelligence platform (TIP) logs showing feeds monitored
✅ Post-zero-day incident reports (e.g., Log4j response timeline)
✅ Updated threat models incorporating VAPT findings

---

### A.8.1: Asset Management (Inventory of Assets)

**Control Statement**: "Assets associated with information and information processing facilities shall be identified, and an inventory of these assets shall be drawn up and maintained."

**VAPT Implementation**:
- **Comprehensive Asset Inventory**: Dynamic register of all testable assets
- **Asset Attributes**: Criticality tier, data classification, owner, last test date
- **Link to VAPT**: Asset inventory drives testing schedule; untested assets flagged as compliance gaps

**Evidence for Auditor**:
✅ [Asset Inventory System](../02-vapt-scope-inventory/Asset-Inventory-System.md)
✅ Asset database export showing all fields populated
✅ Coverage dashboard (% of assets tested per policy)

---

### A.8.8: Management of Technical Vulnerabilities

**Control Statement (Primary VAPT Control)**:
"Information about technical vulnerabilities of information systems in use shall be obtained, the organization's exposure to such vulnerabilities shall be evaluated and appropriate measures shall be taken."

This is the **CORE CONTROL** for VAPT programs. Detailed implementation below.

---

## 3. A.8.8 Detailed Implementation (Core VAPT Control)

### A.8.8(a): Obtaining Information About Technical Vulnerabilities

**Requirement**: "Information about technical vulnerabilities"

**Our Implementation**:

| Source | Method | Frequency | Responsibility |
|--------|--------|-----------|----------------|
| **Vulnerability Scans** | Nessus/Qualys credentialed scans | Weekly | SOC (automated) |
| **Penetration Tests** | Manual testing per OWASP/PTES | Annual-Bi-annual per asset tier | Third-party + internal |
| **CVE/NVD Feeds** | API integration, automated alerts | Real-time | SOC |
| **Vendor Security Advisories** | Email subscriptions (Microsoft, Oracle, AWS, etc.) | As published | SOC |
| **Bug Bounty** (if applicable) | External researchers | Continuous | Security team triage |
| **Code Reviews** | SAST (SonarQube, Checkmarx) | Per commit (CI/CD) | DevOps |

**Evidence for Auditor**:
✅ Vulnerability scan schedules and outputs (Nessus scan reports from last quarter)
✅ Penetration test reports (last 3 engagements)
✅ CVE monitoring logs (screenshot of TIP dashboard)
✅ SAST integration in CI/CD (Jenkins pipeline configuration showing security scans)

---

### A.8.8(b): Evaluating Exposure to Vulnerabilities

**Requirement**: "Organization's exposure to such vulnerabilities shall be evaluated"

**Our Implementation**:

**1. Asset-Vulnerability Correlation**:
- Cross-reference discovered vulnerabilities against asset inventory
- Query: "Which assets are affected by CVE-2024-XXXXX?"
- Example:
  ```sql
  SELECT asset_name, criticality_tier, data_classification
  FROM assets
  WHERE software = 'OpenSSL' AND version IN ('1.1.1', '1.1.1a', ..., '1.1.1t')
  AND cve_id = 'CVE-2022-0778';  -- Infinite loop DoS
  ```

**2. Risk Scoring**:
- **CVSS Base Score** (vulnerability severity: 0-10)
- **+Business Context Adjustment**:
  - Asset criticality (Tier 1/2/3)
  - Data classification (Restricted/Confidential/Internal)
  - Exploit availability (public PoC? active exploitation?)
- **=Final Risk Rating** (Critical/High/Medium/Low)

**Example**:
> CVE-2024-1234: SQL Injection (CVSS 8.5 - High)  
> Asset: Customer Portal (Tier 1, Restricted data - PII)  
> Public Exploit: Yes  
> **Final Rating: CRITICAL** (High → Critical due to Tier 1 + PII)

**3. Exposure Reporting**:
- Automated: Critical findings → email+SMS to CISO within 4 hours
- Weekly: Vulnerability summary dashboard to IT Security Manager
- Quarterly: Executive risk report with trend analysis

**Evidence for Auditor**:
✅ Vulnerability assessment reports with CVSS scores
✅ [Risk Remediation Governance](../01-policy-governance/Risk-Remediation-Governance.md) (severity classification methodology)
✅ Critical finding notification emails (redacted examples)
✅ Vulnerability management dashboard (screenshot)

---

### A.8.8(c): Taking Appropriate Measures

**Requirement**: "Appropriate measures shall be taken to address the associated risks"

**Our Implementation: 4-Track Approach**

#### Track 1: Remediation (Primary Response)
- **Patching**: Apply vendor security updates per SLA:
  - Critical: 7 days
  - High: 30 days
  - Medium: 90 days
- **Configuration Changes**: Harden systems per CIS Benchmarks
- **Code Fixes**: Remediate application vulnerabilities (SQL injection → parameterized queries)
- **Removal**: Decommission unused/vulnerable services

**Workflow**:
```
Vulnerability Discovered
  ↓
Jira/ServiceNow Ticket Created (auto-assigned to asset owner)
  ↓
DevOps Remediates
  ↓
Re-Test Verification (SOC or pentester confirms fix)
  ↓
Ticket Closed (with evidence: patch version, clean scan screenshot)
```

#### Track 2: Compensating Controls (When Remediation Not Immediately Feasible)
- **WAF Virtual Patching**: Deploy ModSecurity/Cloudflare WAF rules to block exploits
- **Network Segmentation**: Isolate vulnerable systems (VLAN restrictions, firewall rules)
- **MFA**: Add authentication layer for privilege escalation paths
- **Monitoring**: Enhanced SIEM alerts for exploitation attempts

**Example**:
> Vulnerability: Unpatched Windows Server 2012 (EOL, vendor patch unavailable)  
> Compensating Controls:  
> - Isolated on dedicated VLAN (no internet access)  
> - Access restricted to 3 authorized admins (MFA required)  
> - IDS monitoring for lateral movement attempts  
> Status: Risk-Accepted with compensating controls (re-assessed annually)

#### Track 3: Risk Acceptance (Exception Process)
- **When Used**: Economic justification OR no technical solution OR imminent decommissioning
- **Approval**: High/Critical require CISO approval (Critical also needs CIO)
- **Documentation**: Risk acceptance form with expiration/renewal date (max 1 year)
- **Re-Assessment**: Quarterly review of all accepted risks

**Evidence**: [Risk Acceptance Request Form](../01-policy-governance/Risk-Remediation-Governance.md#appendix-a)

#### Track 4: Removal/Decommissioning
- **Vulnerable Legacy Systems**: If cannot patch or secure → decommission
- **Unused Services**: Remove attack surface (disable unused protocols, uninstall unnecessary software)

**Evidence for Auditor**:
✅ Remediation tickets (Jira/SNOW) showing full lifecycle:
- Opening (vulnerability discovered)
- Assignment (to responsible team)
- Remediation (patch applied, config changed)
- Verification (re-test clean)
- Closure (evidence attached)

✅ Sample tickets for each track:
- Track 1: Patched Apache Tomcat (Critical → remediated in 5 days)
- Track 2: Legacy app with WAF protection (compensating control)
- Track 3: Risk acceptance for decommissioning-scheduled server
- Track 4: Removed outdated TLS 1.0 support from web servers

✅ SLA compliance metrics (e.g., "98% of Critical vulnerabilities remediated within 7-day SLA in 2025")

---

### A.8.8(d): Logging and Monitoring (Implied in ISO 27001:2022)

**Our Implementation**:
- **All Scans Logged**: Nessus scan results stored for 7 years
- **Remediation Tracked**: Vulnerability management platform maintains full audit trail
- **Metrics Monitored**: MTTR, SLA compliance, vulnerability density

**Evidence for Auditor**:
✅ Vulnerability database with historical records
✅ [Findings Database Schema](../04-data-infrastructure/Findings-Database-Schema.md)
✅ Audit trail showing vulnerability lifecycle (from discovery to closure)

---

## 4. Additional Relevant Annex A Controls

### A.5.23: Information Security for Use of Cloud Services

**Control Statement**: "Processes for acquisition, use, management, and exit from cloud services shall be established."

**VAPT Linkage**:
- Cloud security assessments (AWS/Azure/GCP pentests) validate cloud configurations
- CIS Benchmark compliance testing

**Evidence**:
✅ Cloud-specific pentest reports
✅ Prowler/ScoutSuite scan results

---

### A.8.16: Monitoring Activities

**Control Statement**: "Networks, systems, and applications shall be monitored for anomalous behavior."

**VAPT Linkage**:
- VAPT findings → SIEM correlation rules
- Example: SQL injection vulnerability found → deploy SIEM rule to detect SQLi attempts

**Evidence**:
✅ SIEM rules created from VAPT findings
✅ SOC playbooks updated based on VAPT-identified attack paths

---

### A.8.23: Web Filtering

**Control Statement**: "Access to external websites shall be managed to reduce exposure to malicious content."

**VAPT Linkage**:
- Web application pentests validate filtering effectiveness
- Test for filter bypasses

---

### A.8.24: Use of Cryptography

**Control Statement**: "Rules for effective use of cryptography shall be defined and implemented."

**VAPT Linkage**:
- VAPT tests validate crypto implementation:
  - SSL/TLS configuration (testssl.sh, SSLScan)
  - Weak ciphers detected and reported
  - Certificate validation issues

**Evidence**:
✅ Pentest reports showing SSL/TLS findings
✅ Remediation: Disabled TLS 1.0/1.1, enforced TLS 1.3

---

### A.14.2: Security in Development and Support Processes

**Control Statement**: "Information security shall be integrated into development processes."

**VAPT Linkage**:
- Pre-production security testing (QA environment pentests required before prod)
- CI/CD security scans (SAST/DAST)

**Evidence**:
✅ CI/CD pipeline configs showing integrated security gates
✅ Pre-production test reports

---

## 5. ISO 27001 Audit Evidence Checklist

### For Certification Auditor

| Annex A Control | Evidence Required | VAPT Program Artifact |
|-----------------|-------------------|----------------------|
| **A.5.7** (Threat Intel) | Threat monitoring records | Zero-Day Response Process doc, TIP logs |
| **A.8.1** (Asset Mgmt) | Asset inventory | Asset Inventory System, database export |
| **A.8.8(a)** (Vuln Info) | Scan schedules, reports | Nessus scan reports, Pentest reports |
| **A.8.8(b)** (Exposure Eval) | Risk assessments | CVSS-scored findings, Risk Remediation Governance |
| **A.8.8(c)** (Measures) | Remediation records | Jira/SNOW tickets (closed with evidence), Risk acceptance forms |
| **A.8.8(d)** (Logging) | Audit trails | Findings database, 7-year retention proof |
| **A.8.16** (Monitoring) | SIEM integration | SIEM rules from VAPT findings |
| **A.8.24** (Crypto) | Crypto validation | SSL/TLS scan results |
| **A.14.2** (Secure Dev) | Pre-prod testing | QA pentest reports, CI/CD security gates |

---

## 6. Sample Audit Narrative

**Auditor Question**: *"How do youmanage technical vulnerabilities per A.8.8?"*

**Response**:
> "We have a comprehensive VAPT program that fully implements A.8.8:
>
> **(a) Obtaining vulnerability information**: We conduct weekly authenticated vulnerability scans using Nessus across all assets, plus annual to bi-annual penetration tests based on asset criticality. We also monitor CVE feeds and vendor advisories in real-time through our threat intelligence platform.
>
> **(b) Evaluating exposure**: When a vulnerability is discovered, we score it using CVSS v3.1, then adjust for business context—our Tier 1 assets with Restricted data (like customer PII databases) automatically elevate severity. We can query our asset inventory to instantly identify which systems are affected by any given CVE.
>
> **(c) Taking appropriate measures**: We have four tracks—remediation (with SLAs: 7 days for Critical, 30 for High, 90 for Medium), compensating controls (like WAF rules for unpatched systems), formal risk acceptance (CISO-approved), or decommissioning. All remediation is tracked in our ticketing system with re-test verification before closure. Last year, we achieved 98% SLA compliance for Critical vulnerabilities.
>
> **(d) Logging**: All vulnerability data is retained for 7 years in our findings database for audit purposes. We monitor metrics like mean-time-to-remediate and report quarterly to management."

---

## 7. Related Documents

- [VAPT Policy](../01-policy-governance/VAPT-Policy.md)
- [Asset Inventory System](../02-vapt-scope-inventory/Asset-Inventory-System.md)
- [Risk Remediation Governance](../01-policy-governance/Risk-Remediation-Governance.md)
- [Findings Database Schema](../04-data-infrastructure/Findings-Database-Schema.md)
- Corporate ISO/IEC 27001:2022 Information Security Policy
- Statement of Applicability (SoA)

---

**Document Control Log**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-15 | CISO / Security Team | Initial ISO 27001 mapping for VAPT |

---

*Internal - Management*
