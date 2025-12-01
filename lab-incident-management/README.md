# Incident Management & Alerting System

A production-ready incident management and alerting platform with SLO-driven monitoring, automated remediation, intelligent notification routing, and comprehensive postmortem workflows.

## 🎯 Goals & Success Criteria

### Core Capabilities

- **Detect**: Meaningful alerts with low noise (SLO-driven where possible)
- **Notify**: Immediate, targeted notifications via Slack, email, SMS, and on-call (PagerDuty)
- **Act**: Automated runbook actions for common incidents (restart pod, scale, run diagnostics)
- **Track**: Create incident records with timeline, owners, and status
- **Review**: Automated postmortem templates and follow-up task creation
- **SLOs**: Define and monitor key SLOs for availability and latency

### Success Metrics

- ✅ **MTTD** (Mean Time to Detect) < 2 minutes
- ✅ **MTTA** (Mean Time to Acknowledge) < 5 minutes for P0/P1
- ✅ **MTTR** (Mean Time to Resolve) improvement by 30%
- ✅ **Alert Noise** < 5 false positives per week
- ✅ **Postmortem Completion** 100% within 72 hours
- ✅ **Auto-Remediation Success** > 80%

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Data Sources                             │
│  Applications • Kubernetes • Nodes • Databases               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Prometheus (Metrics Collection)                 │
│         + Thanos/Cortex (Long-term Storage)                  │
└────────────┬────────────────────────┬───────────────────────┘
             │                        │
             ▼                        ▼
┌────────────────────┐    ┌──────────────────────────┐
│  Alert Rules       │    │  Grafana Dashboards      │
│  (SLO-based)       │    │  (Visualization)         │
└────────┬───────────┘    └──────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Alertmanager                              │
│         (Routing, Grouping, Deduplication)                   │
└───┬─────────────┬─────────────┬──────────────┬──────────────┘
    │             │             │              │
    ▼             ▼             ▼              ▼
┌─────────┐ ┌─────────┐ ┌──────────┐ ┌────────────────────┐
│PagerDuty│ │  Slack  │ │Email/SMS │ │  Incident API      │
└─────────┘ └────┬────┘ └──────────┘ └─────┬──────────────┘
                 │                           │
                 ▼                           ▼
         ┌──────────────┐         ┌──────────────────────┐
         │  Slack Bot   │◄────────┤  PostgreSQL DB       │
         │  (ChatOps)   │         │  (Incident Data)     │
         └──────┬───────┘         └──────────────────────┘
                │
                ▼
    ┌──────────────────────────┐
    │  Automation & Runbooks   │
    │  (Auto-Remediation)      │
    └──────────────────────────┘
