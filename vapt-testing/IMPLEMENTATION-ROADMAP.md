# VAPT Implementation Roadmap - DevOps & Security Engineer

**Role**: DevOps & Security Implementation Lead  
**Objective**: Deploy production-ready VAPT program from scratch  
**Timeline**: 90 days (3 months) to baseline, 6 months to full maturity  
**Status Tracking**: ☐ Not Started | 🔄 In Progress | ✅ Complete | ⏭️ Deferred

---

## Phase 1: Foundation (Days 1-30)

### Checkpoint 1.1: Environment Setup (Days 1-5)

**Goal**: Prepare infrastructure and access

- [ ] **Infrastructure Provisioning**
  - [ ] Provision VM for Nessus Scanner (8 vCPU, 16GB RAM, 500GB SSD)
    - Platform: VMware/AWS EC2/Azure VM
    - OS: Ubuntu 22.04 LTS
    - Network: Management VLAN with access to all scan targets
  - [ ] Provision VM for PostgreSQL Database (4 vCPU, 16GB RAM, 1TB SSD)
    - Same platform as scanner
    - Network: Management VLAN (isolated, no direct internet)
  - [ ] Provision VM for Grafana/Tools (4 vCPU, 8GB RAM, 250GB SSD)

**Validation**:
```bash
# SSH to each VM
ssh ubuntu@<scanner-ip>
ssh ubuntu@<database-ip>
ssh ubuntu@<grafana-ip>

# Verify resources
free -h  # Check RAM
df -h    # Check disk
nproc    # Check CPU cores
```

**Time Estimate**: 1-2 days (depends on approval process)

---

- [ ] **Network Configuration**
  - [ ] Create Management VLAN (VLAN 10: 10.0.10.0/24)
  - [ ] Configure firewall rules:
    ```
    Allow: Scanner → Production (TCP 22,445,3389,443 for credentialed scans)
    Allow: Database ← Scanner, Grafana only
    Deny: Database → Internet (security)
    Allow: Grafana → Internet (dashboard access)
    ```
  - [ ] Test connectivity from scanner to sample target
    ```bash
    # From scanner VM
    ping <production-target>
    nmap -p 22,80,443 <production-target>
    ```

**Validation**: Successful ping and port scan from scanner to production

**Time Estimate**: 1 day

---

- [ ] **Access & Credentials**
  - [ ] Create service accounts for scanning:
    - Linux scanner account: `vapt_scanner` with sudo (passwordless for specific commands)
    - Windows scanner account: Domain account with local admin rights
    - Cloud accounts: AWS IAM role `VAPTSecurityAudit`, Azure Service Principal
  - [ ] Store credentials in vault (HashiCorp Vault, AWS Secrets Manager, or encrypted KeePass)
  - [ ] Document credential locations in runbook

**Validation**:
```bash
# Test Linux credentials
ssh vapt_scanner@<target-linux> "sudo systemctl status ssh"

# Test Windows (from scanner with smbclient)
smbclient -L <target-windows> -U DOMAIN\\vapt_scanner
```

**Time Estimate**: 1-2 days

---

### Checkpoint 1.2: Core Tools Deployment (Days 6-15)

- [ ] **Deploy Nessus Professional**
  ```bash
  # On scanner VM
  wget https://www.tenable.com/downloads/api/v2/pages/nessus/files/Nessus-10.x.x-ubuntu1404_amd64.deb
  sudo dpkg -i Nessus-*.deb
  sudo systemctl start nessusd
  sudo systemctl enable nessusd
  
  # Access https://<scanner-ip>:8834
  # Activate with license key
  # Wait for plugin compilation (~30 min)
  ```
  - [ ] Create admin account
  - [ ] Create scan policies:
    - [ ] "Weekly Internal Scan - Production"
    - [ ] "Weekly Internal Scan - Development"
    - [ ] "External Scan - DMZ"
  - [ ] Configure SMTP for email alerts (Critical/High findings)

**Validation**:
```bash
# Run test scan on single host
# Target: Test server
# Verify scan completes and generates report
```

**Time Estimate**: 1 day (excluding plugin compilation wait time)

---

