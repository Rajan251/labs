# VAPT Program & ISO Compliance Framework

**Version**: 1.0.0  
**Last Updated**: December 15, 2025  
**Program Owner**: Chief Information Security Officer (CISO)  
**Classification**: Internal - Management

---

## 🎯 Executive Summary

This repository contains the complete documentation framework for an enterprise-grade **Vulnerability Assessment and Penetration Testing (VAPT) program** designed to achieve two parallel objectives:

1. **Technical Excellence**: Establish a comprehensive, systematic VAPT process covering all organizational assets (A-to-Z approach)
2. **Compliance Assurance**: Ensure full demonstrable alignment with **ISO 9001:2015** (Quality Management) and **ISO/IEC 27001:2022** (Information Security Management) certification requirements

The framework provides clear audit trails from vulnerability discovery through risk acceptance or verified remediation, satisfying both quality and security management system requirements.

---

## 📂 Documentation Structure

```
vapt-testing/
├── 01-policy-governance/          # Policy & Governance Framework
├── 02-vapt-scope-inventory/       # A-to-Z VAPT Scope & Inventory
├── 03-compliance-integration/     # ISO 9001 & ISO 27001 Mappings
├── 04-data-infrastructure/        # Data Management & Infrastructure
├── 05-audit-preparedness/         # Audit Evidence & Preparation
└── README.md                      # This file
```

---

## 🚀 Quick Start

### For Executives
1. Read: [VAPT Policy](./01-policy-governance/VAPT-Policy.md) (Overview of program objectives and scope)
2. Review: [ISO 9001 Mapping](./03-compliance-integration/ISO-9001-Mapping.md) (Quality management integration)
3. Review: [ISO 27001 Mapping](./03-compliance-integration/ISO-27001-Mapping.md) (Security management integration)

### For IT Security Team
1. Implement: [Asset Inventory System](./02-vapt-scope-inventory/Asset-Inventory-System.md)
2. Plan: [Testing Schedule Matrix](./02-vapt-scope-inventory/Testing-Schedule-Matrix.md)
3. Execute: [Methodology Framework](./01-policy-governance/Methodology-Framework.md)
4. Track: [Risk Remediation Governance](./01-policy-governance/Risk-Remediation-Governance.md)

### For Auditors
1. Start: [Audit Evidence Checklist](./05-audit-preparedness/Audit-Evidence-Checklist.md)
2. Review: Compliance mappings in Section 03
3. Verify: Evidence artifacts per checklist

---

## 📋 Section A: VAPT Program Policy & Governance Framework

**Purpose**: Establishes the foundational policies, methodologies, and governance processes for the VAPT program.

| Document | Description | Key Audience |
|----------|-------------|--------------|
| **[VAPT Policy](./01-policy-governance/VAPT-Policy.md)** | Primary policy document with program objectives, scope, roles (CISO, IT Security, DevOps, SOC), testing frequency, and compliance statement | Executive, Management, All Staff |
| **[Methodology Framework](./01-policy-governance/Methodology-Framework.md)** | Technical methodologies (OWASP, NIST SP 800-115, PTES), testing phases (7-phase PTES), quality assurance, approved tools, tester qualifications | Security Team, Testers |
| **[Rules of Engagement Template](./01-policy-governance/Rules-of-Engagement-Template.md)** | Standardized RoE template for all engagements: scope definition, authorization, attack constraints, communication protocols, legal protections | Security Manager, Testers, Legal |
| **[Risk Remediation Governance](./01-policy-governance/Risk-Remediation-Governance.md)** | Vulnerability lifecycle management: severity classification (CVSS + business context), remediation SLAs (7/30/90 days), risk acceptance workflow, escalation procedures | Security Team, DevOps, Management |

**ISO Compliance Links**:
- ISO 9001:2015 Clause 8.1 (Operational Planning), 8.5.1 (Controlled Processes)
- ISO 27001:2022 A.8.8 (Management of Technical Vulnerabilities) - Core control

---

## 📝 Section B: "A to Z" VAPT Scope & Inventory

**Purpose**: Defines the complete scope of VAPT activities, asset inventory management, testing schedules, and emergent threat response.

