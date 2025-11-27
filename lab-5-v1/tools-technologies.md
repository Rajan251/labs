## 9. Tools & Technologies

### 9.1 Tool Stack Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    DR TOOL ECOSYSTEM                             │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Infrastructure as Code                                  │   │
│  │  • Terraform • Pulumi • CloudFormation                   │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Configuration Management                                │   │
│  │  • Ansible • Chef • Puppet                               │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Backup & Recovery                                       │   │
│  │  • Velero • Restic • AWS Backup • Azure Backup           │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Migration & Replication                                 │   │
│  │  • CloudEndure • Rclone • AWS DMS • Azure Migrate        │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Monitoring & Observability                              │   │
│  │  • Prometheus • Grafana • Datadog • New Relic            │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Secrets Management                                      │   │
│  │  • HashiCorp Vault • AWS Secrets Manager • Azure KV      │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Orchestration & Automation                              │   │
│  │  • Kubernetes • Jenkins • GitLab CI • GitHub Actions     │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 9.2 Infrastructure as Code (Terraform)

**Why Terraform for Multi-Cloud DR:**
- **Multi-cloud support**: Single tool for AWS, Azure, GCP
- **State management**: Track infrastructure across clouds
- **Modularity**: Reusable modules for DR components
- **Plan/Apply workflow**: Preview changes before execution

**Project Structure:**

```
terraform/
├── environments/
│   ├── production/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── terraform.tfvars
│   └── staging/
│       └── ...
├── modules/
│   ├── aws/
│   │   ├── networking/
│   │   ├── compute/
│   │   ├── database/
│   │   └── storage/
│   ├── azure/
│   │   └── ...
│   ├── gcp/
│   │   └── ...
│   └── dr/
│       ├── failover/
│       ├── replication/
│       └── monitoring/
├── global/
│   ├── dns/
│   ├── iam/
│   └── secrets/
└── README.md
```

**Example Multi-Cloud Module:**

```hcl
# modules/dr/multi-cloud-database/main.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# AWS RDS Primary
resource "aws_db_instance" "primary" {
  provider = aws.primary

  identifier     = "${var.app_name}-primary"
  engine         = "postgres"
  engine_version = "14.9"
  instance_class = var.primary_instance_class

  allocated_storage     = var.storage_size
  storage_encrypted     = true
  kms_key_id            = var.kms_key_id
  
  multi_az              = true
  backup_retention_period = 7
  
  vpc_security_group_ids = var.security_group_ids
  db_subnet_group_name   = var.db_subnet_group_name

  tags = merge(var.tags, {
    DR_Role = "primary"
    DR_Tier = var.dr_tier
  })
}

# AWS RDS Read Replica (Secondary Region)
resource "aws_db_instance" "secondary" {
  provider = aws.secondary

  identifier             = "${var.app_name}-secondary"
  replicate_source_db    = aws_db_instance.primary.arn
  instance_class         = var.secondary_instance_class
  
  storage_encrypted      = true
  kms_key_id             = var.secondary_kms_key_id
  
  backup_retention_period = 7

  tags = merge(var.tags, {
    DR_Role = "secondary"
    DR_Tier = var.dr_tier
  })
}

# Azure SQL Database (Tertiary)
resource "azurerm_mssql_server" "tertiary" {
  provider = azurerm

  name                         = "${var.app_name}-tertiary"
  resource_group_name          = var.azure_resource_group
  location                     = var.azure_location
  version                      = "12.0"
  administrator_login          = var.admin_username
  administrator_login_password = var.admin_password

  tags = merge(var.tags, {
    DR_Role = "tertiary"
    DR_Tier = var.dr_tier
  })
}

resource "azurerm_mssql_database" "tertiary" {
  provider = azurerm

  name      = var.database_name
  server_id = azurerm_mssql_server.tertiary.id
  sku_name  = var.azure_sku

  geo_backup_enabled = true
  
  tags = var.tags
}

# Outputs for application configuration
output "primary_endpoint" {
  value = aws_db_instance.primary.endpoint
}

output "secondary_endpoint" {
  value = aws_db_instance.secondary.endpoint
}

output "tertiary_endpoint" {
  value = azurerm_mssql_server.tertiary.fully_qualified_domain_name
}
```

