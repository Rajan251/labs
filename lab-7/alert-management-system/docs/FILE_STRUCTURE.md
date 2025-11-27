# Alert Management System - File Structure Explanation

## 📁 Complete Directory Structure

```
alert-management-system/
├── README.md                                    # Main documentation
├── docker/
│   ├── docker-compose.yml                      # Container orchestration
│   ├── .env.example                            # Environment template
│   └── .env                                    # Your configuration (gitignored)
├── prometheus/
│   ├── prometheus.yml                          # Main Prometheus config
│   ├── blackbox.yml                            # Blackbox exporter config
│   ├── rules/
│   │   ├── node_alerts.yml                    # System-level alerts
│   │   ├── application_alerts.yml             # Application alerts
│   │   └── custom_alerts.yml                  # Your custom alerts
│   └── targets/
│       └── targets.json                       # Service discovery
├── alertmanager/
│   ├── alertmanager.yml                       # Alertmanager config
│   └── templates/
│       ├── email.tmpl                         # Email templates
│       ├── slack.tmpl                         # Slack templates
│       └── pagerduty.tmpl                     # PagerDuty templates
├── pagerduty/
│   └── integration-guide.md                   # PagerDuty setup guide
├── scripts/
│   ├── setup.sh                               # Initial setup
│   ├── test-alerts.sh                         # Test alert routing
│   ├── health-check.sh                        # System health check
│   └── backup.sh                              # Backup configurations
├── docs/
│   ├── TROUBLESHOOTING.md                     # Common issues
│   ├── EXECUTION_GUIDE.md                     # Step-by-step guide
│   └── FILE_STRUCTURE.md                      # This file
└── examples/
    └── (sample applications and scenarios)
```

---

## 📄 File Descriptions

### Root Level

#### `README.md`
**Purpose**: Main entry point for documentation

**Contains**:
- Project overview and architecture
- Quick start guide
- Detailed implementation steps
- Troubleshooting basics
- Best practices

**When to use**: First file to read when starting with the project

---

### Docker Directory (`docker/`)

#### `docker-compose.yml`
**Purpose**: Orchestrates all monitoring services

**Contains**:
- Service definitions (Prometheus, Alertmanager, exporters)
- Port mappings
- Volume mounts
- Network configuration
- Health checks
- Environment variable references

**Key sections**:
```yaml
services:
  prometheus:        # Metrics collection
  alertmanager:      # Alert routing
  node-exporter:     # System metrics
  blackbox-exporter: # Endpoint monitoring
```

**When to modify**:
- Adding new exporters
- Changing ports
- Adjusting resource limits
- Adding new services

---

#### `.env.example`
**Purpose**: Template for environment variables

**Contains**:
- PagerDuty integration key placeholder
- Slack webhook URL placeholder
- SMTP configuration placeholders
- Other configurable values

**How to use**:
1. Copy to `.env`
2. Fill in actual values
3. Never commit `.env` to version control

---

#### `.env`
**Purpose**: Your actual configuration (created from `.env.example`)

**Contains**:
- Real PagerDuty integration key
- Real Slack webhook URL
- Real SMTP credentials
- Other sensitive data

**Security**: This file is gitignored and should never be committed

---

### Prometheus Directory (`prometheus/`)

#### `prometheus.yml`
**Purpose**: Main Prometheus configuration

**Contains**:
- Global settings (scrape interval, evaluation interval)
- Alertmanager endpoints
- Scrape configurations (what to monitor)
- Rule file locations
- Service discovery settings

**Key sections**:
```yaml
global:              # Global settings
alerting:            # Alertmanager config
rule_files:          # Alert rules
scrape_configs:      # What to scrape
```

**When to modify**:
- Adding new scrape targets
- Changing scrape intervals
- Adding new exporters
- Configuring service discovery

---

#### `blackbox.yml`
**Purpose**: Blackbox Exporter configuration

