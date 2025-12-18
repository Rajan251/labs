# Testing Schedule Matrix
**Document Control**
- **Version**: 1.0.0
- **Effective Date**: December 15, 2025
- **Document Owner**: IT Security Manager
- **Review Cycle**: Annual
- **Classification**: Internal - Technical

---

## 1. Master Testing Calendar

This matrix defines the **frequency and type** of VAPT activities for each asset class based on criticality tier and exposure level.

---

## 2. Annual Testing Schedule by Asset Class

### 2.1 External-Facing Assets

| Asset Type | Criticality | Test Type | Frequency | Performer | Compliance Driver |
|------------|-------------|-----------|-----------|-----------|-------------------|
| **Public Web Applications** | Tier 1 | Penetration Test (Black-box) | Annual | Third-party certified | PCI-DSS (if payment processing) |
| | | Penetration Test (White-box) | Bi-annual | Third-party or internal | ISO 27001 A.8.8 |
| | | Vulnerability Scan | Weekly | Automated (Nessus) | Continuous monitoring |
| **Public APIs** | Tier 1 | API Security Test | Bi-annual | Third-party (OWASP API Top 10) | ISO 27001 A.8.8 |
| | | Automated API Scan | Weekly | Automated | Continuous monitoring |
| **Mobile Applications** | Tier 1 | Mobile App Pentest (iOS/Android) | Per major release + Annual | Third-party (OWASP MASVS) | App store security requirements |
| | | SAST/DAST Scans | Per build (CI/CD) | Automated | DevSecOps |
| **Network Perimeter** | Tier 1 | External Black-box Pentest | Annual | Third-party | ISO 27001 A.8.8 |
| | | External Vulnerability Scan | Weekly | Automated | PCI-DSS Requirement 11.2 |

---

### 2.2 Cloud Infrastructure

| Cloud Provider | Asset Type | Test Type | Frequency | Performer | Tools/Standards |
|----------------|------------|-----------|-----------|-----------|-----------------|
| **AWS** | EC2, S3, RDS, Lambda, IAM | Cloud Security Assessment | Bi-annual | Third-party AWS certified | Prowler, AWS Security Hub, CIS AWS Benchmark |
| | | Automated Config Scans | Daily | AWS Config, Security Hub | Native cloud tools |
| **Azure** | VMs, Storage, SQL, App Services | Cloud Security Assessment | Bi-annual | Third-party Azure certified | ScoutSuite, Azure Defender, CIS Azure Benchmark |
| | | Automated Config Scans | Daily | Azure Security Center/Defender | Native cloud tools |
| **GCP** | Compute Engine, Cloud Storage, GKE | Cloud Security Assessment | Bi-annual | Third-party GCP certified | ScoutSuite, Security Command Center, CIS GCP Benchmark |
| | | Automated Config Scans | Daily | GCP Security Command Center | Native cloud tools |
| **Kubernetes** | EKS, AKS, GKE clusters | Container Security Review | Quarterly | Internal + annual third-party | kube-bench, kube-hunter, Trivy |
| **Container Images** | Docker images in registries | Image Vulnerability Scan | Per build + daily registry scan | Trivy, Clair, Snyk | CI/CD integrated |

---

### 2.3 Internal Infrastructure

