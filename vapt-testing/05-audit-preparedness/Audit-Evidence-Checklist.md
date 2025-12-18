# Audit Evidence Checklist
**Document Control**
- **Version**: 1.0.0
- **Effective Date**: December 15, 2025
- **Document Owner**: CISO / Quality Manager
- **Classification**: Internal - Management

---

## 1. Purpose

Pre-audit self-assessment checklist to ensure all required evidence is prepared for ISO 9001:2015 and ISO/IEC 27001:2022 certification audits.

**Usage**: Complete this checklist 60 days before scheduled audit, address any gaps, conduct internal audit.

---

## 2. ISO 9001:2015 Evidence Checklist

### Quality Management System - VAPT Program

- [ ] **VAPT Policy Document**
  - Policy approved by top management (CEO/CIO signature)
  - Effective date within last 12 months (or documented review if older)
  - Distributed to relevant personnel (email distribution list or SharePoint access logs)

- [ ] **Quality Objective for VAPT**
  - Documented objective (e.g., "Reduce High/Critical vulnerabilities by 20% YoY")
  - Measurable and time-bound
  - Progress tracked in management reviews

- [ ] **Annual VAPT Schedule** (Clause 8.1: Operational Planning)
  - Planned testing calendar for current year
  - Actual testing dates recorded
  - Coverage: All Tier 1 assets included

- [ ] **Rules of Engagement** (Clause 8.5.1: Controlled Production)
  - Minimum 2 recent signed RoEs (from different engagements)
  - Signatures: CISO, Asset Owner, Testing Team Lead
  - Scope clearly defined (in-scope and out-of-scope assets listed)

- [ ] **Vulnerability Management Procedure**
  - [Risk Remediation Governance](../01-policy-governance/Risk-Remediation-Governance.md) document
  - Severity classification methodology (CVSS + business context)
  - SLA definitions (7/30/90 days for Critical/High/Medium)

- [ ] **Remediation Tracking Evidence** (Clause 10.2: Nonconformity)
  - Sample of closed vulnerability tickets (minimum 5, mixture of Critical/High/Medium)
  - Each ticket must show:
    - Discovery (initial finding)
    - Remediation action (patch applied, config changed)
    - Verification (re-test passed)
    - Closure evidence (clean scan screenshot or re-test report)

- [ ] **Root Cause Analysis** (Clause 10.2.1)
  - At least 1 RCA for a recurring vulnerability
  - Example: "SQL injection found in 3 apps → Root cause: No secure coding training → Corrective action: Mandatory OWASP training implemented"

- [ ] **Management Review Minutes** (Clause 9.3)
  - Last 3-4 quarterly management review meetings
  - VAPT KPIs discussed in each meeting:
    - Vulnerability trends
    - SLA compliance
    - Resource needs
  - Action items documented with owners and due dates

- [ ] **Training Records** (Clause 7.2: Competence)
  - Internal SOC staff: Security training completion records
  - External testers: Certifications on file (OSCP, CEH, GPEN, etc.)
  - Annual refresher training (security awareness)

- [ ] **Continuous Improvement Evidence** (Clause 10.3)
  - [Continuous Improvement Log](./Continuous-Improvement-Records.md)
  - Minimum 3 documented improvements in last 12 months
  - Each improvement must show:
    - Problem identified
    - Action taken
    - Effectiveness measured (before/after metrics)
  - Examples:
    - "Implemented automated Certificate Transparency monitoring after pentest found untracked subdomain"
    - "Added SAST to CI/CD pipeline after recurring code vulnerabilities"

- [ ] **Internal Audit Results** (Clause 9.2)
  - Internal audit of VAPT program conducted (within last 12 months)
  - Audit report showing:
    - Scope: VAPT policy, procedures, execution
    - Findings (if any)
    - Corrective actions taken (closed before certification audit)
  - Auditor independence (not auditing their own work)

---