### 9.3 Kubernetes Backup with Velero

**Installation:**

```bash
# Install Velero CLI
wget https://github.com/vmware-tanzu/velero/releases/download/v1.12.0/velero-v1.12.0-linux-amd64.tar.gz
tar -xvf velero-v1.12.0-linux-amd64.tar.gz
sudo mv velero-v1.12.0-linux-amd64/velero /usr/local/bin/

# Install Velero on AWS EKS
velero install \
  --provider aws \
  --plugins velero/velero-plugin-for-aws:v1.8.0 \
  --bucket velero-backups-us-east-1 \
  --backup-location-config region=us-east-1 \
  --snapshot-location-config region=us-east-1 \
  --secret-file ./credentials-velero \
  --use-volume-snapshots=true \
  --use-node-agent

# Install on Azure AKS
velero install \
  --provider azure \
  --plugins velero/velero-plugin-for-microsoft-azure:v1.8.0 \
  --bucket velero-backups \
  --secret-file ./credentials-velero \
  --backup-location-config resourceGroup=velero-rg,storageAccount=velerobackups \
  --snapshot-location-config apiTimeout=5m,resourceGroup=velero-rg

# Install on GCP GKE
velero install \
  --provider gcp \
  --plugins velero/velero-plugin-for-gcp:v1.8.0 \
  --bucket velero-backups-gcp \
  --secret-file ./credentials-velero \
  --backup-location-config serviceAccount=velero@PROJECT_ID.iam.gserviceaccount.com
```

**Backup Configuration:**

```yaml
# velero/backup-schedule.yaml
apiVersion: velero.io/v1
kind: Schedule
metadata:
  name: production-backup
  namespace: velero
spec:
  schedule: "0 */6 * * *"  # Every 6 hours
  template:
    includedNamespaces:
    - production
    - monitoring
    - ingress-nginx
    
    excludedResources:
    - events
    - events.events.k8s.io
    
    storageLocation: default
    volumeSnapshotLocations:
    - default
    
    ttl: 720h  # 30 days
    
    hooks:
      resources:
      - name: postgres-backup-hook
        includedNamespaces:
        - production
        labelSelector:
          matchLabels:
            app: postgres
        pre:
        - exec:
            container: postgres
            command:
            - /bin/bash
            - -c
            - pg_dump -U postgres proddb > /tmp/backup.sql
        post:
        - exec:
            container: postgres
            command:
            - /bin/bash
            - -c
            - rm /tmp/backup.sql
```

**Cross-Cloud Restore:**

```bash
# Backup from AWS EKS
velero backup create eks-to-aks-backup \
  --include-namespaces production \
  --wait

# Download backup to local
velero backup download eks-to-aks-backup

# Configure Velero for AKS cluster
kubectl config use-context aks-cluster

# Restore to AKS
velero restore create --from-backup eks-to-aks-backup \
  --namespace-mappings production:production-azure \
  --wait

# Verify restore
kubectl get pods -n production-azure
```

### 9.4 CloudEndure for Live Migration

**Setup CloudEndure:**

```bash
# Install CloudEndure agent on source servers
wget -O ./installer_linux.py https://console.cloudendure.com/installer_linux.py
sudo python3 ./installer_linux.py \
  --token YOUR_CLOUDENDURE_TOKEN \
  --project YOUR_PROJECT_NAME \
  --no-prompt

# Configure replication settings via API
curl -X POST https://console.cloudendure.com/api/latest/projects/PROJECT_ID/replicationConfigurations \
  -H "Content-Type: application/json" \
  -H "X-XSRF-TOKEN: YOUR_TOKEN" \
  -d '{
    "volumeEncryptionKey": "arn:aws:kms:us-west-2:ACCOUNT_ID:key/xxxxx",
    "replicationServerInstanceType": "c5.large",
    "subnetId": "subnet-xxxxx",
    "replicationTags": [
      {"key": "DR", "value": "true"},
      {"key": "Environment", "value": "production"}
    ]
  }'

# Launch test instance
curl -X POST https://console.cloudendure.com/api/latest/projects/PROJECT_ID/launchMachines \
  -H "Content-Type: application/json" \
  -H "X-XSRF-TOKEN: YOUR_TOKEN" \
  -d '{
    "items": ["MACHINE_ID"],
    "launchType": "TEST"
  }'

# Perform cutover
curl -X POST https://console.cloudendure.com/api/latest/projects/PROJECT_ID/launchMachines \
  -H "Content-Type: application/json" \
  -H "X-XSRF-TOKEN: YOUR_TOKEN" \
  -d '{
    "items": ["MACHINE_ID"],
    "launchType": "CUTOVER"
  }'
```