**Contains**:
- HTTP probe modules
- TCP probe modules
- ICMP probe modules
- DNS probe modules

**When to modify**:
- Adding custom probe types
- Changing probe timeouts
- Adding SSL verification

---

#### `rules/node_alerts.yml`
**Purpose**: System-level alert rules

**Contains**:
- CPU usage alerts
- Memory usage alerts
- Disk space alerts
- Network alerts
- System load alerts

**Alert structure**:
```yaml
- alert: AlertName
  expr: PromQL expression
  for: duration
  labels:
    severity: critical/warning/info
  annotations:
    summary: Brief description
    description: Detailed description
```

**When to modify**:
- Adjusting thresholds (e.g., CPU > 80%)
- Changing alert durations
- Adding new system metrics
- Customizing annotations

---

#### `rules/application_alerts.yml`
**Purpose**: Application-level alert rules

**Contains**:
- HTTP endpoint alerts
- Error rate alerts
- Latency alerts
- Prometheus/Alertmanager health alerts

**When to modify**:
- Adding application-specific alerts
- Monitoring new endpoints
- Adjusting error thresholds

---

#### `rules/custom_alerts.yml`
**Purpose**: Your custom alert rules

**Contains**:
- Template examples
- Commented-out sample alerts
- Organization-specific alerts

**When to use**:
- Adding business metric alerts
- Database-specific alerts
- Custom application alerts

---

#### `targets/targets.json`
**Purpose**: File-based service discovery

**Format**:
```json
[
  {
    "targets": ["host:port"],
    "labels": {
      "job": "service-name",
      "env": "production"
    }
  }
]
```

**When to modify**:
- Adding new scrape targets dynamically
- Changing target labels
- Removing old targets

---

### Alertmanager Directory (`alertmanager/`)

#### `alertmanager.yml`
**Purpose**: Alert routing and notification configuration

**Contains**:
- Global settings (SMTP, PagerDuty, Slack)
- Routing rules (where alerts go)
- Receiver definitions (how to notify)
- Inhibition rules (suppress related alerts)
- Template references

**Key sections**:
```yaml
global:          # SMTP, API URLs
templates:       # Template files
route:           # Routing logic
receivers:       # Notification channels
inhibit_rules:   # Alert suppression
```

**When to modify**:
- Adding new notification channels
- Changing routing logic
- Adjusting grouping behavior
- Adding inhibition rules

---

#### `templates/email.tmpl`
**Purpose**: Email notification templates

**Contains**:
- HTML email template
- Plain text email template
- Template functions and variables

**Template variables**:
- `{{ .Status }}` - firing/resolved
- `{{ .GroupLabels }}` - Alert group labels
- `{{ .CommonLabels }}` - Common labels
- `{{ .CommonAnnotations }}` - Common annotations
- `{{ .Alerts.Firing }}` - Firing alerts
- `{{ .Alerts.Resolved }}` - Resolved alerts

**When to modify**:
- Customizing email appearance
- Adding/removing information
- Changing formatting

---

#### `templates/slack.tmpl`
**Purpose**: Slack notification templates

**Contains**:
- Slack message formatting
- Emoji usage
- Markdown formatting

**When to modify**:
- Changing message format
- Adding/removing fields
- Customizing appearance

---

#### `templates/pagerduty.tmpl`
**Purpose**: PagerDuty notification templates

**Contains**:
- Incident description template
- Custom details template

**When to modify**:
- Customizing incident details
- Adding custom fields

---

### PagerDuty Directory (`pagerduty/`)

#### `integration-guide.md`
**Purpose**: Complete PagerDuty setup guide

**Contains**:
- Step-by-step PagerDuty setup
- Integration key retrieval
- Advanced configuration
- Troubleshooting

**When to use**: Setting up PagerDuty for the first time

---

### Scripts Directory (`scripts/`)

#### `setup.sh`
**Purpose**: Initial system setup

