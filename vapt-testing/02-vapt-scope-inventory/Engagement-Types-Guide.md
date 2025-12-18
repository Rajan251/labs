# Engagement Types Guide
**Document Control**
- **Version**: 1.0.0
- **Effective Date**: December 15, 2025
- **Document Owner**: IT Security Manager
- **Classification**: Internal - Technical

---

## 1. Overview

This guide defines the three primary penetration testing approaches and provides guidance on which approach to use for different asset classes.

**Testing Perspectives**: Black-box, Gray-box, and White-box testing represent different levels of knowledge provided to testers, simulating various threat actor scenarios.

---

## 2. Black-Box Testing

### Definition
Tester has **no prior knowledge** of the target system. Simulates an external attacker with zero inside information.

### Tester's Perspective
- No credentials provided
- No architecture diagrams or documentation
- Must discover everything through reconnaissance
- Mimics real-world external threat

### Use Cases
| Asset Type | Rationale | Example |
|------------|-----------|---------|
| **External Web Applications** | Test defenses from internet attack | Public e-commerce site |
| **Public APIs** (unauthenticated endpoints) | Assess exposure to external attackers | Open data APIs |
| **Network Perimeter** | External firewall and edge device testing | Internet-facing infrastructure |
| **M&A Due Diligence** | Independent assessment with no insider knowledge | Acquisition target evaluation |

### Advantages
✅ Most realistic external threat simulation  
✅ Unbiased assessment (no preconceptions)  
✅ Tests security visibility and detection capabilities  

### Limitations
❌ Time-consuming (more reconnaissance required)  
❌ May miss vulnerabilities requiring insider knowledge  
❌ Higher chance of false negatives (things missed)  

### Deliverables
- Attack surface map (what was discovered)
- Exploitation paths and findings
- Recommendations for reducing external exposure

---

## 3. Gray-Box Testing

### Definition
Tester has **partial knowledge** - typically user-level credentials and basic documentation. Simulates an insider threat or compromised user account.

### Tester's Perspective
- Standard user credentials provided
- Basic network diagrams may be shared
- Application URLs and endpoints known
- Limited system access (non-privileged)

### Use Cases
| Asset Type | Rationale | Example |
|------------|-----------|---------|
| **Internal Web Applications** | Simulate authenticated user attacking from inside | Employee portal, CRM, intranet |
| **APIs with Authentication** | Test with valid API keys/OAuth tokens | RESTful APIs, microservices |
| **Internal Network** | Simulate insider threat or laptop compromise | Corporate LAN testing |
| **Cloud Infrastructure** | Test with read-only IAM role | AWS security assessment with limited credentials |
| **Mobile Applications** | Test with valid user account | iOS/Android app with authenticated features |

### Advantages
✅ Balances realism with efficiency  
✅ Identifies privilege escalation paths  
✅ Realistic insider threat scenario  
✅ More comprehensive than black-box in same timeframe  

### Limitations
⚠️ May not catch all external attack vectors  
⚠️ Tester knowledge can introduce bias  

### Deliverables
- Privilege escalation findings
- Lateral movement opportunities
- User access control weaknesses
- Business logic flaws (exploiting authenticated features)

---

## 4. White-Box Testing

### Definition
Tester has **full knowledge** - source code, admin credentials, architecture diagrams, and complete documentation. Most thorough assessment.

### Tester's Perspective
- Administrator-level credentials
- Complete architecture documentation
- Source code access (for applications)
- Database schemas and configurations
- Network diagrams and asset inventory

### Use Cases
| Asset Type | Rationale | Example |
|------------|-----------|---------|
| **Critical Applications (Pre-Production)** | Maximum thoroughness before launch | Payment processing system |
| **Code Review + Pentest Hybrid** | Find both code and deployment issues | Custom-developed enterprise application |
| **Compliance Testing** | Meet PCI-DSS 11.3 requirements (full scope testing) | Cardholder data environment |
| **Complex Infrastructure** | Shortest path to finding all vulnerabilities | Multi-tier cloud architecture |
| **Annual Third-Party Audit** | Demonstrate due diligence with comprehensive test | ISO 27001 certification support |

### Advantages
✅ Most comprehensive coverage  
✅ Identifies complex logic flaws  
✅ Faster execution (less discovery time)  
✅ Best return on investment (findings per hour)  
✅ Can test design weaknesses, not just implementation  

