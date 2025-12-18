# Risk Acceptance & Remediation Governance
**Document Control**
- **Version**: 1.0.0
- **Effective Date**: December 15, 2025
- **Document Owner**: CISO
- **Review Cycle**: Annual
- **Classification**: Internal - Management

---

## 1. Purpose

This document defines the governance framework for managing the complete lifecycle of security vulnerabilities discovered through VAPT activities, from initial identification through verified remediation or formal risk acceptance.

**Objective**: Ensure systematic, risk-based prioritization and timely resolution of security weaknesses according to their business impact.

**ISO Compliance Alignment**:
- **ISO 9001:2015 Clause 10.2**: Vulnerabilities treated as nonconformities requiring corrective action
- **ISO/IEC 27001:2022 A.8.8**: Management of technical vulnerabilities - defines how appropriate measures are taken

---

## 2. Severity Classification Framework

### 2.1 CVSS v3.1 Base Scoring

All vulnerabilities are initially scored using the Common Vulnerability Scoring System (CVSS) v3.1:

| CVSS Score | Severity Rating | Color Code |
|------------|-----------------|------------|
| 9.0 - 10.0 | **Critical** | 🔴 Red |
| 7.0 - 8.9 | **High** | 🟠 Orange |
| 4.0 - 6.9 | **Medium** | 🟡 Yellow |
| 0.1 - 3.9 | **Low** | 🔵 Blue |
| 0.0 | **Informational** | ⚪ White |

**CVSS Components**:
- **Attack Vector (AV)**: Network (N), Adjacent (A), Local (L), Physical (P)
- **Attack Complexity (AC)**: Low (L), High (H)
- **Privileges Required (PR)**: None (N), Low (L), High (H)
- **User Interaction (UI)**: None (N), Required (R)
- **Scope (S)**: Unchanged (U), Changed (C)
- **Impact (C/I/A)**: None (N), Low (L), High (H) for Confidentiality, Integrity, Availability

**Example**: SQL Injection in login page
- CVSS Vector: `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H`
- **Base Score**: 10.0 (Critical)

