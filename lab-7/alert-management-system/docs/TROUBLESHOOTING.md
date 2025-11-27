# Troubleshooting Guide

## 📋 Common Issues and Solutions

This guide covers common issues you might encounter and how to resolve them.

---

## 🔴 Services Not Starting

### Issue: Docker Compose fails to start services

**Symptoms**:
```bash
ERROR: for prometheus  Cannot start service prometheus: ...
```

**Solutions**:

1. **Check if ports are already in use**:
   ```bash
   # Check if ports are occupied
   sudo lsof -i :9090  # Prometheus
   sudo lsof -i :9093  # Alertmanager
   sudo lsof -i :9100  # Node Exporter
   sudo lsof -i :9115  # Blackbox Exporter
   ```
   
   **Fix**: Stop the conflicting service or change ports in `docker-compose.yml`

2. **Check Docker daemon**:
   ```bash
   sudo systemctl status docker
   sudo systemctl start docker
   ```

3. **Check disk space**:
   ```bash
   df -h
   ```
   
   **Fix**: Free up disk space if needed

4. **View detailed logs**:
   ```bash
   docker-compose up
   # (without -d flag to see output)
   ```

---

## 🔴 Prometheus Issues

### Issue: Prometheus configuration invalid

**Symptoms**:
```
level=error msg="Error loading config" err="..."
```

**Solutions**:

1. **Validate configuration**:
   ```bash
   # If promtool is installed
   promtool check config prometheus/prometheus.yml
   
   # Or use Docker
   docker run --rm -v $(pwd)/prometheus:/etc/prometheus \
     prom/prometheus:latest \
     promtool check config /etc/prometheus/prometheus.yml
   ```

2. **Common YAML errors**:
   - Incorrect indentation (use spaces, not tabs)
   - Missing colons
   - Unquoted special characters

3. **Reload configuration**:
   ```bash
   # After fixing
   docker-compose restart prometheus
   
   # Or reload without restart
   curl -X POST http://localhost:9090/-/reload
   ```

### Issue: Targets are down

**Symptoms**:
- Targets show as "DOWN" in Prometheus UI
- http://localhost:9090/targets shows unhealthy targets

**Solutions**:

1. **Check target accessibility**:
   ```bash
   # Test from Prometheus container
   docker exec prometheus wget -O- http://node-exporter:9100/metrics
   ```

2. **Check Docker network**:
   ```bash
   docker network ls
   docker network inspect alert-management-system_monitoring
   ```

3. **Verify service is running**:
   ```bash
   docker-compose ps
   curl http://localhost:9100/metrics
   ```

### Issue: Alert rules not firing

**Symptoms**:
- No alerts in Alertmanager
- Rules show as "inactive" in Prometheus

**Solutions**:

1. **Validate alert rules**:
   ```bash
   promtool check rules prometheus/rules/*.yml
   ```

2. **Check rule evaluation**:
   - Go to http://localhost:9090/rules
   - Verify rules are loaded
   - Check "Last Evaluation" time

3. **Test PromQL query**:
   - Go to http://localhost:9090/graph
   - Run the alert expression manually
   - Verify it returns data

4. **Check `for` duration**:
   ```yaml
   # Alert fires only after condition is true for 5m
   for: 5m
   ```
   
   **Fix**: Reduce `for` duration for testing

---

## 🔴 Alertmanager Issues

### Issue: Alertmanager configuration invalid

**Symptoms**:
```
level=error msg="Loading configuration file failed"
```

**Solutions**:

1. **Validate configuration**:
   ```bash
   # If amtool is installed
   amtool check-config alertmanager/alertmanager.yml
   
   # Or use Docker
   docker run --rm -v $(pwd)/alertmanager:/etc/alertmanager \
     prom/alertmanager:latest \
     amtool check-config /etc/alertmanager/alertmanager.yml
   ```

