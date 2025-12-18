# ISO 9001:2015 Compliance Mapping
**Document Control**
- **Version**:1.0.0
- **Effective Date**: December 15, 2025
- **Document Owner**: Quality Manager / CISO
- **Classification**: Internal - Management

---

## 1. Purpose

Demonstrates how the VAPT program satisfies ISO 9001:2015 Quality Management System requirements, treating security vulnerabilities as quality nonconformities.

---

## 2. ISO 9001:2015 Clause Mapping

### Clause 4.4: Quality Management System and its Processes

**Requirement**: Determine processes needed for QMS, including inputs, outputs, criteria, resources

**VAPT Implementation**:
- **Process**: Vulnerability Assessment and Penetration Testing
- **Inputs**: Asset inventory, threat intelligence, testing schedules
- **Outputs**: Vulnerability reports, remediated systems, security improvements
- **Criteria**: Testing frequency per asset criticality, remediation SLAs
- **Resources**: Security tools (Nessus, Metasploit), trained personnel, budget

**Evidence for Auditor**:
- [VAPT Policy](../01-policy-governance/VAPT-Policy.md) - Process definition
- [Methodology Framework](../01-policy-governance/Methodology-Framework.md) - Process details

---

### Clause 5.1: Leadership and Commitment

**Requirement**: Top management demonstrates leadership and commitment to QMS

**VAPT Implementation**:
- CISO (top management) accountable for VAPT program
- VAPT policy approved by CEO/CIO (demonstrated in signature block)
- VAPT results presented to Board/Management Review quarterly

**Evidence for Auditor**:
- VAPT Policy signature page (CEO/CIO approval)
- Management Review meeting minutes showing VAPT KPIs discussed
- Budget allocation for VAPT program (demonstrates resource commitment)

---

### Clause 6.1: Actions to Address Risks and Opportunities

**Requirement**: Determine risks and opportunities, plan actions to address them

**VAPT Implementation**:
- **Risk Identification**: Vulnerabilities discovered = identified risks
- **Risk Assessment**: CVSS scoring + business context = risk evaluation
- **Risk Treatment**: Remediation or risk acceptance with compensating controls

**Evidence for Auditor**:
- Vulnerability reports with CVSS scores
- [Risk Remediation Governance](../01-policy-governance/Risk-Remediation-Governance.md)
- Risk acceptance forms (documented decisions)

---

### Clause 7.1.2: People

**Requirement**: Determine and provide resources needed for QMS

**VAPT Implementation**:
- Dedicated IT Security team (1.5-2 FTE for VAPT coordination)
- External pentest vendors (third-party expertise)
- Training budget for certifications (OSCP, CEH)

**Evidence for Auditor**:
- Organizational chart showing IT Security Manager + SOC team
- External vendor contracts
- Training records (certifications, annual security training)

---

### Clause 7.1.5: Monitoring and Measuring Resources

**Requirement**: Determine resources needed for monitoring/measuring, ensure validity

**VAPT Implementation**:
- Vulnerability scanners (Nessus, Qualys) - calibrated and updated
- Penetration testing tools (Metasploit, Burp Suite) - latest versions
- CVSS calculator (FIRST.org standard)

**Evidence for Auditor**:
- Tool licenses and version records
- Vulnerability scanner update logs (plugin updates weekly)
- Tool calibration records (scan accuracy validation tests)

---

### Clause 7.2: Competence

**Requirement**: Determine necessary competence, ensure personnel are competent

**VAPT Implementation**:
- **Testers**: Certifications required (OSCP, CEH, GPEN for external firms)
- **Internal SOC**: Annual security training, vulnerability management courses
- **Competence Evidence**: Certifications on file, training completion records

**Evidence for Auditor**:
- Tester CVs with certifications
- Internal training matrix (who completed what training)
- External vendor SOC 2 reports (demonstrates their competence)

---

### Clause 8.1: Operational Planning and Control

**Requirement**: Plan, implement, control processes needed to meet requirements

**VAPT Implementation**:
- **Planning**: Annual VAPT schedule (which assets, when, by whom)
- **Implementation**: Execution per [Testing Schedule Matrix](../02-vapt-scope-inventory/Testing-Schedule-Matrix.md)
- **Control**: RoE sign-off required before testing, control measures for production testing

**Evidence for Auditor**:
✅ [VAPT Policy](../01-policy-governance/VAPT-Policy.md) (planned approach)
✅ Annual testing calendar (Gantt chart showing planned vs. actual tests)
✅ Signed RoEs for each engagement (controlled authorization)
✅ Coverage dashboard showing % of assets tested per plan

**Audit Question**: *"How do you plan your security testing?"*

**Answer**: "We maintain an annual testing schedule based on asset criticality. Tier 1 assets undergo bi-annual penetration tests plus weekly automated scans. All testing requires signed Rules of Engagement with explicit scope and authorization. Our dashboard tracks actual vs. planned testing—current compliance is 94% (see coverage report)."

---

### Clause 8.5.1: Control of Production and Service Provision