## 3. ISO/IEC 27001:2022 Evidence Checklist

### Information Security Management System - VAPT Program

- [ ] **Asset Inventory** (A.8.1)
  - Complete, current asset database export (as of audit date)
  - All required fields populated:
    - Asset ID, Name, Owner, Criticality, Data Classification
    - Last Test Date, Next Test Due Date
  - Evidence of regular updates (quarterly review meeting minutes or automated sync logs)

- [ ] **Asset-to-Test Mapping**
  - Demonstrates all Tier 1 (critical) assets tested per policy frequency
  - Coverage report: % of assets tested within required intervals
  - Target: 100% Tier 1, >95% overall
  - Overdue tests documented with justification (e.g., "Scheduled for next week")

- [ ] **Vulnerability Information Sources** (A.8.8a)
  - CVE/NVD monitor configuration (API integration screenshot or feed subscription)
  - Vulnerability scan schedule (weekly automated Nessus scans - evidence: cron jobs, scan history)
  - Penetration test reports (last 3 engagements, covering external, internal, web app)

- [ ] **CVSS Scoring Methodology** (A.8.8b)
  - Documented process for risk rating (CVSS + business context)
  - [Risk Remediation Governance](../01-policy-governance/Risk-Remediation-Governance.md) - Severity Classification section
  - Sample findings showing CVSS scores applied

- [ ] **Vulnerability Reports** (A.8.8)
  - **From Automated Scans**: Last quarter's Nessus/Qualys reports
  - **From Manual Pentests**: At least 1 recent penetration test report (within last 12 months)
  - Reports must include:
    - Severity ratings (CVSS scores)
    - Affected assets
    - Remediation recommendations
    - Proof-of-concept (for critical findings)

- [ ] **Remediation Evidence** (A.8.8c)
  - **Critical Findings**: Show 7-day closure for at least 3 recent Critical vulnerabilities
    - Each must have: Jira/SNOW ticket → Remediation action → Re-test verification → Closure
  - **Risk Acceptance**: Sample waiver (Risk Acceptance Form) with:
    - CISO signature
    - Compensating controls documented
    - Justification why not remediating
    - Re-assessment date set (max 1 year)

- [ ] **Zero-Day Response Evidence** (A.5.7 Threat Intelligence)
  - Example of zero-day response (e.g., Log4j, ProxyLogon)
  - Timeline documented:
    - Alert detection (when we learned of the zero-day)
    - Asset triage (how many of our assets affected?)
    - Mitigation deployed (patch or WAF rule)
    - Verification (re-scan results clean)
  - Post-mortem report with lessons learned

- [ ] **SIEM Integration** (A.8.16 Monitoring)
  - Evidence that vulnerability findings feed into SIEM
  - Sample SIEM correlation rule created from VAPT finding
  - Example: "SQL injection found in /api/users → SIEM rule deployed to detect SQLi payloads in that endpoint"

- [ ] **Access Control to Evidence Repository** (A.5.18)
  - SharePoint/file server access logs showing restricted access
  - Only CISO, Security Manager, SOC, and auditors have access
  - Audit logs retained for 7 years

- [ ] **Threat Intelligence Integration** (A.5.7)
  - Threat intelligence platform (TIP) screenshot showing monitored feeds
  - Evidence that VAPT findings incorporated into organizational threat model
  - Example: Updated threat model showing attack paths discovered in pentest

- [ ] **Pre-Production Security Testing** (A.14.2)
  - CI/CD pipeline configuration showing security gates:
    - SAST (SonarQube, Checkmarx)
    - Dependency scanning (Snyk, Dependabot)
    - Container scanning (Trivy)
  - QA environment pentest requirement enforced (deployment blocked without security test approval)
  - Sample pre-production test report

---

## 4. Common Evidence Artifacts

### Must-Have Documents (for BOTH ISO 9001 and 27001)