2. **Check environment variables**:
   ```bash
   # Verify .env file exists and has values
   cat docker/.env | grep PAGERDUTY
   ```

3. **Reload configuration**:
   ```bash
   docker-compose restart alertmanager
   
   # Or reload without restart
   curl -X POST http://localhost:9093/-/reload
   ```

### Issue: Alerts not routing correctly

**Symptoms**:
- Alerts appear in Alertmanager but no notifications
- Alerts go to wrong receiver

**Solutions**:

1. **Check routing logic**:
   - Review `alertmanager.yml` route configuration
   - Verify label matchers are correct
   - Check `continue: true/false` settings

2. **Test routing**:
   ```bash
   # Use amtool to test routing
   amtool config routes test \
     --config.file=alertmanager/alertmanager.yml \
     --tree \
     severity=critical alertname=TestAlert
   ```

3. **View alert details**:
   - Go to http://localhost:9093/#/alerts
   - Click on alert to see labels
   - Verify labels match routing rules

---

## 🔴 PagerDuty Integration Issues

### Issue: No incidents in PagerDuty

**Symptoms**:
- Alerts in Alertmanager
- No incidents in PagerDuty

**Solutions**:

1. **Verify integration key**:
   ```bash
   # Check .env file
   cat docker/.env | grep PAGERDUTY_INTEGRATION_KEY
   ```
   
   **Fix**: Ensure key is correct (no extra spaces/quotes)

2. **Check Alertmanager logs**:
   ```bash
   docker-compose logs alertmanager | grep -i pagerduty
   ```
   
   Look for errors like:
   - `403 Forbidden` - Invalid integration key
   - `400 Bad Request` - Malformed request
   - `timeout` - Network issues

3. **Test PagerDuty API directly**:
   ```bash
   curl -X POST https://events.pagerduty.com/v2/enqueue \
     -H 'Content-Type: application/json' \
     -d '{
       "routing_key": "YOUR_INTEGRATION_KEY",
       "event_action": "trigger",
       "payload": {
         "summary": "Test Alert",
         "severity": "critical",
         "source": "manual-test"
       }
     }'
   ```
   
   **Expected response**: `{"status":"success","message":"Event processed"}`

4. **Check PagerDuty service status**:
   - Go to https://status.pagerduty.com
   - Verify no outages

### Issue: Duplicate incidents

**Symptoms**:
- Multiple incidents for same alert

**Solutions**:

1. **Check deduplication key**:
   ```yaml
   # In alertmanager.yml
   pagerduty_configs:
     - service_key: '${PAGERDUTY_INTEGRATION_KEY}'
       # Add dedup_key for better deduplication
       dedup_key: '{{ .GroupLabels.alertname }}-{{ .GroupLabels.instance }}'
   ```

2. **Adjust grouping**:
   ```yaml
   route:
     group_by: ['alertname', 'instance']
     group_wait: 30s
     group_interval: 5m
   ```

---

## 🔴 Notification Issues

### Issue: Email notifications not working

**Symptoms**:
- No emails received
- Alertmanager logs show SMTP errors

**Solutions**:

1. **Check SMTP configuration**:
   ```bash
   # Verify .env file
   cat docker/.env | grep SMTP
   ```

2. **For Gmail**:
   - Use App Password, not regular password
   - Enable "Less secure app access" OR use OAuth2

3. **Test SMTP connection**:
   ```bash
   # From Alertmanager container
   docker exec -it alertmanager sh
   telnet smtp.gmail.com 587
   ```

4. **Check Alertmanager logs**:
   ```bash
   docker-compose logs alertmanager | grep -i smtp
   ```

### Issue: Slack notifications not working

**Symptoms**:
- No messages in Slack
- Alertmanager logs show webhook errors

**Solutions**:

1. **Verify webhook URL**:
   ```bash
   cat docker/.env | grep SLACK_WEBHOOK_URL
   ```

