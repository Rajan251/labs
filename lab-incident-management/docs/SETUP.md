# Setup Guide - Incident Management & Alerting System

This guide will walk you through setting up the incident management and alerting system from scratch.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Docker** (version 20.10+)
- **Docker Compose** (version 2.0+)
- **Git**
- **Python 3.9+** (for incident API, Phase 4)
- **kubectl** (if deploying to Kubernetes)
- **Helm** (if using Helm charts)

### Optional Tools

- **promtool** - For validating Prometheus configurations
- **curl** - For testing endpoints
- **jq** - For JSON processing

## Quick Start (Local Development)

### 1. Clone and Setup

```bash
# Navigate to the project directory
cd /home/rk/Documents/labs/lab-incident-management

# Run setup script
./scripts/setup.sh
```

The setup script will:
- Check prerequisites
- Create `.env` file from template
- Create necessary directories
- Validate Prometheus and alert configurations

### 2. Configure Credentials

Edit the `.env` file with your actual credentials:

```bash
nano .env
```

**Required configurations:**
- `SLACK_WEBHOOK_URL` - Your Slack incoming webhook URL
- `PAGERDUTY_SERVICE_KEY` - Your PagerDuty integration key
- `POSTGRES_PASSWORD` - Database password (change from default)

**Optional configurations:**
- SMTP settings for email notifications
- Jira/GitHub tokens for postmortem integration

### 3. Update Alertmanager Configuration

Edit `monitoring/alertmanager/config.yml`:

```bash
nano monitoring/alertmanager/config.yml
```

Replace placeholders:
- `YOUR_PAGERDUTY_SERVICE_KEY` with your actual PagerDuty service key
- `YOUR/SLACK/WEBHOOK` with your Slack webhook path

### 4. Deploy Monitoring Stack

```bash
# Deploy all services
./scripts/deploy_monitoring.sh
```

This will:
- Pull Docker images
- Start all services
- Verify health checks

### 5. Access Services

Once deployed, access the following:

| Service | URL | Credentials |
|---------|-----|-------------|
| **Prometheus** | http://localhost:9090 | None |
| **Grafana** | http://localhost:3000 | admin / admin |
| **Alertmanager** | http://localhost:9093 | None |
| **Node Exporter** | http://localhost:9100 | None |
| **cAdvisor** | http://localhost:8080 | None |

### 6. Verify Setup

```bash
# Test alert flow
./scripts/test_alerts.sh
```

Check:
1. Alert appears in Alertmanager UI
2. Notification sent to Slack (if configured)
3. PagerDuty incident created (if configured)

---

## Detailed Setup Instructions

### Slack Integration

#### 1. Create Slack App

1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. Name: "Incident Management Bot"
4. Select your workspace

#### 2. Configure Incoming Webhooks

1. In your app settings, go to "Incoming Webhooks"
2. Activate incoming webhooks
3. Click "Add New Webhook to Workspace"
4. Select channel (e.g., `#alerts-critical`)
5. Copy the webhook URL

#### 3. Create Multiple Webhooks

Create separate webhooks for:
- `#alerts-critical` - Critical alerts
- `#alerts-warnings` - Warning alerts
- `#database-alerts` - Database team
- `#platform-alerts` - Platform team
- `#backend-alerts` - Backend team

#### 4. Update Configuration

Add webhook URLs to `monitoring/alertmanager/config.yml`:

```yaml
slack_configs:
  - channel: '#alerts-critical'
    api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
```

### PagerDuty Integration

#### 1. Create Service in PagerDuty

1. Log in to PagerDuty
2. Go to **Services** → **Service Directory**
3. Click **New Service**
4. Name: "Production Incidents"
5. Escalation Policy: Select or create
6. Integration: **Prometheus**

#### 2. Get Integration Key

1. In your service, go to **Integrations**
2. Find the Prometheus integration
3. Copy the **Integration Key**

#### 3. Update Configuration

Add to `monitoring/alertmanager/config.yml`:

```yaml
pagerduty_configs:
  - service_key: 'YOUR_INTEGRATION_KEY_HERE'
```

And to `.env`:

```bash
PAGERDUTY_SERVICE_KEY=YOUR_INTEGRATION_KEY_HERE
```

### Grafana Setup

#### 1. First Login

1. Navigate to http://localhost:3000
2. Login with `admin` / `admin`
3. Change password when prompted

#### 2. Verify Datasource

