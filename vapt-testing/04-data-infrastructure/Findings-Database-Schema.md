# Findings Database Schema
**Document Control**
- **Version**: 1.0.0
- **Effective Date**: December 15, 2025
- **Document Owner**: IT Security Manager
- **Classification**: Internal - Technical

---

## 1. Purpose

Defines the standardized data model for storing, tracking, and reporting vulnerability findings throughout their entire lifecycle.

**Objectives**:
- Consistent vulnerability data capture
- Full audit trail from discovery to closure
- Integration with ticketing/GRC systems
- Compliance reporting (ISO 9001, ISO 27001)

---

## 2. Core Schema

### Finding Entity

```sql
CREATE TABLE findings (
  -- Primary Key
  finding_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- Asset Relationship
  asset_id UUID NOT NULL REFERENCES assets(asset_id),
  asset_name VARCHAR(255),
  hostname VARCHAR(255),
  ip_address INET,
  
  -- Vulnerability Details
  vulnerability_title VARCHAR(500) NOT NULL,
  cve_id VARCHAR(50),  -- e.g., CVE-2024-1234 (NULL if no CVE assigned)
  cwe_id VARCHAR(50),  -- e.g., CWE-89 (SQL Injection)
  
  -- Severity and Risk
  cvss_base_score DECIMAL(3,1) CHECK (cvss_base_score >= 0 AND cvss_base_score <= 10),
  cvss_vector VARCHAR(100),  -- e.g., CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H
  severity VARCHAR(20) CHECK (severity IN ('Critical', 'High', 'Medium', 'Low', 'Informational')),
  original_severity VARCHAR(20),  -- Before business context adjustment
  
  -- Description
  description TEXT NOT NULL,
  technical_details TEXT,
  proof_of_concept TEXT,  -- Steps to reproduce
  affected_component VARCHAR(255),  -- e.g., "Apache Tomcat 9.0.45", "/api/users endpoint"
  
  -- Remediation
  remediation_recommendation TEXT NOT NULL,
  remediation_effort VARCHAR(20),  -- 'Low', 'Medium', 'High', 'Very High'
  remediation_action TEXT,  -- What was actually done
  
  -- Lifecycle Status
  status VARCHAR(30) CHECK (status IN ('New', 'In Progress', 'Pending Verification', 
                                        'Remediated', 'Risk Accepted', 'False Positive', 
                                        'Duplicate', 'Deferred')) DEFAULT 'New',
  
  -- Dates
  discovered_date TIMESTAMP NOT NULL DEFAULT NOW(),
  assigned_date TIMESTAMP,
  due_date TIMESTAMP,  -- Auto-calculated from severity SLA
  remediated_date TIMESTAMP,
  verified_date TIMESTAMP,
  closed_date TIMESTAMP,
  
  -- Ownership
  discovered_by VARCHAR(100),  -- Tester name or 'Nessus', 'Qualys', etc.
  assigned_to VARCHAR(100),  -- Individual or team
  asset_owner VARCHAR(100),
  
  -- Evidence
  screenshot_paths TEXT[],  -- Array of file paths
  test_report_id UUID REFERENCES test_reports(report_id),
  ticket_id VARCHAR(50),  -- Jira/ServiceNow ticket (e.g., VULN-1234)
  
  -- Verification
  re_test_required BOOLEAN DEFAULT TRUE,
  re_test_date TIMESTAMP,
  re_tester VARCHAR(100),
  verification_evidence TEXT,  -- e.g., "Clean Nessus scan on 2025-03-15"
  
  -- Metadata
  test_type VARCHAR(50),  -- 'Automated Scan', 'Manual Pentest', 'Code Review', 'DAST', 'SAST'
  finding_source VARCHAR(100),  -- 'Nessus', 'External Pentest (Acme Corp)', 'Burp Suite'
  compliance_scope VARCHAR(100)[],  -- e.g., ['PCI-DSS', 'ISO 27001', 'SOC 2']
  
  -- Audit Trail
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  created_by VARCHAR(100),
  updated_by VARCHAR(100)
);

-- Indexes for performance
CREATE INDEX idx_findings_asset_id ON findings(asset_id);
CREATE INDEX idx_findings_status ON findings(status);
CREATE INDEX idx_findings_severity ON findings(severity);
CREATE INDEX idx_findings_due_date ON findings(due_date);
CREATE INDEX idx_findings_cve_id ON findings(cve_id);
```

---

## 3. Supporting Tables

### Test Reports Table

