# Hands-On Tutorials - Learn By Doing!

## Table of Contents
1. [Tutorial 1: Your First Alert](#tutorial-1-your-first-alert)
2. [Tutorial 2: Creating a Custom Dashboard](#tutorial-2-creating-a-custom-dashboard)
3. [Tutorial 3: Writing Your First Runbook](#tutorial-3-writing-your-first-runbook)
4. [Tutorial 4: Setting Up SLOs](#tutorial-4-setting-up-slos)
5. [Tutorial 5: Simulating an Incident](#tutorial-5-simulating-an-incident)
6. [Tutorial 6: Creating Auto-Remediation](#tutorial-6-creating-auto-remediation)

---

## Tutorial 1: Your First Alert

### What You'll Learn
- How to write a Prometheus alert rule
- How to test it
- How to make it fire

### Prerequisites
- Docker Compose running (`./scripts/deploy_monitoring.sh`)
- Basic understanding of what alerts are

---

### Step 1: Understand the Problem

**Scenario:**
You want to know if your website is down.

**Simple Rule:**
"If my website doesn't respond for 2 minutes, alert me!"

---

### Step 2: Write the Alert Rule

Create a new file: `monitoring/prometheus/alerts/my_first_alert.yaml`

```yaml
groups:
  - name: my_first_alerts
    interval: 30s  # Check every 30 seconds
    rules:
      # Alert when service is down
      - alert: MyWebsiteDown
        # This is the condition (PromQL query)
        expr: up{job="my-website"} == 0
        # Wait 2 minutes before firing
        for: 2m
        labels:
          severity: critical
          team: my-team
        annotations:
          summary: "My website is down!"
          description: "Website {{ $labels.instance }} has been down for more than 2 minutes."
          impact: "Users cannot access the website"
          runbook_url: "https://runbooks.example.com/website-down"
```

**Let's Break This Down:**

```yaml
expr: up{job="my-website"} == 0
```
**Translation:** "Find the metric called 'up' for job 'my-website', and check if it equals 0"
- `up` = Is the service responding? (1 = yes, 0 = no)
- `{job="my-website"}` = Filter for only "my-website"
- `== 0` = Check if it equals 0 (down)

```yaml
for: 2m
```
**Translation:** "Don't fire immediately. Wait 2 minutes to make sure it's really down, not just a brief blip."

```yaml
labels:
  severity: critical
```
**Translation:** "This is a critical alert" (will determine who gets notified)

---

### Step 3: Add Your Service to Prometheus

Edit `monitoring/prometheus/prometheus.yml`:

```yaml
scrape_configs:
  # ... existing configs ...
  
  # Add your website
  - job_name: 'my-website'
    static_configs:
      - targets: ['my-website.example.com:443']
        labels:
          service: 'my-website'
          team: 'my-team'
```

---

### Step 4: Validate Your Alert

```bash
# Check if the alert rule is valid
promtool check rules monitoring/prometheus/alerts/my_first_alert.yaml
```

**Expected Output:**
```
Checking monitoring/prometheus/alerts/my_first_alert.yaml
  SUCCESS: 1 rules found
```

**If you see errors:**
```
FAILED: invalid expression in alert rule
```
**Fix:** Check your PromQL syntax, make sure quotes match, etc.

---

### Step 5: Reload Prometheus

```bash
# Restart Prometheus to load new config
docker-compose restart prometheus

# Check Prometheus logs
docker-compose logs -f prometheus
```

**Look for:**
```
level=info msg="Loading configuration file" filename=/etc/prometheus/prometheus.yml
level=info msg="Completed loading of configuration file"
```

---

### Step 6: Verify in Prometheus UI

1. Open http://localhost:9090
2. Click "Alerts" in the top menu
3. Look for "MyWebsiteDown"

**You should see:**
```
Alert: MyWebsiteDown
State: Inactive (green) ✅
```

This means:
- ✅ Alert is loaded
- ✅ Condition is not met (website is up)
- ✅ Everything is working!

---

### Step 7: Test Your Alert (Make It Fire!)

**Option 1: Simulate Downtime**

Edit `monitoring/prometheus/prometheus.yml`:

```yaml
- job_name: 'my-website'
  static_configs:
    - targets: ['fake-website-that-doesnt-exist.com:443']  # This will fail!
```

**Option 2: Use Blackbox Exporter**

```yaml
- job_name: 'blackbox'
  metrics_path: /probe
  params:
    module: [http_2xx]
  static_configs:
    - targets:
        - http://this-will-fail.example.com  # Intentionally broken URL
```

---

### Step 8: Watch It Fire

```bash
# Restart Prometheus
docker-compose restart prometheus

# Wait 2 minutes (the "for" duration)
# Then check http://localhost:9090/alerts
```

**After 2 minutes, you should see:**
```
Alert: MyWebsiteDown
State: FIRING (red) 🚨
Active Since: 2 minutes ago
```

**Click on the alert to see details:**
```
Labels:
  alertname: MyWebsiteDown
  severity: critical
  team: my-team
  
Annotations:
  summary: My website is down!
  description: Website fake-website-that-doesnt-exist.com:443 has been down for more than 2 minutes.
```

---

### Step 9: Check Alertmanager

1. Open http://localhost:9093
2. You should see your alert!
3. If Slack is configured, check your Slack channel

---

### Step 10: Fix and Resolve

```bash
# Put back the correct URL
# Edit monitoring/prometheus/prometheus.yml
# Change back to real website

docker-compose restart prometheus

# Wait a minute, alert should resolve automatically
```

**In Prometheus:**
```
Alert: MyWebsiteDown
State: Inactive (green) ✅
```

**In Alertmanager:**
```
Alert: MyWebsiteDown
Status: RESOLVED ✅
```

---

### 🎉 Congratulations!

You just:
1. ✅ Wrote your first alert rule
2. ✅ Validated it
3. ✅ Made it fire
4. ✅ Saw it in Alertmanager
5. ✅ Resolved it

---

## Tutorial 2: Creating a Custom Dashboard

### What You'll Learn
- How to create a Grafana dashboard
- How to add panels with metrics
- How to save and share dashboards

---

### Step 1: Open Grafana

1. Go to http://localhost:3000
2. Login: `admin` / `admin`
3. Change password when prompted (or skip)

---

### Step 2: Create a New Dashboard

1. Click the "+" icon on the left sidebar
2. Click "Dashboard"
3. Click "Add new panel"

---

### Step 3: Your First Panel - Request Rate

**What we want to show:**
"How many requests per second is my service handling?"

**In the panel editor:**

1. **Query:**
   ```promql
   rate(http_requests_total{job="my-service"}[5m])
   ```
   
   **Translation:**
   - `http_requests_total` = Total number of requests
   - `{job="my-service"}` = For my service
   - `[5m]` = Over the last 5 minutes
   - `rate()` = Calculate requests per second

2. **Panel Title:** "Request Rate (req/s)"

3. **Visualization:** Time series (line graph)

4. **Legend:** `{{instance}}` (shows which server)

5. Click "Apply"

---

### Step 4: Second Panel - Error Rate

**What we want to show:**
"What percentage of requests are failing?"

**Add another panel:**

1. Click "Add panel" → "Add new panel"

2. **Query:**
   ```promql
   sum(rate(http_requests_total{status=~"5..",job="my-service"}[5m])) 
   / 
   sum(rate(http_requests_total{job="my-service"}[5m])) 
   * 100
   ```
   
   **Translation:**
   - Top: Count of 5xx errors per second
   - Bottom: Count of all requests per second
   - Divide: Get error rate as decimal
   - * 100: Convert to percentage

3. **Panel Title:** "Error Rate (%)"

4. **Visualization:** Stat (big number)

5. **Unit:** Percent (0-100)

6. **Thresholds:**
   - Green: 0-1%
   - Yellow: 1-5%
   - Red: >5%

7. Click "Apply"

---

### Step 5: Third Panel - Latency

**What we want to show:**
"How fast is my service responding?"

**Add another panel:**

1. **Query:**
   ```promql
   histogram_quantile(0.95, 
     sum(rate(http_request_duration_seconds_bucket{job="my-service"}[5m])) by (le)
   )
   ```
   
   **Translation:**
   - Calculate the 95th percentile latency
   - Meaning: 95% of requests are faster than this

2. **Panel Title:** "P95 Latency"

3. **Visualization:** Time series

4. **Unit:** Seconds (s)

5. **Thresholds:**
   - Green: <0.5s
   - Yellow: 0.5-1s
   - Red: >1s

---

### Step 6: Fourth Panel - Active Alerts

**What we want to show:**
"Are there any alerts firing right now?"

**Add another panel:**

1. **Query:**
   ```promql
   ALERTS{alertstate="firing"}
   ```

2. **Panel Title:** "Active Alerts"

3. **Visualization:** Table

4. **Columns to show:**
   - alertname
   - severity
   - summary

---

### Step 7: Organize Your Dashboard

**Add rows to group panels:**

1. Click "Add" → "Row"
2. Name it "Traffic Metrics"
3. Drag Request Rate and Error Rate into this row

4. Add another row: "Performance Metrics"
5. Drag Latency into this row

6. Add another row: "Alerts"
7. Drag Active Alerts into this row

---

### Step 8: Add Variables (Advanced)

**Make your dashboard work for ANY service:**

1. Click the gear icon (⚙️) at the top → "Variables"
2. Click "Add variable"

**Settings:**
```
Name: service
Label: Service
Type: Query
Data source: Prometheus
Query: label_values(up, job)
```

3. Click "Apply"

**Now update your queries:**

Change:
```promql
rate(http_requests_total{job="my-service"}[5m])
```

To:
```promql
rate(http_requests_total{job="$service"}[5m])
```

**Now you have a dropdown to select ANY service!** 🎉

---

### Step 9: Save Your Dashboard

1. Click the save icon (💾) at the top
2. Name: "My Service Dashboard"
3. Folder: General
4. Click "Save"

---

### Step 10: Share Your Dashboard

**Option 1: Export as JSON**
1. Click the share icon
2. Click "Export"
3. Click "Save to file"
4. Share the JSON file with your team

**Option 2: Get a Link**
1. Click the share icon
2. Click "Link"
3. Copy the URL
4. Send to your team

---

### 🎉 Congratulations!

You just created a professional dashboard with:
- ✅ Request rate graph
- ✅ Error rate indicator
- ✅ Latency monitoring
- ✅ Active alerts table
- ✅ Service selector dropdown

---

## Tutorial 3: Writing Your First Runbook

### What You'll Learn
- How to structure a runbook
- What information to include
- How to make it actionable

---

### Step 1: Choose an Alert

Let's write a runbook for: **"HighMemoryUsage"**

**The Alert:**
```yaml
- alert: HighMemoryUsage
  expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.8
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High memory usage on {{ $labels.instance }}"
```

---

### Step 2: Create the Runbook File

Create: `runbooks/high_memory_usage.md`

---

### Step 3: Fill in the Template

```markdown
# High Memory Usage

**Alert:** `HighMemoryUsage`  
**Severity:** Warning  
**Team:** Platform

## Symptoms

What you'll see:
- Alert: "HighMemoryUsage" firing
- Server using > 80% of RAM
- Applications may be slow
- Possible "Out of Memory" errors in logs

## Impact

**Users Affected:** Potentially all users on this server  
**Functionality:** Degraded performance, possible crashes  
**Business Impact:** Slow response times, potential service interruption

## Immediate Checks

### 1. Verify the Alert

```bash
# SSH to the server
ssh user@server-name

# Check current memory usage
free -h
```

**What you're looking for:**
```
              total        used        free      shared  buff/cache   available
Mem:           16Gi        13Gi       500Mi       100Mi        2.5Gi        2.5Gi
```

If "available" is < 3Gi, memory is indeed high.

### 2. Find Memory Hogs

```bash
# Show top memory-consuming processes
ps aux --sort=-%mem | head -20
```

**Example output:**
```
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
app       1234  2.0 45.0 8000000 7200000 ?     Ssl  10:00   1:23 /app/my-service
postgres  5678  1.0 25.0 4000000 4000000 ?     Ssl  09:00   0:45 postgres
redis     9012  0.5 10.0 2000000 1600000 ?     Ssl  09:00   0:12 redis-server
```

**Translation:**
- `my-service` is using 45% of total RAM (7.2GB)
- `postgres` is using 25% (4GB)
- `redis` is using 10% (1.6GB)

### 3. Check for Memory Leaks

```bash
# Check if memory usage is growing over time
# Run this command multiple times, 1 minute apart

watch -n 60 'ps aux --sort=-%mem | head -5'
```

**If memory keeps growing:**
→ Possible memory leak!

**If memory is stable:**
→ Just high usage, not a leak

## Manual Remediation Steps

### Option 1: Restart the Memory-Hungry Service

**When to use:** If one service is using way more memory than normal

```bash
# For systemd services
sudo systemctl restart my-service

# For Docker containers
docker restart my-service-container

# For Kubernetes pods
kubectl rollout restart deployment/my-service -n production
```

**Verify:**
```bash
# Wait 1 minute, then check memory again
free -h
```

### Option 2: Clear Caches

**When to use:** If buff/cache is very high

```bash
# Clear page cache, dentries, and inodes
sudo sync; sudo echo 3 > /proc/sys/vm/drop_caches

# Check memory again
free -h
```

**Note:** This is safe! Linux will rebuild caches as needed.

### Option 3: Kill Specific Process

**When to use:** If a runaway process is consuming all memory

```bash
# Find the process ID (PID)
ps aux --sort=-%mem | head -5

# Kill it gracefully
sudo kill -15 <PID>

# If it doesn't die in 10 seconds, force kill
sudo kill -9 <PID>
```

**⚠️ Warning:** Only kill processes you recognize!

### Option 4: Scale Up (Add More Memory)

**When to use:** If this is a recurring issue

**For VMs:**
```bash
# Resize the instance (requires restart)
# This is cloud-provider specific
aws ec2 modify-instance-attribute --instance-id i-1234567890abcdef0 --instance-type m5.2xlarge
```

**For Kubernetes:**
```yaml
# Edit deployment
kubectl edit deployment my-service -n production

# Increase memory limits
resources:
  limits:
    memory: "4Gi"  # Was 2Gi, now 4Gi
```

## Verification

After taking action:

### 1. Check Memory Usage
```bash
free -h
# Should show more "available" memory
```

### 2. Check Service Health
```bash
# For systemd
sudo systemctl status my-service

# For Docker
docker ps | grep my-service

# For Kubernetes
kubectl get pods -n production | grep my-service
```

### 3. Check Logs
```bash
# Look for any errors after restart
sudo journalctl -u my-service -n 50

# Or for Docker
docker logs my-service-container --tail 50
```

### 4. Monitor for 15 Minutes
- Watch Grafana dashboard
- Ensure memory stays below 80%
- Ensure no new alerts fire

## Escalation

**Escalate if:**
- Memory usage doesn't decrease after restart
- Service keeps crashing
- Memory leak suspected
- Issue affects multiple servers

**Escalation Path:**
1. **Primary:** @platform-team in #platform-alerts
2. **If memory leak:** @dev-team (service owners)
3. **After 30 min:** @engineering-manager

## Post-Incident

### 1. Document What Happened
- Which service was using memory?
- What action fixed it?
- Was it a one-time spike or recurring?

### 2. Create Follow-Up Tasks
- [ ] Investigate memory leak (if applicable)
- [ ] Increase memory limits (if needed)
- [ ] Add memory usage alerts for specific services
- [ ] Optimize memory-hungry queries/operations

### 3. Update This Runbook
- Did you find a new solution?
- Was something unclear?
- Add it here!

## Related Links

- **Dashboard:** [Server Metrics](http://localhost:3000/d/node-exporter)
- **Logs:** [Kibana](http://kibana.example.com)
- **Runbook:** [Out of Memory Kills](./oom_kills.md)

## Runbook Metadata

- **Owner:** @platform-team
- **Last Updated:** 2025-12-01
- **Version:** 1.0
- **Tested:** Yes (2025-11-15)

## Notes

- Memory usage spikes are normal during deployments
- Redis cache can use a lot of memory - this is expected
- If you see OOM kills in logs, memory limits are too low
```

---

### Step 4: Link Runbook to Alert

Update your alert rule:

```yaml
- alert: HighMemoryUsage
  expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.8
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High memory usage on {{ $labels.instance }}"
    runbook_url: "https://github.com/your-org/runbooks/blob/main/high_memory_usage.md"  # ← Add this!
```

---

### Step 5: Test Your Runbook

**Simulate high memory:**

```bash
# Create a program that uses lots of memory
stress --vm 1 --vm-bytes 12G --timeout 300s

# This will:
# - Allocate 12GB of RAM
# - Run for 5 minutes
# - Trigger your alert
```

**Then:**
1. Wait for alert to fire
2. Follow your runbook step-by-step
3. Note anything that's unclear or missing
4. Update the runbook

---

### 🎉 Congratulations!

You just:
- ✅ Wrote a complete runbook
- ✅ Included diagnostic steps
- ✅ Added remediation options
- ✅ Linked it to an alert
- ✅ Tested it!

---

## Tutorial 4: Setting Up SLOs

### What You'll Learn
- How to define an SLO
- How to measure it
- How to create error budget alerts

---

### Step 1: Choose Your SLO

**Example Service:** Payment API

**What we promise:**
"99.9% of payment requests will succeed"

**Translation:**
- Out of 1,000 requests, only 1 can fail
- Error budget: 0.1%

---

### Step 2: Define the SLO in Config

Create: `config/slo_definitions.yaml`

```yaml
services:
  - name: payment-api
    team: payments
    owner: payments-team@example.com
    
    slos:
      availability:
        target: 99.9  # 99.9% success rate
        window: 30d   # Measured over 30 days
        error_budget: 0.1  # 0.1% can fail
        
        measurement:
          success_metric: http_requests_total{job="payment-api",status!~"5.."}
          total_metric: http_requests_total{job="payment-api"}
```

---

### Step 3: Create Recording Rules

Add to `monitoring/prometheus/recording_rules.yaml`:

```yaml
groups:
  - name: payment_api_slo
    interval: 30s
    rules:
      # Success rate (what % of requests succeed)
      - record: payment_api:success_rate
        expr: |
          sum(rate(http_requests_total{job="payment-api",status!~"5.."}[5m]))
          /
          sum(rate(http_requests_total{job="payment-api"}[5m]))
      
      # Error budget remaining (how much budget is left)
      - record: payment_api:error_budget_remaining
        expr: |
          1 - (
            (1 - payment_api:success_rate)
            /
            (1 - 0.999)  # 0.1% error budget
          )
```

---

### Step 4: Create Error Budget Burn Rate Alerts

Add to `monitoring/prometheus/alerts/slo_alerts.yaml`:

```yaml
groups:
  - name: payment_api_slo_alerts
    interval: 30s
    rules:
      # Fast burn: Will exhaust budget in 2 days
      - alert: PaymentAPI_ErrorBudgetBurnFast
        expr: |
          (
            1 - payment_api:success_rate
          ) > (14.4 * (1 - 0.999))
        for: 5m
        labels:
          severity: page
          team: payments
        annotations:
          summary: "Payment API burning error budget fast!"
          description: "At current error rate, will exhaust monthly error budget in 2 days"
          impact: "SLO breach imminent"
          runbook_url: "https://runbooks.example.com/error-budget-burn"
      
      # Slow burn: Will exhaust budget in 5 days
      - alert: PaymentAPI_ErrorBudgetBurnSlow
        expr: |
          (
            1 - avg_over_time(payment_api:success_rate[6h])
          ) > (6 * (1 - 0.999))
        for: 30m
        labels:
          severity: warning
          team: payments
        annotations:
          summary: "Payment API burning error budget slowly"
          description: "At current error rate, will exhaust monthly error budget in 5 days"
          impact: "SLO at risk"
```

---

### Step 5: Create SLO Dashboard

In Grafana, create panels:

**Panel 1: Success Rate**
```promql
payment_api:success_rate * 100
```
- Visualization: Gauge
- Min: 99.5
- Max: 100
- Thresholds: Red < 99.9, Yellow 99.9-99.95, Green > 99.95

**Panel 2: Error Budget Remaining**
```promql
payment_api:error_budget_remaining * 100
```
- Visualization: Bar gauge
- Unit: Percent (0-100)
- Thresholds: Red < 10%, Yellow 10-50%, Green > 50%

**Panel 3: Error Budget Burn Rate**
```promql
(1 - payment_api:success_rate) / (1 - 0.999)
```
- Visualization: Time series
- Threshold line at 1.0 (normal burn)
- Alert zones at 6x and 14.4x

---

### Step 6: Monitor Your SLO

**Daily Check:**
```
1. Open SLO dashboard
2. Check success rate: Should be > 99.9%
3. Check error budget: Should not be depleting too fast
4. If budget < 50%: Slow down deployments, focus on stability
```

**Weekly Review:**
```
1. Calculate actual SLO compliance
2. Review incidents that consumed error budget
3. Discuss: Can we improve reliability?
```

---

### 🎉 Congratulations!

You just:
- ✅ Defined an SLO
- ✅ Created recording rules to measure it
- ✅ Set up error budget burn rate alerts
- ✅ Built an SLO dashboard

---

## Summary

You've completed 4 hands-on tutorials! You now know how to:

1. ✅ **Create alerts** - Write rules, test them, make them fire
2. ✅ **Build dashboards** - Visualize metrics, add panels, share with team
3. ✅ **Write runbooks** - Document procedures, make them actionable
4. ✅ **Set up SLOs** - Define targets, measure compliance, track error budgets

**Next Steps:**
- Try Tutorial 5: Simulating an Incident
- Try Tutorial 6: Creating Auto-Remediation
- Apply these to your own services!

**Remember:** The best way to learn is by doing. Don't be afraid to experiment! 🚀