| Asset Category | Test Type | Tier 1 Frequency | Tier 2 Frequency | Tier 3 Frequency | Performer |
|----------------|-----------|------------------|------------------|------------------|-----------|
| **Windows Servers** (AD, File, SQL) | Authenticated Vulnerability Scan | Weekly | Bi-weekly | Monthly | Nessus/Qualys |
| | Penetration Test | Bi-annual | Annual | On-demand | Internal SOC |
| | | Annual (includes AD pentest) | Annual | - | Third-party |
| **Linux Servers** (Web, App, DB) | Authenticated Vulnerability Scan | Weekly | Bi-weekly | Monthly | Nessus/Qualys |
| | Penetration Test | Bi-annual | Annual | On-demand | Internal SOC + annual third-party |
| **Database Servers** (All types) | Database Vulnerability Scan | Weekly | Bi-weekly | Monthly | Nessus DB plugins, AppDetectivePRO |
| | Database Security Assessment | Bi-annual | Annual | - | Third-party (compliance requirement for PII/PCI) |
| **Network Devices** (Routers, Switches, Firewalls) | Configuration Audit | Quarterly | Quarterly | Annual | Nipper, manual config review |
| | Penetration Test | Annual | Annual | On-demand | Third-party |
| **Wireless Networks** | Wireless Pentest | Annual | Annual | N/A | Third-party (includes WPA/WPA2 testing) |
| | Rogue AP Detection | Continuous | Continuous | Continuous | WIPS (Wireless Intrusion Prevention System) |

---

### 2.4 Development & Pre-Production

| Environment | Test Type | Frequency | Gate Control |
|-------------|-----------|-----------|--------------|
| **QA/UAT** | Security Test (same as prod requirements) | Before EVERY production promotion | **Go/No-Go Decision**: Pass required for prod deployment |
| **Staging** | Configuration Parity Review | Monthly | Ensure staging mirrors production security configs |
| **Development** | SAST (Static Analysis) | Per commit (CI/CD) | Code quality gate |
| | Secrets Scanning | Per commit (CI/CD) | Block commits with hardcoded credentials |
| | Dependency Vulnerability Scan | Daily | Alert on vulnerable libraries (Dependabot, Snyk) |

---

### 2.5 Specialized Assets

| Asset Type | Test Type | Frequency | Special Considerations |
|------------|-----------|-----------|------------------------|
| **IoT Devices** | IoT Security Assessment | Annual | Includes firmware analysis, default credentials check, protocol security (MQTT, CoAP) |
| **OT/ICS/SCADA** (if applicable) | OT Security Assessment | Annual | **Requires coordination with operations, potential for service disruption—testing in maintenance windows only** |
| | | | Use OT-specialized testers (ICS-CERT certified) |
| **Legacy Systems** (EOL OS, unsupported apps) | Vulnerability Scan | Monthly (compensating controls required) | High risk—prioritize decommissioning or network isolation |

---

## 3. Continuous Testing Activities

### 3.1 Weekly Baseline Scans

**Scope**: All in-scope assets (Tier 1, 2, 3)

**Type**: Authenticated credentialed vulnerability scans

**Schedule**: 
- **Internal Assets**: Every Sunday, 02:00-06:00 (off-hours to minimize impact)
- **External Assets**: Every Wednesday, 03:00-05:00

**Configuration**:
- Credentialed scans (admin-level access for thorough checks)
- Safe checks only (no exploitation, no DoS-risk plugins)
- Scan profiles per asset class (Windows, Linux, Network Device templates)

**Output**: 
- Automated report generation
- Critical/High findings trigger immediate alert to SOC
- Findings auto-imported to vulnerability management platform

**Tool**: Tenable Nessus Professional / Qualys VMDR

---

### 3.2 CI/CD Integrated Security Scans

**Trigger**: Every code commit and build

**Scans**:
1. **SAST (Static Application Security Testing)**:
   - Tools: SonarQube, Checkmarx, Semgrep
   - Detects: Code vulnerabilities (injection, XSS, hardcoded secrets)
   - Gate: Block merge if Critical findings detected

2. **Secrets Scanning**:
   - Tools: GitGuardian, TruffleHog, GitHub Secret Scanning
   - Detects: API keys, passwords, tokens in code
   - Gate: Block commit, force secret rotation

3. **Dependency Scanning (SCA - Software Composition Analysis)**:
   - Tools: Snyk, Dependabot, OWASP Dependency-Check
   - Detects: Vulnerable third-party libraries
   - Gate: Alert on High/Critical CVEs in dependencies

