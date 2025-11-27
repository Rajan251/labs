## 7. Cost Optimization Strategy

### 7.1 DR Cost Models Comparison

```
┌─────────────────────────────────────────────────────────────────┐
│                    DR Strategy Cost Comparison                   │
│                                                                  │
│  Monthly Cost                                                    │
│      ▲                                                           │
│      │                                                           │
│  $50K│     ┌────────┐                                            │
│      │     │Active- │                                            │
│  $40K│     │Active  │                                            │
│      │     │        │                                            │
│  $30K│     │        │   ┌────────┐                               │
│      │     │        │   │ Warm   │                               │
│  $20K│     │        │   │Standby │                               │
│      │     │        │   │        │                               │
│  $10K│     │        │   │        │  ┌────────┐  ┌────────┐      │
│      │     │        │   │        │  │ Pilot  │  │Backup &│      │
│   $0│     └────────┘   └────────┘  │ Light  │  │Restore │      │
│      └──────────────────────────────┴────────┴──┴────────┴────► │
│           RTO: 5min    RTO: 1hr    RTO: 4hr   RTO: 24hr         │
│           RPO: 0min    RPO: 15min  RPO: 4hr   RPO: 24hr         │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Cost Breakdown by Strategy

#### Active-Active (Tier 1)
**Monthly Cost: ~$45,000**

| Component | AWS | Azure | GCP | Total |
|-----------|-----|-------|-----|-------|
| Compute (EKS/AKS/GKE) | $8,000 | $7,500 | $7,000 | $22,500 |
| Database (RDS/SQL/CloudSQL) | $4,500 | $4,200 | $3,800 | $12,500 |
| Load Balancers | $800 | $750 | $700 | $2,250 |
| Storage (S3/Blob/GCS) | $1,200 | $1,100 | $1,000 | $3,300 |
| Data Transfer | $1,500 | $1,400 | $1,300 | $4,200 |
| **Total** | **$16,000** | **$14,950** | **$13,800** | **$44,750** |

**Cost Drivers:**
- Full infrastructure running 24/7 in all regions
- Synchronous replication bandwidth costs
- Premium instance types for low latency

**When to Use:**
- Mission-critical systems (payment, trading)
- SLA requirements >99.99%
- Zero data loss tolerance (RPO = 0)

#### Warm Standby (Tier 2)
**Monthly Cost: ~$18,000**

| Component | Primary (AWS) | Secondary (Azure) | Total |
|-----------|---------------|-------------------|-------|
| Compute | $8,000 (full) | $2,400 (30% capacity) | $10,400 |
| Database | $4,500 (full) | $1,350 (replica) | $5,850 |
| Load Balancers | $800 | $240 (minimal) | $1,040 |
| Storage | $1,200 | $360 (replicated) | $1,560 |
| Data Transfer | $1,500 | $450 | $1,950 |
| **Total** | **$16,000** | **$4,800** | **$20,800** |

**Cost Optimization:**
- Run secondary at 20-30% capacity
- Use smaller instance types in standby
- Leverage reserved instances for predictable workloads

**When to Use:**
- Business-critical applications
- RTO 1-4 hours acceptable
- RPO 15-60 minutes acceptable

#### Pilot Light (Tier 3)
**Monthly Cost: ~$6,000**

| Component | Primary (AWS) | Secondary (GCP) | Total |
|-----------|---------------|-----------------|-------|
| Compute | $8,000 | $0 (on-demand) | $8,000 |
| Database | $4,500 | $800 (snapshots) | $5,300 |
| Load Balancers | $800 | $0 (provision on failover) | $800 |
| Storage | $1,200 | $400 (cold storage) | $1,600 |
| Data Transfer | $1,500 | $200 | $1,700 |
| **Total** | **$16,000** | **$1,400** | **$17,400** |

**Cost Optimization:**
- Minimal infrastructure in secondary (just data)
- Use cold storage tiers
- Provision compute only during failover

**When to Use:**
- Important but not critical systems
- RTO 4-8 hours acceptable
- RPO 4-24 hours acceptable

#### Backup & Restore (Tier 4)
**Monthly Cost: ~$3,500**

| Component | Primary (AWS) | Backup Storage | Total |
|-----------|---------------|----------------|-------|
| Compute | $8,000 | $0 | $8,000 |
| Database | $4,500 | $0 | $4,500 |
| Load Balancers | $800 | $0 | $800 |
| Storage | $1,200 | $0 | $1,200 |
| Backups | $0 | $500 (Glacier/Archive) | $500 |
| **Total** | **$14,500** | **$500** | **$15,000** |

**Cost Optimization:**
- Daily backups to cheapest storage tier
- No standby infrastructure
- Restore only when needed

**When to Use:**
- Non-critical systems
- RTO >24 hours acceptable
- RPO 24 hours acceptable

### 7.3 Cost Optimization Techniques

#### 1. Compute Cost Optimization

**Use Spot/Preemptible Instances for Non-Critical Workloads:**

```hcl
# terraform/compute/spot-instances.tf
resource "aws_autoscaling_group" "app_spot" {
  name                = "prod-app-spot"
  vpc_zone_identifier = var.private_subnet_ids
  min_size            = 2
  max_size            = 20
  desired_capacity    = 5

  mixed_instances_policy {
    instances_distribution {
      on_demand_base_capacity                  = 2  # Minimum on-demand
      on_demand_percentage_above_base_capacity = 20 # 20% on-demand, 80% spot
      spot_allocation_strategy                 = "capacity-optimized"
    }

    launch_template {
      launch_template_specification {
        launch_template_id = aws_launch_template.app.id
        version            = "$Latest"
      }

      override {
        instance_type = "c5.large"
      }
      override {
        instance_type = "c5a.large"
      }
      override {
        instance_type = "c5n.large"
      }
    }
  }

  tag {
    key                 = "Name"
    value               = "app-server-spot"
    propagate_at_launch = true
  }
}
```

**Estimated Savings: 60-70% on compute costs**

**Reserved Instances for Predictable Workloads:**

```bash
# Purchase 1-year reserved instances for baseline capacity
aws ec2 purchase-reserved-instances-offering \
  --reserved-instances-offering-id offering-xxxxx \
  --instance-count 10 \
  --offering-type "All Upfront"