```

## 📁 Project Structure

```
lab-incident-management/
├── config/                          # Configuration files
│   ├── slo_definitions.yaml         # Service Level Objectives
│   ├── severity_matrix.yaml         # Incident severity classification
│   ├── on_call_schedule.yaml        # On-call rotation
│   └── service_catalog.yaml         # Service inventory
│
├── monitoring/                      # Monitoring stack configuration
│   ├── prometheus/
│   │   ├── prometheus.yml           # Main Prometheus config
│   │   ├── alerts/                  # Alert rule definitions
│   │   │   ├── service_availability.yaml
│   │   │   ├── error_rate.yaml
│   │   │   ├── latency.yaml
│   │   │   ├── infrastructure.yaml
│   │   │   └── database.yaml
│   │   └── recording_rules.yaml     # Pre-computed metrics
│   │
│   ├── alertmanager/
│   │   ├── config.yml               # Routing configuration
│   │   ├── templates/               # Notification templates
│   │   │   ├── slack.tmpl
│   │   │   └── pagerduty.tmpl
│   │   ├── silence_rules.yaml
│   │   └── inhibition_rules.yaml
│   │
│   └── grafana/
│       ├── dashboards/              # JSON dashboard definitions
│       │   ├── service_overview.json
│       │   ├── slo_tracking.json
│       │   ├── incident_metrics.json
│       │   └── alert_review.json
│       ├── datasources/
│       └── provisioning/
│
├── incident-api/                    # FastAPI incident service
│   ├── main.py                      # Application entry point
│   ├── models.py                    # Database models
│   ├── schemas.py                   # Pydantic schemas
│   ├── database.py                  # DB connection
│   ├── config.py                    # Configuration
│   ├── requirements.txt
│   ├── Dockerfile
│   │
│   ├── routers/                     # API routes
│   │   ├── incidents.py
│   │   ├── timeline.py
│   │   ├── webhooks.py
│   │   └── health.py
│   │
│   ├── services/                    # Business logic
│   │   ├── incident_service.py
│   │   ├── notification_service.py
│   │   ├── pagerduty_service.py
│   │   ├── slack_service.py
│   │   └── runbook_service.py
│   │
│   ├── migrations/                  # Alembic migrations
│   │   └── versions/
│   │
│   └── k8s/                         # Kubernetes manifests
│       ├── deployment.yaml
│       ├── service.yaml
│       ├── configmap.yaml
│       └── ingress.yaml
│
├── slack-bot/                       # Slack bot for ChatOps
│   ├── bot.py                       # Main bot application
│   ├── commands.py                  # Command implementations
│   ├── blocks.py                    # Slack Block Kit UI
│   ├── config.py
│   ├── requirements.txt
│   ├── Dockerfile
│   │
│   └── handlers/
│       ├── incident_commands.py
│       ├── runbook_commands.py
│       └── interactive_handlers.py
│
├── runbooks/                        # Runbook documentation
│   ├── template.md
│   ├── high_error_rate.md
│   ├── pod_crashloop.md
│   ├── high_latency.md
│   ├── database_slow.md
│   └── disk_pressure.md
│
├── automation/                      # Auto-remediation scripts
│   ├── restart_deployment.py
│   ├── scale_deployment.py
│   ├── clear_cache.py
│   ├── run_diagnostics.py
│   └── k8s-operator/               # Custom K8s operator
│
├── postmortem/                      # Postmortem automation
│   ├── generator.py
│   ├── templates/
│   ├── jira_integration.py
│   └── github_integration.py
│
├── analytics/                       # Metrics & reporting
│   ├── kpi_calculator.py
│   ├── alert_noise_analyzer.py
│   └── weekly_report.py
│
├── terraform/                       # Infrastructure as Code
│   ├── main.tf
│   ├── variables.tf
│   ├── kubernetes.tf
│   └── secrets.tf
│
├── helm/                            # Helm charts
│   ├── prometheus/
│   ├── grafana/
│   └── alertmanager/
│
├── scripts/                         # Setup & utility scripts
│   ├── setup.sh
│   ├── deploy_monitoring.sh
│   ├── deploy_incident_api.sh
│   └── test_alerts.sh
│
├── tests/                           # Test suites
│   ├── test_alert_rules.py
│   ├── test_incident_api.py
│   ├── test_notifications.py
│   └── integration/
│
├── docs/                            # Documentation
│   ├── ARCHITECTURE.md              # System architecture
│   ├── SETUP.md                     # Setup instructions
│   ├── OPERATIONS.md                # Operational procedures
│   ├── TROUBLESHOOTING.md           # Common issues
│   └── ADR/                         # Architecture decisions
│
├── .github/workflows/               # CI/CD pipelines
│   ├── ci.yml
│   ├── deploy_monitoring.yml
│   └── deploy_incident_api.yml
│
├── docker-compose.yml               # Local development setup
└── README.md                        # This file
```

## 🚀 Quick Start

### Prerequisites

- **Kubernetes cluster** (EKS/GKE/AKS) or Docker Compose for local dev
- **PagerDuty account** with API access
- **Slack workspace** with bot creation permissions
- **PostgreSQL** database (or use Docker Compose)
- **Terraform** (optional, for infrastructure provisioning)
- **Helm** (for Kubernetes deployments)

### Local Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd lab-incident-management

# Start local environment with Docker Compose
docker-compose up -d

# Access services
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000 (admin/admin)
# - Alertmanager: http://localhost:9093
# - Incident API: http://localhost:8000

# Run tests
pytest tests/ -v
```

### Production Deployment

See [docs/SETUP.md](docs/SETUP.md) for detailed setup instructions.

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 2. Deploy monitoring stack
./scripts/deploy_monitoring.sh

# 3. Deploy incident API
./scripts/deploy_incident_api.sh

# 4. Configure Slack bot
# Follow docs/SETUP.md for Slack app creation