1. Go to **Configuration** → **Data Sources**
2. Verify "Prometheus" datasource exists
3. Click "Test" to verify connection

#### 3. Import Dashboards

Dashboards are auto-provisioned from `monitoring/grafana/dashboards/`.

To manually import:
1. Go to **Dashboards** → **Import**
2. Upload JSON file or paste JSON
3. Select Prometheus datasource

### PostgreSQL Setup

The database is automatically created by Docker Compose.

#### Connect to Database

```bash
docker-compose exec postgres psql -U incident_user -d incidents
```

#### Run Migrations (Phase 4)

```bash
cd incident-api
alembic upgrade head
```

### Redis Setup

Redis is automatically configured. No additional setup required.

#### Verify Redis

```bash
docker-compose exec redis redis-cli ping
# Should return: PONG
```

---

## Configuration Files

### Prometheus Configuration

**File:** `monitoring/prometheus/prometheus.yml`

Key sections:
- `global`: Scrape intervals and external labels
- `alerting`: Alertmanager endpoints
- `rule_files`: Alert and recording rules
- `scrape_configs`: Targets to scrape

### Alert Rules

**Location:** `monitoring/prometheus/alerts/`

Files:
- `service_availability.yaml` - Service uptime alerts
- `error_rate.yaml` - Error rate and SLO alerts
- `latency.yaml` - Latency threshold alerts
- `infrastructure.yaml` - Node and container alerts
- `database.yaml` - PostgreSQL and Redis alerts

### Alertmanager Configuration

**File:** `monitoring/alertmanager/config.yml`

Key sections:
- `route`: Routing tree for alerts
- `receivers`: Notification destinations
- `inhibit_rules`: Alert suppression logic

---

## Validation

### Validate Prometheus Config

```bash
promtool check config monitoring/prometheus/prometheus.yml
```

### Validate Alert Rules

```bash
promtool check rules monitoring/prometheus/alerts/*.yaml
promtool check rules monitoring/prometheus/recording_rules.yaml
```

### Test Alert Rules

```bash
promtool test rules tests/alert_test_cases.yaml
```

---

## Troubleshooting

### Services Not Starting

```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs <service-name>

# Restart specific service
docker-compose restart <service-name>
```

### Prometheus Not Scraping Targets

1. Check Prometheus targets: http://localhost:9090/targets
2. Verify service is running: `docker-compose ps`
3. Check network connectivity: `docker-compose exec prometheus ping <service-name>`

### Alerts Not Firing

1. Check alert rules: http://localhost:9090/alerts
2. Verify Alertmanager connection: http://localhost:9090/config
3. Check Alertmanager logs: `docker-compose logs alertmanager`

### Grafana Dashboards Not Loading

1. Check datasource: **Configuration** → **Data Sources**
2. Verify Prometheus URL: `http://prometheus:9090`
3. Check provisioning logs: `docker-compose logs grafana`

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres psql -U incident_user -d incidents -c "SELECT 1;"
```

---

## Maintenance

### Backup Configuration

```bash
# Backup Prometheus data
docker-compose exec prometheus tar czf /tmp/prometheus-backup.tar.gz /prometheus

# Copy to host
docker cp prometheus:/tmp/prometheus-backup.tar.gz ./backups/

# Backup Grafana dashboards
docker-compose exec grafana tar czf /tmp/grafana-backup.tar.gz /var/lib/grafana

# Copy to host
docker cp grafana:/tmp/grafana-backup.tar.gz ./backups/
```

### Update Services

```bash
# Pull latest images
docker-compose pull

# Restart services
docker-compose up -d
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f prometheus

# Last 100 lines
docker-compose logs --tail=100 prometheus
```

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v
```

---

## Next Steps

After completing the basic setup:

1. **Phase 3:** Deploy Alertmanager with notification routing ✅
2. **Phase 4:** Build Incident API (FastAPI service)
3. **Phase 5:** Create Slack Bot for ChatOps
4. **Phase 6:** Implement automation and runbooks
5. **Phase 7:** Add postmortem automation

See [Implementation Plan](../implementation_plan.md) for details.

---

## Additional Resources

- [Architecture Documentation](ARCHITECTURE.md)
- [Operations Guide](OPERATIONS.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [Runbook Templates](../runbooks/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Alertmanager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)

---

## Support

For issues or questions:
- **Slack:** #incident-management
- **Email:** sre-team@example.com
- **Documentation:** [Project README](../README.md)
