# VAPT Methodology Framework
**Document Control**
- **Version**: 1.0.0
- **Effective Date**: December 15, 2025
- **Document Owner**: IT Security Manager
- **Review Cycle**: Annual
- **Classification**: Internal - Technical

---

## 1. Overview

This document defines the technical methodologies, standards, and quality assurance processes for all Vulnerability Assessment and Penetration Testing (VAPT) activities conducted by or on behalf of the organization.

**Purpose**: Ensure consistent, comprehensive, and repeatable security testing that produces actionable results.

---

## 2. Adopted Methodologies and Standards

The organization employs industry-recognized testing frameworks to ensure comprehensive coverage:

### 2.1 OWASP Testing Guide v4.2

**Application**: Web applications, APIs, and web services

**Key Testing Areas**:
1. **Information Gathering**: Fingerprinting web servers, identifying application entry points
2. **Configuration Management**: Default credentials, unnecessary services, security headers
3. **Identity Management**: Registration process weaknesses, account enumeration
4. **Authentication**: Brute force protection, password policy, session management
5. **Authorization**: Path traversal, privilege escalation, insecure direct object references
6. **Session Management**: Cookie security, session fixation, timeout enforcement
7. **Input Validation**: SQL injection, XSS, XXE, command injection, LDAP injection
8. **Error Handling**: Information leakage through error messages
9. **Cryptography**: Weak algorithms, improper certificate validation, insecure random number generation
10. **Business Logic**: Workflow bypass, race conditions, transaction integrity
11. **Client-Side**: DOM-based XSS, JavaScript security, client-side resource manipulation

**Compliance Mapping**: ISO 27001 A.8.8 (Technical Vulnerabilities), A.14.2.8 (System Security Testing)

---

### 2.2 NIST SP 800-115: Technical Security Testing and Assessment

**Application**: Comprehensive infrastructure and application testing

**Testing Techniques**:
1. **Review Techniques**:
   - Documentation review (architecture diagrams, security policies)
   - Log review (SIEM, access logs, audit trails)
   - Ruleset review (firewall rules, IDS signatures, WAF policies)
   - System configuration review (CIS Benchmarks compliance)
   - Network sniffing (passive traffic analysis)
   - File integrity checking

2. **Target Identification and Analysis**:
   - Network discovery (Nmap, masscan)
   - Network port and service identification
   - Vulnerability scanning (Nessus, Qualys, OpenVAS)
   - Wireless network scanning (Aircrack-ng, Kismet)
   - Application security scanner (Burp Suite, OWASP ZAP)

3. **Target Vulnerability Validation**:
   - Password cracking (weak password identification)
   - Penetration testing (controlled exploitation)
   - Social engineering (with explicit approval only)
   - Physical security testing (badge access, tailgating - only if in scope)

**Phase Approach**: Plan → Discover → Attack → Report

---

### 2.3 Penetration Testing Execution Standard (PTES)

**Application**: Structured penetration testing engagements

**Seven-Phase Methodology**:

#### Phase 1: Pre-Engagement Interactions
- Scope definition and Rules of Engagement (RoE)
- Business objectives identification
- Legal agreements (contracts, NDAs, authorization letters)
- Timeline and resource allocation

#### Phase 2: Intelligence Gathering
- **Passive Reconnaissance**: OSINT (Google dorking, social media, job postings, DNS records, WHOIS)
- **Active Reconnaissance**: Port scanning, service enumeration, subdomain discovery
- **Intelligence Analysis**: Attack surface mapping, technology stack identification

#### Phase 3: Threat Modeling
- Business asset analysis (what data/systems are most valuable?)
- Attack vectors identification (how could an attacker exploit these assets?)
- Threat capability analysis (skill level required for each attack)
- Motivations and triggers (why would someone target this?)

#### Phase 4: Vulnerability Analysis
- Automated vulnerability scanning with manual validation
- Configuration weakness identification
- Patch level assessment
- Custom application testing (logic flaws, authentication bypasses)