- [ ] **Deploy PostgreSQL Findings Database**
  ```bash
  # On database VM
  sudo apt update && sudo apt install -y postgresql-15 postgresql-contrib
  sudo systemctl start postgresql
  sudo systemctl enable postgresql
  
  # Create database
  sudo -u postgres psql
  CREATE DATABASE vapt;
  CREATE USER vapt_user WITH PASSWORD 'CHANGE_ME_SECURE_PASSWORD';
  GRANT ALL PRIVILEGES ON DATABASE vapt TO vapt_user;
  \q
  
  # Copy schema from Findings-Database-Schema.md
  # Import schema
  psql -U vapt_user -d vapt -f findings_schema.sql
  ```
  - [ ] Configure PostgreSQL for remote connections (from Grafana VM only)
    - Edit `/etc/postgresql/15/main/postgresql.conf`: `listen_addresses = '<database-ip>'`
    - Edit `/etc/postgresql/15/main/pg_hba.conf`: Add `host vapt vapt_user <grafana-ip>/32 md5`
    - Restart: `sudo systemctl restart postgresql`
  - [ ] Test connection from Grafana VM:
    ```bash
    psql -h <database-ip> -U vapt_user -d vapt -c "SELECT version();"
    ```

**Validation**: Successful remote connection from Grafana VM

**Time Estimate**: 1 day

---

- [ ] **Deploy Grafana**
  ```bash
  # On Grafana VM (Docker method - fastest)
  sudo apt install -y docker.io docker-compose
  
  docker run -d \
    -p 3000:3000 \
    --name=grafana \
    --restart=always \
    -v grafana-storage:/var/lib/grafana \
    -e "GF_SECURITY_ADMIN_PASSWORD=CHANGE_ME" \
    grafana/grafana-oss
  
  # Access http://<grafana-ip>:3000
  # Login: admin / CHANGE_ME
  ```
  - [ ] Add PostgreSQL data source
    - Configuration → Data Sources → PostgreSQL
    - Host: `<database-ip>:5432`
    - Database: `vapt`
    - User: `vapt_user`
    - SSL Mode: `require`
  - [ ] Test connection (should show "Data source is working")

**Validation**: Green "Data source is working" message

**Time Estimate**: 0.5 day

---

- [ ] **Install Command-Line Tools on Scanner VM**
  ```bash
  # Essential tools
  sudo apt update
  sudo apt install -y \
    nmap \
    nikto \
    git \
    python3-pip \
    jq \
    curl \
    smbclient \
    ldap-utils
  
  # Install Prowler (AWS scanning)
  pip3 install prowler-cloud
  
  # Install Trivy (container scanning)
  wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
  echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
  sudo apt update && sudo apt install -y trivy
  
  # Install ScoutSuite (multi-cloud)
  pip3 install scoutsuite
  ```

**Validation**:
```bash
nmap --version
prowler -v
trivy --version
scout --version
```

**Time Estimate**: 0.5 day

---

### Checkpoint 1.3: Asset Inventory (Days 16-25)

- [ ] **Build Initial Asset Inventory**
  - [ ] Method 1: Export from existing CMDB/ITSM
    ```bash
    # If Jira/ServiceNow exists, export asset list
    # Format: CSV with columns: hostname, ip, owner, environment, tier
    ```
  - [ ] Method 2: Network discovery (if no CMDB)
    ```bash
    # Production network
    nmap -sn 10.0.20.0/24 -oG - | grep "Up" > assets_production.txt
    
    # Development network
    nmap -sn 10.0.30.0/24 -oG - | grep "Up" > assets_development.txt
    ```
  - [ ] Method 3: Cloud assets
    ```bash
    # AWS
    aws ec2 describe-instances --query 'Reservations[*].Instances[*].[InstanceId,PrivateIpAddress,Tags[?Key==`Name`].Value|[0],State.Name]' --output table > aws_instances.txt
    
    # Azure
    az vm list --query '[].{name:name, resourceGroup:resourceGroup, location:location}' -o table > azure_vms.txt
    ```

**Deliverable**: Combined asset list (Excel/CSV) with minimum columns:
- Asset ID (generate UUID or use existing)
- Asset Name
- IP Address
- Owner (email)
- Criticality Tier (1/2/3)
- Environment (Production/Staging/Dev)

**Validation**: Minimum 50 assets cataloged (adjust based on org size)

**Time Estimate**: 3-5 days (depends on existing data quality)

---