### Limitations
❌ Less realistic (attackers rarely have this access)  
❌ May miss detection/response capabilities  
❌ Can be more expensive (requires senior testers to leverage full access)  

### Additional Techniques in White-Box
- **SAST (Static Application Security Testing)**: Automated source code analysis
- **Architecture Review**: Design flaw identification
- **Configuration Audit**: Against CIS Benchmarks and hardening guides
- **Threat Modeling**: STRIDE, MITRE ATT&CK mapping

### Deliverables
- Comprehensive vulnerability report (code + infrastructure + config)
- Secure architecture recommendations
- Code-level fixes (specific line numbers and secure code examples)
- Threat model diagram

---

## 5. Asset-to-Type Mapping Matrix

### Recommended Approach by Asset Class

|Asset Class | Tier 1 (Critical) | Tier 2 (Important) | Tier 3 (Low Impact) |
|------------|-------------------|-------------------|---------------------|
| **External Web Apps** | Annual Black-box + Bi-annual White-box | Annual Black-box | Annual Black-box (automated + spot check) |
| **Internal Web Apps** | Bi-annual Gray-box | Annual Gray-box | On-demand Gray-box |
| **Public APIs** | Bi-annual Gray-box (with tokens) + Annual White-box | Annual Gray-box | Annual Gray-box |
| **Mobile Apps** | Per release White-box + Annual Black-box | Per major release Gray-box | Annual Gray-box |
| **Network (External)** | Annual Black-box | Annual Black-box | Bi-annual Black-box |
| **Network (Internal)** | Bi-annual Gray-box + Annual White-box | Annual Gray-box | Annual White-box (config audit) |
| **Cloud Infrastructure** | Bi-annual White-box (full config review) | Annual White-box | Annual White-box |
| **Databases** | Bi-annual White-box | Annual White-box | On-demand White-box |

**Combination Approach** (Best Practice for Tier 1):
- **Black-box** first (find external exposures)
- **Gray-box** second (test authenticated attack surfaces)
- **White-box** annually (comprehensive deep dive)

---

## 6. Selecting the Right Approach

### Decision Tree

```
START: What asset are you testing?
│
├─ Is it externally accessible (internet-facing)?
│  ├─ YES → Start with BLACK-BOX
│  │        Then consider GRAY-BOX if authentication exists
│  │
│  └─ NO (internal only) → Use GRAY-BOX or WHITE-BOX
│
├─ Do you have source code or need to test before launch?
│  └─ YES → Use WHITE-BOX (code review + pentest)
│
├─ Is this for compliance (PCI-DSS, ISO audit)?
│  └─ YES → Use WHITE-BOX (most evidence of thoroughness)
│
├─ Budget constrained, need maximum findings per dollar?
│  └─ YES → Use WHITE-BOX (most efficient use of tester time)
│
└─ Want to test security monitoring and detection capabilities?
   └─ YES → Use BLACK-BOX (tests detection of unknown threats)
```

---

## 7. Hybrid Approaches

### 7.1 Code-Assisted Penetration Testing

**Combination**: White-box source code review + Dynamic testing

**Workflow**:
1. **Phase 1**: SAST tools scan codebase (SonarQube, Checkmarx)
2. **Phase 2**: Manual code review of high-risk areas (authentication, crypto, data handling)
3. **Phase 3**: Dynamic penetration test informed by code insights
4. **Phase 4**: Exploitation validation (prove code flaws are exploitable)

**Benefit**: Finds both theoretical (code-level) and practical (runtime) vulnerabilities

**Best For**: Custom-developed applications, especially those handling sensitive data

---

### 7.2 Assumed Breach Testing

**Combination**: Gray-box with adversarial mindset

**Scenario**: "Assume an attacker has already compromised a user account—how far can they get?"

**Starting Point**: Provide user credentials to tester

**Objectives**:
- Privilege escalation to admin
- Lateral movement to other systems
- Access to sensitive data/databases
- Persistence mechanisms

**Best For**: Testing internal segmentation and "defense in depth"

---

### 7.3 Purple Team Exercise

**Combination**: White-box + Real-time collaboration

**Participants**:
- **Red Team** (Attackers): Pentesters with full knowledge
- **Blue Team** (Defenders): SOC, incident responders
- **Purple Team** (Facilitators): Security architects coordinating both

**Process**:
1. Red Team attacks using white-box knowledge
2. Blue Team detects and responds
3. Real-time debrief: "Did you see this attack? How can we improve detection?"