# Azure Reserved VM Instances
az vm reserved-capacity create \
  --resource-group prod-rg \
  --name prod-reserved-capacity \
  --sku Standard_D4s_v3 \
  --instance-count 5 \
  --term P1Y \
  --billing-frequency upfront
```

**Estimated Savings: 30-50% vs on-demand**

**Right-Sizing Recommendations:**

```python
# cost_optimization/rightsizing.py
import boto3
from datetime import datetime, timedelta

def analyze_instance_utilization():
    cloudwatch = boto3.client('cloudwatch')
    ec2 = boto3.client('ec2')
    
    instances = ec2.describe_instances(
        Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
    )
    
    recommendations = []
    
    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            instance_type = instance['InstanceType']
            
            # Get CPU utilization for last 30 days
            cpu_stats = cloudwatch.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                StartTime=datetime.now() - timedelta(days=30),
                EndTime=datetime.now(),
                Period=86400,  # Daily
                Statistics=['Average', 'Maximum']
            )
            
            if cpu_stats['Datapoints']:
                avg_cpu = sum(d['Average'] for d in cpu_stats['Datapoints']) / len(cpu_stats['Datapoints'])
                max_cpu = max(d['Maximum'] for d in cpu_stats['Datapoints'])
                
                # Recommend downsizing if avg CPU < 20% and max < 40%
                if avg_cpu < 20 and max_cpu < 40:
                    current_cost = get_instance_cost(instance_type)
                    recommended_type = get_smaller_instance_type(instance_type)
                    recommended_cost = get_instance_cost(recommended_type)
                    savings = current_cost - recommended_cost
                    
                    recommendations.append({
                        'instance_id': instance_id,
                        'current_type': instance_type,
                        'avg_cpu': avg_cpu,
                        'max_cpu': max_cpu,
                        'recommended_type': recommended_type,
                        'monthly_savings': savings * 730  # hours per month
                    })
    
    return recommendations

def get_instance_cost(instance_type):
    # Simplified pricing (use AWS Pricing API in production)
    pricing = {
        't3.large': 0.0832,
        't3.medium': 0.0416,
        'c5.2xlarge': 0.34,
        'c5.xlarge': 0.17,
        # Add more instance types
    }
    return pricing.get(instance_type, 0)