```sql
CREATE TABLE test_reports (
  report_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  report_name VARCHAR(255) NOT NULL,
  test_type VARCHAR(50),  -- 'Vulnerability Scan', 'Penetration Test', 'Cloud Security Assessment'
  test_date DATE NOT NULL,
  tester_name VARCHAR(100),
  tester_company VARCHAR(100),  -- 'Internal SOC' or external firm name
  scope TEXT,  -- Free text or JSON with IPs/URLs
  roe_signed BOOLEAN DEFAULT FALSE,
  report_file_path VARCHAR(500),
  executive_summary TEXT,
  total_findings_count INT,
  critical_count INT,
  high_count INT,
  medium_count INT,
  low_count INT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### Remediation History Table (Audit Trail)

```sql
CREATE TABLE remediation_history (
  history_id SERIAL PRIMARY KEY,
  finding_id UUID NOT NULL REFERENCES findings(finding_id),
  status_change VARCHAR(100),  -- e.g., 'New → In Progress', 'In Progress → Remediated'
  changed_by VARCHAR(100),
  change_date TIMESTAMP DEFAULT NOW(),
  notes TEXT,
  attachment_path VARCHAR(500)
);
```

---

## 4. Field Definitions and Business Rules

### CVSS Scoring

**cvss_base_score**: CVSS v3.1 numeric score (0.0 - 10.0)
- **CVSS Calculator**: https://www.first.org/cvss/calculator/3.1

**cvss_vector**: Full CVSS vector string
- Example: `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N`
- Parsing: Extract Attack Vector, Attack Complexity, Privileges Required, etc.

---

### Severity Adjustment Logic

```python
# Pseudo-code for severity determination
def calculate_final_severity(cvss_score, asset_tier, data_classification, exploit_public):
    # Map CVSS to base severity
    if cvss_score >= 9.0:
        base_severity = 'Critical'
    elif cvss_score >= 7.0:
        base_severity = 'High'
    elif cvss_score >= 4.0:
        base_severity = 'Medium'
    elif cvss_score >= 0.1:
        base_severity = 'Low'
    else:
        base_severity = 'Informational'
    
    # Adjust for business context
    adjusted_severity = base_severity
    
    if asset_tier == 'Tier 1' and data_classification == 'Restricted':
        if base_severity == 'Medium':
            adjusted_severity = 'High'
        elif base_severity == 'High':
            adjusted_severity = 'Critical'
    
    if exploit_public and base_severity in ['High', 'Critical']:
        adjusted_severity = 'Critical'  # Ensure escalation for active exploitation
    
    return adjusted_severity
```

---

### Due Date Calculation (SLA)

```sql
-- Trigger function to auto-calculate due_date
CREATE OR REPLACE FUNCTION set_due_date()
RETURNS TRIGGER AS $$
BEGIN
  CASE NEW.severity
    WHEN 'Critical' THEN NEW.due_date := NEW.discovered_date + INTERVAL '7 days';
    WHEN 'High' THEN NEW.due_date := NEW.discovered_date + INTERVAL '30 days';
    WHEN 'Medium' THEN NEW.due_date := NEW.discovered_date + INTERVAL '90 days';
    WHEN 'Low' THEN NEW.due_date := NEW.discovered_date + INTERVAL '180 days';
    ELSE NEW.due_date := NULL;  -- Informational = no SLA
  END CASE;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER findings_due_date BEFORE INSERT OR UPDATE
  ON findings FOR EACH ROW EXECUTE FUNCTION set_due_date();
```

---

### Status Workflow

```
New
 ↓
In Progress (assigned to team, work started)
 ↓
Pending Verification (fix deployed, awaiting re-test)
 ↓
Remediated (re-test passed, confirmed fixed) → Closed
 
OR

