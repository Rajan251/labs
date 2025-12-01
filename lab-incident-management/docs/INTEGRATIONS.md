# Integration Guide - Tools & Platforms

This document lists all the tools and platforms you can integrate with the incident management and alerting system.

## Table of Contents
1. [Notification & Communication](#notification--communication)
2. [Incident Management & On-Call](#incident-management--on-call)
3. [Ticketing & Project Management](#ticketing--project-management)
4. [Monitoring & Observability](#monitoring--observability)
5. [Log Management](#log-management)
6. [APM & Tracing](#apm--tracing)
7. [Cloud Providers](#cloud-providers)
8. [CI/CD & Deployment](#cicd--deployment)
9. [Database Monitoring](#database-monitoring)
10. [Security & Compliance](#security--compliance)
11. [ChatOps & Automation](#chatops--automation)
12. [Status Pages](#status-pages)

---

## Notification & Communication

### 1. **Slack** ✅ (Already Configured)
**What it does:** Team communication and alert notifications

**Integration:**
- Incoming webhooks for alerts
- Slack Bot for ChatOps commands
- Interactive buttons and modals
- Channel-based routing

**Setup:**
```yaml
# In alertmanager/config.yml
slack_configs:
  - channel: '#alerts-critical'
    api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
    username: 'Alertmanager'
    icon_emoji: ':rotating_light:'
```

**Features:**
- ✅ Real-time alert notifications
- ✅ Incident management commands
- ✅ Runbook execution
- ✅ Status updates

---

### 2. **Microsoft Teams**
**What it does:** Enterprise team communication

**Integration:**
```yaml
# In alertmanager/config.yml
webhook_configs:
  - url: 'https://outlook.office.com/webhook/YOUR-WEBHOOK-URL'
    send_resolved: true
```

**Features:**
- Alert cards with action buttons
- Channel-based routing
- Integration with Office 365

---

### 3. **Discord**
**What it does:** Community and team chat

**Integration:**
```yaml
webhook_configs:
  - url: 'https://discord.com/api/webhooks/YOUR/WEBHOOK'
```

**Features:**
- Rich embeds for alerts
- Role mentions
- Channel organization

---

### 4. **Telegram**
**What it does:** Mobile-first messaging

**Integration:**
```python
# Python bot integration
import telegram
bot = telegram.Bot(token='YOUR_BOT_TOKEN')
bot.send_message(chat_id='CHAT_ID', text='Alert: Service Down')
```

**Features:**
- Fast mobile notifications
- Bot commands
- Group chats

---

### 5. **Email** ✅ (Already Configured)
**What it does:** Traditional email notifications

**Integration:**
```yaml
email_configs:
  - to: 'sre-team@example.com'
    from: 'alertmanager@example.com'
    smarthost: 'smtp.gmail.com:587'
    auth_username: 'alertmanager@example.com'
    auth_password: 'YOUR_PASSWORD'
```

**Features:**
- Fallback notification
- Detailed alert information
- Attachment support

---

### 6. **SMS (Twilio)**
**What it does:** Text message alerts

**Integration:**
```python
from twilio.rest import Client

client = Client('ACCOUNT_SID', 'AUTH_TOKEN')
message = client.messages.create(
    body='CRITICAL: Service Down',
    from_='+1234567890',
    to='+0987654321'
)
```

**Features:**
- Critical alerts via SMS
- Global reach
- High reliability

---

## Incident Management & On-Call

### 7. **PagerDuty** ✅ (Already Configured)
**What it does:** On-call management and incident response

**Integration:**
```yaml
pagerduty_configs:
  - service_key: 'YOUR_INTEGRATION_KEY'
    description: '{{ .GroupLabels.alertname }}'
```

**Features:**
- ✅ On-call scheduling
- ✅ Escalation policies
- ✅ Incident timeline
- ✅ Mobile app
- ✅ Phone calls for critical alerts

**API Integration:**
```python
import requests

headers = {
    'Authorization': f'Token token={PAGERDUTY_API_KEY}',
    'Content-Type': 'application/json'
}

incident = {
    'incident': {
        'type': 'incident',
        'title': 'High Error Rate',
        'service': {'id': 'SERVICE_ID', 'type': 'service_reference'},
        'urgency': 'high'
    }
}

response = requests.post(
    'https://api.pagerduty.com/incidents',
    headers=headers,
    json=incident
)
```

---

### 8. **OpsGenie**
**What it does:** Alternative to PagerDuty for on-call management

**Integration:**
```yaml
opsgenie_configs:
  - api_key: 'YOUR_API_KEY'
    message: '{{ .GroupLabels.alertname }}'
    priority: 'P1'
```

**Features:**
- On-call rotations
- Escalation rules
- Mobile app
- Alert enrichment

---

### 9. **VictorOps (Splunk On-Call)**
**What it does:** Incident management platform

**Integration:**
```yaml
victorops_configs:
  - api_key: 'YOUR_API_KEY'
    routing_key: 'YOUR_ROUTING_KEY'
```

**Features:**
- Timeline view
- Collaboration tools
- Post-incident reviews

---

## Ticketing & Project Management

### 10. **Jira**
**What it does:** Issue tracking and project management

**Integration:**
```python
from jira import JIRA

jira = JIRA(
    server='https://your-company.atlassian.net',
    basic_auth=('email@example.com', 'API_TOKEN')
)

issue = jira.create_issue(
    project='INC',
    summary='High Error Rate - Payment API',
    description='Error rate spiked to 15%',
    issuetype={'name': 'Incident'}
)
```

**Features:**
- Auto-create tickets from alerts
- Link incidents to tickets
- Track action items
- Generate reports

**Webhook Integration:**
```yaml
webhook_configs:
  - url: 'https://your-incident-api.com/webhooks/jira'
    send_resolved: true
```

---

### 11. **GitHub Issues**
**What it does:** Issue tracking integrated with code

**Integration:**
```python
from github import Github

g = Github('YOUR_ACCESS_TOKEN')
repo = g.get_repo('your-org/your-repo')

issue = repo.create_issue(
    title='Incident: High Error Rate',
    body='## Incident Details\n\nError rate: 15%\nStarted: 2025-12-01 10:00',
    labels=['incident', 'P1']
)
```

**Features:**
- Link incidents to code
- Track postmortem action items
- Integration with PRs

---

### 12. **Linear**
**What it does:** Modern issue tracking

**Integration:**
```graphql
mutation CreateIncident {
  issueCreate(input: {
    title: "High Error Rate"
    description: "Error rate spiked to 15%"
    teamId: "TEAM_ID"
    priority: 1
  }) {
    issue {
      id
      title
    }
  }
}
```

**Features:**
- Fast and modern UI
- Keyboard shortcuts
- Automatic workflows

---

### 13. **ServiceNow**
**What it does:** Enterprise IT service management

**Integration:**
```python
import requests

headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

incident = {
    'short_description': 'High Error Rate',
    'urgency': '1',
    'impact': '1'
}

response = requests.post(
    'https://instance.service-now.com/api/now/table/incident',
    auth=('admin', 'password'),
    headers=headers,
    json=incident
)
```

**Features:**
- ITIL compliance
- Change management
- Asset tracking

---

## Monitoring & Observability

### 14. **Prometheus** ✅ (Already Configured)
**What it does:** Metrics collection and alerting

**Already Integrated:**
- ✅ Scraping metrics
- ✅ Alert rules
- ✅ Recording rules
- ✅ Service discovery

---

### 15. **Grafana** ✅ (Already Configured)
**What it does:** Metrics visualization

**Already Integrated:**
- ✅ Dashboards
- ✅ Alerts
- ✅ Datasources

---

### 16. **Datadog**
**What it does:** Full-stack observability platform

**Integration:**
```yaml
# Datadog Agent configuration
datadog:
  api_key: 'YOUR_API_KEY'
  site: 'datadoghq.com'
  
  # Prometheus integration
  prometheus:
    enabled: true
    url: 'http://prometheus:9090'
```

**Features:**
- APM (Application Performance Monitoring)
- Log management
- Infrastructure monitoring
- Synthetic monitoring
- Custom dashboards

---

### 17. **New Relic**
**What it does:** Application performance monitoring

**Integration:**
```yaml
# New Relic agent
newrelic:
  license_key: 'YOUR_LICENSE_KEY'
  app_name: 'My Application'
```

**Features:**
- Transaction tracing
- Error tracking
- Browser monitoring
- Mobile monitoring

---

### 18. **Dynatrace**
**What it does:** AI-powered observability

**Integration:**
```yaml
dynatrace:
  environment_id: 'YOUR_ENV_ID'
  api_token: 'YOUR_API_TOKEN'
```

**Features:**
- Automatic root cause analysis
- AI-powered anomaly detection
- Full-stack monitoring

---

### 19. **Thanos**
**What it does:** Long-term Prometheus storage

**Integration:**
```yaml
# Prometheus remote write
remote_write:
  - url: 'http://thanos-receive:19291/api/v1/receive'
```

**Features:**
- Unlimited retention
- Global query view
- Downsampling
- Deduplication

---

### 20. **Cortex**
**What it does:** Scalable Prometheus

**Integration:**
```yaml
remote_write:
  - url: 'http://cortex:9009/api/v1/push'
```

**Features:**
- Multi-tenancy
- Horizontal scalability
- Long-term storage

---

## Log Management

### 21. **Elasticsearch + Kibana (ELK Stack)**
**What it does:** Log aggregation and search

**Integration:**
```yaml
# Filebeat configuration
filebeat:
  inputs:
    - type: container
      paths:
        - '/var/lib/docker/containers/*/*.log'
  
  output:
    elasticsearch:
      hosts: ['elasticsearch:9200']
```

**Features:**
- Full-text search
- Log visualization
- Anomaly detection
- Machine learning

---

### 22. **Loki**
**What it does:** Log aggregation (Prometheus-style)

**Integration:**
```yaml
# Promtail configuration
clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: system
    static_configs:
      - targets:
          - localhost
        labels:
          job: varlogs
          __path__: /var/log/*log
```

**Features:**
- Label-based indexing
- Grafana integration
- Cost-effective
- LogQL query language

---

### 23. **Splunk**
**What it does:** Enterprise log management

**Integration:**
```yaml
# Splunk forwarder
[tcpout]
defaultGroup = splunk_indexers

[tcpout:splunk_indexers]
server = splunk-server:9997
```

**Features:**
- Advanced search
- Machine learning
- Security analytics
- Compliance reporting

---

### 24. **Graylog**
**What it does:** Open-source log management

**Integration:**
```yaml
# Graylog input
inputs:
  - type: gelf
    port: 12201
```

**Features:**
- Real-time search
- Alerting
- Dashboards
- Stream processing

---

## APM & Tracing

### 25. **Jaeger**
**What it does:** Distributed tracing

**Integration:**
```yaml
# Application instrumentation
jaeger:
  agent_host: jaeger-agent
  agent_port: 6831
  sampler:
    type: const
    param: 1
```

**Features:**
- Request tracing
- Service dependency graph
- Performance analysis
- Root cause analysis

---

### 26. **Zipkin**
**What it does:** Distributed tracing

**Integration:**
```python
from py_zipkin.zipkin import zipkin_span

@zipkin_span(service_name='my-service')
def my_function():
    # Your code here
    pass
```

**Features:**
- Trace visualization
- Dependency analysis
- Latency analysis

---

### 27. **Tempo**
**What it does:** Distributed tracing backend

**Integration:**
```yaml
# Grafana Tempo
tempo:
  receivers:
    jaeger:
      protocols:
        grpc:
          endpoint: 0.0.0.0:14250
```

**Features:**
- Cost-effective storage
- Grafana integration
- TraceQL query language

---

### 28. **OpenTelemetry**
**What it does:** Unified observability framework

**Integration:**
```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("my-operation"):
    # Your code here
    pass
```

**Features:**
- Vendor-neutral
- Metrics, traces, and logs
- Auto-instrumentation
- Multiple backend support

---

## Cloud Providers

### 29. **AWS CloudWatch**
**What it does:** AWS monitoring and logging

**Integration:**
```yaml
# CloudWatch exporter
cloudwatch_exporter:
  region: us-east-1
  metrics:
    - aws_namespace: AWS/EC2
      aws_metric_name: CPUUtilization
```

**Features:**
- EC2, RDS, Lambda monitoring
- Log aggregation
- Alarms
- Dashboards

---

### 30. **Google Cloud Monitoring (Stackdriver)**
**What it does:** GCP monitoring

**Integration:**
```yaml
# Stackdriver exporter
stackdriver:
  project_id: 'your-project-id'
  credentials_file: '/path/to/credentials.json'
```

**Features:**
- GKE, Compute Engine monitoring
- Log analytics
- Trace analysis
- Profiling

---

### 31. **Azure Monitor**
**What it does:** Azure monitoring

**Integration:**
```yaml
# Azure Monitor exporter
azure_monitor:
  subscription_id: 'YOUR_SUBSCRIPTION_ID'
  tenant_id: 'YOUR_TENANT_ID'
```

**Features:**
- VM, AKS monitoring
- Application Insights
- Log Analytics
- Alerts

---

## CI/CD & Deployment

### 32. **GitHub Actions**
**What it does:** CI/CD automation

**Integration:**
```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Notify deployment start
        run: |
          curl -X POST ${{ secrets.INCIDENT_API_URL }}/deployments \
            -H "Content-Type: application/json" \
            -d '{"service": "my-app", "version": "${{ github.sha }}"}'
```

**Features:**
- Deployment tracking
- Rollback automation
- Integration with incidents

---

### 33. **GitLab CI**
**What it does:** CI/CD platform

**Integration:**
```yaml
# .gitlab-ci.yml
deploy:
  script:
    - curl -X POST $INCIDENT_API_URL/deployments
```

**Features:**
- Pipeline visualization
- Deployment tracking
- Auto-rollback

---

### 34. **Jenkins**
**What it does:** Automation server

**Integration:**
```groovy
// Jenkinsfile
pipeline {
    agent any
    stages {
        stage('Deploy') {
            steps {
                sh 'curl -X POST $INCIDENT_API_URL/deployments'
            }
        }
    }
}
```

**Features:**
- Build tracking
- Deployment correlation
- Rollback automation

---

### 35. **ArgoCD**
**What it does:** GitOps continuous delivery

**Integration:**
```yaml
# ArgoCD notification
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-notifications-cm
data:
  service.webhook.incident-api: |
    url: http://incident-api:8000/webhooks/argocd
```

**Features:**
- Deployment tracking
- Sync status
- Rollback automation

---

## Database Monitoring

### 36. **PostgreSQL Exporter** ✅ (Already Configured)
**What it does:** PostgreSQL metrics

**Already Integrated:**
- ✅ Connection pool monitoring
- ✅ Query performance
- ✅ Replication lag

---

### 37. **MySQL Exporter**
**What it does:** MySQL metrics

**Integration:**
```yaml
# docker-compose.yml
mysql-exporter:
  image: prom/mysqld-exporter
  environment:
    - DATA_SOURCE_NAME=user:password@(mysql:3306)/
```

**Features:**
- Query performance
- Connection monitoring
- Replication status

---

### 38. **MongoDB Exporter**
**What it does:** MongoDB metrics

**Integration:**
```yaml
mongodb-exporter:
  image: percona/mongodb_exporter
  environment:
    - MONGODB_URI=mongodb://user:pass@mongodb:27017
```

**Features:**
- Collection stats
- Operation counters
- Replication lag

---

### 39. **Redis Exporter** ✅ (Already Configured)
**What it does:** Redis metrics

**Already Integrated:**
- ✅ Memory usage
- ✅ Command stats
- ✅ Key eviction

---

## Security & Compliance

### 40. **HashiCorp Vault**
**What it does:** Secrets management

**Integration:**
```yaml
# Vault configuration
vault:
  address: 'https://vault.example.com'
  token: 'YOUR_TOKEN'
  
  secrets:
    - path: 'secret/data/pagerduty'
      key: 'api_key'
```

**Features:**
- Secret rotation
- Dynamic secrets
- Encryption as a service
- Audit logging

---

### 41. **AWS Secrets Manager**
**What it does:** AWS secrets management

**Integration:**
```python
import boto3

client = boto3.client('secretsmanager')
secret = client.get_secret_value(SecretId='pagerduty-api-key')
```

**Features:**
- Automatic rotation
- IAM integration
- Encryption

---

### 42. **Sentry**
**What it does:** Error tracking and monitoring

**Integration:**
```python
import sentry_sdk

sentry_sdk.init(
    dsn="https://your-dsn@sentry.io/project-id",
    traces_sample_rate=1.0
)
```

**Features:**
- Error tracking
- Performance monitoring
- Release tracking
- User feedback

---

## ChatOps & Automation

### 43. **Slack Bot** (Planned - Phase 5)
**What it does:** ChatOps commands

**Integration:**
```python
from slack_bolt import App

app = App(token=SLACK_BOT_TOKEN)

@app.command("/incident")
def handle_incident_command(ack, command):
    ack()
    # Handle incident commands
```

**Features:**
- Incident management
- Runbook execution
- Status updates
- Approvals

---

### 44. **Hubot**
**What it does:** ChatOps bot framework

**Integration:**
```coffeescript
module.exports = (robot) ->
  robot.respond /incident list/i, (res) ->
    # List incidents
```

**Features:**
- Custom commands
- Multi-platform support
- Plugin ecosystem

---

### 45. **Ansible**
**What it does:** Automation platform

**Integration:**
```yaml
# Ansible playbook
- name: Restart service
  hosts: production
  tasks:
    - name: Restart application
      systemd:
        name: my-app
        state: restarted
```

**Features:**
- Auto-remediation
- Configuration management
- Orchestration

---

## Status Pages

### 46. **Statuspage.io**
**What it does:** Public status page

**Integration:**
```python
import requests

headers = {'Authorization': f'OAuth {API_KEY}'}
data = {
    'incident': {
        'name': 'High Error Rate',
        'status': 'investigating',
        'impact_override': 'major'
    }
}

requests.post(
    'https://api.statuspage.io/v1/pages/PAGE_ID/incidents',
    headers=headers,
    json=data
)
```

**Features:**
- Customer communication
- Incident updates
- Metrics display
- Subscriber notifications

---

### 47. **Cachet**
**What it does:** Open-source status page

**Integration:**
```python
import requests

data = {
    'name': 'Payment API',
    'status': 2,  # Performance Issues
    'message': 'Investigating high error rate'
}

requests.post(
    'https://status.example.com/api/v1/incidents',
    headers={'X-Cachet-Token': API_KEY},
    json=data
)
```

**Features:**
- Self-hosted
- Customizable
- Metrics integration

---

## Summary: Integration Matrix

| Category | Tool | Difficulty | Priority | Status |
|----------|------|------------|----------|--------|
| **Notifications** | Slack | Easy | High | ✅ Configured |
| | PagerDuty | Easy | High | ✅ Configured |
| | Email | Easy | Medium | ✅ Configured |
| | MS Teams | Easy | Medium | 📋 Planned |
| | SMS (Twilio) | Medium | Low | 📋 Planned |
| **Monitoring** | Prometheus | Easy | High | ✅ Configured |
| | Grafana | Easy | High | ✅ Configured |
| | Datadog | Medium | Medium | 📋 Optional |
| | New Relic | Medium | Medium | 📋 Optional |
| **Ticketing** | Jira | Medium | High | 📋 Phase 6 |
| | GitHub Issues | Easy | Medium | 📋 Phase 6 |
| | ServiceNow | Hard | Low | 📋 Optional |
| **Logs** | Loki | Easy | High | 📋 Phase 7 |
| | ELK Stack | Hard | Medium | 📋 Optional |
| **Tracing** | Jaeger | Medium | Medium | 📋 Phase 7 |
| | Tempo | Easy | Medium | 📋 Phase 7 |
| **ChatOps** | Slack Bot | Medium | High | 📋 Phase 5 |
| **Secrets** | Vault | Medium | High | 📋 Phase 7 |
| **Status** | Statuspage.io | Easy | Medium | 📋 Phase 7 |

---

## Quick Start Integration Examples

### Example 1: Add Jira Integration

```python
# incident-api/services/jira_service.py
from jira import JIRA

class JiraService:
    def __init__(self):
        self.jira = JIRA(
            server=os.getenv('JIRA_URL'),
            basic_auth=(
                os.getenv('JIRA_USER'),
                os.getenv('JIRA_API_TOKEN')
            )
        )
    
    def create_incident_ticket(self, incident):
        issue = self.jira.create_issue(
            project=os.getenv('JIRA_PROJECT_KEY'),
            summary=f"Incident: {incident.title}",
            description=incident.description,
            issuetype={'name': 'Incident'},
            priority={'name': incident.severity}
        )
        return issue.key
```

### Example 2: Add Datadog Integration

```yaml
# docker-compose.yml
datadog-agent:
  image: datadog/agent:latest
  environment:
    - DD_API_KEY=${DATADOG_API_KEY}
    - DD_SITE=datadoghq.com
    - DD_PROMETHEUS_SCRAPE_ENABLED=true
    - DD_PROMETHEUS_SCRAPE_URL=http://prometheus:9090
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock:ro
    - /proc/:/host/proc/:ro
    - /sys/fs/cgroup/:/host/sys/fs/cgroup:ro
```

### Example 3: Add Loki for Logs

```yaml
# docker-compose.yml
loki:
  image: grafana/loki:latest
  ports:
    - "3100:3100"
  volumes:
    - ./monitoring/loki/config.yml:/etc/loki/local-config.yaml

promtail:
  image: grafana/promtail:latest
  volumes:
    - /var/log:/var/log
    - ./monitoring/promtail/config.yml:/etc/promtail/config.yml
```

---

## Next Steps

1. **Phase 4-5**: Implement Slack Bot and Incident API
2. **Phase 6**: Add Jira/GitHub integration for tickets
3. **Phase 7**: Add Loki for logs, Jaeger for traces
4. **Optional**: Add Datadog, New Relic, or other APM tools

**For detailed integration guides, see:**
- [Slack Integration Guide](./integrations/SLACK.md)
- [PagerDuty Integration Guide](./integrations/PAGERDUTY.md)
- [Jira Integration Guide](./integrations/JIRA.md)