def get_smaller_instance_type(instance_type):
    # Simplified mapping
    downsize_map = {
        't3.large': 't3.medium',
        'c5.2xlarge': 'c5.xlarge',
        'c5.xlarge': 'c5.large',
        # Add more mappings
    }
    return downsize_map.get(instance_type, instance_type)

if __name__ == "__main__":
    recommendations = analyze_instance_utilization()
    total_savings = sum(r['monthly_savings'] for r in recommendations)
    
    print(f"Total potential monthly savings: ${total_savings:.2f}")
    for rec in recommendations:
        print(f"Instance {rec['instance_id']}: {rec['current_type']} → {rec['recommended_type']} (${rec['monthly_savings']:.2f}/month)")
```

#### 2. Storage Cost Optimization

**Lifecycle Policies for S3/Blob/GCS:**

```json
{
  "Rules": [
    {
      "Id": "MoveToInfrequentAccess",
      "Status": "Enabled",
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "STANDARD_IA"
        },
        {
          "Days": 90,
          "StorageClass": "GLACIER"
        },
        {
          "Days": 365,
          "StorageClass": "DEEP_ARCHIVE"
        }
      ],
      "NoncurrentVersionTransitions": [
        {
          "NoncurrentDays": 30,
          "StorageClass": "GLACIER"
        }
      ],
      "Expiration": {
        "Days": 2555
      }
    },
    {
      "Id": "DeleteOldLogs",
      "Status": "Enabled",
      "Prefix": "logs/",
      "Expiration": {
        "Days": 90
      }
    }
  ]
}
```

**Apply lifecycle policy:**

```bash
aws s3api put-bucket-lifecycle-configuration \
  --bucket prod-app-data-us-east-1 \
  --lifecycle-configuration file://lifecycle-policy.json
```

**Estimated Savings: 50-80% on storage costs**

**Storage Tier Comparison:**

| Tier | AWS | Azure | GCP | Use Case | Cost (per GB/month) |
|------|-----|-------|-----|----------|---------------------|
| **Hot/Standard** | S3 Standard | Hot | Standard | Frequent access | $0.023 |
| **Warm** | S3 IA | Cool | Nearline | Monthly access | $0.0125 |
| **Cold** | Glacier | Archive | Coldline | Quarterly access | $0.004 |
| **Archive** | Deep Archive | Archive | Archive | Yearly access | $0.00099 |

**Intelligent Tiering:**

```bash
# Enable S3 Intelligent-Tiering
aws s3api put-bucket-intelligent-tiering-configuration \
  --bucket prod-app-data-us-east-1 \
  --id AutoTiering \
  --intelligent-tiering-configuration '{
    "Id": "AutoTiering",
    "Status": "Enabled",
    "Tierings": [
      {
        "Days": 90,
        "AccessTier": "ARCHIVE_ACCESS"
      },
      {
        "Days": 180,
        "AccessTier": "DEEP_ARCHIVE_ACCESS"
      }
    ]
  }'
```

#### 3. Data Transfer Cost Optimization

**Cross-Region Replication Costs:**

```
Data Transfer Costs (per GB):
- AWS Cross-Region: $0.02
- AWS to Azure: $0.09
- Azure to GCP: $0.08
- Within same region: $0.00
```

**Optimization Strategies:**

**1. Use CloudFront/CDN for Static Content:**

```hcl
# terraform/cdn/cloudfront.tf
resource "aws_cloudfront_distribution" "main" {
  origin {
    domain_name = aws_s3_bucket.static_assets.bucket_regional_domain_name
    origin_id   = "S3-static-assets"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.main.cloudfront_access_identity_path
    }
  }

  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"

  # Cache behavior
  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-static-assets"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
    compress               = true
  }

  # Price class (use only US/EU/Asia for cost savings)
  price_class = "PriceClass_100"

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate.main.arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }
}
```

**Estimated Savings: 60-70% on data transfer costs**

**2. Compress Data Before Transfer:**

```python
# data_sync/compressed_sync.py
import boto3
import gzip
import io