New → False Positive (validated as scanner error) → Closed
New → Duplicate (same as Finding #XXXX) → Closed
New → Risk Accepted (CISO approval) → Closed
New → Deferred (scheduled for next maintenance window)
```

---

## 5. Reporting Views

### Executive Dashboard View

```sql
CREATE VIEW executive_vuln_summary AS
SELECT
  COUNT(*) FILTER (WHERE severity = 'Critical' AND status IN ('New', 'In Progress')) AS critical_open,
  COUNT(*) FILTER (WHERE severity = 'High' AND status IN ('New', 'In Progress')) AS high_open,
  COUNT(*) FILTER (WHERE severity = 'Medium' AND status IN ('New', 'In Progress')) AS medium_open,
  COUNT(*) FILTER (WHERE status = 'Remediated' AND remediated_date >= NOW() - INTERVAL '30 days') AS remediated_last_30_days,
  COUNT(*) FILTER (WHERE due_date < NOW() AND status NOT IN ('Remediated', 'Risk Accepted', 'Closed')) AS overdue_count,
  ROUND(AVG(EXTRACT(DAY FROM (remediated_date - discovered_date))), 1) AS avg_days_to_remediate
FROM findings
WHERE discovered_date >= NOW() - INTERVAL '90 days';
```

**Output Example**:
| critical_open | high_open | medium_open | remediated_last_30_days | overdue_count | avg_days_to_remediate |
|---------------|-----------|-------------|-------------------------|---------------|-----------------------|
| 2 | 15 | 47 | 32 | 3 | 18.5 |

---

### SLA Compliance Report

```sql
CREATE VIEW sla_compliance AS
SELECT
  severity,
  COUNT(*) AS total_findings,
  COUNT(*) FILTER (WHERE remediated_date <= due_date) AS within_sla,
  COUNT(*) FILTER (WHERE remediated_date > due_date) AS sla_breach,
  ROUND(100.0 * COUNT(*) FILTER (WHERE remediated_date <= due_date) / COUNT(*), 1) AS compliance_percentage
FROM findings
WHERE status = 'Remediated'
  AND discovered_date >= NOW() - INTERVAL '1 year'
GROUP BY severity
ORDER BY
  CASE severity
    WHEN 'Critical' THEN 1
    WHEN 'High' THEN 2
    WHEN 'Medium' THEN 3
    WHEN 'Low' THEN 4
  END;
```

---

### Asset Vulnerability Density

```sql
CREATE VIEW asset_vuln_density AS
SELECT
  a.asset_name,
  a.criticality_tier,
  COUNT(f.finding_id) AS open_vulnerabilities,
  COUNT(f.finding_id) FILTER (WHERE f.severity IN ('Critical', 'High')) AS critical_high_count
FROM assets a
LEFT JOIN findings f ON a.asset_id = f.asset_id AND f.status IN ('New', 'In Progress')
GROUP BY a.asset_id, a.asset_name, a.criticality_tier
ORDER BY critical_high_count DESC, open_vulnerabilities DESC
LIMIT 20;
```

**Use Case**: "Top 20 Most Vulnerable Assets"

---

## 6. Integration Points

### Jira/ServiceNow Ticketing

**API Integration** (Bi-directional sync):
```json
{
  "action": "create_ticket",
  "data": {
    "summary": "[Critical] SQL Injection in /api/users",
    "description": "Vulnerability ID: finding_123\nCVSS: 9.8\nAsset: Customer Portal\nSee full details: https://vapt-portal/findings/finding_123",
    "priority": "P0",
    "assignee": "devops-team",
    "due_date": "2025-12-22",
    "labels": ["security", "VAPT", "SQL-injection"]
  }
}
```

**Sync Logic**:
- Finding created in DB → Auto-create Jira ticket (for Critical/High)
- Ticket status "Done" → Update finding status to "Pending Verification"
- Finding verified → Close ticket

---

### SIEM Integration (Forward Findings)

**Use Case**: Alert SOC when vulnerability found in production

**Example (Splunk HEC - HTTP Event Collector)**:
```json
POST /services/collector/event
{
  "event": {
    "finding_id": "finding_456",
    "severity": "High",
    "asset": "web-production-01",
    "vulnerability": "Outdated OpenSSL 1.1.1k (CVE-2021-3711)",
    "action_required": "Upgrade to OpenSSL 1.1.1l+",
    "due_date": "2025-01-14"
  },
  "sourcetype": "vapt:finding"
}
```

---

## 7. Data Retention

**Policy**: 7 years (ISO compliance requirement)

**Implementation**:
```sql
-- Archive old closed findings (but don't delete for audit trail)
CREATE TABLE findings_archive (
  LIKE findings INCLUDING ALL
);

-- Annual archive job (retain only closed findings older than 1 year in main table)
INSERT INTO findings_archive
SELECT * FROM findings
WHERE status IN ('Remediated', 'Risk Accepted', 'False Positive', 'Duplicate')
  AND closed_date < NOW() - INTERVAL '1 year';
```

**Backup**: Daily encrypted backups of findings database

---

## 8. Access Control

### Database Roles

```sql
-- Read-Only (Auditors, Management)
CREATE ROLE vapt_readonly;
GRANT SELECT ON findings, test_reports TO vapt_readonly;

-- Analyst (SOC Team - can update findings)
CREATE ROLE vapt_analyst;
GRANT SELECT, INSERT, UPDATE ON findings TO vapt_analyst;
GRANT SELECT ON test_reports TO vapt_analyst;

-- Admin (IT Security Manager - full control)
CREATE ROLE vapt_admin;
GRANT ALL PRIVILEGES ON findings, test_reports, remediation_history TO vapt_admin;
```

---

## 9. Compliance Evidence

**For ISO 27001 A.8.8**: This database demonstrates:
- ✅ "Information about technical vulnerabilities obtained" (all findings logged)
- ✅ "Exposure evaluated" (CVSS scoring, asset linkage)
- ✅ "Appropriate measures taken" (remediation tracking, status workflow)
- ✅ Logging (full audit trail with remediation_history table)

**For ISO 9001 Clause 10.2** (Nonconformity):
- ✅ Vulnerabilities = Nonconformities (tracked from discovery to corrective action to verification)

---

## 10. Related Documents

- [VAPT Policy](../01-policy-governance/VAPT-Policy.md)
- [Risk Remediation Governance](../01-policy-governance/Risk-Remediation-Governance.md)
- [ISO 27001 Mapping](../03-compliance-integration/ISO-27001-Mapping.md)
- [Reporting Templates](./Reporting-Templates/) (uses this schema for report generation)

---

**Document Control Log**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-15 | IT Security Team | Initial findings database schema |

---

*Internal - Technical*
