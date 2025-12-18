# Data Classification and Handling
**Document Control**
- **Version**: 1.0.0
- **Effective Date**: December 15, 2025
- **Document Owner**: CISO / Data Protection Officer
- **Classification**: Internal - Management

---

## 1. Purpose

Defines how different data classifications are handled during VAPT activities to protect sensitive information while ensuring thorough security testing.

**Key Principle**: **Security testing must never compromise data privacy or regulatory compliance.**

---

## 2. Data Classification Scheme

| Classification | Definition | Examples | Access Restrictions |
|----------------|------------|----------|---------------------|
| **Restricted** | Highest sensitivity - regulatory/legal protections | PII (SSNs, financial data), PCI (credit cards), PHI (medical records), Trade secrets, M&A data | Need-to-know only, encryption required, special handling |
| **Confidential** | Internal-only business data | Internal communications, business plans, employee data, non-public financials | Internal staff only, not for public disclosure |
| **Internal** | General business information | Employee directory, internal procedures, company policies | All employees |
| **Public** | No confidentiality | Marketing materials, public website content, press releases | Unrestricted |

---

## 3. VAPT Data Handling Requirements by Classification

### 3.1 Restricted Data

**Testing Environments**:
- ❌ **Production Data PROHIBITED** for destructive testing
- ✅ **Tokenized/Anonymized Data ONLY** for test environments
- ✅ **Synthetic/Generated Test Data** preferred

**Example Scenarios**:

#### Scenario 1: SQL Injection Testing on Customer Database
**Problem**: Need to test SQL injection on production customer table with 10M records containing PII (names, emails, SSNs)

**Prohibited Approach**: ❌
```sql
-- Tester extracts real data
SELECT first_name, last_name, ssn FROM customers WHERE id=1 OR 1=1;
-- Data exfiltration = regulatory violation
```

**Permitted Approach**: ✅
```sql
-- Read-only test in production:
SELECT COUNT(*) FROM customers WHERE id=1 OR 1=1;
-- Proves vulnerability exists without data exfiltration
-- Screenshot shows elevated row count = PoC sufficient

-- OR use staging environment with tokenized data:
-- SSN: 123-45-6789 → XXX-XX-6789
-- Email: john.doe@gmail.com → user12345@example-test.com
```

#### Scenario 2: Penetration Test Discovers Backup File
**Situation**: Tester finds `/backups/customer_db_2025-01-01.sql` exposed on web server

**Required Actions**:
1. **Do NOT download the file** (GDPR/CCPA violation)
2. Take screenshot of file listing (proves exposed)
3. Immediately notify CISO (potential data breach)
4. If file must be analyzed (to assess scope), do so on-premise with legal approval

---

#### PII-Specific Controls

**For Systems with Personal Identifiable Information**:
- [ ] Tester signs enhanced NDA with data protection clauses
- [ ] Tester completes privacy training (GDPR, CCPA awareness)
- [ ] Background check on testers (external firms must provide certificates)
- [ ] No data exfiltration clause in RoE (breach clause with penalties)
- [ ] Testing conducted in secure environment (VPN-only access, MFA required)
- [ ] All evidence (screenshots) reviewed to redact PII before reporting

**Data Minimization**: Screenshots should show **proof of vulnerability**, not actual data content.

**Good Screenshot**:
```
Screenshot shows: "You have permission to view 500,000 customer records"
                  [Only first 3 sanitized rows visible in screenshot]
```

**Bad Screenshot**: ❌ Full table dump with real names, emails, addresses

---

#### PCI-DSS Scope (Payment Card Data)

**PCI-DSS Requirement 11.3**: Penetration testing required annually

**Special Requirements**:
- **Never store full PAN** (Primary Account Number) in test evidence
- Use PCI-DSS approved testing methodology (e.g., PA-DSS validated tools)
- Tester must be **PCI-DSS QSA (Qualified Security Assessor)** or work under one
- Testing in CDE (Cardholder Data Environment) requires **change control board** approval
- Test credit cards: Use **test PANs** from payment processor (e.g., Stripe test mode: 4242 4242 4242 4242)

