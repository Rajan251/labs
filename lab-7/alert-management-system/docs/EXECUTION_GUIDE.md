# Step-by-Step Execution Guide

## 📋 Complete Deployment Workflow

This guide provides **exact commands** and **detailed explanations** for deploying the Alert Management System from scratch.

---

## 🎯 Prerequisites Checklist

Before starting, ensure you have:

- [ ] Linux/macOS/Windows with WSL2
- [ ] Docker installed (version 20.10+)
- [ ] Docker Compose installed (version 1.29+)
- [ ] 4GB+ RAM available
- [ ] 20GB+ disk space available
- [ ] Internet connection
- [ ] PagerDuty account (free trial: https://www.pagerduty.com)

---

## 📝 Phase 1: Initial Setup

### Step 1.1: Navigate to Project Directory

```bash
cd /home/rk/Documents/labs/lab-7/alert-management-system
```

**What this does**: Changes to the project directory where all configuration files are located.

---

### Step 1.2: Verify File Structure

```bash
tree -L 2
```

**Expected output**:
```
.
├── README.md
├── alertmanager/
│   ├── alertmanager.yml
│   └── templates/
├── docker/
│   ├── docker-compose.yml
│   └── .env.example
├── prometheus/
│   ├── prometheus.yml
│   ├── rules/
│   └── targets/
├── scripts/
│   ├── setup.sh
│   ├── test-alerts.sh
│   ├── health-check.sh
│   └── backup.sh
└── docs/
```

---

### Step 1.3: Make Scripts Executable

```bash
chmod +x scripts/*.sh
```

**What this does**: Adds execute permissions to all shell scripts.

**Verification**:
```bash
ls -l scripts/
```

You should see `-rwxr-xr-x` permissions.

---

### Step 1.4: Run Setup Script

```bash
./scripts/setup.sh
```

**What this does**:
- Validates Docker installation
- Creates necessary directories
- Validates configuration files
- Creates `.env` file from template

**Expected output**:
```
============================================
Alert Management System - Setup
============================================

[1/6] Checking prerequisites...
✓ Docker installed: 24.0.7
✓ Docker Compose installed: 2.23.0
✓ Docker daemon is running

[2/6] Creating directories...
✓ Directories created

[3/6] Setting up environment file...
✓ Created .env file from template
⚠ IMPORTANT: Edit docker/.env and add your PagerDuty integration key!

...

Setup completed successfully!
```

---

## 📝 Phase 2: PagerDuty Configuration

### Step 2.1: Create PagerDuty Account

1. Go to https://www.pagerduty.com
2. Click "Start Free Trial"
3. Fill in your details and verify email

---

### Step 2.2: Create PagerDuty Service

1. **Log in to PagerDuty**

2. **Create Escalation Policy**:
   - Navigate: **People** → **Escalation Policies**
   - Click **+ New Escalation Policy**
   - Name: `Production Alerts`
   - Add yourself to Level 1
   - Click **Save**

3. **Create Service**:
   - Navigate: **Services** → **Service Directory**
   - Click **+ New Service**
   - Name: `Production Monitoring`
   - Escalation Policy: `Production Alerts`
   - Integration Type: **Prometheus**
   - Click **Create Service**

4. **Copy Integration Key**:
   - After creation, click on the service
   - Find the **Integration** section
   - Copy the **Integration Key** (32-character string)
   - Example: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`

---

### Step 2.3: Configure Environment Variables

```bash
cd docker
nano .env
```

**Edit the file**:
```bash
# Find this line:
PAGERDUTY_INTEGRATION_KEY=your_pagerduty_integration_key_here

# Replace with your actual key:
PAGERDUTY_INTEGRATION_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

**Save and exit**: `Ctrl+X`, then `Y`, then `Enter`

**Verification**:
```bash
cat .env | grep PAGERDUTY_INTEGRATION_KEY
```

Should show your actual key (not the placeholder).

---

## 📝 Phase 3: Start the System

### Step 3.1: Start All Services

```bash
cd /home/rk/Documents/labs/lab-7/alert-management-system/docker
docker-compose up -d
```

**What this does**:
- Downloads Docker images (first time only)
- Creates Docker network
- Starts all containers in background

**Expected output**:
```
Creating network "monitoring" with driver "bridge"
Creating volume "prometheus_data" with default driver
Creating volume "alertmanager_data" with default driver
Creating alertmanager ... done
Creating prometheus ... done
Creating node-exporter ... done
Creating blackbox-exporter ... done
```

**Time**: 2-5 minutes (first time), 10-30 seconds (subsequent starts)

---

### Step 3.2: Verify Services are Running

```bash
docker-compose ps
```

**Expected output**:
```
NAME                 STATUS              PORTS
alertmanager         Up 30 seconds       0.0.0.0:9093->9093/tcp
prometheus           Up 30 seconds       0.0.0.0:9090->9090/tcp
node-exporter        Up 30 seconds       0.0.0.0:9100->9100/tcp
blackbox-exporter    Up 30 seconds       0.0.0.0:9115->9115/tcp
```

All services should show `Up` status.

---

### Step 3.3: Check Service Health

```bash
cd ..
./scripts/health-check.sh
```

**Expected output**:
```
============================================
Alert Management System - Health Check
============================================

[1/3] Checking Docker containers...

Checking container prometheus... ✓ Running
Checking container alertmanager... ✓ Running
Checking container node-exporter... ✓ Running
Checking container blackbox-exporter... ✓ Running

[2/3] Checking service endpoints...

Checking Prometheus... ✓ OK (HTTP 200)
Checking Alertmanager... ✓ OK (HTTP 200)
Checking Node Exporter... ✓ OK (HTTP 200)
Checking Blackbox Exporter... ✓ OK (HTTP 200)

[3/3] Checking Prometheus targets...

Target prometheus... ✓ UP
Target alertmanager... ✓ UP
Target node-exporter... ✓ UP

============================================
✓ All checks passed!
============================================
```

---

## 📝 Phase 4: Verify Web Interfaces

### Step 4.1: Access Prometheus

```bash
# Open in browser
xdg-open http://localhost:9090
# OR manually visit: http://localhost:9090
```

**What to check**:
1. **Status** → **Targets**: All targets should be "UP"
2. **Status** → **Rules**: Alert rules should be loaded
3. **Alerts**: Should show configured alerts (may be inactive initially)

---

### Step 4.2: Access Alertmanager

```bash
xdg-open http://localhost:9093
```

**What to check**:
1. **Alerts**: Should be empty initially
2. **Silences**: Should be empty
3. **Status**: Should show configuration loaded

---

### Step 4.3: Check Node Exporter Metrics

```bash
curl http://localhost:9100/metrics | head -20
```

**Expected output**: Should show system metrics like:
```
# HELP node_cpu_seconds_total Seconds the CPUs spent in each mode.
# TYPE node_cpu_seconds_total counter
node_cpu_seconds_total{cpu="0",mode="idle"} 12345.67
node_cpu_seconds_total{cpu="0",mode="system"} 234.56
...
```

---

## 📝 Phase 5: Test Alerts

### Step 5.1: Send Test Alerts

```bash
./scripts/test-alerts.sh
```

**What this does**:
- Sends 3 test alerts to Alertmanager:
  1. Critical alert (→ PagerDuty)
  2. Warning alert (→ Slack, if configured)
  3. Info alert (→ Email, if configured)

**Expected output**:
```
============================================
Alert Management System - Test Alerts
============================================

Checking Alertmanager status...
✓ Alertmanager is running

Sending test alerts...

Sending test alert: TestCriticalAlert
✓ Alert sent successfully

Sending test alert: TestWarningAlert
✓ Alert sent successfully

Sending test alert: TestInfoAlert
✓ Alert sent successfully

============================================
Test alerts sent successfully!
============================================
```

---

### Step 5.2: Verify Alerts in Alertmanager

```bash
xdg-open http://localhost:9093/#/alerts
```

**What to check**:
- Should see 3 test alerts
- Each with different severity (critical, warning, info)
- Status should be "active"

---

### Step 5.3: Verify PagerDuty Incident

1. **Log in to PagerDuty**: https://your-subdomain.pagerduty.com

2. **Navigate to Incidents**:
   - Click **Incidents** in top menu
   - Should see new incident: "TEST: Critical alert for PagerDuty"

3. **Check Incident Details**:
   - Click on the incident
   - Should show:
     - Summary
     - Cluster: production
     - Severity: critical
     - Description

4. **Acknowledge the Incident**:
   - Click **Acknowledge**
   - Status changes to "Acknowledged"

5. **Resolve the Incident**:
   - Click **Resolve**
   - Status changes to "Resolved"

---

## 📝 Phase 6: Monitor Real Alerts

### Step 6.1: View Prometheus Alerts

```bash
xdg-open http://localhost:9090/alerts
```

**What to check**:
- All alert rules are loaded
- Some alerts may be firing based on current system state
- Check alert state: Inactive, Pending, or Firing

---

### Step 6.2: Query Metrics

**In Prometheus UI** (http://localhost:9090/graph):

1. **CPU Usage**:
   ```promql
   100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
   ```

2. **Memory Usage**:
   ```promql
   (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100
   ```

3. **Disk Usage**:
   ```promql
   (1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) * 100
   ```

**Click "Execute"** to see current values.

---

### Step 6.3: Trigger Real Alert (Optional)

**Simulate high CPU usage**:

```bash
# Start CPU stress (requires stress tool)
# Install: sudo apt-get install stress

# Run for 5 minutes
stress --cpu 4 --timeout 300s
```

**What happens**:
1. CPU usage increases above threshold (80%)
2. After 5 minutes, `HighCPUUsage` alert fires
3. Alert sent to Alertmanager
4. Alertmanager routes to PagerDuty (if severity=critical)
5. PagerDuty creates incident
6. You receive notification

**Monitor**:
```bash
# Watch Prometheus alerts
watch -n 5 'curl -s http://localhost:9090/api/v1/alerts | jq ".data.alerts[] | {alertname: .labels.alertname, state: .state}"'
```

---

## 📝 Phase 7: Maintenance Operations

### Step 7.1: View Logs

```bash
cd docker

# All services
docker-compose logs -f

# Specific service
docker-compose logs -f prometheus
docker-compose logs -f alertmanager

# Last 100 lines
docker-compose logs --tail=100 prometheus
```

---

### Step 7.2: Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart prometheus

# Stop all
docker-compose stop

# Start all
docker-compose start
```

---

### Step 7.3: Update Configuration

**After editing configuration files**:

```bash
# Validate Prometheus config
docker run --rm -v $(pwd)/../prometheus:/etc/prometheus \
  prom/prometheus:latest \
  promtool check config /etc/prometheus/prometheus.yml

# Reload Prometheus (no restart needed)
curl -X POST http://localhost:9090/-/reload

# Reload Alertmanager
curl -X POST http://localhost:9093/-/reload
```

---

### Step 7.4: Backup Data

```bash
./scripts/backup.sh
```

**What this does**:
- Backs up all configuration files
- Backs up Prometheus data
- Backs up Alertmanager data
- Creates timestamped archives in `backups/` directory

---

### Step 7.5: Stop System

```bash
cd docker

# Stop services (keeps data)
docker-compose down

# Stop and remove data
docker-compose down -v
```

---

## 📝 Phase 8: Production Considerations

### Step 8.1: Secure the System

1. **Add authentication**:
   ```bash
   # Generate password hash
   htpasswd -nB admin
   
   # Add to docker-compose.yml
   ```

2. **Use HTTPS**:
   - Set up reverse proxy (Nginx/Traefik)
   - Configure SSL certificates

3. **Restrict network access**:
   - Use firewall rules
   - Limit exposed ports

---

### Step 8.2: Scale for Production

1. **Increase retention**:
   ```yaml
   # In docker-compose.yml
   - '--storage.tsdb.retention.time=90d'
   - '--storage.tsdb.retention.size=50GB'
   ```

2. **Add more exporters**:
   - Database exporters (postgres, mysql)
   - Application exporters
   - Cloud exporters (AWS, GCP)

3. **Set up high availability**:
   - Multiple Prometheus instances
   - Alertmanager clustering
   - Remote storage (Thanos, Cortex)

---

### Step 8.3: Monitor the Monitors

1. **Set up external monitoring**:
   - Use external service to monitor Prometheus
   - Alert if Prometheus is down

2. **Create dashboards**:
   - Install Grafana
   - Import Prometheus dashboards
   - Create custom dashboards

---

## 🎉 Success Criteria

Your system is successfully deployed if:

- [ ] All Docker containers are running
- [ ] All Prometheus targets are UP
- [ ] Alert rules are loaded
- [ ] Test alerts reach PagerDuty
- [ ] PagerDuty incidents can be acknowledged/resolved
- [ ] Real alerts fire based on system metrics
- [ ] Web interfaces are accessible
- [ ] Health check script passes

---

## 📚 Next Steps

1. **Customize alert rules** for your environment
2. **Add more integrations** (Slack, email, webhooks)
3. **Create runbooks** for common alerts
4. **Set up dashboards** in Grafana
5. **Implement SLOs** and SLIs
6. **Document your processes**

---

**Last Updated**: 2025-11-27