- [ ] **Import Assets to Database**
  ```sql
  -- Create assets table (from Asset-Inventory-System.md schema)
  -- Import CSV
  psql -U vapt_user -d vapt
  
  \copy assets(asset_name, hostname, ip_address, owner_email, criticality_tier, environment) FROM 'assets.csv' CSV HEADER;
  
  -- Verify import
  SELECT criticality_tier, COUNT(*) 
  FROM assets 
  GROUP BY criticality_tier;
  ```

**Validation**: 
```sql
SELECT COUNT(*) FROM assets;  -- Should match CSV row count
```

**Time Estimate**: 1 day

---

- [ ] **Classify Assets (Criticality Tiering)**
  - [ ] Identify Tier 1 (Critical) assets:
    - Production databases with customer data
    - External-facing web applications
    - Payment processing systems
    - Active Directory domain controllers
  - [ ] Update database:
    ```sql
    UPDATE assets 
    SET criticality_tier = 1 
    WHERE asset_name IN ('prod-db-01', 'customer-portal', 'payment-gateway');
    ```
  - [ ] Tag remaining as Tier 2 (Important) or Tier 3 (Low-Impact)

**Validation**: All assets have criticality tier assigned (no NULL values)

**Time Estimate**: 2 days (requires business input)

---

### Checkpoint 1.4: First Baseline Scan (Days 26-30)

- [ ] **Configure First Nessus Scan**
  - [ ] Scope: Tier 1 assets only (10-20 assets for first scan)
  - [ ] Policy: "Basic Network Scan" with credentials
  - [ ] Schedule: Manual (on-demand for baseline)
  - [ ] Add credentials to scan:
    - SSH: vapt_scanner account
    - Windows: Domain scanner account

**Time Estimate**: 0.5 day

---

- [ ] **Execute Baseline Scan**
  ```bash
  # Launch scan from Nessus UI
  # Monitor progress
  # Typical scan time: 2-4 hours for 20 hosts
  ```
  - [ ] Wait for completion
  - [ ] Export results:
    - PDF (for review)
    - CSV (for database import)

**Validation**: Scan completes successfully with 0% failed hosts

**Time Estimate**: 1 day (mostly waiting)

---

- [ ] **Analyze Baseline Results**
  - [ ] Review Critical/High vulnerabilities
  - [ ] Identify false positives (manual validation):
    ```bash
    # SSH to host, verify vulnerability
    # Example: Check OpenSSH version if flagged
    ssh target-host
    sshd -V
    ```
  - [ ] Document baseline metrics:
    - Total vulnerabilities: ___
    - Critical: ___
    - High: ___
    - Medium: ___
    - Low: ___
    - Vulnerability density: ___ per host

**Deliverable**: Baseline metrics spreadsheet

**Time Estimate**: 2 days

---

- [ ] **Import Findings to Database** (Manual or Script)
  ```python
  # Use nessus_export.py script from TOOLS-GUIDE.md
  # Or manual CSV import
  ```

**Validation**:
```sql
SELECT COUNT(*) FROM findings WHERE discovered_date = CURRENT_DATE;
-- Should match Nessus findings count
```

**Time Estimate**: 1 day

---

## Phase 2: Operationalization (Days 31-60)

### Checkpoint 2.1: Automated Scanning (Days 31-40)

- [ ] **Configure Weekly Automated Scans**
  - [ ] Nessus: Scans → New Scan → Scheduled
    - Name: "Weekly Production Scan"
    - Targets: All Tier 1 + Tier 2 assets
    - Schedule: Every Sunday, 02:00 AM
    - Email notifications: Enable for Critical/High findings
  - [ ] Create separate scans:
    - [ ] Weekly Development Scan (Tier 3)
    - [ ] External Scan (DMZ/Internet-facing)

**Validation**: Scans run automatically on schedule (verify next Monday)

**Time Estimate**: 1 day

---

- [ ] **Automate Findings Import** (Cron Job)
  ```bash
  # On scanner VM
  # Create script: /opt/vapt/nessus_auto_import.sh
  
  #!/bin/bash
  # Export latest scan results and import to database
  # (Use Nessus API - see TOOLS-GUIDE.md)
  
  python3 /opt/vapt/nessus_export.py --scan-id latest --export-db
  
  # Add to crontab
  crontab -e
  # Run every Monday at 08:00 (after Sunday scan completes)
  0 8 * * 1 /opt/vapt/nessus_auto_import.sh >> /var/log/vapt/import.log 2>&1
  ```