4. **Container Image Scanning**:
   - Tools: Trivy, Clair, Anchore
   - Detects: Vulnerabilities in base images and packages
   - Gate: Block deployment if Critical CVEs in production images

5. **DAST (Dynamic Application Security Testing)** (Pre-Production):
   - Tools: OWASP ZAP, Burp Suite (headless mode)
   - Detects: Runtime vulnerabilities
   - Gate: Required for release candidate builds

**Integration**: Jenkins, GitLab CI, GitHub Actions pipelines

---

## 4. Quarterly Testing Activities

### 4.1 Q1 (January - March)

| Week | Activity | Assets | Type |
|------|----------|--------|------|
| Week 2-3 | **Internal Infrastructure Assessment** | Tier 1 & 2 Windows/Linux servers | Authenticated scan + manual config review |
| Week 6-8 | **Cloud Security Review** | AWS/Azure/GCP (Bi-annual cadence) | CIS Benchmark audit, IAM review |
| Week 10-12 | **Vulnerability Remediation Sprint** | All assets with open Medium+ findings | Focus on SLA-approaching vulnerabilities |

---

### 4.2 Q2 (April - June)

| Week | Activity | Assets | Type |
|------|----------|--------|------|
| Week 2-4 | **External Penetration Test** (Annual) | Public web apps, APIs, network perimeter | Third-party black-box pentest |
| Week 6 | **Mobile App Pentest** (if new major release) | iOS/Android apps | Third-party OWASP MASVS testing |
| Week 8-10 | **Wireless Network Assessment** (Annual) | Corporate Wi-Fi, guest networks | WPA3 testing, rogue AP detection validation |
| Week 12 | **Management Review** | N/A | Present Q1-Q2 VAPT results to CISO, update risk register |

---

### 4.3 Q3 (July - September)

| Week | Activity | Assets | Type |
|------|----------|--------|------|
| Week 2-3 | **Internal Infrastructure Assessment** | Tier 1 & 2 servers (quarterly cadence) | Authenticated scan |
| Week 6-8 | **Web Application Pentest** (Bi-annual) | Critical web applications (Tier 1) | White-box/gray-box pentest (internal or third-party) |
| Week 10-12 | **Physical Security Assessment** (if in scope, annual) | Data centers, office facilities | Badge access testing, tailgating attempts (with approval) |

---

### 4.4 Q4 (October - December)

| Week | Activity | Assets | Type |
|------|----------|--------|------|
| Week 2-4 | **Annual Third-Party Infrastructure Pentest** | Internal network, AD, critical servers | Comprehensive third-party assessment |
| Week 6-8 | **API Security Testing** (Bi-annual) | RESTful APIs, GraphQL endpoints | OWASP API Top 10 testing |
| Week 10-11 | **IoT/OT Assessment** (if applicable, annual) | Smart building systems, ICS | Specialized IoT/OT security testing |
| Week 12 | **Year-End Compliance Review** | All assets | Verify 100% coverage for ISO audit, identify gaps |
| Week 13 | **Annual Policy Review & Planning** | N/A | Update VAPT policy, plan next year's testing calendar |

---

## 5. Event-Driven (Ad-Hoc) Testing

### 5.1 Triggers for Out-of-Cycle Testing

| Trigger Event | Response Timeline | Test Type |
|---------------|-------------------|-----------|
| **Critical Zero-Day Announced** (e.g., Log4Shell) | Within 24 hours | Targeted scan for affected systems, emergency patching validation |
| **New Production Deployment** | Before go-live (mandatory gate) | Security test matching prod requirements (e.g., pentest for Tier 1 app) |
| **Major Infrastructure Change** (cloud migration, network redesign) | Within 2 weeks post-change | Configuration review + targeted pentest |
| **Security Incident / Breach** | Immediately post-incident | Forensic analysis + residual vulnerability assessment |
| **M&A Due Diligence** | Per deal timeline | Full security assessment of target company infrastructure |
| **Regulatory Audit Preparation** (ISO, PCI, SOC 2) | 60 days before audit | Comprehensive testing to ensure coverage, gap remediation |
| **Vendor-Reported Vulnerability** | Within 48 hours of notification | Validate applicability, test patch effectiveness |