### 9.5 Monitoring with Prometheus & Grafana

**Prometheus Configuration for Multi-Cloud:**

```yaml
# prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'multi-cloud-dr'
    environment: 'production'

# Alertmanager configuration
alerting:
  alertmanagers:
  - static_configs:
    - targets:
      - alertmanager:9093

# Load rules
rule_files:
  - "alerts/*.yml"

# Scrape configurations
scrape_configs:
  # AWS EKS
  - job_name: 'kubernetes-aws'
    kubernetes_sd_configs:
    - role: pod
      api_server: 'https://eks-cluster-us-east-1.amazonaws.com'
      bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
    relabel_configs:
    - source_labels: [__meta_kubernetes_pod_label_app]
      target_label: app
    - source_labels: [__meta_kubernetes_namespace]
      target_label: namespace
    - replacement: 'aws'
      target_label: cloud_provider

  # Azure AKS
  - job_name: 'kubernetes-azure'
    kubernetes_sd_configs:
    - role: pod
      api_server: 'https://aks-cluster-eastus.azure.com'
      bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
    relabel_configs:
    - source_labels: [__meta_kubernetes_pod_label_app]
      target_label: app
    - source_labels: [__meta_kubernetes_namespace]
      target_label: namespace
    - replacement: 'azure'
      target_label: cloud_provider

  # GCP GKE
  - job_name: 'kubernetes-gcp'
    kubernetes_sd_configs:
    - role: pod
      api_server: 'https://gke-cluster-us-central1.googleapis.com'
      bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
    relabel_configs:
    - source_labels: [__meta_kubernetes_pod_label_app]
      target_label: app
    - source_labels: [__meta_kubernetes_namespace]
      target_label: namespace
    - replacement: 'gcp'
      target_label: cloud_provider

  # CloudWatch Exporter (AWS)
  - job_name: 'cloudwatch'
    static_configs:
    - targets: ['cloudwatch-exporter:9106']
    relabel_configs:
    - replacement: 'aws'
      target_label: cloud_provider

  # Azure Monitor Exporter
  - job_name: 'azure-monitor'
    static_configs:
    - targets: ['azure-monitor-exporter:9276']
    relabel_configs:
    - replacement: 'azure'
      target_label: cloud_provider

  # Stackdriver Exporter (GCP)
  - job_name: 'stackdriver'
    static_configs:
    - targets: ['stackdriver-exporter:9255']
    relabel_configs:
    - replacement: 'gcp'
      target_label: cloud_provider
```

**DR-Specific Alerts:**

```yaml
# prometheus/alerts/dr-alerts.yml
groups:
- name: dr_alerts
  interval: 30s
  rules:
  
  # Replication lag alert
  - alert: HighReplicationLag
    expr: pg_replication_lag_seconds > 300
    for: 5m
    labels:
      severity: critical
      component: database
    annotations:
      summary: "High replication lag detected"
      description: "Database replication lag is {{ $value }}s (threshold: 300s)"
  
  # Cross-region sync failure
  - alert: CrossRegionSyncFailure
    expr: rate(s3_replication_errors_total[5m]) > 0
    for: 10m
    labels:
      severity: high
      component: storage
    annotations:
      summary: "S3 cross-region replication failing"
      description: "S3 replication errors detected in the last 10 minutes"
  
  # Health check failures
  - alert: PrimaryRegionDown
    expr: up{job="kubernetes-aws",namespace="production"} == 0
    for: 3m
    labels:
      severity: critical
      component: compute
    annotations:
      summary: "Primary region appears down"
      description: "AWS primary region health checks failing for 3 minutes"
  
  # Backup failures
  - alert: BackupFailed
    expr: velero_backup_failure_total > 0
    for: 1m
    labels:
      severity: high
      component: backup
    annotations:
      summary: "Velero backup failed"
      description: "Kubernetes backup failed. Check Velero logs."
  
  # Cost anomaly
  - alert: UnexpectedCostIncrease
    expr: (aws_cost_total - aws_cost_total offset 24h) / aws_cost_total offset 24h > 0.5
    for: 1h
    labels:
      severity: warning
      component: cost
    annotations:
      summary: "Unexpected cost increase"
      description: "AWS costs increased by {{ $value | humanizePercentage }} in the last 24 hours"
```

