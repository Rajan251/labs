# Rules of Engagement (RoE) Template
**Document Type**: Template for Penetration Testing Authorization
**Version**: 1.0.0
**Status**: TEMPLATE - Must be customized for each engagement

---

> [!IMPORTANT]
> **Authorization Requirement**
> 
> This document MUST be completed, reviewed, and signed by all parties before any penetration testing activities commence. Testing without signed authorization is strictly prohibited and may constitute illegal activity.

---

## 1. Engagement Overview

| Field | Details |
|-------|---------|
| **Engagement Name** | [e.g., "Q4 2025 External Penetration Test"] |
| **Test Type** | [Black-box / Gray-box / White-box] |
| **Asset Class** | [Web Application / Network Infrastructure / Cloud / Mobile / etc.] |
| **Testing Vendor** | [Internal SOC Team / External Company Name] |
| **Engagement ID** | [Unique identifier for tracking] |
| **Requestor** | [Business Unit / Application Owner] |

---

## 2. Legal Authorization

### 2.1 Authorizing Parties

**I, the undersigned, hereby authorize the named security testing team to conduct a controlled penetration test under the terms defined in this document.**

| Role | Name | Title | Signature | Date |
|------|------|-------|-----------|------|
| **CISO (Primary Authority)** | | | | |
| **Asset/Application Owner** | | | | |
| **IT Security Manager** | | | | |

### 2.2 Testing Team

| Role | Name | Organization | Certifications | Contact |
|------|------|--------------|----------------|---------|
| **Lead Penetration Tester** | | | [OSCP/CEH/GPEN] | |
| **Technical Tester(s)** | | | | |
| **Project Manager** | | | | |

### 2.3 Legal Agreements

- [ ] Non-Disclosure Agreement (NDA) executed
- [ ] Master Service Agreement (MSA) in place (for external vendors)
- [ ] Statement of Work (SOW) signed
- [ ] Professional Indemnity Insurance verified (External vendors: Min. $2M coverage)

---

## 3. Scope Definition

### 3.1 In-Scope Assets

**Explicit Authorization**: Testing is authorized **ONLY** for the following assets:

#### Network Ranges
| Network | CIDR | Description | Environment |
|---------|------|-------------|-------------|
| Example: DMZ | 203.0.113.0/24 | Public-facing web servers | Production |
| | | | |

#### Hostnames/URLs
| Asset | URL/Hostname | IP Address | Purpose |
|-------|--------------|------------|---------|
| Example: Corporate Web Portal | https://portal.example.com | 203.0.113.10 | Customer portal |
| | | | |

#### Applications/Services
| Application | Version | Credentials Provided | Access Level |
|-------------|---------|---------------------|--------------|
| Example: CRM System | Salesforce v2024.1 | Yes (User-level) | Gray-box |
| | | | |

#### Cloud Resources (AWS/Azure/GCP)
| Cloud Provider | Account/Subscription ID | Resources | Access Type |
|----------------|------------------------|-----------|-------------|
| Example: AWS | 123456789012 | EC2, S3, RDS in us-east-1 | Read-only IAM role |
| | | | |

### 3.2 Explicitly Out-of-Scope Assets

**PROHIBITED**: Testing the following assets is **NOT AUTHORIZED** and must be avoided:

- [ ] Production databases (except: _________________________ )
- [ ] Third-party hosted services (SaaS applications not owned by us)
- [ ] Partner/vendor networks
- [ ] Specific exclusions:
  - _______________________________________________________
  - _______________________________________________________

**Handling Out-of-Scope Discoveries**: If vulnerabilities are accidentally discovered in out-of-scope assets during testing, testers must:
1. Immediately cease testing that asset
2. Document the finding without exploitation
3. Notify the primary contact within 2 hours

---

## 4. Testing Window

### 4.1 Authorized Timeframe

| Start Date & Time | End Date & Time | Total Duration |
|-------------------|-----------------|----------------|
| [YYYY-MM-DD HH:MM Timezone] | [YYYY-MM-DD HH:MM Timezone] | [X days] |

### 4.2 Time Restrictions

- [ ] **No restrictions** - Testing permitted 24/7 during the authorized window
- [ ] **Business hours only**: [Specify: Monday-Friday, 09:00-17:00 EST]
- [ ] **Non-business hours only**: [Specify: Weekends and 18:00-06:00 EST]
- [ ] **Custom schedule**: _______________________________________

**Rationale**: [e.g., "Production system - minimize user impact by testing after hours"]

### 4.3 Extension Policy

If additional testing time is required:
- Tester must request extension **at least 48 hours** before RoE expiration
- Extension requires email approval from CISO or designated authority
- Original RoE reference number must be cited in extension request

---

## 5. Attack Constraints and Prohibited Actions

### 5.1 Explicitly Prohibited Activities

The following actions are **NEVER PERMITTED** without separate written authorization:

- [ ] **Denial of Service (DoS/DDoS) attacks** - No resource exhaustion or service disruption
- [ ] **Destructive actions** - No data deletion, encryption (ransomware simulation), or permanent modification
- [ ] **Social Engineering** - No phishing emails, vishing calls, or physical impersonation (unless explicitly approved below)
- [ ] **Physical Security Testing** - No tailgating, badge cloning, or facility intrusion attempts
- [ ] **Production Data Exfiltration** - No downloading or transmission of actual PII, PCI, or confidential data
- [ ] **Wireless Attacks** - No deauthentication attacks, rogue AP deployment, or WPA cracking (unless explicitly approved)
- [ ] **Third-Party Attacks** - No pivoting attacks into partner/vendor networks

### 5.2 Permitted Social Engineering (If Applicable)

If social engineering is approved, specify:
- [ ] **Phishing Emails**: Targeting [Department / Specific individuals / All staff]
  - Payload restrictions: [No malware / Benign payload only / Tracked links only]
- [ ] **Vishing (Voice Phishing)**: Targeting [Help Desk / Specific roles]
- [ ] **Physical Intrusion**: Targeting [Specific facilities]
  - Constraints: [No forced entry / Only during business hours]

**Approval**: Requires HR Director and Legal Counsel sign-off (attach separate authorization)

### 5.3 Resource Consumption Limits

To prevent accidental service degradation:
- **Network Traffic**: Do not exceed [X Mbps / % of bandwidth] sustained traffic
- **CPU/Memory**: Exploitation attempts should not consume more than [X%] of system resources for longer than [Y seconds]
- **Storage**: Maximum [X GB] of test data may be uploaded/created
- **API Rate Limits**: Respect published rate limits; do not exceed [X requests/second]

**Safe Words / Stop Conditions**:
- If system performance degrades (response time >5 seconds), cease activity immediately
- If unintended user impact is observed (complaints received), halt and notify contact

---

## 6. Data Handling and Confidentiality

### 6.1 Test Data Guidelines

- [ ] **Production Data Permitted** - Testing in live environment with real data (requires stringent controls)
- [ ] **Sanitized Data Only** - Use anonymized/tokenized copies of production data
- [ ] **Synthetic Data Only** - Use generated test data only

**PII/PCI/PHI Handling**:
- If sensitive data is encountered: [Screenshot filename/record count only - NO EXFILTRATION]
- Data retention post-test: [Immediate deletion / Retention for X days for re-testing / Secure archival]

### 6.2 Confidentiality and Non-Disclosure

- All findings are **CONFIDENTIAL** and property of [Organization Name]
- Tester shall not disclose vulnerabilities to third parties (including vulnerability disclosure programs)
- Findings may not be used in marketing materials without written consent
- Secure communication required: Findings transmitted only via [Encrypted email / Secure file share / VPN]

### 6.3 Evidence Handling

- Screenshots and proof-of-concept code: Stored in [Designated secure repository]
- Network captures: [Permitted / Not permitted] - If permitted, encrypted and password-protected
- Credentials discovered: Must be reported immediately and not used beyond minimal PoC

---

## 7. Communication Protocol

### 7.1 Primary Contacts

| Role | Name | Phone | Email | Availability |
|------|------|-------|-------|--------------|
| **Primary Contact (IT Security Manager)** | | | | [Business hours / 24/7] |
| **Secondary Contact (SOC Lead)** | | | | [Business hours / 24/7] |
| **Emergency Escalation (CISO)** | | | | [24/7 - Critical findings only] |

### 7.2 Status Reporting

- **Daily Status Updates**: Email summary sent by [EOD / specific time] to [Primary Contact]
- **Weekly Progress Reports**: [Required / Not required] for engagements longer than 5 days
- **Critical Finding Notification**: Immediate (within 4 hours) via [Phone call + Email]

### 7.3 Emergency Stop Procedure

**Trigger Conditions**: Testing must immediately cease if:
- Unintended service disruption occurs
- Regulations or law enforcement involvement is suspected
- Safety or legal concerns arise
- Primary Contact issues stop directive

**Stop Protocol**:
1. Cease all testing activities immediately
2. Call Primary Contact: [Phone number]
3. If unreachable, escalate to Secondary Contact within 15 minutes
4. Document all actions taken up to stop point
5. Await explicit authorization to resume

---

## 8. Deliverables and Timeline

### 8.1 Required Deliverables

| Deliverable | Description | Format | Delivery Date |
|-------------|-------------|--------|---------------|
| **Daily Status Email** | Brief summary of testing activities and preliminary findings | Email | Daily by [time] |
| **Draft Report** | Technical findings with severity ratings | PDF | [X business days] after testing completion |
| **Final Report** | Includes remediation guidance and executive summary | PDF + Excel (finding list) | [Y business days] after organization review |
| **Re-test Report** | Validation of remediation for Critical/High findings | PDF | [Z days] after remediation |
| **Evidence Package** | Screenshots, logs, PoC code (sanitized) | Encrypted ZIP | With Final Report |

### 8.2 Report Components