#### Phase 5: Exploitation
- Proof-of-concept exploitation (demonstrate impact with minimal damage)
- Privilege escalation attempts (local and domain-level)
- Lateral movement simulation (pivoting to other systems)
- Data access validation (can sensitive data be accessed?)
- Persistence mechanisms (could an attacker maintain access?)

**Exploitation Guidelines**:
- Always get explicit approval before exploiting production systems
- Use safer exploit variants when available (no DoS-causing exploits)
- Document every action taken (for audit trail and replication)
- Stop immediately if unintended impact occurs and notify stakeholders

#### Phase 6: Post-Exploitation
- Assess value of compromised asset
- Pillaging (searching for sensitive data - simulated only)
- Business impact analysis (what would a real attacker do with this access?)
- Cleanup and evidence removal (restore systems to original state)

#### Phase 7: Reporting
- Executive summary (business risk in non-technical terms)
- Technical details (methodology, tools, findings, evidence)
- Remediation roadmap (prioritized action plan)
- Re-test plan (verification approach for fixes)

---

### 2.4 OSSTMM (Open Source Security Testing Methodology Manual)

**Application**: Network, infrastructure, and operational security testing

**Key Sections**:
1. **Information Security**: Data integrity, authentication mechanisms
2. **Process Security**: Policies, procedures, security awareness
3. **Internet Technology Security**: Network protocols, routing, firewall efficacy
4. **Communications Security**: PBX, VoIP, unified communications
5. **Wireless Security**: Wi-Fi, Bluetooth, RFID vulnerabilities
6. **Physical Security**: Facility access controls, badge systems

**Operational Security Metrics**:
- **RAV (Risk Assessment Values)**: Quantified risk scoring
- **Security Posture**: Actual vs. perceived security level

---

## 3. Testing Phases (Universal Workflow)

All VAPT engagements follow this structured workflow:

### Phase 1: Pre-Engagement (Planning)
**Activities**:
- Kick-off meeting with stakeholders
- Scope confirmation and asset enumeration
- RoE finalization and sign-off
- Tool selection and test environment setup
- Communication plan establishment

**Deliverables**:
- Signed Rules of Engagement document
- Test plan with timeline
- Contact escalation matrix

**Quality Gate**: Signed authorization from CISO and asset owner

---

### Phase 2: Reconnaissance (Intelligence Gathering)
**Activities**:
- **Passive**: OSINT, public database searches, DNS enumeration, SSL certificate analysis
- **Active**: Network discovery, port scanning, service fingerprinting, technology identification

**Tools**:
- Passive: Shodan, Censys, SecurityTrails, Google Dorks, theHarvester
- Active: Nmap, Masscan, Amass, Sublist3r

**Deliverables**: Attack surface map, technology inventory

---

### Phase 3: Scanning (Automated Vulnerability Identification)
**Activities**:
- Authenticated vulnerability scans (with credentials)
- Unauthenticated external scans (black-box perspective)
- Web application scanning (DAST - Dynamic Application Security Testing)
- Configuration compliance checks (CIS Benchmarks)

**Tools**:
- Network: Nessus, Qualys, OpenVAS, Rapid7 Nexpose
- Web: Burp Suite Pro, OWASP ZAP, Nikto, Acunetix
- Container/Cloud: Trivy, Prowler, ScoutSuite, Checkov

**Deliverables**: Prioritized vulnerability list (CVSS-scored)

---

### Phase 4: Enumeration (Deep Analysis)
**Activities**:
- Service-specific enumeration (SMB shares, LDAP, SNMP, databases)
- User enumeration (valid accounts, email addresses)
- Software version identification (exact patch levels)
- SSL/TLS configuration analysis (supported ciphers, certificate validity)

**Tools**: Enum4linux, SNMPwalk, LDAP search, Nmap NSE scripts, SSLScan, testssl.sh

**Deliverables**: Detailed system and service profiles

---