**What it does**:
1. Checks prerequisites (Docker, Docker Compose)
2. Creates necessary directories
3. Copies `.env.example` to `.env`
4. Validates configurations
5. Provides next steps

**When to run**: First time setup

---

#### `test-alerts.sh`
**Purpose**: Test alert routing

**What it does**:
1. Sends test alerts to Alertmanager
2. Tests critical, warning, and info severity levels
3. Verifies routing to different receivers

**When to run**:
- After initial setup
- After configuration changes
- To verify PagerDuty integration

---

#### `health-check.sh`
**Purpose**: System health verification

**What it does**:
1. Checks Docker containers are running
2. Checks service endpoints are accessible
3. Checks Prometheus targets are UP
4. Reports overall health status

**When to run**:
- Daily monitoring
- After deployments
- Troubleshooting issues

---

#### `backup.sh`
**Purpose**: Backup configurations and data

**What it does**:
1. Backs up configuration files
2. Backs up Prometheus data
3. Backs up Alertmanager data
4. Creates timestamped archives

**When to run**:
- Before major changes
- Scheduled backups (daily/weekly)
- Before upgrades

---

### Docs Directory (`docs/`)

#### `TROUBLESHOOTING.md`
**Purpose**: Common issues and solutions

**Contains**:
- Service startup issues
- Configuration errors
- Alert routing problems
- PagerDuty integration issues
- Performance problems
- Debugging commands

**When to use**: When encountering problems

---

#### `EXECUTION_GUIDE.md`
**Purpose**: Complete deployment walkthrough

**Contains**:
- Step-by-step commands
- Detailed explanations
- Expected outputs
- Verification steps
- Production considerations

**When to use**: Deploying the system from scratch

---

#### `FILE_STRUCTURE.md`
**Purpose**: This file - explains the project structure

**When to use**: Understanding the project organization

---

## 🔄 Typical Workflow

### Initial Setup
1. Read `README.md`
2. Follow `docs/EXECUTION_GUIDE.md`
3. Run `scripts/setup.sh`
4. Configure `docker/.env`
5. Start with `docker-compose up -d`
6. Test with `scripts/test-alerts.sh`

### Daily Operations
1. Check health: `scripts/health-check.sh`
2. View logs: `docker-compose logs -f`
3. Monitor alerts: Visit Prometheus/Alertmanager UIs

### Making Changes
1. Edit configuration files
2. Validate changes
3. Reload services (no restart needed)
4. Test changes

### Troubleshooting
1. Check `docs/TROUBLESHOOTING.md`
2. View logs
3. Run health check
4. Verify configurations

---

## 📝 Configuration Files Priority

When Prometheus/Alertmanager starts, they read files in this order:

### Prometheus
1. `prometheus/prometheus.yml` - Main config
2. `prometheus/rules/*.yml` - Alert rules
3. `prometheus/targets/*.json` - Service discovery

### Alertmanager
1. `alertmanager/alertmanager.yml` - Main config
2. `alertmanager/templates/*.tmpl` - Templates
3. Environment variables from `.env`

---

## 🔒 Security Considerations

### Files to Keep Secure
- `docker/.env` - Contains secrets
- Backup files - May contain sensitive data

### Files Safe to Share
- All `.yml` configuration files (after removing secrets)
- Documentation files
- Scripts (after review)

### Best Practices
1. Never commit `.env` to version control
2. Use environment variables for secrets
3. Rotate PagerDuty integration keys regularly
4. Limit file permissions on sensitive files

---

## 📊 File Modification Frequency

| File | Frequency | Reason |
|------|-----------|--------|
| `prometheus.yml` | Occasional | Add new scrape targets |
| `alertmanager.yml` | Rare | Change routing logic |
| `rules/*.yml` | Frequent | Adjust thresholds, add alerts |
| `.env` | Rare | Update credentials |
| `docker-compose.yml` | Rare | Add services, change ports |
| Templates | Rare | Customize notifications |

---

**Last Updated**: 2025-11-27