**Handling Discovered PANs**:
- Finding: Tester discovers credit card numbers in web server logs
- **Action**: Immediately notify CISO, document finding with masked PAN (4111-XXXX-XXXX-1111), secure deletion of evidence post-reporting

---

### 3.2 Confidential Data

**Permitted in Testing**:
- ✅ Production testing allowed (with approval and read-only access preferred)
- ✅ Data can be included in evidence if necessary for proof

**Controls**:
- Reports marked **CONFIDENTIAL** (distribution list limited to security team + audit)
- Evidence encrypted (AES-256) and access-controlled repository
- No disclosure to third parties (including responsible disclosure platforms)

**Example**: Internal HR system pentest
- Tester can access employee records to test access controls
- Report may include redacted employee data as proof (e.g., "Captured screenshot showing unauthorized access to Employee Records for John D., Department: Finance")
- Full data not included in report (only metadata necessary for PoC)

---

### 3.3 Internal & Public Data

**Minimal Restrictions**:
- ✅ Standard VAPT procedures apply
- ✅ Evidence handling per normal process

**Note**: Even public-facing assets may have confidential backend data—always verify data classification before testing.

---

## 4. Test Data Management

### 4.1 Synthetic Data Generation

**When Required**: All non-production environments, training, demos

**Generation Methods**:

| Data Type | Synthetic Generation Tool/Method | Example |
|-----------|----------------------------------|---------|
| **Names** | Faker library (Python/JS), Mockaroo | Faker: `John Smith` → `Katherine Rodriguez` (random realistic names) |
| **Email Addresses** | test domain (e.g., `@example-testing.com`) | Real: `john.doe@gmail.com` → Test: `user12345@example-testing.com` |
| **Phone Numbers** | Unused area codes (e.g., 555 prefix in US) | (555) 123-4567 |
| **SSN / National IDs** | Test SSNs (IRS: 987-65-4320 through 987-65-4329) | 987-65-4320 |
| **Credit Cards** | Luhn-valid test numbers (Stripe, PayPal provide) | 4242 4242 4242 4242 (Visa test card) |
| **Addresses** | Randomized with real zip codes but fake street names | 123 Test Avenue, Springfield, IL 62701 |

**Tools**:
- **Faker Library** (Python): Generates realistic fake data (names, addresses, emails, etc.)
- **Mockaroo**: Web-based synthetic data generator (CSV export)
- **Tonic.ai**: Enterprise data masking/synthetic data platform
- **Delphix**: Data virtualization and masking

---

### 4.2 Data Anonymization/Tokenization

**When Required**: Using production data for staging/QA environments

**Techniques**:

| Technique | Description | Use Case | Reversibility |
|-----------|-------------|----------|---------------|
| **Masking** | Replace characters with X or * | SSN: 123-45-6789 → XXX-XX-6789 | ❌ Irreversible |
| **Tokenization** | Replace with random token, maintain lookup table (encrypted) | Credit card: 4111111111111111 → TOKEN-ABC-123 | ✅ Reversible (for authorized personnel) |
| **Shuffling** | Randomize within same column | Shuffle all emails so Email #1 assigned to User #37 | ❌ Irreversible |
| **Hashing** | One-way cryptographic hash | User ID: 12345 → SHA256(12345+salt) | ❌ Irreversible (proper salting required) |
| **Generalization** | Replace specific with category | Age: 47 → Age Range: 40-50 | ❌ Irreversible |

**Best Practice**: Tokenization for structured PII (reversible if needed), Synthetic Generation for non-production

---

### 4.3 Test Data Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│                Test Data Lifecycle                           │
└─────────────────────────────────────────────────────────────┘