**Grafana Dashboard:**

```json
{
  "dashboard": {
    "title": "Multi-Cloud DR Dashboard",
    "panels": [
      {
        "id": 1,
        "title": "Regional Health Status",
        "type": "stat",
        "targets": [{
          "expr": "up{job=~\"kubernetes-.*\"}"
        }],
        "fieldConfig": {
          "defaults": {
            "thresholds": {
              "steps": [
                {"value": 0, "color": "red"},
                {"value": 1, "color": "green"}
              ]
            }
          }
        }
      },
      {
        "id": 2,
        "title": "Replication Lag",
        "type": "graph",
        "targets": [{
          "expr": "pg_replication_lag_seconds",
          "legendFormat": "{{instance}}"
        }]
      },
      {
        "id": 3,
        "title": "Failover Readiness Score",
        "type": "gauge",
        "targets": [{
          "expr": "(sum(up{job=\"kubernetes-aws\"}) / count(up{job=\"kubernetes-aws\"}) + sum(up{job=\"kubernetes-azure\"}) / count(up{job=\"kubernetes-azure\"})) / 2 * 100"
        }],
        "fieldConfig": {
          "defaults": {
            "min": 0,
            "max": 100,
            "thresholds": {
              "steps": [
                {"value": 0, "color": "red"},
                {"value": 70, "color": "yellow"},
                {"value": 90, "color": "green"}
              ]
            }
          }
        }
      },
      {
        "id": 4,
        "title": "Cross-Cloud Data Transfer",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(s3_bytes_transferred_total[5m])",
            "legendFormat": "AWS S3"
          },
          {
            "expr": "rate(azure_blob_bytes_transferred_total[5m])",
            "legendFormat": "Azure Blob"
          },
          {
            "expr": "rate(gcs_bytes_transferred_total[5m])",
            "legendFormat": "GCP GCS"
          }
        ]
      },
      {
        "id": 5,
        "title": "RTO/RPO Compliance",
        "type": "table",
        "targets": [{
          "expr": "dr_rto_compliance",
          "format": "table"
        }]
      }
    ]
  }
}
```

### 9.6 Ansible for Configuration Management

**Playbook for DR Failover:**

```yaml
# ansible/playbooks/dr-failover.yml
---
- name: Execute DR Failover
  hosts: localhost
  gather_facts: no
  vars:
    source_region: "us-east-1"
    target_region: "us-west-2"
    
  tasks:
    - name: Send failover start notification
      slack:
        token: "{{ slack_token }}"
        msg: "🚨 DR Failover initiated from {{ source_region }} to {{ target_region }}"
        channel: "#dr-alerts"
    
    - name: Promote RDS read replica
      command: >
        aws rds promote-read-replica
        --db-instance-identifier prod-db-replica-{{ target_region }}
        --region {{ target_region }}
      register: rds_promotion
    
    - name: Wait for RDS promotion
      command: >
        aws rds wait db-instance-available
        --db-instance-identifier prod-db-replica-{{ target_region }}
        --region {{ target_region }}
    
    - name: Update DNS records
      route53:
        state: present
        zone: example.com
        record: api.example.com
        type: CNAME
        ttl: 60
        value: "{{ target_lb_dns }}"
        overwrite: yes
    
    - name: Scale up Auto Scaling Groups
      ec2_asg:
        name: "prod-asg-{{ item }}-{{ target_region }}"
        region: "{{ target_region }}"
        desired_capacity: "{{ item.capacity }}"
      loop:
        - { name: "web", capacity: 10 }
        - { name: "app", capacity: 15 }
    
    - name: Update application configuration
      aws_ssm_parameter_store:
        name: "/prod/database/primary-endpoint"
        value: "prod-db-replica-{{ target_region }}.xxxxx.rds.amazonaws.com"
        region: "{{ target_region }}"
        overwrite: yes
    
    - name: Restart Kubernetes deployments
      k8s:
        state: present
        definition:
          apiVersion: apps/v1
          kind: Deployment
          metadata:
            name: "{{ item }}"
            namespace: production
          spec:
            template:
              metadata:
                annotations:
                  kubectl.kubernetes.io/restartedAt: "{{ ansible_date_time.iso8601 }}"
      loop:
        - api-server
        - web-server
    
    - name: Run health checks
      uri:
        url: "https://api.example.com/health"
        method: GET
        status_code: 200
      register: health_check
      until: health_check.status == 200
      retries: 20
      delay: 10
    
    - name: Send failover complete notification
      slack:
        token: "{{ slack_token }}"
        msg: "✅ DR Failover completed successfully to {{ target_region }}"
        channel: "#dr-alerts"
```