def sync_with_compression(source_bucket, dest_bucket, key):
    s3 = boto3.client('s3')
    
    # Download from source
    response = s3.get_object(Bucket=source_bucket, Key=key)
    data = response['Body'].read()
    
    # Compress
    compressed = io.BytesIO()
    with gzip.GzipFile(fileobj=compressed, mode='wb') as gz:
        gz.write(data)
    
    compressed.seek(0)
    
    # Upload compressed to destination
    s3.put_object(
        Bucket=dest_bucket,
        Key=f"{key}.gz",
        Body=compressed,
        ContentEncoding='gzip',
        Metadata={'original-size': str(len(data))}
    )
    
    print(f"Compressed {len(data)} bytes to {compressed.getbuffer().nbytes} bytes")
    print(f"Compression ratio: {compressed.getbuffer().nbytes / len(data) * 100:.1f}%")
```

**3. Use VPN/Direct Connect for Large Transfers:**

```bash
# AWS Direct Connect pricing vs Internet transfer
# Direct Connect: $0.02/GB (port fee + data transfer)
# Internet: $0.09/GB
# Breakeven: ~1TB/month

# Calculate if Direct Connect is worth it
MONTHLY_TRANSFER_GB=5000
INTERNET_COST=$(echo "$MONTHLY_TRANSFER_GB * 0.09" | bc)
DIRECT_CONNECT_COST=$(echo "($MONTHLY_TRANSFER_GB * 0.02) + 300" | bc)  # $300 port fee

echo "Internet cost: \$$INTERNET_COST"
echo "Direct Connect cost: \$$DIRECT_CONNECT_COST"
echo "Savings: \$$(echo "$INTERNET_COST - $DIRECT_CONNECT_COST" | bc)"
```

#### 4. Database Cost Optimization

**Use Read Replicas Instead of Multi-AZ for DR:**

```
Multi-AZ RDS (db.r6g.2xlarge):
- Primary: $0.504/hour
- Standby: $0.504/hour (included)
- Total: $0.504/hour = $367/month

Read Replica (db.r6g.xlarge):
- Primary: $0.504/hour = $367/month
- Replica: $0.252/hour = $183/month
- Total: $550/month

Savings with right-sized replica: $184/month per database
```

**Aurora Serverless for Non-Production:**

```hcl
# terraform/database/aurora-serverless.tf
resource "aws_rds_cluster" "staging" {
  cluster_identifier      = "staging-cluster"
  engine                  = "aurora-postgresql"
  engine_mode             = "serverless"
  database_name           = "stagingdb"
  master_username         = "admin"
  master_password         = var.db_password
  
  scaling_configuration {
    auto_pause               = true
    max_capacity             = 16
    min_capacity             = 2
    seconds_until_auto_pause = 300
    timeout_action           = "ForceApplyCapacityChange"
  }

  backup_retention_period = 7
  preferred_backup_window = "03:00-04:00"
  
  tags = {
    Environment = "staging"
    AutoPause   = "enabled"
  }
}
```

**Estimated Savings: 70-90% for non-production databases**

#### 5. Kubernetes Cost Optimization

**Cluster Autoscaler Configuration:**

```yaml
# k8s/cluster-autoscaler.yaml
apiVersion: apps/v1
kind:Deployment
metadata:
  name: cluster-autoscaler
  namespace: kube-system
spec:
  replicas: 1
  selector:
    matchLabels:
      app: cluster-autoscaler
  template:
    metadata:
      labels:
        app: cluster-autoscaler
    spec:
      serviceAccountName: cluster-autoscaler
      containers:
      - image: k8s.gcr.io/autoscaling/cluster-autoscaler:v1.28.0
        name: cluster-autoscaler
        command:
        - ./cluster-autoscaler
        - --v=4
        - --stderrthreshold=info
        - --cloud-provider=aws
        - --skip-nodes-with-local-storage=false
        - --expander=least-waste
        - --node-group-auto-discovery=asg:tag=k8s.io/cluster-autoscaler/enabled,k8s.io/cluster-autoscaler/prod-cluster
        - --balance-similar-node-groups
        - --skip-nodes-with-system-pods=false
        - --scale-down-enabled=true
        - --scale-down-delay-after-add=10m
        - --scale-down-unneeded-time=10m
        - --scale-down-utilization-threshold=0.5