1. CREATION
   ├── Production → Anonymization Pipeline → Staging/QA
   └── OR Synthetic Data Generation → Staging/QA

2. USAGE (During VAPT)
   ├── Testers access staging with tokenized data
   └── Evidence collected (screenshots)

3. RETENTION
   ├── Evidence stored in encrypted repository (7 years for audit)
   └── Test data refreshed monthly (re-tokenize with new random seeds)

4. DESTRUCTION
   ├── Post-engagement: Tester deletes all local copies within 30 days
   └── Staging environment: Data refreshed/wiped quarterly
```

---

## 5. Tester Requirements by Data Classification

### 5.1 Background Checks and Training

| Data Classification | Background Check | Training Required | NDA Type |
|---------------------|------------------|-------------------|----------|
| **Restricted (PII/PCI/PHI)** | ✅ Required (criminal + credit check) | GDPR, HIPAA, PCI-DSS awareness | Enhanced NDA with liquidated damages clause |
| **Confidential** | ✅ Recommended | General security awareness | Standard NDA |
| **Internal/Public** | ❌ Not required | Standard VAPT training | Standard NDA |

**External Testing Firms**:
- Must provide certificates of background checks for all testers
- Insurance: Cyber liability coverage min. $2M (covers potential data breach)
- SOC 2 Type II certification preferred (demonstrates their own data handling controls)

---

### 5.2 Tester Workspace Security

**For Restricted Data Testing**:
- [ ] Dedicated secure workstation (encrypted disk, no personal use)
- [ ] VPN + MFA for all remote access
- [ ] No public Wi-Fi or unencrypted connections
- [ ] Screen privacy filters (prevent shoulder surfing in public)
- [ ] Clean desk policy (lock screens when leaving workspace)

**Evidence Collection**:
- Screenshots stored on encrypted USB drive or encrypted cloud storage (Box, SharePoint with DLP)
- Network packet captures: Encrypted PCAP files, password protected

---

## 6. Evidence Handling and Retention

### 6.1 Evidence Repository Security

**Platform**: SharePoint Online (E5 with DLP) or on-premise file server

**Access Controls**:
```
Evidence Repository: /VAPT_Evidence/

Permissions:
├── CISO: Full Control
├── IT Security Manager: Modify
├── SOC Team: Read-only (for post-test review)
├── Auditors: Read-only (time-limited access during audits)
└── Testers (External): Upload-only during engagement, revoked post-delivery
```

**Technical Controls**:
- Encryption at rest: AES-256
- Encryption in transit: TLS 1.3
- DLP (Data Loss Prevention): Block download of files containing patterns like SSN, credit cards
- Audit logging: All access logged for 7 years (who, what, when)
- Retention: 7 years (ISO requirement), then secure deletion

---

### 6.2 Data Sanitization in Reports

**Before Finalizing Reports**:
1. **Automated Scan**: Run regex to detect PII/PCI patterns
   - SSN: `\d{3}-\d{2}-\d{4}`
   - Credit Card: `\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}`
   - Email: `\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b`

2. **Manual Review**: Security analyst reviews all screenshots for inadvertent data exposure

3. **Redaction**: Replace with `[REDACTED]` or truncate (e.g., `john.****@****.com`)

**Example Report Snippet**:
```
Finding: SQL Injection in /api/users endpoint

Proof of Concept:
GET /api/users?id=1'+OR+'1'='1

Response returned 450 user records, including:
- User ID: 78392
- Username: [REDACTED FOR PRIVACY]
- Email: user****@****.com
- Phone: [REDACTED]