### 9.7 Tool Comparison Matrix

| Category | Tool | AWS | Azure | GCP | Pros | Cons | Best For |
|----------|------|-----|-------|-----|------|------|----------|
| **IaC** |
| | Terraform | ✅ | ✅ | ✅ | Multi-cloud, large community | State management complexity | Multi-cloud DR |
| | Pulumi | ✅ | ✅ | ✅ | Real programming languages | Smaller community | Developer-friendly IaC |
| | CloudFormation | ✅ | ❌ | ❌ | Native AWS integration | AWS-only | AWS-only deployments |
| **Backup** |
| | Velero | ✅ | ✅ | ✅ | K8s-native, cross-cloud | K8s-only | Kubernetes workloads |
| | Restic | ✅ | ✅ | ✅ | Lightweight, encrypted | Manual setup | File-level backups |
| | AWS Backup | ✅ | ❌ | ❌ | Managed service | AWS-only | AWS resources |
| **Migration** |
| | CloudEndure | ✅ | ✅ | ❌ | Live migration, minimal downtime | Cost | Large-scale migrations |
| | AWS DMS | ✅ | Partial | Partial | Managed, continuous replication | AWS-centric | Database migrations |
| | Rclone | ✅ | ✅ | ✅ | Free, versatile | Manual configuration | Storage sync |
| **Monitoring** |
| | Prometheus | ✅ | ✅ | ✅ | Open-source, powerful | Self-managed | Metrics collection |
| | Datadog | ✅ | ✅ | ✅ | Unified platform, easy setup | Cost | Enterprise monitoring |
| | Grafana | ✅ | ✅ | ✅ | Beautiful dashboards | Requires data source | Visualization |
| **Secrets** |
| | Vault | ✅ | ✅ | ✅ | Multi-cloud, dynamic secrets | Operational complexity | Centralized secrets |
| | AWS Secrets Manager | ✅ | ❌ | ❌ | Managed, integrated | AWS-only | AWS workloads |
| | Azure Key Vault | ❌ | ✅ | ❌ | Managed, HSM support | Azure-only | Azure workloads |

### 9.8 Recommended Tool Stack

**For Small Organizations (<50 servers):**
- **IaC**: Terraform
- **Backup**: Velero + Restic
- **Monitoring**: Prometheus + Grafana
- **Secrets**: AWS Secrets Manager + Azure Key Vault
- **Automation**: Ansible

**For Medium Organizations (50-500 servers):**
- **IaC**: Terraform + Terragrunt
- **Backup**: Velero + AWS Backup + Azure Backup
- **Monitoring**: Prometheus + Grafana + Datadog
- **Secrets**: HashiCorp Vault
- **Automation**: Ansible + Jenkins
- **Migration**: CloudEndure

**For Large Enterprises (>500 servers):**
- **IaC**: Terraform Enterprise
- **Backup**: Velero + Veeam + Cloud-native backups
- **Monitoring**: Datadog + Splunk
- **Secrets**: HashiCorp Vault Enterprise
- **Automation**: Ansible Tower + GitLab CI/CD
- **Migration**: CloudEndure + AWS DMS
- **Compliance**: Prisma Cloud + Aqua Security

