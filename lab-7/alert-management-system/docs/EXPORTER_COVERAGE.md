# Comprehensive Exporter Coverage Guide

## 📊 Overview

This Alert Management System now includes **13 different exporters** covering all major infrastructure components, databases, web servers, containers, messaging systems, and search engines.

---

## 🔧 Exporters Included

### Infrastructure Exporters

| Exporter | Port | Purpose | Metrics |
|----------|------|---------|---------|
| **Node Exporter** | 9100 | System metrics | CPU, memory, disk, network |
| **Blackbox Exporter** | 9115 | Endpoint monitoring | HTTP, TCP, ICMP probes |
| **cAdvisor** | 8080 | Container metrics | Container CPU, memory, network |

### Database Exporters

| Exporter | Port | Purpose | Key Metrics |
|----------|------|---------|-------------|
| **MySQL Exporter** | 9104 | MySQL monitoring | Connections, queries, replication |
| **PostgreSQL Exporter** | 9187 | PostgreSQL monitoring | Connections, locks, replication |
| **Redis Exporter** | 9121 | Redis monitoring | Memory, keys, connections |
| **MongoDB Exporter** | 9216 | MongoDB monitoring | Connections, replication, operations |

### Web Server Exporters

| Exporter | Port | Purpose | Key Metrics |
|----------|------|---------|-------------|
| **Nginx Exporter** | 9113 | Nginx monitoring | Requests, connections, status codes |

### Messaging & Search Exporters

| Exporter | Port | Purpose | Key Metrics |
|----------|------|---------|-------------|
| **RabbitMQ Exporter** | 9419 | RabbitMQ monitoring | Queues, messages, connections |
| **Elasticsearch Exporter** | 9114 | Elasticsearch monitoring | Cluster health, indices, queries |

### Monitoring Exporters

| Exporter | Port | Purpose | Key Metrics |
|----------|------|---------|-------------|
| **Prometheus** | 9090 | Self-monitoring | Targets, rules, storage |
| **Alertmanager** | 9093 | Alert monitoring | Alerts, silences, notifications |

---

## 📋 Alert Rules Summary

### Total Alert Coverage

- **Total Alert Rules**: 90+
- **Alert Rule Files**: 6
- **Severity Levels**: Critical, Warning, Info

### Alert Rules by Category

| Category | File | Alert Count | Coverage |
|----------|------|-------------|----------|
| **System** | node_alerts.yml | 15+ | CPU, memory, disk, network |
| **Application** | application_alerts.yml | 12+ | HTTP, errors, latency |
| **Database** | database_alerts.yml | 30+ | MySQL, PostgreSQL, Redis, MongoDB |
| **Web/Container** | webserver_container_alerts.yml | 20+ | Nginx, Docker, containers |
| **Messaging/Search** | messaging_search_alerts.yml | 20+ | RabbitMQ, Elasticsearch |
| **Custom** | custom_alerts.yml | Templates | Your custom alerts |

---

## 🎯 Alert Examples by Exporter

### Node Exporter Alerts
- HighCPUUsage (>80%)
- CriticalCPUUsage (>95%)
- HighMemoryUsage (>80%)
- LowDiskSpace (<20%)
- InstanceDown
- NetworkErrors

### MySQL Exporter Alerts
- MySQLDown
- MySQLHighConnections (>80%)
- MySQLSlowQueries
- MySQLReplicationLag
- MySQLReplicationStopped

### PostgreSQL Exporter Alerts
- PostgreSQLDown
- PostgreSQLHighConnections (>80%)
- PostgreSQLReplicationLag
- PostgreSQLHighDeadTuples
- PostgreSQLLongRunningQueries

### Redis Exporter Alerts
- RedisDown
- RedisHighMemoryUsage (>90%)
- RedisHighFragmentation
- RedisRejectedConnections
- RedisReplicationBroken

### MongoDB Exporter Alerts
- MongoDBDown
- MongoDBHighConnections (>80%)
- MongoDBReplicationLag
- MongoDBReplicationHeadroomLow

### Nginx Exporter Alerts
- NginxDown
- NginxHighConnections
- NginxHigh4xxRate (>5%)
- NginxHigh5xxRate (>1%)

### cAdvisor Alerts
- ContainerHighCPU (>80%)
- ContainerHighMemory (>80%)
- ContainerMemoryAtLimit (>95%)
- ContainerRestarting
- ContainerFilesystemUsageHigh

### RabbitMQ Exporter Alerts
- RabbitMQDown
- RabbitMQMemoryAlarm
- RabbitMQDiskAlarm
- RabbitMQQueueMessagesPilingUp
- RabbitMQNoConsumers
- RabbitMQClusterPartition

### Elasticsearch Exporter Alerts
- ElasticsearchDown
- ElasticsearchClusterRed
- ElasticsearchClusterYellow
- ElasticsearchHighJVMMemory (>90%)
- ElasticsearchUnassignedShards
- ElasticsearchSlowQueries

---

## 🚀 Quick Start with All Exporters

### Option 1: Start Only Core Exporters (Recommended for Testing)

```bash
cd /home/rk/Documents/labs/lab-7/alert-management-system/docker

# Start core monitoring stack
docker-compose up -d prometheus alertmanager node-exporter blackbox-exporter
```