**Requirement**: Implement production and service provision under controlled conditions

**VAPT Implementation**:
- **Controlled Testing**: All tests follow approved methodologies (OWASP, NIST SP 800-115)
- **Documented Procedures**: Methodology Framework defines standard practices
- **Competent Personnel**: Only certified testers (internal or vetted external firms)
- **Change Control**: Emergency changes for critical vulnremediations follow CAB process

**Evidence for Auditor**:
✅ [Methodology Framework](../01-policy-governance/Methodology-Framework.md)
✅ [Rules of Engagement Template](../01-policy-governance/Rules-of-Engagement-Template.md)
✅ Completed test reports showing methodology adherence
✅ Change requests linked to vulnerability remediation

---

### Clause 9.1.1: Monitoring, Measurement, Analysis, and Evaluation

**Requirement**: Determine what needs monitoring, when to monitor, when to analyze

**VAPT Implementation**:
- **What to Monitor**: Vulnerability trends, remediation velocity, SLA compliance
- **When**: Weekly automated scans, quarterly pentests, monthly metrics review
- **Analysis**: Quarterly trend analysis (are we improving?)

**KPIs Monitored**:
1. Mean Time to Remediate (MTTR) by severity
2. SLA Compliance Rate (% of vulns fixed within SLA)
3. Vulnerability Density (total vulns per 1,000 assets)
4. Asset Coverage (% tested within policy frequency)
5. Recurrence Rate (same vulns found repeatedly = systemic issue)

**Evidence for Auditor**:
✅ VAPT Dashboard (Grafana/Power BI) with real-time KPIs
✅ Quarterly trend reports
✅ Management review presentations showing metrics

---

### Clause 9.1.3: Analysis and Evaluation

**Requirement**: Analyze and evaluate data from monitoring and measurement

**VAPT Implementation**:
- **Quarterly Analysis**: Vulnerability trend analysis, root cause for recurring issues
- **Evaluation**: Are we meeting targets? (95% SLA compliance, 100% Tier 1 coverage)
- **Action**: If targets missed, corrective actions initiated

**Example Analysis**:
```
Q4 2025 VAPT Analysis:
- Total vulnerabilities discovered: 450 (-15% vs. Q3) ✅ Improving
- Critical vulnerabilities: 3 (all remediated within 7 days) ✅ SLA met
- Medium vulnerabilities overdue: 12 (8% breach of SLA) ⚠️ Action needed
- Root Cause: Patch deployment delays due to change freeze in December
- Corrective Action: Pre-approve security patches for deployment even during freeze periods
```

**Evidence for Auditor**:
✅ [Quarterly Analysis Reports](../04-data-infrastructure/Reporting-Templates/)
✅ Action items from analysis (tracked to closure)

---

### Clause 9.2: Internal Audit

**Requirement**: Conduct internal audits to verify QMS conformity

**VAPT Implementation**:
- **Self-Assessment**: Annual internal audit of VAPT program (before external ISO audit)
- **Audit Scope**: Verify all policy requirements met (coverage, documentation, SLAs)
- **Findings**: Any gaps identified → corrective actions

**Evidence for Auditor**:
✅ Internal audit plan (including VAPT process in scope)
✅ Internal audit report with findings
✅ Corrective actions from internal audit (closed before certification audit)

---

### Clause 9.3: Management Review

**Requirement**: Top management reviews QMS at planned intervals

**VAPT Implementation**:
- **Frequency**: Quarterly VAPT results presented to CISO, Annual to Board
- **Inputs**: Vulnerability trends, compliance status, resource needs
- **Outputs**: Decisions on resource allocation, policy updates, risk acceptances

**Management Review Agenda** (includes VAPT):
1. Previous action items status
2. Changes in external/internal issues (new threats, regulatory changes)
3. **VAPT Program Performance**: KPIs, SLA compliance, coverage
4. Nonconformities and corrective actions (critical vulnerabilities = nonconformities)
5. Improvement opportunities (tool upgrades, process enhancements)
6. Resource needs (budget for next fiscal year)

**Evidence for Auditor**:
✅ Management review meeting minutes (last 3-4 quarters)
✅ VAPT presentations to management
✅ Action items from management reviews (with owners and due dates)

---

### Clause 10.2: Nonconformity and Corrective Action

**Requirement**: When nonconformity occurs, react, evaluate need for action, implement corrective action

**VAPT Implementation**: **Vulnerabilities = Nonconformities**

**Process**:
1. **React**: Vulnerability discovered → Immediate notification for Critical/High
2. **Evaluate**: Assess impact, assign severity, determine cause
3. **Corrective Action**: Remediate (patch, config change, code fix)
4. **Verify Effectiveness**: Re-test to confirm vulnerability resolved
5. **Update Process**: If recurring vulnerability class → systemic fix (training, tooling)