| Document | Description | Key Audience |
|----------|-------------|--------------|
| **[Asset Inventory System](./02-vapt-scope-inventory/Asset-Inventory-System.md)** | Dynamic asset register with taxonomy (External-facing, Cloud, Internal, IoT/OT), criticality tiering (Tier 1/2/3), discovery methods, CMDB integration, coverage tracking | Security Team, Asset Owners |
| **[Testing Schedule Matrix](./02-vapt-scope-inventory/Testing-Schedule-Matrix.md)** | Master testing calendar: annual cadence (external/internal/cloud/mobile), continuous scans (weekly baselines, CI/CD integration), quarterly activities, event-driven testing | Security Manager, All Teams |
| **[Engagement Types Guide](./02-vapt-scope-inventory/Engagement-Types-Guide.md)** | Black-box, Gray-box, White-box testing definitions, use cases, asset-to-type mapping matrix, hybrid approaches (code-assisted, assumed breach, purple team) | Security Team, Testers |
| **[Data Classification Handling](./02-vapt-scope-inventory/Data-Classification-Handling.md)** | VAPT data handling by classification (PII/PCI/PHI requirements), synthetic data generation, test data lifecycle, tester requirements, evidence sanitization, regulatory compliance (GDPR, CCPA, HIPAA) | Security Team, Legal, DPO |
| **[Zero-Day Response Process](./02-vapt-scope-inventory/Zero-Day-Response-Process.md)** | Rapid response for critical vulnerabilities: threat intelligence sources, 0-7 day response timeline (detection → assessment → patching → verification), pre-positioned capabilities (emergency scanning, WAF rules), decision matrix | SOC, Security Manager, CISO |

**ISO Compliance Links**:
- ISO 27001:2022 A.8.1 (Asset Management), A.5.7 (Threat Intelligence)

---

## ✅ Section C: Compliance Integration for ISO 9001 & ISO 27001

**Purpose**: Demonstrates how the VAPT program satisfies ISO certification requirements with explicit clause-by-clause mappings.

| Document | Description | Key Audience |
|----------|-------------|--------------|
| **[ISO 9001:2015 Mapping](./03-compliance-integration/ISO-9001-Mapping.md)** | Map VAPT to Quality Management System: vulnerabilities as nonconformities (Clause 10.2), operational planning (8.1), analysis & evaluation (9.1.3), management review (9.3), continual improvement (10.3) | Quality Manager, Auditors, Management |
| **[ISO 27001:2022 Mapping](./03-compliance-integration/ISO-27001-Mapping.md)** | Map VAPT to Information Security controls: Core A.8.8 implementation (obtaining vuln info, evaluating exposure, taking measures, logging), plus A.5.7 (Threat Intel), A.8.1 (Assets), A.8.16 (Monitoring), A.14.2 (Secure Development) | CISO, Security Team, Auditors |

**Key Takeaway**: The VAPT program serves dual purposes:
- **Quality Process** (ISO 9001): Security testing as quality control, vulnerabilities as quality nonconformities
- **Security Control** (ISO 27001): Systematic technical vulnerability management per A.8.8

---

## 🗄️ Section D: Data Management, Records & Server Infrastructure

**Purpose**: Defines data architecture, infrastructure platforms, and reporting framework for the VAPT program.

| Document | Description | Key Audience |
|----------|-------------|--------------|
| **[Findings Database Schema](./04-data-infrastructure/Findings-Database-Schema.md)** | PostgreSQL schema for vulnerability lifecycle tracking: Core fields (finding_id, asset linkage, CVSS scoring, severity, status workflow), supporting tables (test_reports, remediation_history), reporting views (executive dashboard, SLA compliance), integrations (Jira/ServiceNow, SIEM), 7-year retention | Database Admin, Security Team, Developers |
| **[Infrastructure Architecture](./04-data-infrastructure/Infrastructure-Architecture.md)** | Technical platform specifications: Vulnerability Management Server (Nessus/Qualys), Pentest Collaboration Platform (Faraday/Dradis), Findings Database (PostgreSQL), GRC/Ticketing (Jira/SNOW), SIEM integration, Dashboards (Grafana/Power BI), Evidence Repository (SharePoint), Network segmentation (VLANs), cloud integration (AWS/Azure/GCP), deployment options (on-prem vs. hybrid cloud), budget estimates | Infrastructure Team, Security Manager, CISO |