**Validation**: Check database Monday morning for new findings

**Time Estimate**: 2 days

---

- [ ] **Cloud Scanning Automation**
  ```bash
  # AWS Prowler scan (weekly)
  # Create script: /opt/vapt/prowler_scan.sh
  
  #!/bin/bash
  prowler aws --output-formats json html \
    --output-directory /var/vapt/reports/prowler/$(date +%Y%m%d)
  
  # Crontab: Every Saturday 22:00
  0 22 * * 6 /opt/vapt/prowler_scan.sh
  ```

**Time Estimate**: 1 day

---

- [ ] **Set Up Alerting**
  - [ ] Configure Nessus email alerts (already done)
  - [ ] Create Grafana alerts:
    - Alert: Critical vulnerability count > 5
    - Notification: Email to security@company.com
  - [ ] Create Slack/Teams webhook (optional):
    ```bash
    # Post to Slack when Critical found
    curl -X POST -H 'Content-type: application/json' \
      --data '{"text":"🚨 CRITICAL vulnerability found: <link>"}' \
      https://hooks.slack.com/services/YOUR/WEBHOOK
    ```

**Validation**: Trigger test alert, verify receipt

**Time Estimate**: 1 day

---

### Checkpoint 2.2: Remediation Workflow (Days 41-50)

- [ ] **Integrate with Jira/ServiceNow**
  - [ ] Create Jira project: "SEC" (Security Vulnerabilities)
  - [ ] Custom issue type: "Security Vulnerability"
  - [ ] Required fields:
    - Severity (Critical/High/Medium/Low)
    - CVSS Score
    - Affected Asset
    - Remediation Due Date
  - [ ] API integration script:
    ```python
    # create_jira_ticket.py
    # For each Critical/High finding in database, create Jira ticket
    # (See TOOLS-GUIDE.md for API payload)
    ```

**Validation**: Create 1-2 test tickets manually, verify workflow

**Time Estimate**: 3 days

---

- [ ] **Automate Ticket Creation**
  ```bash
  # Cron job: Run after findings import
  # /opt/vapt/create_remediation_tickets.sh
  
  python3 /opt/vapt/create_jira_ticket.py --severity CRITICAL HIGH
  ```

**Validation**: Ticket auto-created for new Critical finding

**Time Estimate**: 2 days

---

- [ ] **Document SLA Reminders**
  - [ ] Jira automation rule:
    - Trigger: Issue created (Security Vulnerability)
    - Condition: Severity = Critical
    - Action: Set due date = Created Date + 7 days
  - [ ] Jira automation rule (SLA breach warning):
    - Trigger: Scheduled (daily)
    - Condition: Due date within 2 days AND status ≠ Done
    - Action: Send email to assignee + CISO

**Validation**: Create test ticket, verify due date set correctly

**Time Estimate**: 1 day

---

### Checkpoint 2.3: Dashboards & Reporting (Days 51-60)

- [ ] **Create Grafana Dashboards**
  
  **Dashboard 1: Executive Overview**
  - [ ] Panel: Open Vulnerabilities by Severity (Gauge chart)
  - [ ] Panel: Vulnerability Trend (Line chart, last 90 days)
  - [ ] Panel: Mean Time to Remediate (Bar chart by severity)
  - [ ] Panel: SLA Compliance (Percentage)
  - [ ] Panel: Top 10 Most Vulnerable Assets (Table)

  ```sql
  -- Example query for "Open Vulnerabilities by Severity"
  SELECT 
    severity,
    COUNT(*) AS count
  FROM findings
  WHERE status IN ('New', 'In Progress')
  GROUP BY severity;
  ```

**Time Estimate**: 3 days

---

**Dashboard 2: Operational Dashboard**
  - [ ] Panel: Overdue Remediation (Table with countdown)
  - [ ] Panel: Findings by Status (Pie chart)
  - [ ] Panel: Asset Coverage (% scanned in last 30 days)
  - [ ] Panel: Recent Critical Findings (Table, last 7 days)

**Time Estimate**: 2 days

---

- [ ] **Automated Weekly Report**
  ```bash
  # Script to generate PDF report from Grafana dashboard
  # Install grafana-reporter or use Grafana Enterprise (paid)
  
  # Alternative: Python script to query database and generate PDF
  # /opt/vapt/weekly_report.py
  
  # Crontab: Every Monday 09:00
  0 9 * * 1 /opt/vapt/weekly_report.py | mail -s "Weekly VAPT Report" security@company.com
  ```