### Option 2: Start All Exporters (Requires Backend Services)

```bash
# Start everything
docker-compose up -d
```

> **Note**: Database, web server, and messaging exporters require their respective services (MySQL, PostgreSQL, Redis, etc.) to be running. If these services are not available, those exporters will show as DOWN in Prometheus, which is expected.

---

## 🔧 Configuring Exporters

### For Exporters WITHOUT Backend Services

If you don't have MySQL, PostgreSQL, etc. running, you can:

**Option 1: Comment out unused exporters**
```bash
# Edit docker-compose.yml
nano docker/docker-compose.yml

# Comment out services you don't need
```

**Option 2: Start only needed services**
```bash
# Start specific services
docker-compose up -d prometheus alertmanager node-exporter cadvisor
```

### For Exporters WITH Backend Services

Update the `.env` file with your service connection details:

```bash
# MySQL
MYSQL_EXPORTER_DSN=root:password@(mysql-host:3306)/

# PostgreSQL
POSTGRES_EXPORTER_DSN=postgresql://user:pass@postgres-host:5432/db

# Redis
REDIS_ADDR=redis-host:6379
REDIS_PASSWORD=your-password

# MongoDB
MONGODB_URI=mongodb://mongo-host:27017

# Nginx
NGINX_SCRAPE_URI=http://nginx-host:8080/stub_status

# RabbitMQ
RABBITMQ_URL=http://rabbitmq-host:15672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest

# Elasticsearch
ELASTICSEARCH_URI=http://elasticsearch-host:9200
```

---

## 📊 Viewing Metrics

### Prometheus Targets

```bash
# Open Prometheus UI
http://localhost:9090/targets
```

**What to check**:
- All enabled exporters should show as "UP"
- Exporters without backend services will show as "DOWN" (expected)

### Sample Queries

**Node Exporter**:
```promql
# CPU usage
100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Memory usage
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100
```

**MySQL Exporter**:
```promql
# Connection usage
(mysql_global_status_threads_connected / mysql_global_variables_max_connections) * 100

# Query rate
rate(mysql_global_status_queries[5m])
```

**Redis Exporter**:
```promql
# Memory usage
(redis_memory_used_bytes / redis_memory_max_bytes) * 100

# Connected clients
redis_connected_clients
```

**Container Metrics**:
```promql
# Container CPU
sum(rate(container_cpu_usage_seconds_total{container!=""}[5m])) by (name) * 100

# Container memory
container_memory_usage_bytes{container!=""}
```

---

## 🎯 Alert Testing

### Test Specific Exporter Alerts

```bash
# Send test alert for database
curl -X POST http://localhost:9093/api/v2/alerts \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "MySQLDown",
      "severity": "critical",
      "component": "database",
      "db_type": "mysql"
    },
    "annotations": {
      "summary": "TEST: MySQL database is down"
    }
  }]'
```

---

## 📈 Monitoring Best Practices

### 1. Start Small
Begin with core exporters (Node, Blackbox) and add others as needed.

### 2. Adjust Thresholds
Default thresholds may not fit your environment. Adjust in alert rule files:
```yaml
# Example: Increase CPU threshold
expr: cpu_usage > 90  # Changed from 80
```

### 3. Use Labels Effectively
All alerts include labels for routing:
- `severity`: critical, warning, info
- `component`: database, web-server, container, etc.
- `team`: infrastructure, backend, database, etc.

### 4. Monitor the Monitors
Set up external monitoring for Prometheus itself to ensure the monitoring system is always available.

---

## 🔍 Troubleshooting

### Exporter Shows as DOWN

**Check exporter logs**:
```bash
docker-compose logs mysql-exporter
docker-compose logs postgres-exporter
```

**Common issues**:
- Backend service not running
- Incorrect connection credentials in `.env`
- Network connectivity issues
- Firewall blocking connections

### No Metrics Appearing

**Verify scrape configuration**:
```bash
# Check Prometheus config
curl http://localhost:9090/api/v1/status/config | jq

# Check targets
curl http://localhost:9090/api/v1/targets | jq
```

### Alerts Not Firing

**Check alert rules**:
```bash
# View loaded rules
http://localhost:9090/rules

# Test PromQL query manually
http://localhost:9090/graph
```

---

## 📚 Additional Resources

- [Prometheus Exporters](https://prometheus.io/docs/instrumenting/exporters/)
- [MySQL Exporter](https://github.com/prometheus/mysqld_exporter)
- [PostgreSQL Exporter](https://github.com/prometheus-community/postgres_exporter)
- [Redis Exporter](https://github.com/oliver006/redis_exporter)
- [MongoDB Exporter](https://github.com/percona/mongodb_exporter)
- [Nginx Exporter](https://github.com/nginxinc/nginx-prometheus-exporter)
- [cAdvisor](https://github.com/google/cadvisor)
- [RabbitMQ Exporter](https://github.com/kbudde/rabbitmq_exporter)
- [Elasticsearch Exporter](https://github.com/prometheus-community/elasticsearch_exporter)

---

**Last Updated**: 2025-11-27  
**Total Exporters**: 13  
**Total Alert Rules**: 90+