Required sections in Final Report:
- [ ] Executive Summary (non-technical, business risk focus)
- [ ] Methodology and Scope
- [ ] Detailed Findings (CVSS scored, with PoC steps)
- [ ] Remediation Recommendations (prioritized)
- [ ] Appendices (raw scan data, tool outputs)

### 8.3 Confidentiality of Deliverables

- Reports marked **CONFIDENTIAL**
- Distribution limited to: [CISO, IT Security Manager, Asset Owner, Audit Team]
- Retention: Organization retains reports for 7 years (audit requirement)
- Tester retention: External testers must delete all client data within [30 days] after final delivery (unless contractually obligated for longer)

---

## 9. Compliance and Regulatory Considerations

### 9.1 Applicable Regulations

This testing engagement must comply with:
- [ ] ISO/IEC 27001:2022 (Information Security Management)
- [ ] ISO 9001:2015 (Quality Management)
- [ ] PCI-DSS v4.0 (if payment card data in scope)
- [ ] HIPAA (if protected health information in scope)
- [ ] GDPR / CCPA (data privacy laws)
- [ ] [Other: _______________________________]

### 9.2 Audit Trail Requirements

For ISO compliance, the following must be documented:
- All testing activities with timestamps (for A.16.1.7 Evidence Collection)
- Authorization chain (this signed RoE)
- Findings and remediation tracking (links to ticketing system)

---

## 10. Risk Acknowledgment and Liability

### 10.1 Inherent Risks

Both parties acknowledge that penetration testing involves inherent risks, including:
- Potential for service disruption despite safeguards
- Possibility of data corruption or loss
- Discovery of vulnerabilities that may temporarily weaken security posture if disclosed

**Mitigation**: Testers will exercise reasonable care to minimize risks. Organization accepts residual risk.

### 10.2 Limitation of Liability

- **External Vendors**: Liability limited per Master Service Agreement (typically capped at service fees)
- **Internal Testers**: Acting within scope of employment; corporate liability applies
- **Force Majeure**: Testing may be suspended due to unforeseen circumstances (natural disasters, major security incidents)

### 10.3 Indemnification

- Tester indemnifies organization against third-party claims arising from unauthorized actions outside RoE scope
- Organization indemnifies tester for authorized actions within RoE scope that result in claims

---

## 11. Post-Engagement Activities

### 11.1 Data Destruction

Within [30 days] of final report delivery, tester must:
- [ ] Delete all test data, credentials, and network captures
- [ ] Wipe any systems used for testing that contain client data
- [ ] Provide written certification of data destruction

**Exception**: Sanitized findings (no client PII/credentials) may be retained for:
- Internal training purposes
- Methodology improvement
- Anonymous case studies (requires separate approval)

### 11.2 Re-Testing

- Critical and High findings require verification testing after remediation
- Re-test RoE: [Use this same RoE / Requires new abbreviated RoE]
- Re-test window: Within [30 days] of remediation completion notification

### 11.3 Lessons Learned

Post-engagement debrief meeting:
- Date: [Within 2 weeks of final report]
- Attendees: CISO, IT Security Manager, Testing Team Lead, Asset Owner
- Purpose: Discuss findings, remediation approach, process improvements

---

## 12. Special Conditions and Amendments

**Custom requirements for this engagement**:

[Insert any special conditions, such as:]
- Additional compliance requirements (PCI ASV scan, etc.)
- Specific technologies requiring specialized testing (IoT devices, SCADA, etc.)
- Coordination with ongoing projects (migration windows, freeze periods)
- Multi-party coordination (third-party vendor involvement)

**Amendments**: Any changes to this RoE must be documented via email and acknowledged by both CISO and Testing Team Lead.

---

## 13. Acknowledgment and Acceptance

By signing below, all parties confirm:
1. Understanding and acceptance of all terms in this Rules of Engagement
2. Authorization to proceed with testing as scoped
3. Commitment to adhere to all constraints and communication protocols
4. Agreement to handle findings and data per confidentiality terms

---

### Signature Block

**Authorizing Party (Organization)**

| Name & Title | Signature | Date |
|--------------|-----------|------|
| **CISO**: | | |
| **Asset Owner**: | | |
| **IT Security Manager**: | | |

**Testing Team**

| Name & Title | Signature | Date |
|--------------|-----------|------|
| **Lead Penetration Tester**: | | |
| **Project Manager** (if external): | | |

---

**Document Control**

| Engagement ID | Version | Created Date | Authorized Period |
|---------------|---------|--------------|-------------------|
| [e.g., VAPT-2025-Q4-001] | 1.0 | [YYYY-MM-DD] | [Start] to [End] |

**Retention**: This signed RoE must be stored in the secure evidence repository for 7 years (ISO audit requirement).

**Reference**: [VAPT Policy](./VAPT-Policy.md) | [Methodology Framework](./Methodology-Framework.md)

---

*This document is marked as **CONFIDENTIAL**. Unauthorized distribution is prohibited.*