```

**Pod Resource Requests/Limits:**

```yaml
# k8s/app-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-server
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: api
        image: api-server:latest
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        # Vertical Pod Autoscaler will adjust these based on actual usage
```

**Vertical Pod Autoscaler:**

```yaml
# k8s/vpa.yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: api-server-vpa
spec:
  targetRef:
    apiVersion: "apps/v1"
    kind: Deployment
    name: api-server
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: api
      minAllowed:
        cpu: 100m
        memory: 128Mi
      maxAllowed:
        cpu: 1000m
        memory: 1Gi
```

**Estimated Savings: 30-50% on Kubernetes costs**

### 7.4 Cost Monitoring and Alerting

**AWS Cost Anomaly Detection:**

```bash
# Enable AWS Cost Anomaly Detection
aws ce create-anomaly-monitor \
  --anomaly-monitor '{
    "MonitorName": "DR-Infrastructure-Monitor",
    "MonitorType": "DIMENSIONAL",
    "MonitorDimension": "SERVICE"
  }'

# Create alert subscription
aws ce create-anomaly-subscription \
  --anomaly-subscription '{
    "SubscriptionName": "DR-Cost-Alerts",
    "Threshold": 100.0,
    "Frequency": "DAILY",
    "MonitorArnList": ["arn:aws:ce::ACCOUNT_ID:anomalymonitor/xxxxx"],
    "Subscribers": [{
      "Type": "EMAIL",
      "Address": "ops-team@example.com"
    }, {
      "Type": "SNS",
      "Address": "arn:aws:sns:us-east-1:ACCOUNT_ID:cost-alerts"
    }]
  }'
```

**Cost Dashboard with Grafana:**

```yaml
# grafana/dashboards/cost-dashboard.json
{
  "dashboard": {
    "title": "Multi-Cloud DR Cost Dashboard",
    "panels": [
      {
        "title": "Monthly Cost by Cloud Provider",
        "targets": [{
          "expr": "sum(aws_cost_explorer_cost_total) by (service)",
          "legendFormat": "AWS - {{service}}"
        }, {
          "expr": "sum(azure_cost_management_cost_total) by (service)",
          "legendFormat": "Azure - {{service}}"
        }, {
          "expr": "sum(gcp_billing_cost_total) by (service)",
          "legendFormat": "GCP - {{service}}"
        }]
      },
      {
        "title": "Cost per DR Tier",
        "targets": [{
          "expr": "sum(cloud_cost_total) by (dr_tier)"
        }]
      },
      {
        "title": "Data Transfer Costs",
        "targets": [{
          "expr": "sum(rate(data_transfer_bytes_total[1h])) * 0.09"
        }]
      }
    ]
  }
}
```

### 7.5 Cost Optimization Checklist

```markdown
## Monthly Cost Review Checklist

### Compute
- [ ] Review instance utilization (target: >60% CPU average)
- [ ] Identify and terminate unused instances
- [ ] Convert stable workloads to reserved instances
- [ ] Increase spot instance usage for non-critical workloads
- [ ] Right-size over-provisioned instances

### Storage
- [ ] Review storage lifecycle policies
- [ ] Delete old snapshots (>90 days)
- [ ] Move infrequently accessed data to cheaper tiers
- [ ] Enable intelligent tiering
- [ ] Compress large objects before storage

### Database
- [ ] Review database instance sizes
- [ ] Delete old automated backups
- [ ] Use Aurora Serverless for dev/staging
- [ ] Optimize read replica count
- [ ] Review and optimize expensive queries

### Networking
- [ ] Review data transfer patterns
- [ ] Optimize cross-region replication frequency
- [ ] Use CDN for static content
- [ ] Compress data before transfer
- [ ] Review VPN vs Direct Connect costs

### Kubernetes
- [ ] Review pod resource requests/limits
- [ ] Enable cluster autoscaling
- [ ] Use Vertical Pod Autoscaler
- [ ] Identify and remove unused namespaces
- [ ] Optimize container image sizes

### General
- [ ] Review and delete unused resources
- [ ] Check for unattached EBS volumes
- [ ] Review and optimize CloudWatch log retention
- [ ] Consolidate underutilized resources
- [ ] Review tagging for cost allocation
```

**Estimated Total Savings: 30-50% of overall DR infrastructure costs**