**Supporting Documents** (in sub-directories):
- **Reporting Templates/**: Technical Report, Executive Summary, Auditor Evidence templates (Markdown drafts for customization)

---

## 🔍 Section E: Certification Audit Preparedness

**Purpose**: Pre-audit preparation materials to ensure audit readiness with comprehensive evidence checklists.

| Document | Description | Key Audience |
|----------|-------------|--------------|
| **[Audit Evidence Checklist](./05-audit-preparedness/Audit-Evidence-Checklist.md)** | Comprehensive checklist for ISO 9001 & 27001 audits: Required evidence (policies, schedules, RoEs, test reports, remediation tickets, management reviews, CIlog), evidence organization (folder structure), 60-day preparation timeline, common auditor questions & answers | Quality Manager, CISO, Audit Team |

**Additional Documents**:
- **Continuous Improvement Records Template**: Framework for documenting VAPT program improvements (captures problem → action → effectiveness measurement)
- **Document Control Procedure**: Version control, approval workflows, review schedules for all VAPT documentation

---

## 🎯 Program Objectives

### Technical Objectives (A-to-Z VAPT Coverage)

1. **Complete Asset Visibility**: 100% of Tier 1 (critical) assets tested within policy-defined frequency
2. **Risk-Based Prioritization**: CVSS scoring with business context adjustments (asset criticality + data classification)
3. **Timely Remediation**: SLA-driven response (Critical=7 days, High=30 days, Medium=90 days)
4. **Continuous Monitoring**: Weekly automated scans + CI/CD integrated security gates
5. **Emergent Threat Response**: Zero-day response capability (≤24 hours for assessment)

### Compliance Objectives (ISO 9001 & ISO 27001)

| ISO Standard | Objective | VAPT Program Evidence |
|--------------|-----------|----------------------|
| **ISO 9001:2015** | Demonstrate security testing as quality control mechanism | VAPT as operational process (Clause 8.1), vulnerabilities as nonconformities (Clause 10.2), trend analysis for improvement (Clause 9.1.3) |
| **ISO/IEC 27001:2022** | Systematic technical vulnerability management | Full implementation of A.8.8 (vulnerability lifecycle), threat intelligence integration (A.5.7), asset-centric approach (A.8.1) |

**Target Metrics**:
- SLA Compliance: >95% for High/Critical vulnerabilities
- Asset Coverage: 100% Tier 1, >95% overall
- Mean Time to Remediate (MTTR): <7 days Critical, <30 days High
- Vulnerability Recurrence Rate: <5% (same class re-discovered)

---

## 👥 Roles and Responsibilities (RACI)

| Activity | CISO | IT Security Manager | DevOps | SOC | External Auditors | Asset Owners |
|----------|------|---------------------|--------|-----|-------------------|--------------|
| **Policy Approval** | A | R | I | I | I | C |
| **VAPT Program Oversight** | A | R | I | C | - | I |
| **Asset Inventory Maintenance** | I | A | R | C | - | R |
| **Test Scheduling** | A | R | C | I | - | C |
| **Vulnerability Scanning** | I | A | C | R | - | I |
| **Penetration Testing** | C | A | I | C | R (Ext.) | I |
| **Remediation Execution** | I | C | R/A | C | - | R |
| **Risk Acceptance Decision** | A | R | I | I | - | C |
| **Management Reporting** | A/R | R | C | C | - | I |

**Legend**: R = Responsible, A = Accountable, C = Consulted, I = Informed

---

## 📈 Key Performance Indicators (KPIs)

### Operational KPIs (Monthly Tracking)
1. **Vulnerability Density**: Total vulnerabilities per 1,000 assets (trend over time)
2. **Mean Time to Remediate (MTTR)**: Days from discovery to verified closure (by severity)
3. **SLA Compliance Rate**: % of vulnerabilities remediated within SLA (target: >95%)
4. **Asset Coverage**: % of assets tested within policy frequency (target: 100% Tier 1)
5. **Critical Vulnerability Count**: Open Critical findings (target: ≤3 at any time)

### Compliance KPIs (Quarterly Review)
6. **Audit Readiness Score**: % of audit checklist items complete (target: 100%)
7. **Risk Acceptance Rate**: % of findings risk-accepted vs. remediated (target: <10%)
8. **Recurrence Rate**: Same vulnerability class found repeatedly (target: <5%)
9. **Coverage by Asset Type**: % tested per asset category (Web/API/Cloud/Network/etc.)

**Dashboard**: Grafana/Power BI dashboards updated weekly with these KPIs, reviewed in quarterly management meetings.

---

## 🔄 VAPT Program Lifecycle (Plan-Do-Check-Act)

```
┌──────────────────────────────────────────────────────────────┐
│                    VAPT Program PDCA Cycle                    │
└──────────────────────────────────────────────────────────────┘

PLAN (Annual):
├─ Update asset inventory (add new systems, decommission old)
├─ Review and update VAPT policy
├─ Create annual testing schedule (allocate budget, assign resources)
└─ Define success metrics for the year

DO (Continuous):
├─ Execute testing per schedule:
│  ├─ Weekly automated vulnerability scans
│  ├─ Quarterly/Bi-annual penetration tests
│  ├─ CI/CD integrated scans (per commit)
│  └─ Ad-hoc testing (zero-days, new deployments)
├─ Document findings in database
└─ Remediate vulnerabilities per SLA

CHECK (Monthly/Quarterly):
├─ Review KPIs (SLA compliance, MTTR, coverage)
├─ Analyze vulnerability trends (improving or degrading?)
├─ Verify remediation effectiveness (re-test results)
└─ Management review (quarterly) - present findings to CISO

ACT (Quarterly/Annual):
├─ Continuous improvement initiatives:
│  ├─ Update methodologies (new attack techniques)
│  ├─ Tool upgrades (scanner updates, new tools)
│  ├─ Process enhancements (automation, integration)
│  └─ Training (secure coding, security awareness)
├─ Adjust policies based on lessons learned
└─ Prepare for certification audits (evidence review)
```

---

## 🛠️ Implementation Roadmap

### Phase 1: Foundation (Months 1-2)
- [ ] Establish governance: Approve VAPT Policy (CISO + CEO sign-off)
- [ ] Build asset inventory: Catalog all in-scope assets with criticality tiers
- [ ] Deploy infrastructure: Set up vulnerability scanner (Nessus), findings database
- [ ] Define baseline: Conduct initial vulnerability assessment to establish current state

### Phase 2: Process Implementation (Months 3-4)
- [ ] Operationalize testing: Configure automated weekly scans, schedule first pentest
- [ ] Establish tracking: Integrate findings database with Jira/ServiceNow for remediation workflow
- [ ] Train teams: Security awareness for all staff, technical training for SOC/DevOps
- [ ] Create dashboards: Deploy Grafana dashboards for KPI monitoring

### Phase 3: Compliance Integration (Months 5-6)
- [ ] Map to ISO standards: Document compliance mappings (complete Sections C)
- [ ] Conduct internal audit: Self-assessment against ISO requirements, identify gaps
- [ ] Build evidence repository: Organize all VAPT artifacts per audit checklist
- [ ] Dry-run with auditor: Mock audit to test preparedness

### Phase 4: Certification & Optimization (Months 7-12)
- [ ] Certification audit: Submit for ISO 9001 & ISO 27001 certification
- [ ] Address findings: Close any audit non-conformities
- [ ] Optimize processes: Implement continuous improvements from lessons learned
- [ ] Annual review: Update all documentation, refine KPI targets for next year

---

## 📞 Contact Information

**Program Owner**:  
CISO: [Name]  
Email: ciso@example.com  
Phone: [Number]

**Day-to-Day Management**:  
IT Security Manager: [Name]  
Email: security.manager@example.com  
Phone: [Number]

**SOC (24/7 for Critical Findings)**:  
Email: soc@example.com  
Phone: [On-call number]

---

## 📚 Additional Resources

### Internal Links
- Corporate ISO 9001 Quality Manual
- Corporate ISO/IEC 27001 Information Security Policy
- Change Management Procedure (ITIL framework)
- Data Classification Policy
- Incident Response Plan

### External References
- **OWASP Testing Guide v4.2**: https://owasp.org/www-project-web-security-testing-guide/
- **NIST SP 800-115** (Technical Security Testing): https://csrc.nist.gov/publications/detail/sp/800-115/final
- **PTES** (Penetration Testing Execution Standard): http://www.pentest-standard.org/
- **CVSS v3.1 Calculator**: https://www.first.org/cvss/calculator/3.1
- **ISO/IEC 27001:2022**: https://www.iso.org/standard/27001
- **ISO 9001:2015**: https://www.iso.org/standard/62085.html

---

## 📅 Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-15 | CISO Office & Security Team | Initial comprehensive VAPT framework creation |

---

## 📄 License and Confidentiality

**Classification**: Internal - Management

This documentation framework is proprietary and confidential. Unauthorized distribution outside the organization is prohibited.

For external sharing (e.g., with third-party auditors or pentesting firms), obtain approval from CISO and execute appropriate NDAs.

---

## ✅ Next Steps

**For New Users of this Framework**:
1. **Read this README** completely to understand the program structure
2. **Review the VAPT Policy** to understand program scope and your role
3. **Identify where you fit** in the RACI matrix (Section "Roles and Responsibilities")
4. **Access relevant documents** for your role (Quick Start links)
5. **Contact IT Security Manager** with questions

**For ISO Audit Preparation**:
1. Start with [Audit Evidence Checklist](./05-audit-preparedness/Audit-Evidence-Checklist.md)
2. Follow the 60-day preparation timeline
3. Conduct internal audit using the checklist
4. Address any gaps before certification audit

**For Program Execution**:
1. Ensure asset inventory is current ([Asset Inventory System](./02-vapt-scope-inventory/Asset-Inventory-System.md))
2. Follow testing schedule ([Testing Schedule Matrix](./02-vapt-scope-inventory/Testing-Schedule-Matrix.md))
3. Use RoE template for all engagements ([Rules of Engagement](./01-policy-governance/Rules-of-Engagement-Template.md))
4. Track findings through remediation ([Risk Remediation Governance](./01-policy-governance/Risk-Remediation-Governance.md))

---

**Questions or Need Help?**  
Contact: IT Security Manager at security.manager@example.com

---

*Documentation maintained by the Information Security Office. Last review: 2025-12-15*