**Policies and Procedures**: [ ] **VAPT Policy** (approved, signed, current)
- [ ] [VAPT Policy](../01-policy-governance/VAPT-Policy.md)
- [ ] [Methodology Framework](../01-policy-governance/Methodology-Framework.md)
- [ ] [Risk Remediation Governance](../01-policy-governance/Risk-Remediation-Governance.md)

**Planning Documents**:
- [ ] [Asset Inventory System](../02-vapt-scope-inventory/Asset-Inventory-System.md) + actual database
- [ ] [Testing Schedule Matrix](../02-vapt-scope-inventory/Testing-Schedule-Matrix.md) + actual calendar (Gantt chart)

**Execution Evidence**:
- [ ] Signed Rules of Engagement (2-3 recent)
- [ ] Vulnerability scan reports (last quarter)
- [ ] Penetration test reports (last 3 engagements)
- [ ] Screenshots of VAPT dashboard (current state: open vulns, SLA compliance)

**Remediation Evidence**:
- [ ] Closed vulnerability tickets (sample of 10: mixture of severities)
- [ ] Risk acceptance forms (if any exist)
- [ ] Root cause analysis (for recurring vulnerabilities)

**Management and Review**:
- [ ] Management review minutes (3-4 meetings with VAPT discussion)
- [ ] Internal audit report (VAPT program audit)
- [ ] Continuous improvement log ([Continuous-Improvement-Records.md](./Continuous-Improvement-Records.md))

**Compliance Mapping**:
- [ ] [ISO 9001 Mapping](../03-compliance-integration/ISO-9001-Mapping.md)
- [ ] [ISO 27001 Mapping](../03-compliance-integration/ISO-27001-Mapping.md)

---

## 5. Evidence Organization

### Recommended Folder Structure for Auditor Review

```
/Audit_Evidence_Package_2025/
├── /01_Policies_Procedures/
│   ├── VAPT-Policy-v1.0-Signed.pdf
│   ├── Methodology-Framework-v1.0.pdf
│   ├── Risk-Remediation-Governance-v1.0.pdf
│   └── Rules-of-Engagement-Template.pdf
│
├── /02_Planning_Documents/
│   ├── Asset-Inventory-Export-2025-12-01.xlsx
│   ├── Testing-Schedule-2025.pdf
│   ├── Coverage-Dashboard-Screenshot-2025-12-01.png
│   └── Asset-to-Test-Mapping.xlsx
│
├── /03_Test_Reports/
│   ├── /Vulnerability_Scans/
│   │   ├── Nessus-Q4-2025-Summary.pdf
│   │   └── Qualys-Weekly-Scan-2025-11-24.pdf
│   ├── /Penetration_Tests/
│   │   ├── External-Pentest-2025-Q2-Final-Report.pdf
│   │   ├── Web-App-Pentest-2025-Q3-Final-Report.pdf
│   │   └── Internal-Network-Pentest-2025-Q4-Final-Report.pdf
│   └── /Cloud_Assessments/
│       └── AWS-Security-Assessment-2025-Q2.pdf
│
├── /04_Remediation_Evidence/
│   ├── /Sample_Closed_Tickets/
│   │   ├── VULN-1234-SQL-Injection-CLOSED.pdf (Critical, 5-day closure)
│   │   ├── VULN-1245-XSS-CLOSED.pdf (High, 28-day closure)
│   │   └── ... (8 more samples)
│   ├── /Risk_Acceptances/
│   │   └── RA-2025-003-Legacy-Server-Signed.pdf
│   └── /Root_Cause_Analyses/
│       └── RCA-2025-SQL-Injection-Recurrence.pdf
│
├── /05_Management_Review/
│   ├── Management-Review-Minutes-2025-Q1.pdf
│   ├── Management-Review-Minutes-2025-Q2.pdf
│   ├── Management-Review-Minutes-2025-Q3.pdf
│   └── VAPT-KPI-Presentation-to-Board-2025-Q4.pptx
│
├── /06_Continuous_Improvement/
│   ├── Continuous-Improvement-Log-2025.xlsx
│   ├── Example_CI_01_Certificate_Transparency_Monitoring.pdf
│   └── Example_CI_02_Ansible_Patch_Automation.pdf
│
├── /07_Training_Competence/
│   ├── Internal-Staff-Training-Records-2025.xlsx
│   ├── External-Tester-Certifications/
│   │   ├── Pentester_John_Doe_OSCP.pdf
│   │   └── Pentester_Jane_Smith_CEH.pdf
│   └── Security-Awareness-Training-Completion-Report.pdf
│
├── /08_Compliance_Mapping/
│   ├── ISO-9001-Mapping-VAPT.pdf
│   ├── ISO-27001-Mapping-VAPT.pdf
│   └── Cross-Reference-Matrix.xlsx
│
├── /09_Infrastructure_Documentation/
│   ├── Findings-Database-Schema.pdf
│   ├── Infrastructure-Architecture.pdf
│   └── Network-Diagram-VAPT-Infrastructure.vsdx
│
└── /10_Internal_Audit/
    ├── Internal-Audit-Plan-2025.pdf
    ├── Internal-Audit-Report-VAPT-Program-2025-09.pdf
    └── Corrective-Actions-From-Internal-Audit.xlsx
```

