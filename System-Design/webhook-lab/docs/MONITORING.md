# Monitoring Guide

Comprehensive guide for monitoring the Webhook Delivery Platform using Prometheus and Grafana.

## Table of Contents

1. [Overview](#overview)
2. [Metrics](#metrics)
3. [Grafana Dashboards](#grafana-dashboards)
4. [Alerts](#alerts)
5. [Logging](#logging)
6. [Troubleshooting](#troubleshooting)

---

## Overview

The platform exposes Prometheus metrics at `/metrics` endpoint and includes pre-configured Grafana dashboards for visualization.

### Monitoring Stack

- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboarding
- **Structured Logging**: JSON logs for centralized aggregation

### Access URLs

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)
- **Metrics Endpoint**: http://localhost:8000/metrics

---

## Metrics

### Event Metrics

#### `webhook_events_published_total`
**Type**: Counter  
**Labels**: `tenant_id`, `event_type`  
**Description**: Total number of events published to the platform

**Usage**:
```promql
# Events per second
rate(webhook_events_published_total[5m])

# Events by tenant
sum by (tenant_id) (webhook_events_published_total)

# Events by type
sum by (event_type) (webhook_events_published_total)
```

#### `webhook_events_duplicate_total`
**Type**: Counter  
**Labels**: `tenant_id`  
**Description**: Duplicate events caught by idempotency check

**Usage**:
```promql
# Duplicate rate
rate(webhook_events_duplicate_total[5m])

# Duplicate percentage
(rate(webhook_events_duplicate_total[5m]) / rate(webhook_events_published_total[5m])) * 100
```

---

### Delivery Metrics

#### `webhook_delivery_attempts_total`
**Type**: Counter  
**Description**: Total delivery attempts (including retries)

**Usage**:
```promql
# Attempts per second
rate(webhook_delivery_attempts_total[5m])

# Total attempts
webhook_delivery_attempts_total
```

#### `webhook_delivery_success_total`
**Type**: Counter  
**Description**: Successful webhook deliveries

**Usage**:
```promql
# Success rate
rate(webhook_delivery_success_total[5m])

# Success percentage
(rate(webhook_delivery_success_total[5m]) / rate(webhook_delivery_attempts_total[5m])) * 100
```

#### `webhook_delivery_failure_total`
**Type**: Counter  
**Description**: Failed webhook deliveries

**Usage**:
```promql
# Failure rate
rate(webhook_delivery_failure_total[5m])

# Failure percentage
(rate(webhook_delivery_failure_total[5m]) / rate(webhook_delivery_attempts_total[5m])) * 100
```

#### `webhook_delivery_duration_seconds`
**Type**: Histogram  
**Buckets**: [0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]  
**Description**: Webhook delivery duration in seconds

**Usage**:
```promql
# P50 latency
histogram_quantile(0.50, rate(webhook_delivery_duration_seconds_bucket[5m]))

# P95 latency
histogram_quantile(0.95, rate(webhook_delivery_duration_seconds_bucket[5m]))

# P99 latency
histogram_quantile(0.99, rate(webhook_delivery_duration_seconds_bucket[5m]))

# Average latency
rate(webhook_delivery_duration_seconds_sum[5m]) / rate(webhook_delivery_duration_seconds_count[5m])
```

---

### Rate Limiting Metrics

#### `webhook_rate_limit_hits_total`
**Type**: Counter  
**Labels**: `tenant_id`  
**Description**: Number of requests blocked by rate limiter

**Usage**:
```promql
# Rate limit hits per second
rate(webhook_rate_limit_hits_total[5m])

# Tenants hitting rate limits
topk(10, sum by (tenant_id) (rate(webhook_rate_limit_hits_total[5m])))
```

---

### Dead Letter Queue Metrics

#### `webhook_dlq_size`
**Type**: Gauge  
**Description**: Number of unresolved entries in DLQ

**Usage**:
```promql
# Current DLQ size
webhook_dlq_size

# DLQ growth rate
deriv(webhook_dlq_size[5m])
```

---

### System Metrics

#### `webhook_active_tenants`
**Type**: Gauge  
**Description**: Number of active tenants

#### `webhook_active_endpoints`
**Type**: Gauge  
**Description**: Number of active webhook endpoints

---

## Grafana Dashboards

### Dashboard 1: Overview

**Panels**:

1. **Event Throughput**
   - Query: `rate(webhook_events_published_total[5m])`
   - Type: Graph
   - Description: Events published per second

2. **Delivery Success Rate**
   - Query: `(rate(webhook_delivery_success_total[5m]) / rate(webhook_delivery_attempts_total[5m])) * 100`
   - Type: Gauge
   - Description: Percentage of successful deliveries

3. **Active Tenants**
   - Query: `webhook_active_tenants`
   - Type: Stat
   - Description: Current number of active tenants

4. **DLQ Size**
   - Query: `webhook_dlq_size`
   - Type: Stat
   - Description: Unresolved DLQ entries

5. **P95 Latency**
   - Query: `histogram_quantile(0.95, rate(webhook_delivery_duration_seconds_bucket[5m]))`
   - Type: Graph
   - Description: 95th percentile delivery latency

### Dashboard 2: Delivery Performance

**Panels**:

1. **Delivery Attempts**
   - Query: `rate(webhook_delivery_attempts_total[5m])`
   - Type: Graph

2. **Success vs Failure**
   - Queries:
     - Success: `rate(webhook_delivery_success_total[5m])`
     - Failure: `rate(webhook_delivery_failure_total[5m])`
   - Type: Graph (stacked)

3. **Latency Percentiles**
   - Queries:
     - P50: `histogram_quantile(0.50, rate(webhook_delivery_duration_seconds_bucket[5m]))`
     - P95: `histogram_quantile(0.95, rate(webhook_delivery_duration_seconds_bucket[5m]))`
     - P99: `histogram_quantile(0.99, rate(webhook_delivery_duration_seconds_bucket[5m]))`
   - Type: Graph

4. **Retry Distribution**
   - Query: `sum by (attempt_number) (rate(webhook_delivery_attempts_total[5m]))`
   - Type: Bar chart

### Dashboard 3: Per-Tenant Metrics

**Panels**:

1. **Events by Tenant**
   - Query: `sum by (tenant_id) (rate(webhook_events_published_total[5m]))`
   - Type: Table

2. **Rate Limit Hits**
   - Query: `topk(10, sum by (tenant_id) (rate(webhook_rate_limit_hits_total[5m])))`
   - Type: Bar chart

3. **Events by Type**
   - Query: `sum by (event_type) (rate(webhook_events_published_total[5m]))`
   - Type: Pie chart

---

## Alerts

### Alert Rules

Create `alerts.yml` for Prometheus:

```yaml
groups:
  - name: webhook_platform
    interval: 30s
    rules:
      # High failure rate
      - alert: HighDeliveryFailureRate
        expr: |
          (rate(webhook_delivery_failure_total[5m]) / rate(webhook_delivery_attempts_total[5m])) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High webhook delivery failure rate"
          description: "Delivery failure rate is {{ $value | humanizePercentage }} (threshold: 10%)"
      
      # DLQ growing
      - alert: DLQGrowing
        expr: |
          deriv(webhook_dlq_size[10m]) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Dead Letter Queue is growing"
          description: "DLQ is growing at {{ $value }} entries per minute"
      
      # High latency
      - alert: HighDeliveryLatency
        expr: |
          histogram_quantile(0.95, rate(webhook_delivery_duration_seconds_bucket[5m])) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High webhook delivery latency"
          description: "P95 latency is {{ $value }}s (threshold: 5s)"
      
      # Rate limit abuse
      - alert: HighRateLimitHits
        expr: |
          rate(webhook_rate_limit_hits_total[5m]) > 1
        for: 5m
        labels:
          severity: info
        annotations:
          summary: "High rate limit hits"
          description: "Tenant {{ $labels.tenant_id }} is hitting rate limits frequently"
      
      # No events
      - alert: NoEventsPublished
        expr: |
          rate(webhook_events_published_total[10m]) == 0
        for: 30m
        labels:
          severity: info
        annotations:
          summary: "No events published"
          description: "No events have been published in the last 30 minutes"
      
      # Worker down
      - alert: NoDeliveryAttempts
        expr: |
          rate(webhook_delivery_attempts_total[5m]) == 0
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "No delivery attempts"
          description: "Workers may be down - no delivery attempts in 10 minutes"
```

### Alert Configuration

Add to `prometheus.yml`:

```yaml
rule_files:
  - "alerts.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']
```

---

## Logging

### Log Format

All logs are structured JSON:

```json
{
  "asctime": "2024-01-01T00:00:00.000Z",
  "name": "app.workers.delivery_worker",
  "levelname": "INFO",
  "message": "Webhook delivered successfully",
  "event_id": 123,
  "tenant_id": 1,
  "duration_ms": 245,
  "http_status": 200
}
```

### Log Levels

- **DEBUG**: Detailed debugging information
- **INFO**: General informational messages
- **WARNING**: Warning messages (e.g., retries)
- **ERROR**: Error messages (e.g., delivery failures)
- **CRITICAL**: Critical errors (e.g., system failures)

### Viewing Logs

```bash
# All logs
docker-compose logs -f

# API logs
docker-compose logs -f api

# Worker logs
docker-compose logs -f worker

# Filter by level
docker-compose logs api | grep ERROR

# JSON parsing with jq
docker-compose logs api --no-log-prefix | jq 'select(.levelname == "ERROR")'
```

### Log Aggregation

For production, use centralized logging:

**ELK Stack**:
```yaml
# docker-compose.yml
  filebeat:
    image: docker.elastic.co/beats/filebeat:8.0.0
    volumes:
      - ./filebeat.yml:/usr/share/filebeat/filebeat.yml
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
```

**Loki**:
```yaml
  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
```

---

## Troubleshooting

### Common Monitoring Issues

#### 1. Metrics Not Appearing

**Check**:
```bash
# Verify metrics endpoint
curl http://localhost:8000/metrics

# Check Prometheus targets
# Visit: http://localhost:9090/targets
```

**Solution**:
- Ensure API is running
- Verify Prometheus scrape configuration
- Check network connectivity

#### 2. Grafana Dashboard Empty

**Check**:
- Prometheus data source configured
- Time range is appropriate
- Queries are correct

**Solution**:
```bash
# Test Prometheus query
curl 'http://localhost:9090/api/v1/query?query=webhook_events_published_total'
```

#### 3. High Memory Usage

**Monitor**:
```promql
# Prometheus memory
process_resident_memory_bytes{job="webhook-platform"}

# Container memory
container_memory_usage_bytes{name="webhook-api"}
```

---

## Best Practices

1. **Set Up Alerts**: Configure alerts for critical metrics
2. **Monitor Trends**: Track metrics over time to identify patterns
3. **Regular Reviews**: Review dashboards weekly
4. **Capacity Planning**: Monitor resource usage for scaling decisions
5. **Incident Response**: Use metrics to diagnose issues quickly
6. **Documentation**: Document custom metrics and dashboards

---

## Useful Queries

### Event Analysis

```promql
# Top event types
topk(10, sum by (event_type) (webhook_events_published_total))

# Events per tenant
sum by (tenant_id) (rate(webhook_events_published_total[1h]))

# Hourly event volume
sum(increase(webhook_events_published_total[1h]))
```

### Performance Analysis

```promql
# Slow deliveries (> 5s)
sum(rate(webhook_delivery_duration_seconds_bucket{le="5"}[5m])) / sum(rate(webhook_delivery_duration_seconds_count[5m]))

# Average attempts per event
rate(webhook_delivery_attempts_total[5m]) / rate(webhook_events_published_total[5m])
```

### Reliability Analysis

```promql
# Uptime percentage
avg_over_time(up{job="webhook-platform"}[24h]) * 100

# Error rate
rate(webhook_delivery_failure_total[5m]) / rate(webhook_delivery_attempts_total[5m])
```

---

## Grafana Dashboard JSON

See `monitoring/grafana/dashboards/webhook-platform.json` for the complete dashboard configuration.

To import:
1. Open Grafana (http://localhost:3000)
2. Go to Dashboards → Import
3. Upload the JSON file
4. Select Prometheus data source
5. Click Import