**Benefit**: Improves both vulnerabilities AND detection/response capabilities

**Best For**: Mature security programs focused on detection engineering

---

## 8. Scope Considerations by Type

### Black-Box Scope Definition

**Required in RoE**:
- Target domains/IP ranges (very explicit boundaries)
- **Out-of-scope third parties** (CDN, SaaS providers you don't own)
- Prohibited techniques (usually DoS, social engineering)

**Example Black-Box Scope**:
```
IN-SCOPE:
- *.example.com (all subdomains)
- 203.0.113.0/24 (DMZ network)

OUT-OF-SCOPE:
- partner.example.com (hosted by third party)
- Cloudflare IPs (CDN infrastructure)
- Social engineering of employees
```

---

### Gray-Box Scope Definition

**Required in RoE**:
- All black-box requirements PLUS:
- Credentials provided (username, password, API keys)
  - **Specify privilege level** (standard user, power user, read-only admin)
- Documentation provided (architecture diagrams, user guides)
- Permitted actions (e.g., "You may test privilege escalation but must not modify production data")

**Example Gray-Box Scope**:
```
IN-SCOPE:
- Internal web app: https://internal-crm.corp.example.com
- Credentials: username=testuser1, password=[provided separately]
- User Role: Sales Representative (limited access to customer records)

TEST OBJECTIVES:
- Privilege escalation to Admin role
- Horizontal escalation (access other sales reps' data)
- SQL injection, XSS, business logic bypasses

CONSTRAINTS:
- Read-only operations preferred
- If data modification necessary, use test customer records only (ID 1000-1050)
```

---

### White-Box Scope Definition

**Required in RoE**:
- All gray-box requirements PLUS:
- Source code repository access (Git URL, branch)
- Admin credentials for all in-scope systems
- Complete architecture diagrams
- Database connection strings (for test/QA environments)
- Cloud console access (read-only IAM roles for production, full access for staging)

**Example White-Box Scope**:
```
IN-SCOPE:
- Application: Customer Portal v3.2
- Source Code: https://github.com/company/customer-portal (main branch)
- Admin Access: Provided via 1Password share
- Environments:
  - Production: https://portal.example.com (read-only to minimize impact)
  - Staging: https://portal-staging.example.com (full admin, test data)
- Cloud: AWS Account 123456789012 (us-east-1, us-west-2)
  - IAM Role: arn:aws:iam::123456789012:role/SecurityAudit (read-only)
  
DELIVERABLES:
- Architecture review report
- Source code security findings (SAST + manual)
- Infrastructure vulnerabilities (DAST + config audit)
- Threat model (STRIDE analysis)
```

---

## 9. Reporting Differences by Type

### Black-Box Report Focus
- External attack surface enumeration
- Publicly exposed vulnerabilities
- OSINT findings (leaked credentials, exposed documents)
- Detection capability assessment ("Were our alerts triggered?")

### Gray-Box Report Focus
- Privilege escalation paths
- Lateral movement opportunities
- Access control weaknesses
- Business logic flaws exploitable by authenticated users

### White-Box Report Focus
- Architectural security flaws
- Code-level vulnerabilities (with line numbers)
- Configuration weaknesses (vs. CIS Benchmarks)
- Secure design recommendations
- Threat model diagram

---

## 10. Cost and Time Comparison

### Typical Engagement Duration (Medium-complexity Web Application)

| Type | Duration | Consultant Days | Estimated Cost |
|------|----------|----------------|----------------|
| **Black-Box** | 2-3 weeks | 10-15 days | $15,000 - $30,000 |
| **Gray-Box** | 1-2 weeks | 7-10 days | $10,000 - $20,000 |
| **White-Box** | 1-2 weeks | 10-15 days (but more thorough) | $15,000 - $35,000 |

**Note**: White-box takes similar time but yields 2-3x more findings due to efficiency gains from provided documentation.

**ROI Perspective**: White-box often best value (cost per finding)

---

## 11. Related Documents

- [Testing Schedule Matrix](./Testing-Schedule-Matrix.md)
- [Asset Inventory System](./Asset-Inventory-System.md)
- [Rules of Engagement Template](../01-policy-governance/Rules-of-Engagement-Template.md)

---

**Document Control Log**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-15 | IT Security Team | Initial engagement types guide |

---

*Internal - Technical*