**Tools**: CVSS calculators at [first.org/cvss/calculator/3.1](https://www.first.org/cvss/calculator/3.1)

---

### 2.2 Business Context Adjustment

**CVSS Base Score is adjusted based on organizational context:**

#### Criticality Multipliers

| Asset Criticality Tier | Adjustment | Example Assets |
|------------------------|------------|----------------|
| **Tier 1 (Mission-Critical)** | +1.0 severity level (if borderline) | Payment processing, customer PII databases, authentication services |
| **Tier 2 (Important)** | No adjustment | Internal business applications, employee portals |
| **Tier 3 (Low Impact)** | -0.5 severity level (if borderline) | Development environments, test systems, archived data |

#### Threat Intelligence Context

- **Actively Exploited in Wild**: Upgrade to Critical (regardless of CVSS)
- **Exploit Code Publicly Available**: Upgrade severity by 1 level if exploitability is trivial
- **Targeted Attack Campaign**: If organization is specifically targeted, upgrade by 1 level

#### Data Exposure Assessment

| Data Classification on Asset | Impact on Severity |
|-------------------------------|--------------------|
| **Restricted (PII, PCI, IP, PHI)** | +1 severity level |
| **Confidential** | No adjustment |
| **Internal/Public** | -1 severity level (if Low/Info only) |

**Example Adjustment**:
- Finding: Directory Traversal (CVSS 6.5 - Medium)
- Asset: Customer PII database (Tier 1, Restricted data)
- **Adjusted Severity**: **High** (Medium → High due to data sensitivity)

---

### 2.3 Final Severity Determination

**Decision Matrix**:

| CVSS Score | Asset Tier 1 | Asset Tier 2 | Asset Tier 3 |
|------------|--------------|--------------|--------------|
| Critical (9.0-10.0) | **Critical** | **Critical** | **High** |
| High (7.0-8.9) | **High** | **High** | **Medium** |
| Medium (4.0-6.9) | **High** (if restricted data) | **Medium** | **Low** |
| Low (0.1-3.9) | **Medium** (if restricted data) | **Low** | **Informational** |

**Authority for Adjustment**: IT Security Manager (documented in finding record)

---

## 3. Remediation SLAs (Service Level Agreements)

### 3.1 Standard Remediation Timelines

Vulnerabilities must be remediated or formally risk-accepted within the following timeframes **from date of discovery**:

| Severity | SLA (Calendar Days) | Remediation Responsibility | Escalation if Breached |
|----------|---------------------|----------------------------|------------------------|
| **Critical** | **7 days** | DevOps/IT (Priority 0) | CISO + CIO notification |
| **High** | **30 days** | DevOps/IT (Priority 1) | IT Security Manager escalates to CISO |
| **Medium** | **90 days** | DevOps/IT (Priority 2) | Tracking in quarterly review |
| **Low** | **Next maintenance window** or **180 days** (whichever is sooner) | DevOps/IT (Priority 3) | Annual audit may flag if >1 year old |
| **Informational** | No SLA (advisory only) | Optional | N/A |

### 3.2 SLA Clock Start and Stop

**Start Time**: SLA begins when:
- Automated scan finding is validated by SOC (false positives don't start SLA)
- Penetration test report is delivered to IT Security Manager
- Zero-day alert is confirmed applicable to organization

**Pause Conditions**: SLA may be paused (requires IT Security Manager approval):
- Awaiting vendor patch availability (for third-party software vulnerabilities)
- Scheduled maintenance window required (e.g., must wait for quarterly downtime)
- Dependency on external party (service provider, vendor)
- **Pause must be documented in ticket with justification**

**Stop Time**: SLA stops when:
- Remediation is deployed to production **AND** verified (re-test passed)
- Formal risk acceptance is approved and documented

---

### 3.3 Critical Vulnerability Expedited Process

**For Critical Findings (CVSS ≥9.0 or actively exploited)**:

**Hour 0-4**: Discovery and Notification
- SOC validates finding (within 2 hours)
- CISO and IT Security Manager notified immediately (phone + email)
- Emergency change request initiated

**Hour 4-24**: Assessment and Planning
- Engineering team assesses impact and remediation approach
- Business impact analysis (can we patch immediately or need rollback plan?)
- Interim mitigation deployed if immediate patch not feasible (e.g., WAF rule, network segmentation)

**Day 1-7**: Remediation and Verification
- Patch/fix developed and tested in staging
- Emergency change approval (expedited CAB process)
- Deployment to production
- Verification testing by SOC or external tester
- Closure documentation

**Fallback**: If remediation cannot be completed in 7 days, formal risk acceptance required from CISO (see Section 4).

---

## 4. Risk Acceptance Workflow

### 4.1 When Risk Acceptance is Appropriate

Risk acceptance (choosing NOT to remediate) may be considered only if:
- [ ] Remediation cost significantly outweighs risk (economic justification)
- [ ] Compensating controls reduce risk to acceptable level
- [ ] System is scheduled for decommissioning within [30 days]
- [ ] Vendor patch not available and workaround not feasible (document vendor communication)
- [ ] Remediation would break critical business functionality (requires detailed business case)

**Prohibited**: Risk acceptance for Critical vulnerabilities on Tier 1 assets is generally **NOT PERMITTED** unless:
- No technical remediation exists AND
- Compensating controls are implemented AND
- CISO and CIO jointly approve

---

### 4.2 Risk Acceptance Process

**Step 1: Request Submission** (Asset Owner or DevOps Lead)

Submit risk acceptance request including:
- Vulnerability details (CVSS score, description, affected asset)
- Business justification (why not remediating?)
- Compensating controls (what alternative protections are in place?)
- Proposed acceptance period (maximum 1 year, requires annual renewal)
- Residual risk assessment (what risk remains?)

**Form**: [Risk Acceptance Request Form - Appendix A](#appendix-a-risk-acceptance-request-form)

---

**Step 2: Technical Review** (IT Security Manager)

Security team evaluates:
- Adequacy of compensating controls
- Accuracy of risk assessment
- Compliance impact (does this violate regulatory requirements?)

**Output**: Recommendation (Approve / Reject / Approve with Conditions)

---

**Step 3: Approval Authority**

| Vulnerability Severity | Approval Authority | Documentation Required |
|------------------------|-------------------|------------------------|
| **Critical** | CISO + CIO (joint approval) | Full risk acceptance package + Board notification |
| **High** | CISO | Risk acceptance form + compensating control evidence |
| **Medium** | IT Security Manager | Risk acceptance form |
| **Low** | IT Security Manager (delegated) | Email approval acceptable |

---

**Step 4: Documentation and Tracking**

Approved risk acceptances must be:
- Logged in vulnerability management system (status = "Risk Accepted")
- Stored in evidence repository: `/VAPT_Evidence/Risk_Acceptances/YYYY/`
- Added to Risk Register (for ISO 27001 compliance)
- Reviewed in quarterly management reviews

---

### 4.3 Compensating Controls Requirement

**Definition**: Alternative security measures that reduce risk when remediation is not feasible.

**Examples**:

| Vulnerability | Compensating Control Example |
|---------------|------------------------------|
| Unpatched web server (vendor patch unavailable) | Deploy Web Application Firewall (WAF) with virtual patching rule |
| SQL injection in legacy app (cannot refactor code) | Database firewall + read-only account + input validation layer |
| Weak encryption on internal system | Network segmentation (restrict access to internal network only) + MFA |
| Default credentials on IoT device (cannot change) | Isolate on dedicated VLAN with strict firewall rules |

**Compensating Control Validation**:
- Must be tested and verified effective (e.g., re-test confirms WAF blocks exploit)
- Must be monitored (alerts if control is bypassed or disabled)
- Documented in risk acceptance form

---

### 4.4 Risk Acceptance Renewal and Re-Assessment

**Annual Review**: All risk acceptances must be re-evaluated every 12 months:
- Is the vulnerability still present?
- Are compensating controls still effective?
- Has the threat landscape changed (e.g., exploit now widely available)?
- Is decommissioning/remediation now feasible?

**Outcomes**:
- **Renew**: Extend acceptance for another year (requires re-approval)
- **Remediate**: Vulnerability now must be fixed
- **Revoke**: Asset must be taken offline if cannot remediate or renew

**Trigger for Early Re-Assessment**:
- Compensating control fails or is removed
- Exploit code for the vulnerability is published
- Regulatory change makes acceptance non-compliant
- Asset criticality changes (e.g., Tier 3 → Tier 1)

---

## 5. Remediation Workflow

### 5.1 Ticket Creation and Assignment

**Automated Process** (for Critical/High findings):
1. Vulnerability finding exported from scanner/pentest report
2. Jira/ServiceNow ticket auto-created via API integration
3. Ticket fields populated:
   - **Title**: [Severity] Vulnerability Name - Asset Name
   - **Description**: CVSS score, PoC steps, business impact
   - **Priority**: Mapped to severity (Critical=P0, High=P1, etc.)
   - **Due Date**: Auto-calculated based on SLA
   - **Assigned To**: Asset owner (from CMDB) or DevOps on-call
   - **Labels**: `security`, `VAPT`, `ISO27001`

**Manual Process** (for Medium/Low):
- IT Security Manager reviews and batches findings
- Creates bundled tickets (e.g., "Q4 2025 Medium Vulnerability Remediation - WebApp-X")

---

### 5.2 Remediation Approaches

| Remediation Type | Description | Example |
|------------------|-------------|---------|
| **Patching** | Apply vendor security update | Install Windows KB5034xxx, upgrade OpenSSL to 3.0.13 |
| **Configuration Change** | Adjust settings to secure state | Disable TLS 1.0, enable HTTP security headers, change default passwords |
| **Code Fix** | Modify application source code | Parameterized queries for SQL injection fix, input validation |
| **Removal/Decommission** | Eliminate vulnerable component | Remove unused admin interface, uninstall obsolete software |
| **Network Segmentation** | Isolate vulnerable system | Move to restricted VLAN, firewall rule to limit access |
| **Upgrade/Replacement** | Replace with secure alternative | Migrate from legacy app to modern platform |

**Best Practice**: Always prefer vendor-provided patches over custom workarounds (for supportability and ongoing security).

---

### 5.3 Testing and Verification

**Before Deployment** (Staging/QA):
- Test fix in non-production environment
- Verify vulnerability is remediated (scan/test the fix)
- Regression testing (ensure functionality not broken)

**After Deployment** (Production):
- **Re-Scan**: Automated vulnerability scanner re-checks the asset (for scanner-found issues)
- **Re-Test**: For manually discovered vulnerabilities (especially Critical/High), request verification from:
  - SOC team (internal findings)
  - External pentester (for their reported findings)
- **Evidence Collection**: Screenshot of clean scan result or re-test confirmation

**Closure Criteria**:
- Vulnerability no longer present in scan/test
- Evidence documented in ticket
- IT Security Manager approves closure

---

### 5.4 Remediation Evidence for Audit

**For ISO compliance, each closed vulnerability must have**:
- **Before**: Original finding with severity and PoC
- **Remediation Action**: What was done (patch version, config change, code commit ID)
- **After**: Re-test result showing vulnerability resolved
- **Approver**: IT Security Manager sign-off

**Storage**: Attach evidence to ticket + archive in Evidence Repository

---

## 6. Escalation Procedures

### 6.1 SLA Breach Escalation

**7 Days Before Due Date**: Automated reminder to assigned engineer + manager

**On Due Date** (SLA Breach):
| Severity | Escalation Level | Notification | Action Required |
|----------|------------------|--------------|-----------------|
| **Critical** | Executive | CISO + CIO email + SMS | Immediate status meeting scheduled |
| **High** | Senior Management | IT Security Manager escalates to CISO | Remediation plan with revised timeline due in 24 hours |
| **Medium** | Management | Flagged in weekly security meeting | Explanation and plan required |
| **Low** | Operational | Noted in quarterly report | Track for annual audit review |

---

### 6.2 Recurring Vulnerability Escalation

**Definition**: Same vulnerability class found in multiple consecutive tests (e.g., SQL injection in 3 apps across 2 quarters)

**Process**:
1. **Root Cause Analysis Required**: Why is this pattern recurring?
   - Developer training gap?
   - Lack of secure coding standards?
   - SAST tools not catching it during development?
2. **Systemic Fix**: Address the underlying cause:
   - Mandatory secure coding training
   - Implement pre-commit SAST scanning
   - Update coding standards and templates
3. **Documented in Continuous Improvement Log**: ISO 9001 Clause 10.3 requirement

**Example**:
> "Q1 & Q2 2025: Found SSRF vulnerabilities in 4 different internal APIs. **Root Cause**: Developers unaware of SSRF risk. **Systemic Fix**: (1) Mandatory OWASP Top 10 training for all backend devs, (2) Integrated Semgrep SAST scans in CI/CD to auto-detect SSRF patterns. **Result**: Q3 & Q4 tests found zero SSRF issues."

---

## 7. Metrics and Reporting

### 7.1 Tracking Metrics

**For ISO 9001 (Quality Management) Analysis**:
1. **Remediation Velocity**:
   - Mean Time to Remediate (MTTR) by severity
   - Trend over quarters (improving or degrading?)
   
2. **SLA Compliance Rate**:
   - Percentage of vulnerabilities remediated within SLA
   - Target: >95% for High/Critical, >85% for Medium

3. **Vulnerability Recurrence Rate**:
   - % of findings that are re-discoveries of previously patched issues
   - Target: <5% (indicates patch effectiveness)

4. **Risk Acceptance Rate**:
   - % of findings risk-accepted vs. remediated
   - Target: <10% overall (risk acceptance should be exception, not norm)

**Dashboard**: Grafana/Power BI dashboard updated weekly with these KPIs

---

### 7.2 Management Reporting

**Quarterly VAPT Summary to CISO**:
- Total vulnerabilities discovered (trend vs. previous quarter)
- Breakdown by severity
- Top 5 vulnerable asset classes
- SLA compliance metrics
- Outstanding risk acceptances requiring renewal

**Annual Board Report**:
- Year-over-year security posture improvement
- Business risk reduction quantified ($$ saved vs. potential breach cost)
- Compliance attestation (ISO audit readiness)
- Investment recommendations (tool upgrades, team expansion)

---

## 8. Integration with Change Management

**Principle**: All security remediations follow standard Change Management procedures (ITIL framework).

**Exception**: **Emergency Changes** for Critical vulnerabilities
- Expedited Change Advisory Board (CAB) approval process
- Post-implementation review required within 5 days

**Traceability**:
- Vulnerability ticket references Change Request (CR) number
- CR references vulnerability ticket for justification
- Audit trail for ISO 9001 Clause 8.5.1 (Controlled Processes)

---

## 9. Governance Review and Continuous Improvement

### 9.1 Quarterly Governance Review

**Attendees**: CISO, IT Security Manager, DevOps Lead, Risk Manager

**Agenda**:
- Review all active risk acceptances (any need re-assessment?)
- SLA breach post-mortems (why did we miss deadline?)
- Remediation process bottlenecks (how to streamline?)
- Tool effectiveness (are scanners catching what pentests find?)

**Output**: Action items for process improvement

---

### 9.2 Annual Policy Review

This governance document reviewed annually or triggered by:
- Regulatory change (new compliance requirements)
- Major security incident (update based on lessons learned)
- ISO audit findings (address non-conformities)

---

## 10. Related Documents

- [VAPT Policy](./VAPT-Policy.md)
- [Methodology Framework](./Methodology-Framework.md)
- [Asset Inventory System](../02-vapt-scope-inventory/Asset-Inventory-System.md)
- [Findings Database Schema](../04-data-infrastructure/Findings-Database-Schema.md)
- [Continuous Improvement Records](../05-audit-preparedness/Continuous-Improvement-Records.md)
- ISO 9001:2015 Quality Manual (Corporate)
- ISO/IEC 27001:2022 Risk Treatment Plan (Corporate)

---

## Appendix A: Risk Acceptance Request Form

**Risk Acceptance Request**

| Field | Details |
|-------|---------|
| **Request ID** | [Auto-generated: RA-YYYY-NNNN] |
| **Submission Date** | [YYYY-MM-DD] |
| **Requestor Name & Title** | |
| **Asset Owner Name** | |

**Vulnerability Details**

| Field | Details |
|-------|---------|
| **Finding ID** | [Link to vulnerability ticket] |
| **Vulnerability Title** | |
| **CVSS Score** | |
| **Adjusted Severity** | [Critical / High / Medium / Low] |
| **Affected Asset(s)** | [Hostname, IP, Application name] |
| **Discovery Date** | |
| **Current SLA Due Date** | |

**Justification for Risk Acceptance**

Why is remediation not feasible? (Select all that apply and provide details)

- [ ] **Economic**: Remediation cost ($______) exceeds risk ($______). *Provide cost-benefit analysis.*
- [ ] **Technical Limitation**: [e.g., Vendor patch unavailable, legacy system incompatibility]
- [ ] **Business Impact**: Remediation breaks critical functionality. *Describe impact and affected business process.*
- [ ] **Scheduled Decommission**: Asset retiring on [Date - must be <90 days]
- [ ] **Other**: _______________________________________________

**Compensating Controls**

What alternative security measures are in place to reduce risk?

| Compensating Control | Implementation Details | Effectiveness Validation |
|----------------------|------------------------|--------------------------|
| [e.g., WAF Rule] | [Rule ID, configuration] | [Re-test shows exploit blocked] |
| | | |

**Residual Risk Assessment**

- **Likelihood** (after compensating controls): [Low / Medium / High]
- **Impact** (if exploited): [Low / Medium / High]
- **Residual Risk Level**: [Low / Medium / High]

**Risk Acceptance Period**

- **Proposed Duration**: [6 months / 12 months] (Maximum 1 year)
- **Re-Assessment Date**: [YYYY-MM-DD]

---

**Approvals**

| Role | Name | Approve/Reject | Signature | Date |
|------|------|---------------|-----------|------|
| **IT Security Manager** (Technical Review) | | | | |
| **CISO** (Required for High/Critical) | | | | |
| **CIO** (Required for Critical only) | | | | |

**Decision**: [Approved / Approved with Conditions / Rejected]

**Conditions** (if applicable): _________________________________________

---

**Document Control Log**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-15 | CISO Office | Initial governance framework |

---

*This document is marked as **Internal - Management**. Unauthorized distribution is prohibited.*
