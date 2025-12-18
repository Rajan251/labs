# VAPT Policy Document
**Document Control**
- **Version**: 1.0.0
- **Effective Date**: December 15, 2025
- **Document Owner**: Chief Information Security Officer (CISO)
- **Review Cycle**: Annual or triggered by major security incidents/regulatory changes
- **Classification**: Internal - Management

---

## 1. Executive Summary

This Vulnerability Assessment and Penetration Testing (VAPT) Policy establishes the framework for systematic identification, assessment, and remediation of security vulnerabilities across all organizational information assets. This policy supports our commitment to information security excellence and provides the foundation for demonstrable compliance with ISO 9001:2015 and ISO/IEC 27001:2022 certification requirements.

**Business Justification**: Proactive vulnerability management reduces the likelihood of security breaches, protects customer data, maintains regulatory compliance, and preserves organizational reputation and financial stability.

---

## 2. Policy Objectives

This VAPT program is established to:

1. **Identify Security Weaknesses**: Systematically discover vulnerabilities across all technical assets before they can be exploited by malicious actors
2. **Risk-Based Prioritization**: Assess and prioritize vulnerabilities based on business impact and exploitability (CVSS scoring with contextual adjustments)
3. **Timely Remediation**: Ensure vulnerabilities are remediated within defined Service Level Agreements (SLAs) based on severity
4. **Continuous Improvement**: Feed vulnerability findings into security architecture, development practices, and operational procedures
5. **Compliance Assurance**: Demonstrate due diligence and meet regulatory requirements, specifically:
   - **ISO 9001:2015** Clause 8.1 (Operational Planning), 9.1.3 (Analysis & Evaluation), 10.2 (Corrective Action)
   - **ISO/IEC 27001:2022** Annex A.8.8 (Management of Technical Vulnerabilities)
6. **Audit Readiness**: Maintain comprehensive evidence of vulnerability management lifecycle for certification audits

---

## 3. Scope

### 3.1 In-Scope Assets

This policy applies to **all** information technology assets owned, operated, or managed by the organization, including but not limited to:

#### External-Facing Assets
- Public-facing web applications and portals
- RESTful APIs and web services
- Mobile applications (iOS, Android, hybrid)
- External network perimeter (firewalls, VPN gateways, load balancers)
- Cloud-hosted services and infrastructure (AWS, Azure, GCP)

#### Internal Infrastructure
- Internal network segments and VLANs
- Windows and Linux servers (physical and virtual)
- Database servers (SQL, NoSQL, data warehouses)
- Network devices (routers, switches, wireless access points)
- End-user workstations and laptops
- Telephony systems and UC infrastructure

#### Cloud & Third-Party Managed
- Infrastructure-as-a-Service (IaaS) configurations
- Platform-as-a-Service (PaaS) applications
- SaaS integrations with corporate data access
- Containerized environments (Docker, Kubernetes)

#### Specialized Assets
- IoT devices (building management, smart devices)
- Operational Technology (OT) / Industrial Control Systems (ICS) / SCADA (if applicable)
- Development, staging, and pre-production environments

### 3.2 Out-of-Scope

- Third-party SaaS applications where the organization has no infrastructure control (subject to vendor security assessments instead)
- Assets explicitly decommissioned and removed from the asset inventory
- Personal devices not enrolled in corporate mobile device management (MDM)

### 3.3 Data Handling

Testing activities must comply with:
- Data classification policies (no exfiltration of production PII/PCI data)
- Use of sanitized or synthetic test data for destructive testing
- Non-Disclosure Agreements (NDAs) for external testers
- Data protection regulations (GDPR, CCPA, etc.)

---

## 4. Roles and Responsibilities (RACI Matrix)

| Activity | CISO | IT Security Manager | DevOps/Engineering | SOC Team | External Auditors | Business Unit Owners |
|----------|------|---------------------|-------------------|----------|-------------------|---------------------|
| **Policy Approval** | A | R | I | I | I | C |
| **VAPT Program Oversight** | A | R | I | C | - | I |
| **Asset Inventory Maintenance** | I | A | R | C | - | R |
| **Test Scheduling** | A | R | C | I | - | C |
| **Rules of Engagement Approval** | A | R | I | I | - | C |
| **Vulnerability Scanning Execution** | I | A | C | R | - | I |
| **Penetration Testing Execution** | C | A | I | C | R (External) | I |
| **Finding Validation** | I | R | C | A | - | I |
| **Remediation Execution** | I | C | R/A | C | - | R |
| **Risk Acceptance Decision** | A | R | I | I | - | C |
| **Management Reporting** | A/R | R | C | C | - | I |
| **Audit Evidence Provision** | A | R | C | C | - | C |