2. **Test webhook directly**:
   ```bash
   curl -X POST YOUR_WEBHOOK_URL \
     -H 'Content-Type: application/json' \
     -d '{"text":"Test message"}'
   ```

3. **Check Slack app permissions**:
   - Go to Slack → Apps → Incoming Webhooks
   - Verify webhook is active
   - Check channel permissions

---

## 🔴 Performance Issues

### Issue: High memory usage

**Symptoms**:
- Prometheus using excessive memory
- System becomes slow

**Solutions**:

1. **Reduce retention**:
   ```yaml
   # In docker-compose.yml
   command:
     - '--storage.tsdb.retention.time=15d'  # Reduce from 30d
     - '--storage.tsdb.retention.size=5GB'  # Reduce from 10GB
   ```

2. **Reduce scrape frequency**:
   ```yaml
   # In prometheus.yml
   global:
     scrape_interval: 30s  # Increase from 15s
   ```

3. **Limit cardinality**:
   - Review metrics with high cardinality
   - Use relabeling to drop unnecessary labels

### Issue: Disk space filling up

**Symptoms**:
- Prometheus data directory growing
- Low disk space alerts

**Solutions**:

1. **Check current usage**:
   ```bash
   docker exec prometheus du -sh /prometheus
   ```

2. **Reduce retention** (see above)

3. **Clean up old data**:
   ```bash
   # Stop Prometheus
   docker-compose stop prometheus
   
   # Remove old data
   docker exec prometheus rm -rf /prometheus/wal/*
   
   # Start Prometheus
   docker-compose start prometheus
   ```

---

## 🔴 Alert Fatigue

### Issue: Too many alerts

**Symptoms**:
- Constant notifications
- Team ignoring alerts

**Solutions**:

1. **Increase thresholds**:
   ```yaml
   # Before
   expr: cpu_usage > 70
   
   # After
   expr: cpu_usage > 85
   ```

2. **Increase `for` duration**:
   ```yaml
   # Before
   for: 1m
   
   # After
   for: 10m
   ```

3. **Use inhibition rules**:
   ```yaml
   inhibit_rules:
     - source_match:
         severity: 'critical'
       target_match:
         severity: 'warning'
       equal: ['instance']
   ```

4. **Adjust grouping**:
   ```yaml
   route:
     group_wait: 5m        # Wait longer before sending
     group_interval: 10m   # Group more alerts together
     repeat_interval: 24h  # Don't repeat as often
   ```

---

## 🛠️ Debugging Commands

### View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f prometheus
docker-compose logs -f alertmanager

# Last 100 lines
docker-compose logs --tail=100 prometheus
```

### Check service health
```bash
# Run health check script
./scripts/health-check.sh

# Manual checks
curl http://localhost:9090/-/healthy
curl http://localhost:9093/-/healthy
```

### Restart services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart prometheus
docker-compose restart alertmanager
```

### View configuration
```bash
# Prometheus config
curl http://localhost:9090/api/v1/status/config | jq

# Alertmanager config
curl http://localhost:9093/api/v1/status | jq
```

### Query metrics
```bash
# Get all metrics
curl http://localhost:9090/api/v1/label/__name__/values | jq

# Query specific metric
curl 'http://localhost:9090/api/v1/query?query=up' | jq
```

---

## 📞 Getting Help

If you're still stuck:

1. **Check logs** for error messages
2. **Search documentation**:
   - Prometheus: https://prometheus.io/docs/
   - Alertmanager: https://prometheus.io/docs/alerting/
   - PagerDuty: https://support.pagerduty.com/

3. **Community support**:
   - Prometheus Slack: https://slack.cncf.io/
   - Stack Overflow: Tag `prometheus` or `alertmanager`

4. **GitHub Issues**:
   - Prometheus: https://github.com/prometheus/prometheus/issues
   - Alertmanager: https://github.com/prometheus/alertmanager/issues

---

**Last Updated**: 2025-11-27