**Time Estimate**: 2 days

---

## Phase 3: Advanced Capabilities (Days 61-90)

### Checkpoint 3.1: CI/CD Integration (Days 61-70)

- [ ] **SAST in CI/CD Pipeline**
  
  **Option 1: Semgrep (Lightweight)**
  ```yaml
  # .github/workflows/semgrep.yml
  name: Semgrep
  on: [pull_request]
  jobs:
    semgrep:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v3
        - uses: returntocorp/semgrep-action@v1
          with:
            config: p/security-audit
  ```
  
  **Option 2: SonarQube (Enterprise)**
  - [ ] Deploy SonarQube server (Docker)
  - [ ] Integrate with Jenkins/GitLab
  - [ ] Configure quality gates (block merge if Critical vulnerabilities)

**Validation**: Create PR with intentional SQL injection, verify block

**Time Estimate**: 3 days

---

- [ ] **Container Scanning**
  ```yaml
  # .gitlab-ci.yml
  container_scan:
    stage: security
    image: aquasec/trivy:latest
    script:
      - trivy image --severity CRITICAL,HIGH $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
    allow_failure: false  # Block pipeline if Critical found
  ```

**Validation**: Push image with known vulnerability, verify pipeline fails

**Time Estimate**: 2 days

---

- [ ] **Dependency Scanning**
  - [ ] GitHub: Enable Dependabot
    - Settings → Security → Dependabot alerts (Enable)
    - Dependabot security updates (Enable)
  - [ ] GitLab: Enable Dependency Scanning
    - `.gitlab-ci.yml`: Include template
    ```yaml
    include:
      - template: Security/Dependency-Scanning.gitlab-ci.yml
    ```

**Validation**: Dependabot creates PR for vulnerable dependency upgrade

**Time Estimate**: 1 day

---

### Checkpoint 3.2: Manual Penetration Testing (Days 71-85)

- [ ] **Contract External Pentest Firm**
  - [ ] RFP process (Request for Proposal)
  - [ ] Vendor selection criteria:
    - [ ] Certifications (OSCP, GPEN, CREST)
    - [ ] Insurance (Cyber liability coverage)
    - [ ] SOC 2 Type II certification
  - [ ] Contract negotiation
  - [ ] NDA and Rules of Engagement signing

**Time Estimate**: 5 days (procurement process)

---

- [ ] **Prepare for Pentest**
  - [ ] Finalize scope (Tier 1 external-facing assets)
  - [ ] Create whitelist for tester IPs (firewall exception)
  - [ ] Notify SOC team (suppress alerts from tester IPs during engagement)
  - [ ] Provide credentials (read-only for gray-box testing)

**Time Estimate**: 2 days

---

- [ ] **Execute Pentest** (External firm performs)
  - Testing duration: 5-10 business days
  - Your role: Daily check-ins, answer questions

**Time Estimate**: 10 days (external dependency)

---

- [ ] **Remediate Pentest Findings**
  - [ ] Import findings to database
  - [ ] Create Jira tickets for Critical/High
  - [ ] Assign to DevOps/Dev teams
  - [ ] Track remediation via dashboard

**Time Estimate**: Ongoing (Days 86-120+)

---

### Checkpoint 3.3: Compliance Prep (Days 86-90)

- [ ] **Internal Audit Dry-Run**
  - [ ] Use Audit Evidence Checklist (from framework)
  - [ ] Gather evidence:
    - [ ] Scan reports (last 3 months)
    - [ ] Remediation tickets (sample 10 closed tickets)
    - [ ] Management review presentation (create if not done)
  - [ ] Conduct self-assessment
  - [ ] Identify gaps

**Time Estimate**: 3 days

---

- [ ] **Update Documentation**
  - [ ] Customize VAPT Policy with company name/contacts
  - [ ] Add actual scan schedule to Testing Schedule Matrix
  - [ ] Document infrastructure in Architecture doc

**Time Estimate**: 2 days

---

## Quick Reference Checklist

### Daily Tasks (After Day 30)
- [ ] Check Grafana dashboard for new Critical findings
- [ ] Review overnight scan results (Monday mornings)
- [ ] Triage false positives