Risk: Unauthorized access to full user database with PII.
```

---

## 7. Regulatory Compliance

### 7.1 GDPR (General Data Protection Regulation)

**Article 32 - Security of Processing**: Appropriate technical and organizational measures required

**VAPT Program as Compliance Measure**: Regular security testing demonstrates "appropriate security" under GDPR

**Data Breach Risk**: Improper handling during VAPT = data breach
- Must notify supervisory authority within 72 hours if tester improperly exfiltrates PII
- Tester = Data Processor (DPA required with external firms)

**DPA (Data Processing Agreement) for External Testers**:
- Clause: "Processor shall not transfer personal data outside EU without adequate safeguards"
- Clause: "Processor shall delete or return all personal data after services concluded"

---

### 7.2 CCPA (California Consumer Privacy Act)

**Business Obligations**: Implement reasonable security (Cal. Civ. Code § 1798.150)

**VAPT as "Reasonable Security"**: Courts recognize security testing as due diligence

**Private Right of Action**: If VAPT activity causes data breach due to negligence, consumers can sue ($100-$750 per consumer per incident)

**Risk Mitigation**: Insurance, strict tester controls, synthetic data usage

---

### 7.3 HIPAA (Health Insurance Portability and Accountability Act)

**Applies To**: Healthcare data (PHI - Protected Health Information)

**HIPAA Security Rule § 164.308**: Conduct security risk analysis (includes pentesting)

**Special Requirements**:
- Business Associate Agreement (BAA) with external testing firms
- PHI may NOT be disclosed without patient consent (even for testing)
- Use de-identified data (remove 18 HIPAA identifiers) for test environments

**HIPAA Safe Harbor**: De-identification removes:
1. Names, 2. Geographic subdivisions smaller than state, 3. Dates (except year), 4. Phone, 5. Fax, 6. Email, 7. SSN, 8. Medical record numbers, 9. Account numbers, 10. Certificate/license numbers, 11. Vehicle IDs, 12. Device IDs, 13. URLs, 14. IP addresses, 15. Biometric IDs, 16. Photos, 17. Other unique identifying numbers

---

## 8. Incident Response: Data Exposure During Testing

### 8.1 Tester Discovers Sensitive Data Leak

**Scenario**: Tester finds publicly accessible AWS S3 bucket with 10,000 customer records (names, emails, phone numbers)

**Immediate Actions (< 4 hours)**:
1. ✅ Tester stops testing that asset immediately
2. ✅ Tester notifies CISO via phone + email (critical finding)
3. ✅ CISO initiates data breach response protocol
4. ✅ DevOps team secures S3 bucket (change permissions to private)
5. ✅ Legal team assesses notification obligations (GDPR 72-hour clock starts)

**Evidence Handling**:
- Tester takes screenshot showing bucket listing (first 10 files) - NO DOWNLOAD of actual customer data
- Screenshot shows column headers and file names only (e.g., `customer-export-2025-01-01.csv`)
- Tester deletes any inadvertently cached data from browser/tools

**Reporting**:
- Finding severity: **CRITICAL**
- Report includes: Timeline of discovery, immediate remediation taken, scope of exposure (10K records, duration exposed: X days)

---

### 8.2 Accidental Data Exfiltration by Tester

**Scenario**: Tester unintentionally downloads production customer database dump during testing

**Immediate Actions**:
1. Tester self-reports to IT Security Manager (same day)
2. CISO determines if data breach has occurred (was data on tester's local drive? Encrypted? Backed up to cloud?)
3. If breach confirmed:
   - Tester's workstation forensically wiped
   - Incident reported per regulatory timelines (GDPR, CCPA, state laws)
   - Tester firm's E&O insurance notified

**Preventive Measure**: RoE includes **automatic termination clause** for unauthorized data exfiltration

---

## 9. Related Documents

- [VAPT Policy](../01-policy-governance/VAPT-Policy.md)
- [Asset Inventory System](./Asset-Inventory-System.md)
- [Rules of Engagement Template](../01-policy-governance/Rules-of-Engagement-Template.md)
- Corporate Data Classification Policy
- Corporate Privacy Policy (GDPR/CCPA)

---

**Document Control Log**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-15 | CISO / DPO | Initial data classification handling procedures |

---

*Confidential - Management*
