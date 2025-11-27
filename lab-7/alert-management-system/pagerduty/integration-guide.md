# PagerDuty Integration Guide

## 📋 Overview

This guide walks you through setting up PagerDuty integration with your Alert Management System.

---

## 🎯 Prerequisites

- PagerDuty account (Free trial available at https://www.pagerduty.com)
- Admin access to create services and integrations

---

## 📝 Step-by-Step Setup

### Step 1: Create a PagerDuty Account

1. Go to https://www.pagerduty.com
2. Click "Start Free Trial" or "Sign Up"
3. Fill in your details:
   - Company name
   - Email address
   - Password
4. Verify your email address

### Step 2: Create an Escalation Policy

Escalation policies define who gets notified and when.

1. **Navigate to Escalation Policies**:
   - Click **People** → **Escalation Policies**
   - Click **+ New Escalation Policy**

2. **Configure the policy**:
   ```
   Name: Production Alerts Escalation
   
   Level 1:
   - Notify: On-Call Engineer
   - Escalate after: 15 minutes
   
   Level 2:
   - Notify: Team Lead
   - Escalate after: 30 minutes
   
   Level 3:
   - Notify: Engineering Manager
   - Repeat: Until acknowledged
   ```

3. Click **Save**

### Step 3: Create a Service

Services represent the systems you're monitoring.

1. **Navigate to Services**:
   - Click **Services** → **Service Directory**
   - Click **+ New Service**

2. **Configure the service**:
   ```
   Name: Production Monitoring
   Description: Alerts from Prometheus/Alertmanager
   Escalation Policy: Production Alerts Escalation
   ```

3. **Select Integration Type**:
   - Choose **Prometheus** from the integration list
   - OR select **Events API v2** for custom integration

4. Click **Create Service**

### Step 4: Get Integration Key

1. After creating the service, you'll see the **Integration** section
2. Find your integration and click on it
3. Copy the **Integration Key** (also called Routing Key)
   ```
   Example: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
   ```

4. **IMPORTANT**: Keep this key secure!

### Step 5: Configure Alertmanager

1. **Edit your `.env` file**:
   ```bash
   cd /home/rk/Documents/labs/lab-7/alert-management-system/docker
   nano .env
   ```

2. **Add your integration key**:
   ```bash
   PAGERDUTY_INTEGRATION_KEY=your_integration_key_here
   ```

3. **Save and exit** (Ctrl+X, then Y, then Enter)

### Step 6: Restart Alertmanager

```bash
cd /home/rk/Documents/labs/lab-7/alert-management-system/docker
docker-compose restart alertmanager
```

### Step 7: Test the Integration

```bash
cd /home/rk/Documents/labs/lab-7/alert-management-system
./scripts/test-alerts.sh
```

**Expected Result**:
- A new incident should appear in PagerDuty
- The on-call engineer should receive a notification

---

## 🔧 Advanced Configuration

### Multiple Services

If you want different alerts to go to different PagerDuty services:

1. **Create multiple services in PagerDuty**:
   - Production Critical
   - Production Warnings
   - Database Alerts

2. **Get integration keys for each**

3. **Update `alertmanager.yml`**:
   ```yaml
   receivers:
     - name: 'pagerduty-critical'
       pagerduty_configs:
         - service_key: 'critical_integration_key'
     
     - name: 'pagerduty-database'
       pagerduty_configs:
         - service_key: 'database_integration_key'
   ```

### Custom Incident Details

Customize what information appears in PagerDuty incidents:

```yaml
pagerduty_configs:
  - service_key: '${PAGERDUTY_INTEGRATION_KEY}'
    description: '{{ .CommonAnnotations.summary }}'
    details:
      cluster: '{{ .CommonLabels.cluster }}'
      severity: '{{ .CommonLabels.severity }}'
      firing_count: '{{ .Alerts.Firing | len }}'
      instance: '{{ .CommonLabels.instance }}'
      runbook: '{{ .CommonAnnotations.runbook_url }}'
    client: 'Prometheus'
    client_url: 'http://your-prometheus-url:9090'
```

### Severity Mapping

Map Prometheus severity to PagerDuty severity:

```yaml
pagerduty_configs:
  - service_key: '${PAGERDUTY_INTEGRATION_KEY}'
    severity: >-
      {{ if eq .CommonLabels.severity "critical" }}critical
      {{ else if eq .CommonLabels.severity "warning" }}warning
      {{ else }}info{{ end }}
```

---

## 📊 Using PagerDuty Features

### On-Call Schedules

1. **Create a schedule**:
   - People → On-Call Schedules → + New On-Call Schedule
   - Define rotation (daily, weekly, custom)
   - Add team members

2. **Assign to escalation policy**:
   - Edit your escalation policy
   - Select the schedule instead of individual users

### Incident Response

When an incident fires:

1. **Acknowledge**: You're working on it
2. **Add responders**: Bring in more help
3. **Add notes**: Document your investigation
4. **Resolve**: Issue is fixed

### Postmortems

After resolving incidents:

1. Go to **Incidents** → Select incident
2. Click **Create Postmortem**
3. Document:
   - What happened
   - Root cause
   - Resolution steps
   - Prevention measures

---

## 🧪 Testing Checklist

- [ ] Integration key configured in `.env`
- [ ] Alertmanager restarted
- [ ] Test alert sent via script
- [ ] Incident appears in PagerDuty
- [ ] Notification received (email/SMS/phone)
- [ ] Incident can be acknowledged
- [ ] Incident can be resolved
- [ ] Auto-resolution works when alert clears

---

## 🔍 Troubleshooting

### Issue: No incidents appearing in PagerDuty

**Solutions**:
1. Verify integration key is correct
2. Check Alertmanager logs:
   ```bash
   docker-compose logs alertmanager | grep -i pagerduty
   ```
3. Test PagerDuty API directly:
   ```bash
   curl -X POST https://events.pagerduty.com/v2/enqueue \
     -H 'Content-Type: application/json' \
     -d '{
       "routing_key": "YOUR_KEY",
       "event_action": "trigger",
       "payload": {
         "summary": "Test",
         "severity": "critical",
         "source": "test"
       }
     }'
   ```

### Issue: Incidents not escalating

**Solutions**:
1. Check escalation policy configuration
2. Verify on-call schedule is active
3. Check user notification settings

### Issue: Too many notifications

**Solutions**:
1. Adjust `group_wait` and `group_interval` in Alertmanager
2. Use inhibition rules to suppress related alerts
3. Increase alert thresholds in Prometheus rules

---

## 📚 Additional Resources

- [PagerDuty Documentation](https://support.pagerduty.com/)
- [PagerDuty Events API v2](https://developer.pagerduty.com/docs/events-api-v2/overview/)
- [Prometheus Integration](https://www.pagerduty.com/docs/guides/prometheus-integration-guide/)
- [Best Practices](https://www.pagerduty.com/resources/learn/call-routing-escalation-policies/)

---

## 💡 Best Practices

1. **Use meaningful service names** that reflect what they monitor
2. **Set up proper escalation** - don't rely on a single person
3. **Configure notification rules** - balance urgency with alert fatigue
4. **Use schedules** for fair on-call rotation
5. **Review incidents regularly** to identify patterns
6. **Create runbooks** and link them in alert annotations
7. **Test your setup** regularly to ensure it works

---

**Last Updated**: 2025-11-27