# 5. Test alert flow
./scripts/test_alerts.sh
```

## 📊 Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Metrics** | Prometheus + Thanos | Time-series metrics collection & storage |
| **Logs** | Loki / OpenSearch | Log aggregation (optional) |
| **Tracing** | Jaeger / Tempo | Distributed tracing (optional) |
| **Dashboards** | Grafana | Visualization & analytics |
| **Alerting** | Alertmanager | Alert routing & deduplication |
| **On-call** | PagerDuty | On-call management & escalation |
| **ChatOps** | Slack Bot | Incident management via Slack |
| **Incident API** | FastAPI + PostgreSQL | Incident orchestration service |
| **Automation** | Python + K8s Operator | Auto-remediation scripts |
| **IaC** | Terraform + Helm | Infrastructure provisioning |
| **CI/CD** | GitHub Actions | Automated testing & deployment |
| **Secrets** | AWS Secrets Manager / Vault | Secrets management |

## 🔔 Alert Examples

### Service Availability
```yaml
alert: ServiceDown
expr: up{job="my-service"} == 0
for: 2m
labels:
  severity: page
annotations:
  summary: "Service {{ $labels.job }} is down"
  runbook_url: "https://runbooks.example.com/service-down"
```

### Error Rate
```yaml
alert: HighErrorRate
expr: |
  sum(rate(http_requests_total{status=~"5.."}[5m])) by (service)
  /
  sum(rate(http_requests_total[5m])) by (service)
  > 0.02
for: 5m
labels:
  severity: critical
```

### Latency
```yaml
alert: HighLatency
expr: |
  histogram_quantile(0.95,
    sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service)
  ) > 0.5
for: 5m
labels:
  severity: warning
```

## 🤖 Slack Bot Commands

```bash
# Incident management
/incident list                    # List active incidents
/incident show INC-123            # Show incident details
/incident ack INC-123             # Acknowledge incident
/incident assign INC-123 @user    # Assign to user
/incident resolve INC-123         # Resolve incident

# Runbook execution
/runbook list                     # List available runbooks
/runbook run high-error-rate      # Execute runbook
/runbook show high-error-rate     # Display runbook content
```

## 📈 Key Metrics & KPIs

The system tracks the following metrics:

- **MTTD** (Mean Time to Detect): Time from issue start to alert
- **MTTA** (Mean Time to Acknowledge): Time from alert to acknowledgment
- **MTTR** (Mean Time to Resolve): Time from alert to resolution
- **Alert Noise**: False positive rate
- **Auto-Remediation Success**: Percentage of successful automated fixes
- **SLO Compliance**: Percentage of time within SLO targets
- **Error Budget**: Remaining error budget per service

View these metrics in the [Incident Metrics Dashboard](http://localhost:3000/d/incident-metrics).

## 🔒 Security & Compliance

- **Authentication**: OAuth2 / OIDC (Okta/Google/GitHub)
- **Authorization**: Role-based access control (RBAC)
- **Secrets**: AWS Secrets Manager / HashiCorp Vault
- **Audit Logging**: All actions logged with user, timestamp, and details
- **Encryption**: TLS for all external communication
- **Least Privilege**: Service accounts with minimal required permissions

## 📚 Documentation

- [Architecture](docs/ARCHITECTURE.md) - System architecture and design
- [Setup Guide](docs/SETUP.md) - Detailed setup instructions
- [Operations](docs/OPERATIONS.md) - Day-to-day operational procedures
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions
- [ADRs](docs/ADR/) - Architecture decision records

## 🧪 Testing

```bash
# Unit tests
pytest tests/ -v

# Alert rule validation
promtool check rules monitoring/prometheus/alerts/*.yaml

# Integration tests
pytest tests/integration/ -v

# Fire drill (test alert)
./scripts/test_alerts.sh
```

## 📅 Implementation Timeline

- **Week 1**: Infrastructure setup, Prometheus, Grafana
- **Week 2**: Alert rules and Alertmanager configuration
- **Week 3-4**: Incident API and Slack bot development
- **Week 5**: Automation and runbooks
- **Week 6**: Postmortem automation
- **Week 7**: Testing, hardening, and documentation
- **Week 8**: Production deployment and handover

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Add tests
4. Submit a pull request

## 📄 License

[Your License Here]

## 📞 Support


- **Email**: rajankumar9354680@gmail.com


---

**Built with ❤️ by Rajan**
