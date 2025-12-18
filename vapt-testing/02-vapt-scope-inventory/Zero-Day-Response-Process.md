# Zero-Day Response Process
**Document Control**
- **Version**: 1.0.0
- **Effective Date**: December 15, 2025
- **Document Owner**: IT Security Manager / SOC Lead
- **Classification**: Internal - Technical

---

## 1. Purpose

Defines the rapid response process for newly discovered critical vulnerabilities (zero-days) and emergent threats that require immediate assessment and mitigation outside the regular VAPT schedule.

**Objective**: Minimize window of exposure when critical vulnerabilities are publicly disclosed.

**ISO 27001 Linkage**: Supports Annex A.5.7 (Threat Intelligence) and A.16.1 (Information Security Event Management)

---

## 2. Zero-Day Definition

**Zero-Day Vulnerability**: A previously unknown vulnerability disclosed publicly, often with:
- No vendor patch available at disclosure time
- Proof-of-concept exploit code publicly released
- Active exploitation in the wild (APT groups, mass scanning)

**Recent Examples**:
- **Log4Shell (CVE-2021-44228)**: Apache Log4j RCE - Dec 2021
- **ProxyLogon (CVE-2021-26855)**: Microsoft Exchange Server RCE - Mar 2021
- **MOVEit Transfer (CVE-2023-34362)**: SQL injection RCE - May 2023
- **Citrix Bleed (CVE-2023-4966)**: Session hijacking - Oct 2023

---

## 3. Threat Intelligence Sources

### 3.1 Automated Feeds (Real-Time Alerts)

| Source | Type | Integration | Alert Trigger |
|--------|------|-------------|---------------|
| **CISA KEV (Known Exploited Vulnerabilities)** | Government | RSS, API | Any new KEV entry |
| **NVD (National Vulnerability Database)** | NIST | API, JSON feed | CVSS ≥9.0 (Critical) |
| **CERT/CC Alerts** | CMU | Email, RSS | Critical vulnerability bulletins |
| **Vendor Security Advisories** | Microsoft, Oracle, Cisco, etc. | Email subscriptions | Critical severity patches |
| **GitHub Security Advisories** | Open source | API, notifications | Vulnerabilities in used dependencies  |

**Aggregation Tool**: Security Information Event Management (SIEM) or Threat Intelligence Platform (TIP) to centralize feeds

---

### 3.2 Proactive Monitoring

| Activity | Frequency | Responsibility |
|----------|-----------|----------------|
| **Twitter/X Security Community** (@threatpunter, @GossiTheDog, etc.) | Continuous (automated keywords) | SOC Analyst (follow trending security hashtags) |
| **Security Mailing Lists** (oss-security, full-disclosure) | Daily review | SOC Lead |
| **Reddit r/netsec, r/cybersecurity** | Daily | SOC Analyst |
| **Dark Web Monitoring** (exploit marketplaces) | Weekly | Threat Intelligence Analyst (if available) |

**Alert Keywords**: "0day", "RCE", "wormable", "in-the-wild", "mass exploitation", "CVSS 10.0"

---

## 4. Zero-Day Response Timeline

### Hour 0-6: Detection and Initial Triage

**Trigger**: Zero-day vulnerability announcement detected

**Actions**:
1. **SOC Analyst Notified** (automated alert from TIP)
2. **Preliminary Assessment** (within 2 hours):
   - What is the vulnerability? (CVE ID, description)
   - What software/versions are affected?
   - Is it remotely exploitable? (CVSS Attack Vector: Network?)
   - Is exploit code public? (Check Exploit-DB, GitHub)
   - Is it actively exploited? (Check CISA KEV, threat intel feeds)

3. **Asset Inventory Query** (within 2 hours):
   ```sql
   -- Example query against asset database
   SELECT asset_name, hostname, owner, criticality_tier
   FROM assets
   WHERE software_name = 'Apache Log4j'
     AND software_version IN ('2.0-beta9' THROUGH '2.14.1')
   ORDER BY criticality_tier;
   ```
   **Output**: List of potentially vulnerable assets