### Weekly Tasks
- [ ] Review SLA compliance (any breaches?)
- [ ] Update management on metrics (if reporting weekly)
- [ ] Check for new CVEs affecting our tech stack

### Monthly Tasks
- [ ] Review asset inventory (add new systems, remove decommissioned)
- [ ] Analyze vulnerability trends
- [ ] Update Nessus plugins (automated, verify)
- [ ] Test disaster recovery (backup restore test)

### Quarterly Tasks
- [ ] Conduct manual pentest (external or internal team)
- [ ] Present metrics to management
- [ ] Review and update policies
- [ ] Conduct internal audit

---

## Success Metrics (Track These!)

| Metric | Day 30 Target | Day 60 Target | Day 90 Target |
|--------|---------------|---------------|---------------|
| **Asset Coverage** | 50% Tier 1 scanned | 100% Tier 1, 50% Tier 2 | 100% Tier 1&2, 80% Tier 3 |
| **Scan Frequency** | Monthly manual | Weekly automated | Weekly + on-demand |
| **MTTR (Critical)** | 30 days | 14 days | 7 days (SLA compliant) |
| **Dashboard Availability** | N/A | Basic dashboard live | Full dashboards + alerts |
| **False Positive Rate** | Unknown | <25% | <10% |
| **Automation Level** | 20% (manual scans) | 60% (auto scan + import) | 80% (auto tickets + reports) |

---

## Troubleshooting Common Issues

### Issue 1: Nessus Scan Fails (0% completion)

**Symptoms**: Scan starts but shows 0% progress, eventually times out

**Causes**:
- Firewall blocking scanner
- Incorrect credentials
- Target host offline

**Resolution**:
```bash
# From scanner VM, test connectivity
ping <target>
nmap -p 22 <target>  # Test SSH port

# Test credentials manually
ssh vapt_scanner@<target>

# Check Nessus logs
tail -f /opt/nessus/var/nessus/logs/nessusd.messages
```

---

### Issue 2: Database Connection Fails from Grafana

**Symptoms**: "Data source is not working" error

**Resolution**:
```bash
# On database VM, check PostgreSQL is listening
sudo netstat -tulpn | grep 5432

# Check pg_hba.conf has correct IP
sudo cat /etc/postgresql/15/main/pg_hba.conf | grep <grafana-ip>

# Test from Grafana VM
psql -h <database-ip> -U vapt_user -d vapt -c "SELECT 1;"

# Check firewall (on database VM)
sudo ufw status
sudo ufw allow from <grafana-ip> to any port 5432
```

---

### Issue 3: Too Many False Positives

**Resolution**:
```bash
# In Nessus, disable noisy plugins:
# Settings → Advanced → Plugins
# Disable plugin families:
#   - "General" (informational only)
#   - "Service detection" (if not needed)

# Or create custom policy with reduced paranoia level
# Policy → New Policy → Advanced Scan
# Settings → Paranoia Level → Normal (not Paranoid)
```

---

## Next Steps After Day 90

1. **Expand Coverage**: Add remaining Tier 3 assets
2. **Optimize**: Reduce false positives to <5%
3. **Advanced Testing**: Implement purple team exercises
4. **Certification**: Prepare for ISO 27001 audit (use checklist)
5. **Continuous Improvement**: Review logs, implement improvements

---

## Resources & Support

**Internal**:
- VAPT Policy: `/path/to/vapt-testing/01-policy-governance/VAPT-Policy.md`
- Tools Guide: `/path/to/vapt-testing/TOOLS-GUIDE.md`
- Database Schema: `/path/to/vapt-testing/04-data-infrastructure/Findings-Database-Schema.md`

**External**:
- Nessus Documentation: https://docs.tenable.com/nessus/
- PostgreSQL Docs: https://www.postgresql.org/docs/
- Grafana Tutorials: https://grafana.com/tutorials/

**Community**:
- OWASP Slack: https://owasp.org/slack/invite
- Nessus Community Forum: https://community.tenable.com/

---

**Last Updated**: 2025-12-15  
**Document Owner**: DevOps & Security Team  
**Status**: Ready for Implementation ✅

---

## Track Your Progress

Create a copy of this document and check off items as you complete them. Update the status indicators:

- ☐ → 🔄 (when you start)
- 🔄 → ✅ (when complete)
- Mark dates next to completed items for your records

**Good luck with your VAPT implementation!** 🚀