**Delivery**: Provide auditor with read-only access to this folder structure (SharePoint link or USB drive)

---

## 6. Pre-Audit Checklist (60-Day Timeline)

### Week 1-2 (Days 1-14): Evidence Gathering

- [ ] Export current asset inventory from database
- [ ] Generate coverage report (% of assets tested)
- [ ] Collect all test reports from last 12 months
- [ ] Query database for closed vulnerability tickets (sample 10)
- [ ] Retrieve management review meeting minutes (last 4 meetings)
- [ ] Compile continuous improvement log

### Week 3-4 (Days 15-28): Gap Analysis

- [ ] Review this checklist - mark any missing evidence
- [ ] Identify gaps (e.g., "No RCA for recurring vulnerabilities performed yet")
- [ ] Create corrective action plan for gaps
- [ ] Assign owners and due dates for gap closure

### Week 5-6 (Days 29-42): Gap Remediation

- [ ] Execute gap closure actions
  - If root cause analysis missing → conduct RCA for 1-2 recurring findings
  - If management review didn't cover VAPT → add VAPT to next meeting agenda
  - If training records incomplete → obtain certificates from external testers
- [ ] Verify all gaps closed

### Week 7 (Days 43-49): Internal Audit

- [ ] Conduct internal audit of VAPT program (by Quality team or independent auditor)
- [ ] Internal auditor reviews evidence against this checklist
- [ ] Document any findings
- [ ] Create corrective actions for internal audit findings

### Week 8 (Days 50-56): Final Preparation

- [ ] Close all internal audit findings
- [ ] Organize evidence into audit package folder structure (see Section 5)
- [ ] Create index document (table of contents for auditor)
- [ ] Dry-run with CISO: walk through evidence as if presenting to auditor
  - Practice answering: "How do you manage vulnerabilities per ISO 27001 A.8.8?"

### Week 9-10 (Days 57-60+): Certification Audit

- [ ] Provide auditor with evidence package (read-only access)
- [ ] Respond to auditor questions
- [ ] Provide any additional evidence requested
- [ ] Address any non-conformities raised (if any) within timeline

---

## 7. Common Auditor Questions & Prepared Answers

### Question 1: "How do you ensure all critical assets are regularly tested?"

**Answer**:
> "We maintain a dynamic asset inventory with 468 total assets, of which 47 are Tier 1 (critical). Each asset has an assigned testing frequency based on criticality—Tier 1 assets undergo bi-annual penetration tests plus weekly automated scans. Our coverage dashboard tracks actual vs. planned testing. As of [Audit Date], our Tier 1 coverage is 100%, and overall coverage is 94%. Overdue tests are escalated to the CISO weekly."