**Example**:
> **Nonconformity**: SQL Injection found in 3 different applications in Q2 and Q3 2025
> 
> **Root Cause Analysis**: Developers lack secure coding training, no SAST tool to catch injection flaws
> 
> **Corrective Action**:
> 1. **Immediate**: Fix all 3 SQL injection vulnerabilities (completed within 30 days)
> 2. **Systemic**: (a) Mandatory OWASP Top 10 training for all backend developers (completed Q4), (b) Integrated Semgrep SAST in CI/CD pipeline (blocks SQLi patterns before merge)
> 
> **Verification**: Q4 2025 pentest found ZERO SQL injection vulnerabilities ✅

**Evidence for Auditor**:
✅ Vulnerability tickets showing lifecycle (discovery → remediation → verification)
✅ Root cause analysis documents (for recurring issues)
✅ Process improvements implemented (e.g., CI/CD integration PRs, training rosters)

---

### Clause 10.3: Continual Improvement

**Requirement**: Continually improve the suitability, adequacy, and effectiveness of the QMS

**VAPT Implementation**:
- **Lessons Learned**: Post-test debriefs, post-zero-day incident reviews
- **Process Enhancements**: Update testing methodologies, tooling upgrades
- **Trend Analysis**: Year-over-year improvements (fewer vulns, faster remediation)

**Documented Improvements** (Evidence):
```
Continuous Improvement Log:

2024-Q3:
- Problem: External pentest discovered API not in asset inventory (untracked for 2 years)
- Improvement: Implemented automated Certificate Transparency log monitoring
- Result: Discovered 12 additional subdomains, all added to inventory

2024-Q4:
- Problem: Manual patching for zero-days took 72 hours (missed 24-hour SLA for Tier 1)
- Improvement: Created Ansible playbooks for automated patch deployment
- Result: Log4j v2 zero-day patched across 200 servers in 18 hours (Q1 2025 zero-day test)

2025-Q1:
- Problem: False positive rate in automated scans = 25% (wasted analyst time)
- Improvement: Fine-tuned Nessus scan policies, added validation scripts
- Result: False positive rate reduced to 8%
```

**Evidence for Auditor**:
✅ [Continuous Improvement Records](../05-audit-preparedness/Continuous-Improvement-Records.md)
✅ Before/after metrics showing improvement
✅ Updated procedures/tooling resulting from improvements

---

## 3. ISO 9001 Audit Evidence Checklist

### For Certification Auditor

| ISO Clause | Evidence Required | Location in VAPT Program |
|------------|-------------------|--------------------------|
| **4.4** (Processes) | Process map, inputs/outputs | VAPT Policy, Methodology Framework |
| **5.1** (Leadership) | Top management approval | VAPT Policy signature page, Board presentations |
| **6.1** (Risk) | Risk assessment records | Vulnerability reports with CVSS, Risk acceptance forms |
| **7.2** (Competence) | Training records | Tester certifications, training logs |
| **8.1** (Planning) | Operational plans | Annual VAPT schedule, Asset inventory |
| **8.5.1** (Control) | Controlled procedures | Methodology Framework, RoE templates |
| **9.1.3** (Analysis) | Performance data analysis | VAPT dashboards, Quarterly trend reports |
| **9.2** (Internal Audit) | Internal audit results | VAPT self-assessment report |
| **9.3** (Management Review) | Review meeting minutes | Quarterly management review minutes (with VAPT KPIs) |
| **10.2** (Corrective Action) | Nonconformity records | Vulnerability tickets (closed), Root cause analysis |
| **10.3**(Improvement) | Improvement initiatives | Continuous Improvement Log, Updated processes |

---

## 4. Sample Audit Narrative

**Auditor Question**: *"How does your organization ensure the quality of IT services from a security perspective?"*

**Response**:
> "Our VAPT program treats security vulnerabilities as quality nonconformities under ISO 9001. We have a planned approach (Clause 8.1) with annual testing schedules based on asset criticality. All testing follows controlled procedures (Clause 8.5.1) with signed authorizations. 
>
> We monitor key performance indicators monthly (Clause 9.1.1), including mean-time-to-remediate and SLA compliance, which are analyzed quarterly to identify trends (Clause 9.1.3). Any vulnerabilities found are treated as nonconformities—we remediate them according to severity-based SLAs, conduct root cause analysis for recurring issues (Clause 10.2), and implement systemic improvements like developer training or CI/CD security integration (Clause 10.3).
>
> Top management reviews VAPT results quarterly (Clause 9.3), making decisions on resource allocation and policy updates. For example, in Q4 2024, management approved additional budget for automated scanning based on our recommendation from lessons learned. This demonstrates our continual improvement cycle."

---

## 5. Related Documents

- [VAPT Policy](../01-policy-governance/VAPT-Policy.md)
- [Risk Remediation Governance](../01-policy-governance/Risk-Remediation-Governance.md)
- [Continuous Improvement Records](../05-audit-preparedness/Continuous-Improvement-Records.md)
- Corporate ISO 9001 Quality Manual

---

**Document Control Log**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-15 | Quality/Security Team | Initial ISO 9001 mapping for VAPT |

---

*Internal - Management*