### Phase 5: Exploitation (Controlled Attack Simulation)
**Activities**:
- Proof-of-concept (PoC) exploitation of confirmed vulnerabilities
- Privilege escalation attempts (local admin to domain admin)
- Lateral movement (pivoting through network segments)
- Sensitive data access validation

**Control Measures**:
- Always maintain change log of actions taken
- Use non-destructive exploits whenever possible
- Take system snapshots before exploitation (if feasible)
- Immediate rollback if unintended impact occurs

**Tools**: Metasploit Framework, SQLMap, Exploit-DB scripts, custom exploits

**Deliverables**: Exploitation evidence (screenshots, command outputs, data samples - sanitized)

---

### Phase 6: Reporting (Documentation and Communication)
**Activities**:
- Finding validation and false positive elimination
- Business impact assessment for each finding
- Risk scoring (CVSS + business context)
- Remediation guidance development
- Report drafting and peer review

**Deliverables**:
- Executive Summary Report (for C-suite)
- Technical Report (for IT teams)
- Auditor Evidence Package (for compliance)

**Timeline**: Draft report within 5 business days of testing completion

---

### Phase 7: Remediation Support and Re-Testing
**Activities**:
- Consultation on remediation approaches
- Verification testing of fixes
- Residual risk assessment
- Final closure or risk acceptance documentation

**Timeline**: Re-test within 30 days of remediation completion

---

## 4. Testing Types and Approaches

### 4.1 Black-Box Testing

**Definition**: Tester has no prior knowledge of the target system. Simulates external attacker perspective.

**Use Cases**:
- External perimeter penetration tests
- Public-facing web applications
- Pre-acquisition due diligence

**Advantages**: Realistic attack simulation, unbiased assessment
**Limitations**: May miss vulnerabilities requiring deep system knowledge, time-consuming

---

### 4.2 Gray-Box Testing

**Definition**: Tester has partial knowledge (e.g., user-level credentials, network diagrams).

**Use Cases**:
- Internal network testing (simulate insider threat)
- API security testing (with valid API keys)
- Cloud configuration review (with read-only AWS/Azure access)

**Advantages**: Balances realism with efficiency, finds privilege escalation paths
**Limitations**: May not catch zero-knowledge attack vectors

---

### 4.3 White-Box Testing

**Definition**: Tester has full knowledge (architecture diagrams, source code, admin credentials).

**Use Cases**:
- Critical application security review
- Pre-production deployment testing
- Code-assisted penetration testing
- Compliance-driven testing (PCI-DSS requirement 11.3)

**Advantages**: Most thorough, identifies complex logic flaws, faster execution
**Limitations**: Less realistic (attackers rarely have this access)

**Additional Techniques**:
- **SAST (Static Application Security Testing)**: Source code analysis (SonarQube, Checkmarx, Fortify)
- **DAST (Dynamic Application Security Testing)**: Runtime testing (Burp, ZAP)
- **IAST (Interactive Application Security Testing)**: Hybrid approach with instrumentation

---

## 5. Approved Tools List

### 5.1 Vulnerability Scanners
- **Tenable Nessus Professional** (Primary - Licensed)
- **Qualys VMDR** (Secondary - Cloud-based)
- **OpenVAS** (Backup - Open source)

### 5.2 Network Discovery and Enumeration
- Nmap (with NSE scripts)
- Masscan (high-speed network scanning)
- Wireshark (packet analysis)

### 5.3 Web Application Testing
- **Burp Suite Professional** (Primary - Licensed)
- **OWASP ZAP** (Secondary - Open source)
- Nikto (web server scanner)
- SQLMap (SQL injection exploitation)

### 5.4 Exploitation Frameworks
- Metasploit Framework (controlled exploitation)
- Exploit-DB (public exploit repository)
- Custom scripts (Python, PowerShell, Bash - peer-reviewed)

### 5.5 Cloud Security
- Prowler (AWS security assessment)
- ScoutSuite (multi-cloud auditing - AWS, Azure, GCP)
- CloudMapper (AWS infrastructure visualization)