4. **Initial Severity Rating**:
   - **P0 (Critical)**: Wormable RCE, active exploitation, affects Tier 1 assets
   - **P1 (High)**: RCE but limited exploitation, affects Tier 2 assets
   - **P2 (Medium)**: Non-RCE or requires user interaction

---

### Hour 6-24: Emergency Assessment and Containment

**P0/P1 Vulnerabilities Only**:

**Step 1: Executive Notification** (within 6 hours)
- Email + SMS to CISO, CIO, IT Security Manager
- Subject: `[CRITICAL] Zero-Day Alert: [CVE-ID] - [Software Name]`
- Body: Asset count affected, exploitation status, immediate actions planned

**Step 2: Emergency Scanning** (within 12 hours)
- Deploy detection scripts to scan for vulnerable versions:
  - **Internal**: Nessus credentialed scan with updated plugins
  - **External**: Shodan/Censys queries for external-facing instances
  - **Cloud**: AWS Systems Manager, Azure Security Center scans
  - **Custom**: Python/PowerShell scripts to check software versions

**Example Detection Script** (Log4j):
```bash
#!/bin/bash
# Find Log4j JAR files and check versions
find /opt /var /usr -name "log4j-core-*.jar" 2>/dev/null | while read jar; do
  version=$(unzip -p "$jar" META-INF/MANIFEST.MF | grep "Implementation-Version" | cut -d' ' -f2)
  echo "Found: $jar - Version: $version"
  # Alert if version between 2.0 and 2.14.1
done
```

**Step 3: Interim Mitigation** (if patch not available)
- **Workarounds**: Apply vendor-recommended mitigations
  - Example (Log4j): Set JVM flag `-Dlog4j2.formatMsgNoLookups=true`
  - WAF rule deployment (virtual patching)
  - Network segmentation (isolate vulnerable systems)
- **Detection Rules**: Deploy SIEM/IDS signatures to detect exploitation attempts
  - Example (Log4j): Snort rule to detect JNDI lookup patterns in HTTP requests

**Step 4: Exploitation Testing** (Optional, within 24 hours)
- **Internal validation**: Confirm vulnerability exploitable in our environment
- **Controlled test**: Non-production replica or isolated lab
- **Output**: Risk confirmation ("Yes, we can be exploited" vs. "Not applicable due to config")

---

### Day 1-7: Patching and Verification

**Step 5: Emergency Patching**

| Asset Tier | Patching SLA | Approval Process |
|------------|--------------|------------------|
| **Tier 1** (Critical) | 24-48 hours | Expedited CAB (emergency change) |
| **Tier 2** | 72 hours | Standard emergency change |
| **Tier 3** | 7 days | Normal change process |

**Patching Workflow**:
1. Vendor patch released (or build custom patch/workaround)
2. Test patch in QA/staging environment (max 4 hours for P0)
3. Backup production system (pre-patch snapshot)
4. Deploy to production (maintenance window or 24/7 if critical)
5. Verify patch applied (re-scan)

**Rollback Plan**: If patch breaks functionality, revert and apply interim mitigation

---

**Step 6: Verification Scanning** (Post-Patch)
- Re-run vulnerability scan on all patched systems
- Confirm CVE no longer detected
- Evidence collection: Clean scan screenshots for compliance records

**Step 7: External Validation** (Optional, for Tier 1 assets)
- Request third-party pentester to verify patch effectiveness (within 1 week)
- Example: "External pentest firm confirmed CVE-2021-44228 no longer exploitable after Log4j upgrade to 2.17.1"

---

### Day 7-30: Post-Incident Review and Improvement

**Step 8: Post-Mortem Analysis**