---

### 5.2 Zero-Day Response Protocol

**Hour 0-6**: Alert and Triage
1. Zero-day CVE announcement detected (via CVE feeds, vendor advisory, threat intelligence)
2. SOC team assesses applicability (query asset inventory for affected software/versions)
3. If applicable: Escalate to CISO (Critical severity assumed for active exploitation)

**Hour 6-24**: Emergency Scanning
4. Deploy detection scripts/scans to identify vulnerable instances
5. Prioritize Tier 1 assets for immediate patching or mitigation

**Day 1-3**: Remediation and Verification
6. Apply vendor patches or interim mitigations (WAF rules, network isolation)
7. Re-scan to verify vulnerability remediated
8. Document response timeline (post-incident review for continuous improvement)

**Example Timeline Reference**: [Log4j Response 2021]
- Dec 9, 2021 (18:00 UTC): Vulnerability disclosed
- Dec 10, 2021 (04:00): Organization begins asset inventory scan for Log4j
- Dec 10, 2021 (12:00): 87 vulnerable instances identified
- Dec 10-12, 2021: Emergency patching (completed 95% within 48 hours)

---

## 6. Coordination and Communication

### 6.1 Testing Notifications

**30 Days Before**: 
- Email asset owners: "Upcoming VAPT activity scheduled for [date range]"
- Request: Confirm testing window, provide updated credentials if needed, identify any business-critical periods to avoid

**7 Days Before**:
- RoE finalized and signed
- Testing team confirmed
- Communication plan established (primary/secondary contacts)

**During Testing**:
- Daily status emails from testing team
- SOC monitors for any unintended impact (performance degradation alerts)

**Post-Testing** (within 5 business days):
- Draft report delivered
- Findings review meeting scheduled

---

### 6.2 Business Impact Coordination

**Production Testing Constraints**:
- **Peak Business Hours**: Avoid testing during known high-traffic periods (e.g., e-commerce sites on Black Friday)
- **Month-End/Quarter-End**: No financial system testing during close periods
- **Deployment Freeze Periods**: Align with change management calendar (typically freeze 2 weeks before major releases)

**Approval Requirements**:
- Tier 1 Production Systems: Require **Business Unit VP approval** for testing window (in addition to CISO)
- Customer-Facing Systems: **Customer Support team notification** (prepare for potential user reports)

---

## 7. Coverage Tracking and Compliance

### 7.1 Asset Coverage Dashboard

**Metrics Displayed**:
```
┌─────────────────────────────────────────────────────────────┐
│              VAPT Coverage Dashboard (2025)                  │
├─────────────────────────────────────────────────────────────┤
│ Tier 1 Assets: 47 total                                     │
│   ✅ Tested within policy: 45 (95.7%)                       │
│   ⚠️  Overdue: 2 (Customer Portal API, Legacy Auth Service) │
│                                                              │
│ Tier 2 Assets: 132 total                                    │
│   ✅ Tested within policy: 125 (94.7%)                      │
│   ⚠️  Overdue: 7                                            │
│                                                              │
│ Tier 3 Assets: 289 total                                    │
│   ✅ Tested within policy: 267 (92.4%)                      │
│   ⚠️  Overdue: 22                                           │
│                                                              │
│ Overall Compliance: 94.1%                                   │
│ Target: >95% (All Tiers), 100% (Tier 1)                    │
└─────────────────────────────────────────────────────────────┘
```

**Weekly Review**: IT Security Manager reviews overdue tests, assigns resources to close gaps

---

### 7.2 ISO Compliance Evidence

