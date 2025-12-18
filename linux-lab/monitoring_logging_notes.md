# Monitoring & Logging Strategy for Enterprise

**Level:** Expert / SRE / DevOps
**Focus:** Observability, alerting, and troubleshooting at scale.

---

## 1. Logging Architecture

### 1.1 Centralized vs Distributed
*   **Centralized (ELK, Splunk)**: All logs flow to a single cluster. Easy to search across all services. Single point of failure.
*   **Distributed (Loki, Grafana Cloud)**: Logs stay closer to source. Better for multi-region. Harder to correlate.

### 1.2 Log Shipping Patterns
*   **Agent-Based** (Filebeat, Fluentd): Agent on each host reads log files and forwards.
    *   *Pros*: Buffering, retries, filtering at source.
    *   *Cons*: Resource overhead on every host.
*   **Direct Shipping** (Syslog, HTTP): Application sends logs directly to collector.
    *   *Pros*: No agent to manage.
    *   *Cons*: Network failures = lost logs (unless app buffers).

### 1.3 Structured Logging
```json
{
  "timestamp": "2025-12-18T22:00:00Z",
  "level": "ERROR",
  "service": "payment-api",
  "hostname": "web-01",
  "request_id": "abc123",
  "message": "Payment gateway timeout",
  "duration_ms": 5000
}
```
*   **Benefits**: Queryable fields, no regex parsing, context enrichment.

---

## 2. Monitoring Pyramid

Focus on what matters to users, not just infrastructure.

```
    Business Metrics (Revenue, Conversions)
         ↓
    Application Metrics (Latency, Errors, Throughput)
         ↓
    System Metrics (CPU, Memory, Disk)
         ↓
    Infrastructure Metrics (Hardware Health)
```

*   **Top-Down Approach**: Start with business impact. If revenue drops, drill down to find the technical cause.

---

## 3. Alerting Philosophy

### 3.1 Symptom-Based vs Cause-Based
*   **Symptom**: "Users cannot login" (Alert on 5xx errors on `/login`).
*   **Cause**: "CPU is at 90%" (Don't alert unless it impacts users).
*   **Rule**: Alert on symptoms. Investigate causes.

### 3.2 Severity Classification
| Severity | Action | Example |
| :--- | :--- | :--- |
| **Page** | Wake someone up | Production down, data loss |
| **Ticket** | Fix next business day | Disk 80% full, minor degradation |
| **Log** | FYI, no action | Informational events |

### 3.3 Alert Fatigue Prevention
*   **Aggregate**: Don't send 100 alerts for 100 failed requests. Send one: "Error rate >10%".
*   **Deduplicate**: If same alert fires 5 times in 1 minute, send once.
*   **Silence**: During maintenance windows.
*   **Runbooks**: Every alert must link to a runbook: "What to do when you get this alert".

---

## 4. Key Performance Indicators (KPIs)

### 4.1 Availability
*   **Uptime**: % of time service is available. SLA: 99.9% = 43 minutes downtime/month.
*   **MTTR** (Mean Time To Repair): How fast you fix issues.
*   **MTBF** (Mean Time Between Failures): How often failures occur.

### 4.2 Performance
*   **Latency**: p50 (median), p95, p99 (tail latency). Focus on p99 (worst user experience).
*   **Throughput**: Requests per second.

### 4.3 Capacity
*   **Utilization Trends**: Is disk growing 10GB/day? When will it fill?
*   **Growth Rate**: User signups increasing 20%/month? Scale proactively.

---

## 5. Tool Selection

### 5.1 Metrics: Prometheus vs Nagios
| Feature | **Prometheus** | **Nagios** |
| :--- | :--- | :--- |
| **Model** | Pull (scrapes targets) | Push (agents report) |
| **Query** | PromQL (powerful) | Limited |
| **Scalability** | Excellent (federation) | Poor (single server) |
| **Use Case** | Cloud-native, Kubernetes | Legacy infrastructure |

### 5.2 Logs: ELK vs Loki
| Feature | **ELK Stack** | **Loki** |
| :--- | :--- | :--- |
| **Indexing** | Full-text (expensive) | Labels only (cheap) |
| **Storage** | High (Elasticsearch) | Low (object storage) |
| **Query** | Lucene (complex) | LogQL (simple) |
| **Use Case** | Deep log analysis | Cost-effective aggregation |

### 5.3 Visualization: Grafana
*   **Universal**: Works with Prometheus, Loki, Elasticsearch, InfluxDB.
*   **Dashboards**: Pre-built for common stacks (Node Exporter, MySQL).

---

## 6. Troubleshooting with Logs

### 6.1 Pattern Recognition
*   **Spike Detection**: Error rate suddenly 10x normal.
*   **Anomaly Detection**: ML-based (Elasticsearch Anomaly Detection).

### 6.2 Correlation
*   **Request Tracing**: Follow a single request across microservices (Jaeger, Zipkin).
*   **Timeline**: "At 14:00, deployment happened. At 14:05, errors spiked."

### 6.3 Statistical Analysis
*   **Top N**: "Top 10 error messages in last hour."
*   **Grouping**: Count errors by `service`, `hostname`, `error_code`.

---

## 7. Implementation Patterns

### 7.1 Microservices
*   **Service Mesh** (Istio, Linkerd): Automatic metrics (request rate, latency) for every service.
*   **Distributed Tracing**: Jaeger. Track request through 10 microservices.
*   **Log Correlation**: Use `request_id` in all logs.

### 7.2 Databases
*   **Replication Lag**: Alert if replica is >10s behind master.
*   **Query Performance**: Slow query log analysis.
*   **Connection Pool**: Monitor active vs max connections.

### 7.3 Network Infrastructure
*   **SNMP**: Monitor switches, routers (bandwidth, errors).
*   **Flow Data** (NetFlow, sFlow): Traffic analysis.