**Post-Mortem Report** (Template):
```markdown
# Zero-Day Incident: [CVE-ID] - [Software Name]

## Timeline
- [Date/Time]: Vulnerability disclosed
- [Date/Time]: Detection by SOC
- [Date/Time]: Asset inventory query completed (findings: X assets affected)
- [Date/Time]: CISO notified
- [Date/Time]: Interim mitigation deployed
- [Date/Time]: Vendor patch released
- [Date/Time]: Patching completed (% complete)
- [Date/Time]: Verification complete

## Impact Assessment
- Total vulnerable assets: [X]
  - Tier 1: [X]
  - Tier 2: [X]
  - Tier 3: [X]
- Assets successfully patched: [X] (%)
- Assets with interim mitigation: [X]
- Assets risk-accepted (if any): [X] - Justification: [Decommissioning in 14 days]

## Root Cause
- Why were we vulnerable? [e.g., Widespread use of Apache Log4j in Java applications]
- Why didn't we detect sooner? [e.g., No automated dependency tracking for third-party libraries]

## Lessons Learned
- What went well? [e.g., Asset inventory query identified all instances within 2 hours]
- What went poorly? [e.g., Manual patching took 72 hours due to lack of automated deployment]
- What will we change? [e.g., Implement automated Software Bill of Materials (SBOM) tracking]

## Action Items
1. [Action]: Implement dependency scanning in CI/CD (Snyk, Dependabot)
   - Owner: DevOps Lead
   - Due Date: [30 days]
2. [Action]: Create automated patch deployment playbooks (Ansible)
   - Owner: Infrastructure Team
   - Due Date: [60 days]
```

**Step 9: Continuous Improvement**
- Update asset inventory with software version tracking (enable faster future queries)
- Update VAPT testing to include checks for this vulnerability class in future tests
- Enhance monitoring (add SIEM detection rules for this attack pattern)

---

## 5. Pre-Positioned Response Capabilities

### 5.1 Rapid Scanning Infrastructure

**Dedicated "Emergency Scanner"**:
- **Purpose**: Pre-configured Nessus/OpenVAS instance ready to deploy custom plugins immediately
- **Credentials**: Pre-loaded with admin credentials for all critical systems (encrypted vault)
- **Network Access**: Bypass firewall rules via dedicated VLAN (emergency scan VLAN)
- **Automation**: API-driven scan launch (script accepts CVE ID → auto-creates scan → emails results)

---

### 5.2 Virtual Patching (WAF Rules)

**Web Application Firewall** (ModSecurity, Cloudflare WAF):
- **Capability**: Deploy custom rules to block exploitation attempts while patching
- **Example (Log4j)**:
  ```apache
  # ModSecurity rule to block JNDI injection attempts
  SecRule REQUEST_LINE|ARGS|REQUEST_HEADERS "@rx \$\{jndi:" \
    "id:9001,phase:2,deny,status:403,log,msg:'Log4Shell Exploitation Attempt Blocked'"
  ```
- **Deployment**: WAF rule can be deployed in <30 minutes (vs. days for code patch)

**Network-Level Mitigation**:
- IDS/IPS signatures (Snort, Suricata) to detect/block exploit traffic
- Cloud Provider Security Groups (AWS: NACL rule update via CLI in minutes)

---

### 5.3 Communication Templates

**Pre-Written Email Templates** (reduces response time):

#### Template 1: Internal Alert (to Asset Owners)
```
Subject: [URGENT] Security Vulnerability [CVE-ID] - Action Required

Dear [Asset Owner],

A critical security vulnerability (CVE-ID: [X]) has been identified affecting [Software Name].
Your asset [Asset Name] is potentially vulnerable.

SEVERITY: [Critical/High]
EXPLOITATION: [Publicly available exploit / Active attacks observed / Vendor advisory only]

REQUIRED ACTION:
- Review vendor patch: [Link]
- Apply emergency mitigation: [Steps] OR
- Await IT Security team's automated patching (ETA: [X] hours)

DEADLINE: [48 hours for Tier 1 assets]

For questions, contact SOC: [Email/Phone]

- IT Security Team
```