**Evidence to Show**: Asset inventory export, coverage dashboard, testing schedule calendar

---

### Question 2: "Can you show the lifecycle of a vulnerability from discovery to closure?"

**Answer**:
> "Absolutely. Let me walk you through VULN-1234 (SQL Injection in Customer Portal):
> 1. **Discovery** (2025-10-05): External pentest identified SQL injection, CVSS 9.8 (Critical)
> 2. **Entry** (2025-10-05): Finding logged in database, Jira ticket VULN-1234 auto-created, assigned to DevOps team, due date 2025-10-12 (7-day SLA)
> 3. **Remediation** (2025-10-10): Developers applied parameterized queries fix
> 4. **Verification** (2025-10-11): Pentester re-tested, confirmed vulnerability resolved
> 5. **Closure** (2025-10-11): Ticket closed with re-test report attached, finding status updated to 'Remediated'
>
> Total time: 6 days (within 7-day SLA). We have similar evidence for all closed Critical/High findings."

**Evidence to Show**: Sample Jira ticket with full history, finding database record, re-test confirmation

---

### Question 3: "How do you handle vulnerabilities that cannot be immediately patched?"

**Answer**:
> "We have a formal risk acceptance process for cases where remediation is not feasible—for example, legacy systems awaiting decommissioning or vendor patches not yet available. The asset owner submits a Risk Acceptance Request Form documenting:
> - Why remediation isn't possible
> - Compensating controls (e.g., WAF rule, network isolation)
> - Residual risk assessment
>
> High and Critical findings require CISO approval (Critical additionally requires CIO approval). All risk acceptances have a maximum 1-year expiration and are re-assessed quarterly. Here's a sample: RA-2025-003 for a legacy Windows Server 2012 scheduled for decommissioning in 90 days, with compensating controls including isolated VLAN and MFA."

**Evidence to Show**: Risk Acceptance Form (signed), compensating control validation (e.g., firewall rules screenshot)

---

### Question 4: "What improvements have you made to the VAPT program based on findings?"

**Answer**:
> "We have a continuous improvement process documented in our CI log. Three recent examples:
> 1. **Q2 2025**: External pentest discovered an API subdomain not in our asset inventory (untracked for 2 years). **Action**: Implemented automated Certificate Transparency log monitoring. **Result**: Discovered 12 additional subdomains, all now tracked and tested.
> 2. **Q3 2025**: False positive rate in automated scans was 25%, wasting analyst time. **Action**: Fine-tuned Nessus scan policies, added automated validation scripts. **Result**: False positive rate reduced to 8%.
> 3. **Q4 2025**: Zero-day patching took 72 hours (missed 24-hour SLA for Tier 1). **Action**: Created Ansible playbooks for automated patch deployment. **Result**: Next zero-day (simulation test) patched in 18 hours across 200 servers.
>
> Each improvement is tracked with before/after metrics showing effectiveness."

**Evidence to Show**: Continuous Improvement Log, before/after metric screenshots

---

## 8. Post-Audit Actions

- [ ] **If Non-Conformities Raised**: Create corrective action plan with timelines
- [ ] **Update Documentation**: Incorporate auditor feedback into policies/procedures
- [ ] **Communicate Results**: Share audit outcome with management and team
- [ ] **Plan Next Cycle**: Schedule next internal audit (6-12 months)

---

## 9. Related Documents

- [VAPT Policy](../01-policy-governance/VAPT-Policy.md)
- [ISO 9001 Mapping](../03-compliance-integration/ISO-9001-Mapping.md)
- [ISO 27001 Mapping](../03-compliance-integration/ISO-27001-Mapping.md)
- [Continuous Improvement Records](./Continuous-Improvement-Records.md)

---

**Document Control Log**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-15 | Quality/Security Team | Initial audit evidence checklist |

---

*Internal - Management*