### 5.6 Password Auditing
- Hashcat (GPU-accelerated password cracking)
- John the Ripper (traditional password cracker)
- CrackMapExec (Active Directory assessment)

### 5.7 Mobile Application Testing
- MobSF (Mobile Security Framework - SAST/DAST for iOS/Android)
- Frida (dynamic instrumentation toolkit)
- Objection (runtime mobile exploration)

**Tool Approval Process**: New tools require IT Security Manager approval and license compliance verification.

---

## 6. Quality Assurance Process

### 6.1 False Positive Elimination

**Requirement**: All automated findings must be **manually validated** before reporting.

**Validation Steps**:
1. Reproduce the finding independently
2. Assess actual exploitability (theoretical vs. practical)
3. Confirm business impact assessment
4. Document validation results

**Target**: <5% false positive rate in final reports

---

### 6.2 Peer Review Process

**For Critical and High Findings**:
- Minimum **two-person review**
- Second reviewer must independently verify exploitability
- Conflicting assessments escalated to IT Security Manager

**For All Reports**:
- Technical review by senior tester
- Editorial review for clarity and grammar
- Legal review for compliance language (annual pentests)

---

### 6.3 Tester Qualifications

**Internal Testers**:
- Minimum 2 years security experience
- Completion of VAPT training program
- Annual skills assessment

**External Testers** (for annual third-party tests):
- Certified by recognized body: **OSCP, CEH, GPEN, GWAPT, or equivalent**
- Firm must have E&O insurance (minimum $2M coverage)
- Demonstrated experience in similar industry/technology stack

---

### 6.4 Test Documentation Standards

Every test must maintain:
- **Activity Log**: Timestamped record of all actions taken
- **Evidence Archive**: Screenshots, command outputs, network captures
- **Tool Configurations**: Scan settings, custom wordlists, exploit parameters
- **Findings Database Entry**: Structured data per schema (see Data Management section)

**Retention**: All test documentation retained for **7 years** for audit purposes.

---

## 7. Continuous Improvement

### 7.1 Lessons Learned Process

After each major test engagement:
- Post-test debrief with testing team
- Identification of methodology gaps or tool limitations
- Documentation of novel attack techniques discovered
- Update to testing playbooks and checklists

**Example**:
> "2024-Q3 Pentest revealed testers missed GraphQL introspection vulnerability. **Action**: Added GraphQL testing section to Web App Testing Checklist. **Result**: Q4 test found 3 additional GraphQL APIs with exposed schemas."

### 7.2 Threat Intelligence Integration

- Subscribe to vulnerability disclosure mailing lists (CVE, NVD, vendor lists)
- Incorporate MITRE ATT&CK framework techniques into testing scenarios
- Update testing methodologies based on emerging attack trends (e.g., supply chain attacks, container escapes)

---

## 8. Compliance and Audit Trail

**ISO 9001:2015 Mapping**:
- **Clause 8.5.1 (Controlled Processes)**: This methodology document + RoE templates = controlled testing procedures
- **Clause 7.1.6 (Organizational Knowledge)**: Lessons learned feed into organizational security knowledge base

**ISO/IEC 27001:2022 Mapping**:
- **A.8.8 (Technical Vulnerabilities)**: Methodology ensures systematic vulnerability identification
- **A.14.2.8 (System Security Testing)**: Defines how testing is conducted during development lifecycle

---

## 9. Related Documents

- [VAPT Policy](./VAPT-Policy.md) (Parent policy)
- [Rules of Engagement Template](./Rules-of-Engagement-Template.md)
- [Testing Schedule Matrix](../02-vapt-scope-inventory/Testing-Schedule-Matrix.md)
- [Findings Database Schema](../04-data-infrastructure/Findings-Database-Schema.md)

---

**Document Control Log**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-15 | IT Security Team | Initial methodology framework |

---

*This document is marked as **Internal - Technical**. Distribution limited to security team and authorized testers.*