#### Template 2: Executive Briefing (to CISO/CIO)
```
Subject: [CRITICAL ALERT] Zero-Day Vulnerability - [CVE-ID]

SITUATION:
- Vulnerability: [Name] (CVE-[ID])
- Affected: [Software], versions [X-Y]
- Severity: CVSS [Score] ([Attack Vector/Impact])

IMPACT TO [ORGANIZATION]:
- [X] assets identified as vulnerable
  - Tier 1: [X] (Critical business systems)
  - External-facing: [X]
- Exploitation: [Active in wild / PoC public / Vendor notification only]

CURRENT STATUS:
- Vendor patch: [Available / Expected [Date]]
- Interim mitigation: [Deployed/In Progress]
- Estimated patch completion: [Timeline]

RECOMMENDATIONS:
- [Emergency change freeze exception approved for immediate patching]
- [Consider public statement if customer-facing systems affected]

Next update: [6 hours]

- IT Security Manager
```

---

## 6. Decision Matrix: Patch vs. Mitigate

| Scenario | Vendor Patch Available? | Exploitation in Wild? | Our Recommendation |
|----------|-------------------------|----------------------|-------------------|
| **Scenario 1** | ✅ Yes (same day) | ❌ No | Apply patch within normal SLA (72 hours Tier 1) |
| **Scenario 2** | ✅ Yes | ✅ Yes (active) | **Emergency patch within 24 hours** |
| **Scenario 3** | ❌ No (vendor "working on it") | ✅ Yes | **Interim mitigation immediately** (WAF, isolation, disable service if possible) |
| **Scenario 4** | ❌ No | ❌ No (theoretical) | Monitor closely, prepare mitigation plan, wait for patch |
| **Scenario 5** | ✅ Yes, but patch breaks functionality | ✅ Yes | Apply interim mitigation + expedited workaround (custom code fix, WAF rule) |

---

## 7. Roles and Responsibilities

| Role | Hour 0-6 (Detection) | Hour 6-24 (Assessment) | Day 1-7 (Response) | Day 7-30 (Review) |
|------|---------------------|------------------------|-------------------|-------------------|
| **SOC Analyst** | Detect alert, preliminary triage | Asset inventory query, scanning | Monitor for exploitation attempts | Contribute to post-mortem |
| **IT Security Manager** | Assess severity, notify CISO | Coordinate emergency response | Oversee patching, track progress | Lead post-mortem |
| **CISO** | Review initial assessment | Approve emergency changes | Executive updates | Approve action items |
| **DevOps/SysAdmin** | Standby | Validate affected systems | Execute patches, verify | Implement improvements |
| **Comms/PR** (if public-facing assets) | N/A | Draft customer notification (if needed) | Issue statement (if breach) | N/A |

---

## 8. Success Metrics

**Post-Zero-Day KPIs**:
1. **Time to Detection**: How quickly did we learn of the zero-day after public disclosure?
   - Target: <6 hours
2. **Time to Asset Identification**: Query asset inventory to identify vulnerable systems
   - Target: <4 hours
3. **Time to Mitigation**: Interim protection in place
   - Target: <24 hours (P0), <72 hours (P1)
4. **Time to Patch**: Full remediation
   - Target: <7 days (Tier 1)
5. **Coverage**: % of vulnerable assets addressed
   - Target: 100% (Tier 1), >95% (All tiers)

---

## 9. Related Documents

- [VAPT Policy](../01-policy-governance/VAPT-Policy.md)
- [Asset Inventory System](./Asset-Inventory-System.md)
- [Risk Remediation Governance](../01-policy-governance/Risk-Remediation-Governance.md)
- [ISO 27001 Mapping](../03-compliance-integration/ISO-27001-Mapping.md) (A.5.7 Threat Intelligence)

---

**Document Control Log**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-15 | SOC Team | Initial zero-day response process |

---

*Internal - Technical*