**Legend**: R = Responsible, A = Accountable, C = Consulted, I = Informed

### Role Definitions

**Chief Information Security Officer (CISO)**
- Ultimate accountability for VAPT program effectiveness
- Approves policy, testing schedules, and risk acceptance decisions for Critical/High vulnerabilities
- Presents VAPT results to executive leadership and Board
- Budget authority for VAPT tools and services

**IT Security Manager**
- Day-to-day VAPT program management
- Coordinates testing activities with business units
- Reviews and validates all findings
- Tracks remediation progress against SLAs
- Manages relationships with external testing vendors

**DevOps/Engineering Teams**
- Executes vulnerability remediation (patching, configuration changes, code fixes)
- Integrates security scanning into CI/CD pipelines
- Provides technical expertise during testing (white-box/gray-box engagements)
- Implements compensating controls for risk-accepted vulnerabilities

**Security Operations Center (SOC) Team**
- Monitors automated vulnerability scans
- Performs initial triage and validation of findings
- Escalates critical vulnerabilities for immediate action
- Integrates VAPT findings into threat intelligence and SIEM

**External Auditors/Penetration Testers**
- Conducts independent third-party penetration tests (annual)
- Provides objective assessment of security posture
- Delivers detailed technical reports and remediation guidance

**Business Unit Owners**
- Provides business context for risk assessment
- Approves testing windows for production systems
- Assigns resources for remediation activities
- Accepts residual risk for their applications (with CISO approval)

---

## 5. VAPT Methodology

The organization adopts the following industry-standard methodologies:

### 5.1 Standards and Frameworks

1. **OWASP Testing Guide v4.2**: Web application security testing
2. **NIST SP 800-115**: Technical Security Testing and Assessment
3. **Penetration Testing Execution Standard (PTES)**: Structured pentest approach
4. **OSSTMM (Open Source Security Testing Methodology Manual)**: Network and infrastructure testing

### 5.2 Testing Phases

All penetration tests follow these phases:

1. **Pre-Engagement**: Scope definition, RoE negotiation, authorization
2. **Intelligence Gathering**: Reconnaissance (OSINT, DNS enumeration, network discovery)
3. **Threat Modeling**: Attack surface analysis, entry point identification
4. **Vulnerability Analysis**: Automated scanning + manual validation
5. **Exploitation**: Proof-of-concept exploitation (controlled, with safeguards)
6. **Post-Exploitation**: Lateral movement assessment, privilege escalation, data exposure evaluation
7. **Reporting**: Detailed findings with business risk context and remediation roadmap
8. **Remediation Support**: Re-testing and verification of fixes

### 5.3 Quality Assurance

- All automated scan results must be manually validated before reporting to eliminate false positives
- Minimum two-person review for all Critical and High findings
- External pentests conducted by certified professionals (OSCP, CEH, GPEN, or equivalent)

---

## 6. Testing Frequency and Triggers

### 6.1 Scheduled Testing (Annual Cadence)

| Asset Class | Frequency | Test Type | Performer |
|-------------|-----------|-----------|-----------|
| **External Perimeter** | Annual | Black-box Penetration Test | Third-party certified |
| **Critical Web Applications** | Bi-annual | Gray/White-box Pentest | Third-party or internal |
| **Public APIs** | Bi-annual | Gray-box API Security Test | Third-party or internal |
| **Internal Network** | Quarterly | Gray-box Infrastructure Test | Internal SOC + annual third-party |
| **Cloud Infrastructure** | Bi-annual | Configuration Review + Pentest | Third-party cloud security specialist |
| **Mobile Applications** | Per major release + annual | White-box Mobile App Test | Third-party |
| **All In-Scope Assets** | Weekly | Authenticated Vulnerability Scan | Automated (Nessus/Qualys) |
| **Production Deployments** | Per release | SAST/DAST Scans | Automated CI/CD integration |

### 6.2 Event-Driven Testing (Ad-Hoc)

Testing is triggered outside the regular schedule for:
- **New Application Launch**: Must complete security testing before production deployment
- **Major Infrastructure Changes**: Network redesign, cloud migration, datacenter relocation
- **Post-Incident**: After security breach or near-miss to identify residual vulnerabilities
- **Mergers & Acquisitions**: Due diligence testing of acquired infrastructure
- **Critical Zero-Day Disclosure**: Emergent threat assessment (e.g., Log4Shell, Heartbleed)
- **Significant Code Changes**: Major refactoring or feature additions to critical applications
- **Compliance Requirement**: Regulatory mandate (PCI-DSS quarterly scans, etc.)

---

## 7. Rules of Engagement (RoE)

All penetration tests require a signed RoE document before commencement. Minimum RoE components:

1. **Authorization**: Written approval from CISO and asset owner
2. **Scope Definition**: Explicit list of in-scope targets (IP ranges, URLs, applications) and exclusions
3. **Testing Window**: Permitted dates and times (e.g., "Non-business hours only" for production)
4. **Attack Constraints**:
   - Prohibited actions (e.g., no Denial of Service attacks, no social engineering without approval)
   - Data handling restrictions (no exfiltration of production data)
   - Stop conditions (maximum resource consumption limits)
5. **Communication Protocol**:
   - Primary and secondary contacts
   - Emergency escalation procedure (24/7 contact for critical issues)
   - Daily status updates requirement
6. **Legal Protections**: Indemnification clauses, limitation of liability, confidentiality obligations
7. **Deliverables**: Report format, delivery timeline, re-test requirements

See: [Rules of Engagement Template](./Rules-of-Engagement-Template.md)

---

## 8. Compliance Statement

### 8.1 ISO 9001:2015 Alignment

This VAPT program serves as a **quality control mechanism** ensuring IT services meet security specifications:

- **Clause 8.1 (Operational Planning & Control)**: VAPT activities are planned, scheduled, and documented
- **Clause 9.1.3 (Analysis & Evaluation)**: Vulnerability trends analyzed for process improvement
- **Clause 10.2 (Nonconformity & Corrective Action)**: Vulnerabilities treated as nonconformities, tracked to closure with root cause analysis

### 8.2 ISO/IEC 27001:2022 Alignment

- **Annex A.8.1 (Asset Management)**: Asset inventory linked to VAPT schedule
- **Annex A.8.8 (Management of Technical Vulnerabilities)**: Core control—entire VAPT lifecycle addresses this requirement
- **Annex A.5.7 (Threat Intelligence)**: VAPT findings feed threat modeling and risk assessments
- **Annex A.16.1 (Information Security Event Management)**: Critical findings escalated as security events

---

## 9. Reporting and Metrics

### 9.1 Reporting Cadence

- **Real-Time**: Critical vulnerabilities reported within 4 hours of discovery
- **Weekly**: Automated scan summaries to IT Security Manager
- **Quarterly**: VAPT program KPI dashboard to CISO
- **Annual**: Comprehensive security posture report to Board of Directors

### 9.2 Key Performance Indicators (KPIs)

1. **Vulnerability Density**: Total vulnerabilities per 1,000 assets (trend over time)
2. **Mean Time to Remediate (MTTR)**:
   - Critical: Target <7 days
   - High: Target <30 days
   - Medium: Target <90 days
3. **SLA Compliance Rate**: Percentage of vulnerabilities remediated within SLA
4. **Asset Coverage**: Percentage of assets tested within policy-defined frequency
5. **Critical Vulnerability Recurrence Rate**: Same vulnerability class found in multiple tests (indicates systemic weakness)
6. **Risk Acceptance Rate**: Percentage of findings risk-accepted vs. remediated (should be minimal)

---

## 10. Policy Review and Continuous Improvement

### 10.1 Review Schedule

This policy is reviewed:
- **Annually**: Scheduled review every December
- **Triggered Reviews**: Following major security incidents, significant regulatory changes, or failed audits

### 10.2 Improvement Process

Lessons learned from each VAPT cycle are documented and used to:
- Update baseline security configurations
- Enhance secure development training
- Improve vulnerability detection capabilities
- Refine testing methodologies

See: [Continuous Improvement Records Template](../05-audit-preparedness/Continuous-Improvement-Records.md)

---

## 11. Policy Violations and Enforcement

- Bypassing VAPT requirements for production deployments is a **major policy violation**
- Unauthorized security testing (without RoE) is prohibited and subject to disciplinary action
- Failure to remediate Critical vulnerabilities within SLA requires executive escalation and may result in system isolation

---

## 12. Related Documents

- [Methodology Framework](./Methodology-Framework.md)
- [Rules of Engagement Template](./Rules-of-Engagement-Template.md)
- [Risk Acceptance & Remediation Governance](./Risk-Remediation-Governance.md)
- [Asset Inventory System](../02-vapt-scope-inventory/Asset-Inventory-System.md)
- ISO 9001:2015 Quality Manual
- ISO/IEC 27001:2022 Information Security Policy

---

## 13. Approval and Authorization

| Role | Name | Signature | Date |
|------|------|-----------|------|
| **Policy Owner (CISO)** | [Name] | [Signature] | [Date] |
| **Reviewed By (IT Security Manager)** | [Name] | [Signature] | [Date] |
| **Approved By (CEO/CIO)** | [Name] | [Signature] | [Date] |

---

**Document Control Log**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-15 | CISO Office | Initial policy creation |

---

*This document is marked as **Internal - Management**. Unauthorized distribution is prohibited.*