**For ISO 27001 Auditor**:
- ✅ Testing Schedule Matrix (this document) - demonstrates planned approach
- ✅ Actual Testing Calendar (Gantt chart or project plan) - execution evidence
- ✅ Coverage Report - shows all assets tested per policy
- ✅ Test Reports Archive - evidence repository with all deliverables

**Audit Question**: *"How do you ensure all critical assets are tested regularly?"*

**Answer**: "We maintain a dynamic asset inventory (see Asset Inventory System doc) with each asset assigned a testing frequency based on criticality tier and compliance requirements. Our Testing Schedule Matrix defines the cadence. We track coverage via automated dashboard, and overdue tests are escalated to CISO weekly. Current Tier 1 coverage is [X]%, meeting our 100% target."

---

## 8. Budget and Resource Planning

### 8.1 Annual Testing Budget Estimate

| Activity | Annual Cost (Estimate) | Notes |
|----------|------------------------|-------|
| **External Penetration Testing** | $40,000 - $80,000 | 2-3 engagements/year, $15-30K per test depending on scope |
| **Cloud Security Assessments** | $20,000 - $40,000 | Bi-annual, multi-cloud environments |
| **Mobile App Testing** | $15,000 - $25,000 | Per major release (typically 2-3 per year) |
| **Vulnerability Scanning Tools** | $25,000 - $50,000 | Nessus/Qualys licenses (based on IP count) |
| **SAST/DAST Tools** | $30,000 - $100,000 | SonarQube, Snyk, Checkmarx (enterprise licenses) |
| **Internal SOC Staff** (allocated %) | $150,000 - $250,000 | 1.5-2 FTE dedicated to VAPT coordination, testing, remediation tracking |
| **Training & Certifications** | $10,000 - $15,000 | OSCP, GPEN training for internal testers |
| **Total Annual Budget** | **$290,000 - $560,000** | Scales with organization size and asset count |

**Budget Justification**: Compare against average cost of a data breach ($4.45M per IBM 2023 Cost of a Breach report). VAPT program is risk mitigation investment.

---

### 8.2 Resource Allocation

| Quarter | Internal FTE Hours | External Vendor Days | Tools/Automation |
|---------|-------------------|----------------------|------------------|
| Q1 | 320 hours (2 FTE × 40 hours/week × 4 weeks) | 10 days | Weekly scans (automated) |
| Q2 | 400 hours (includes annual external pentest support) | 20 days (external pentest + mobile) | Weekly scans + CI/CD |
| Q3 | 320 hours | 15 days (web app pentest) | Weekly scans |
| Q4 | 480 hours (includes compliance prep) | 25 days (infrastructure pentest + API testing) | Weekly scans + year-end reporting |

**Total Annual**: 1,520 internal hours (~0.75 FTE) + 70 external consulting days

---

## 9. Continuous Improvement

### 9.1 Lessons Learned Integration

**Example**:
> "2024-Q2: External pentest identified critical vulnerability in new mobile app released 3 weeks prior. **Root Cause**: QA security test was skipped due to release deadline pressure."
> 
> **Corrective Action**: Implemented **hard gate** in deployment pipeline—production deployment script checks for security test sign-off in Jira. If ticket "Security Test - [App Name]" status ≠ "Passed", deployment fails with error message.
> 
> **Result**: Zero security test bypasses in subsequent 6 months (4 releases blocked until testing completed).

---

## 10. Related Documents

- [VAPT Policy](../01-policy-governance/VAPT-Policy.md)
- [Asset Inventory System](./Asset-Inventory-System.md)
- [Engagement Types Guide](./Engagement-Types-Guide.md)
- [Zero-Day Response Process](./Zero-Day-Response-Process.md)

---

**Document Control Log**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-15 | IT Security Team | Initial testing schedule matrix |

---

*This document is marked as **Internal - Technical**. Distribution limited to IT Security and management.*
