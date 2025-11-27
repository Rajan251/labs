## 5. Multi-Cloud Failover Mechanism

### Failover Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    FAILOVER CONTROL PLANE                        │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Health     │───▶│   Decision   │───▶│   Execution  │      │
│  │   Monitors   │    │    Engine    │    │    Engine    │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                    │                    │             │
│         ▼                    ▼                    ▼             │
│  ┌──────────────────────────────────────────────────────┐      │
│  │         Observability & Alerting Layer               │      │
│  │  (Prometheus, Datadog, PagerDuty, Slack)             │      │
│  └──────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
   ┌─────────┐          ┌─────────┐          ┌─────────┐
   │   AWS   │          │  Azure  │          │   GCP   │
   │ Primary │          │Secondary│          │Tertiary │
   └─────────┘          └─────────┘          └─────────┘
```

### 5.1 Manual Failover Process

**Use Cases:**
- Planned maintenance windows
- Controlled migration testing
- Compliance-driven failovers
- When automatic failover is disabled

**Step-by-Step Manual Failover Procedure:**

#### Pre-Failover Checklist

```bash
#!/bin/bash
# pre-failover-checklist.sh

echo "=== DR Failover Pre-Flight Checklist ==="
echo ""

# 1. Verify secondary region health
echo "[1/10] Checking secondary region health..."
aws ec2 describe-instance-status --region us-west-2 --filters "Name=instance-state-name,Values=running" | jq '.InstanceStatuses | length'
az vm list --resource-group prod-rg-westus2 --query "[?powerState=='VM running'] | length(@)"
gcloud compute instances list --filter="status=RUNNING" --format="value(name)" | wc -l

# 2. Verify database replication lag
echo "[2/10] Checking database replication lag..."
psql -h prod-db-replica-us-west-2.xxxxx.rds.amazonaws.com -U admin -d proddb -c "SELECT now() - pg_last_xact_replay_timestamp() AS replication_lag;"

# 3. Verify storage replication status
echo "[3/10] Checking S3 replication status..."
aws s3api get-bucket-replication --bucket prod-app-data-us-east-1 | jq '.ReplicationConfiguration.Rules[].Status'

# 4. Verify DNS configuration
echo "[4/10] Checking DNS records..."
dig +short api.example.com
dig +short www.example.com

# 5. Verify backup freshness
echo "[5/10] Checking latest backup timestamps..."
aws backup list-recovery-points-by-backup-vault --backup-vault-name Default --query 'RecoveryPoints[0].CreationDate'

# 6. Verify Kubernetes cluster health
echo "[6/10] Checking Kubernetes cluster health..."
kubectl get nodes --context=aws-us-west-2
kubectl get nodes --context=azure-westus2
kubectl get nodes --context=gcp-us-central1

# 7. Verify load balancer health
echo "[7/10] Checking load balancer target health..."
aws elbv2 describe-target-health --target-group-arn arn:aws:elasticloadbalancing:us-west-2:ACCOUNT_ID:targetgroup/prod-tg/xxxxx

# 8. Verify monitoring and alerting
echo "[8/10] Checking monitoring systems..."
curl -s http://prometheus-us-west-2:9090/-/healthy
curl -s http://grafana-us-west-2:3000/api/health

# 9. Verify secrets availability
echo "[9/10] Checking secrets manager..."
aws secretsmanager list-secrets --region us-west-2 | jq '.SecretList | length'

# 10. Verify team notification channels
echo "[10/10] Sending test notification..."
curl -X POST https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK \
  -H 'Content-Type: application/json' \
  -d '{"text":"DR Failover Pre-Flight Check Complete"}'

echo ""
echo "=== Pre-Flight Check Complete ==="
```

#### Failover Execution Script

```bash
#!/bin/bash
# execute-failover.sh

set -e

SOURCE_REGION="us-east-1"
TARGET_REGION="us-west-2"
FAILOVER_TYPE="${1:-manual}"  # manual or automatic

echo "=== Starting DR Failover from $SOURCE_REGION to $TARGET_REGION ==="
echo "Failover Type: $FAILOVER_TYPE"
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# Log to S3 for audit trail
LOG_FILE="/tmp/failover-$(date +%s).log"
exec > >(tee -a $LOG_FILE)
exec 2>&1

# Function to send notifications
notify() {
  local message="$1"
  local severity="${2:-info}"
  
  echo "[NOTIFY] $message"
  
  # Slack notification
  curl -X POST https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK \
    -H 'Content-Type: application/json' \
    -d "{\"text\":\"🚨 DR Failover: $message\", \"username\":\"DR-Bot\"}"
  
  # PagerDuty alert
  if [ "$severity" == "critical" ]; then
    curl -X POST https://api.pagerduty.com/incidents \
      -H 'Authorization: Token token=YOUR_PAGERDUTY_TOKEN' \
      -H 'Content-Type: application/json' \
      -d "{\"incident\":{\"type\":\"incident\",\"title\":\"DR Failover: $message\",\"service\":{\"id\":\"YOUR_SERVICE_ID\",\"type\":\"service_reference\"}}}"
  fi
}

# Step 1: Promote database replica to primary
notify "Step 1: Promoting database replica to primary" "critical"
echo "[1/8] Promoting RDS read replica to standalone instance..."

aws rds promote-read-replica \
  --db-instance-identifier prod-db-replica-$TARGET_REGION \
  --backup-retention-period 7 \
  --region $TARGET_REGION

# Wait for promotion to complete
echo "Waiting for database promotion..."
aws rds wait db-instance-available \
  --db-instance-identifier prod-db-replica-$TARGET_REGION \
  --region $TARGET_REGION

notify "Database promoted successfully"

# Step 2: Update DNS records
notify "Step 2: Updating DNS records"
echo "[2/8] Updating Route 53 DNS records..."

# Get current DNS record
CURRENT_IP=$(aws route53 list-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --query "ResourceRecordSets[?Name=='api.example.com.'].ResourceRecords[0].Value" \
  --output text)

# Get new load balancer IP
NEW_IP=$(aws elbv2 describe-load-balancers \
  --names prod-alb-$TARGET_REGION \
  --region $TARGET_REGION \
  --query 'LoadBalancers[0].DNSName' \
  --output text)

# Update DNS record
cat > /tmp/dns-change.json <<EOF
{
  "Changes": [{
    "Action": "UPSERT",
    "ResourceRecordSet": {
      "Name": "api.example.com",
      "Type": "CNAME",
      "TTL": 60,
      "ResourceRecords": [{"Value": "$NEW_IP"}]
    }
  }]
}
EOF

aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --change-batch file:///tmp/dns-change.json

notify "DNS updated from $CURRENT_IP to $NEW_IP"

# Step 3: Scale up compute resources
notify "Step 3: Scaling up compute resources"
echo "[3/8] Scaling up Auto Scaling Groups..."

aws autoscaling set-desired-capacity \
  --auto-scaling-group-name prod-asg-web-$TARGET_REGION \
  --desired-capacity 10 \
  --region $TARGET_REGION

aws autoscaling set-desired-capacity \
  --auto-scaling-group-name prod-asg-app-$TARGET_REGION \
  --desired-capacity 15 \
  --region $TARGET_REGION

# Wait for instances to be healthy
echo "Waiting for instances to become healthy..."
sleep 60

notify "Compute resources scaled up"

# Step 4: Update Kubernetes ingress
notify "Step 4: Updating Kubernetes ingress"
echo "[4/8] Switching Kubernetes traffic..."

kubectl --context=aws-$TARGET_REGION patch ingress prod-ingress \
  -p '{"metadata":{"annotations":{"nginx.ingress.kubernetes.io/canary":"false"}}}'

kubectl --context=aws-$TARGET_REGION scale deployment/api-server --replicas=10
kubectl --context=aws-$TARGET_REGION scale deployment/web-server --replicas=8

notify "Kubernetes traffic switched"

# Step 5: Verify application health
notify "Step 5: Verifying application health"
echo "[5/8] Running health checks..."

for i in {1..10}; do
  HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://api.example.com/health)
  if [ "$HTTP_STATUS" == "200" ]; then
    echo "Health check passed (attempt $i/10)"
    break
  else
    echo "Health check failed (attempt $i/10), status: $HTTP_STATUS"
    sleep 5
  fi
done

if [ "$HTTP_STATUS" != "200" ]; then
  notify "Health checks failed! Rolling back..." "critical"
  # Rollback logic here
  exit 1
fi

notify "Application health verified"

# Step 6: Update monitoring dashboards
notify "Step 6: Updating monitoring dashboards"
echo "[6/8] Updating Grafana dashboards..."

curl -X POST http://grafana.example.com/api/annotations \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_GRAFANA_TOKEN' \
  -d "{\"text\":\"DR Failover to $TARGET_REGION\",\"tags\":[\"failover\",\"dr\"],\"time\":$(date +%s)000}"

notify "Monitoring dashboards updated"

# Step 7: Enable write traffic to new primary database
notify "Step 7: Enabling write traffic to new primary"
echo "[7/8] Updating application configuration..."

# Update application config in Parameter Store
aws ssm put-parameter \
  --name /prod/database/primary-endpoint \
  --value "prod-db-replica-$TARGET_REGION.xxxxx.rds.amazonaws.com" \
  --type String \
  --overwrite \
  --region $TARGET_REGION

# Restart application pods to pick up new config
kubectl --context=aws-$TARGET_REGION rollout restart deployment/api-server
kubectl --context=aws-$TARGET_REGION rollout status deployment/api-server

notify "Write traffic enabled to new primary"

# Step 8: Final verification
notify "Step 8: Final verification"
echo "[8/8] Running end-to-end tests..."

# Run smoke tests
./scripts/smoke-tests.sh --region $TARGET_REGION

notify "✅ DR Failover completed successfully!" "critical"

# Upload log to S3
aws s3 cp $LOG_FILE s3://dr-logs-bucket/failover-logs/$(basename $LOG_FILE)

echo ""
echo "=== Failover Complete ==="
echo "New Primary Region: $TARGET_REGION"
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Log file: s3://dr-logs-bucket/failover-logs/$(basename $LOG_FILE)"
```

### 5.2 Automatic Failover Mechanism

**Architecture Components:**

```
┌─────────────────────────────────────────────────────────────────┐
│                  AUTOMATIC FAILOVER SYSTEM                       │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Health Check Layer                          │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐         │   │
│  │  │ Endpoint   │  │ Database   │  │ Application│         │   │
│  │  │ Monitors   │  │ Monitors   │  │ Monitors   │         │   │
│  │  └────────────┘  └────────────┘  └────────────┘         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                            │                                     │
│                            ▼                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           Failure Detection Engine                       │   │
│  │  • Consecutive failure threshold: 3                      │   │
│  │  • Health check interval: 30 seconds                     │   │
│  │  • Failure window: 90 seconds                            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                            │                                     │
│                            ▼                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           Decision Engine (State Machine)                │   │
│  │  States: HEALTHY → DEGRADED → CRITICAL → FAILOVER       │   │
│  └──────────────────────────────────────────────────────────┘   │
│                            │                                     │
│                            ▼                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           Failover Orchestrator                          │   │
│  │  • DNS update                                            │   │
│  │  • Database promotion                                    │   │
│  │  • Traffic shifting                                      │   │
│  │  • Notification dispatch                                 │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

**Health Check Implementation:**

```python
# health_monitor.py
import boto3
import requests
import psycopg2
import time
import json
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict
from enum import Enum

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    FAILED = "failed"

@dataclass
class HealthCheckResult:
    component: str
    status: HealthStatus
    latency_ms: float
    timestamp: datetime
    details: Dict

class MultiCloudHealthMonitor:
    def __init__(self):
        self.failure_threshold = 3
        self.check_interval = 30
        self.failure_counts = {}
        
        # Initialize cloud clients
        self.aws_client = boto3.client('cloudwatch')
        self.route53_client = boto3.client('route53')
        
    def check_endpoint_health(self, endpoint: str) -> HealthCheckResult:
        """Check HTTP endpoint health"""
        try:
            start_time = time.time()
            response = requests.get(
                f"https://{endpoint}/health",
                timeout=5,
                headers={"User-Agent": "DR-HealthMonitor/1.0"}
            )
            latency = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                status = HealthStatus.HEALTHY
            elif response.status_code >= 500:
                status = HealthStatus.CRITICAL
            else:
                status = HealthStatus.DEGRADED
                
            return HealthCheckResult(
                component=endpoint,
                status=status,
                latency_ms=latency,
                timestamp=datetime.utcnow(),
                details={"status_code": response.status_code}
            )
        except requests.exceptions.Timeout:
            return HealthCheckResult(
                component=endpoint,
                status=HealthStatus.FAILED,
                latency_ms=5000,
                timestamp=datetime.utcnow(),
                details={"error": "timeout"}
            )
        except Exception as e:
            return HealthCheckResult(
                component=endpoint,
                status=HealthStatus.FAILED,
                latency_ms=0,
                timestamp=datetime.utcnow(),
                details={"error": str(e)}
            )
    
    def check_database_health(self, db_config: Dict) -> HealthCheckResult:
        """Check database health and replication lag"""
        try:
            start_time = time.time()
            conn = psycopg2.connect(
                host=db_config['host'],
                port=db_config['port'],
                database=db_config['database'],
                user=db_config['user'],
                password=db_config['password'],
                connect_timeout=5
            )
            
            cursor = conn.cursor()
            
            # Check if this is a replica
            cursor.execute("SELECT pg_is_in_recovery();")
            is_replica = cursor.fetchone()[0]
            
            replication_lag = 0
            if is_replica:
                # Check replication lag
                cursor.execute("""
                    SELECT EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp()))::int;
                """)
                replication_lag = cursor.fetchone()[0] or 0
            
            latency = (time.time() - start_time) * 1000
            
            # Determine status based on replication lag
            if replication_lag < 30:
                status = HealthStatus.HEALTHY
            elif replication_lag < 300:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.CRITICAL
            
            cursor.close()
            conn.close()
            
            return HealthCheckResult(
                component=f"database-{db_config['host']}",
                status=status,
                latency_ms=latency,
                timestamp=datetime.utcnow(),
                details={
                    "is_replica": is_replica,
                    "replication_lag_seconds": replication_lag
                }
            )
        except Exception as e:
            return HealthCheckResult(
                component=f"database-{db_config['host']}",
                status=HealthStatus.FAILED,
                latency_ms=0,
                timestamp=datetime.utcnow(),
                details={"error": str(e)}
            )
    
    def check_kubernetes_health(self, context: str) -> HealthCheckResult:
        """Check Kubernetes cluster health"""
        import subprocess
        
        try:
            start_time = time.time()
            
            # Check node status
            result = subprocess.run(
                ["kubectl", "--context", context, "get", "nodes", "-o", "json"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            latency = (time.time() - start_time) * 1000
            
            if result.returncode == 0:
                nodes_data = json.loads(result.stdout)
                total_nodes = len(nodes_data['items'])
                ready_nodes = sum(
                    1 for node in nodes_data['items']
                    if any(
                        condition['type'] == 'Ready' and condition['status'] == 'True'
                        for condition in node['status']['conditions']
                    )
                )
                
                if ready_nodes == total_nodes:
                    status = HealthStatus.HEALTHY
                elif ready_nodes >= total_nodes * 0.7:
                    status = HealthStatus.DEGRADED
                else:
                    status = HealthStatus.CRITICAL
                
                return HealthCheckResult(
                    component=f"kubernetes-{context}",
                    status=status,
                    latency_ms=latency,
                    timestamp=datetime.utcnow(),
                    details={
                        "total_nodes": total_nodes,
                        "ready_nodes": ready_nodes
                    }
                )
            else:
                return HealthCheckResult(
                    component=f"kubernetes-{context}",
                    status=HealthStatus.FAILED,
                    latency_ms=latency,
                    timestamp=datetime.utcnow(),
                    details={"error": result.stderr}
                )
        except Exception as e:
            return HealthCheckResult(
                component=f"kubernetes-{context}",
                status=HealthStatus.FAILED,
                latency_ms=0,
                timestamp=datetime.utcnow(),
                details={"error": str(e)}
            )
    
    def evaluate_failover_decision(self, results: List[HealthCheckResult]) -> bool:
        """Determine if failover should be triggered"""
        critical_components = [
            r for r in results 
            if r.status in [HealthStatus.CRITICAL, HealthStatus.FAILED]
        ]
        
        # Update failure counts
        for result in critical_components:
            component = result.component
            self.failure_counts[component] = self.failure_counts.get(component, 0) + 1
        
        # Reset counts for healthy components
        healthy_components = [
            r.component for r in results 
            if r.status == HealthStatus.HEALTHY
        ]
        for component in healthy_components:
            self.failure_counts[component] = 0
        
        # Trigger failover if any component exceeds threshold
        for component, count in self.failure_counts.items():
            if count >= self.failure_threshold:
                print(f"Failover triggered: {component} failed {count} consecutive times")
                return True
        
        return False
    
    def trigger_automatic_failover(self, source_region: str, target_region: str):
        """Trigger automatic failover"""
        print(f"🚨 AUTOMATIC FAILOVER INITIATED: {source_region} → {target_region}")
        
        # Send critical notifications
        self.send_notification(
            message=f"Automatic DR failover initiated from {source_region} to {target_region}",
            severity="critical"
        )
        
        # Execute failover script
        import subprocess
        subprocess.run([
            "/opt/dr/scripts/execute-failover.sh",
            "automatic",
            source_region,
            target_region
        ])
    
    def send_notification(self, message: str, severity: str = "info"):
        """Send notifications via multiple channels"""
        # Slack
        requests.post(
            "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
            json={"text": f"🚨 {message}", "username": "DR-AutoFailover"}
        )
        
        # PagerDuty
        if severity == "critical":
            requests.post(
                "https://api.pagerduty.com/incidents",
                headers={
                    "Authorization": "Token token=YOUR_PAGERDUTY_TOKEN",
                    "Content-Type": "application/json"
                },
                json={
                    "incident": {
                        "type": "incident",
                        "title": message,
                        "service": {
                            "id": "YOUR_SERVICE_ID",
                            "type": "service_reference"
                        }
                    }
                }
            )
    
    def run_monitoring_loop(self):
        """Main monitoring loop"""
        print("Starting Multi-Cloud DR Health Monitor...")
        
        # Define components to monitor
        endpoints = [
            "api.example.com",
            "www.example.com"
        ]
        
        databases = [
            {
                "host": "prod-db-us-east-1.xxxxx.rds.amazonaws.com",
                "port": 5432,
                "database": "proddb",
                "user": "monitor",
                "password": "MonitorPassword123"
            },
            {
                "host": "prod-db-us-west-2.xxxxx.rds.amazonaws.com",
                "port": 5432,
                "database": "proddb",
                "user": "monitor",
                "password": "MonitorPassword123"
            }
        ]
        
        k8s_contexts = [
            "aws-us-east-1",
            "aws-us-west-2",
            "azure-eastus",
            "gcp-us-central1"
        ]
        
        while True:
            results = []
            
            # Check all endpoints
            for endpoint in endpoints:
                result = self.check_endpoint_health(endpoint)
                results.append(result)
                print(f"[{result.timestamp}] {result.component}: {result.status.value} ({result.latency_ms:.2f}ms)")
            
            # Check all databases
            for db_config in databases:
                result = self.check_database_health(db_config)
                results.append(result)
                print(f"[{result.timestamp}] {result.component}: {result.status.value} (lag: {result.details.get('replication_lag_seconds', 0)}s)")
            
            # Check Kubernetes clusters
            for context in k8s_contexts:
                result = self.check_kubernetes_health(context)
                results.append(result)
                print(f"[{result.timestamp}] {result.component}: {result.status.value}")
            
            # Evaluate failover decision
            should_failover = self.evaluate_failover_decision(results)
            
            if should_failover:
                self.trigger_automatic_failover("us-east-1", "us-west-2")
                break  # Exit loop after triggering failover
            
            # Wait before next check
            time.sleep(self.check_interval)

if __name__ == "__main__":
    monitor = MultiCloudHealthMonitor()
    monitor.run_monitoring_loop()
```

**Deploy as Kubernetes CronJob:**

```yaml
# k8s/dr-health-monitor.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: dr-monitor-config
  namespace: dr-system
data:
  config.yaml: |
    failure_threshold: 3
    check_interval: 30
    endpoints:
      - api.example.com
      - www.example.com
    databases:
      - host: prod-db-us-east-1.xxxxx.rds.amazonaws.com
        port: 5432
        database: proddb
    kubernetes_contexts:
      - aws-us-east-1
      - aws-us-west-2
      - azure-eastus
      - gcp-us-central1
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dr-health-monitor
  namespace: dr-system
spec:
  replicas: 2  # Run 2 replicas for HA
  selector:
    matchLabels:
      app: dr-health-monitor
  template:
    metadata:
      labels:
        app: dr-health-monitor
    spec:
      serviceAccountName: dr-monitor
      containers:
      - name: monitor
        image: your-registry/dr-health-monitor:latest
        env:
        - name: AWS_REGION
          value: "us-east-1"
        - name: SLACK_WEBHOOK_URL
          valueFrom:
            secretKeyRef:
              name: dr-secrets
              key: slack-webhook
        - name: PAGERDUTY_TOKEN
          valueFrom:
            secretKeyRef:
              name: dr-secrets
              key: pagerduty-token
        volumeMounts:
        - name: config
          mountPath: /etc/dr-monitor
        - name: kubeconfig
          mountPath: /root/.kube
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      volumes:
      - name: config
        configMap:
          name: dr-monitor-config
      - name: kubeconfig
        secret:
          secretName: multi-cloud-kubeconfig
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: dr-monitor
  namespace: dr-system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: dr-monitor-role
rules:
- apiGroups: [""]
  resources: ["nodes", "pods", "services"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "statefulsets"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: dr-monitor-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: dr-monitor-role
subjects:
- kind: ServiceAccount
  name: dr-monitor
  namespace: dr-system
```

### 5.3 DNS-Based Failover

**Route 53 Health Checks and Failover Routing:**

```bash
# Create health check for primary endpoint
aws route53 create-health-check \
  --caller-reference $(date +%s) \
  --health-check-config '{
    "Type": "HTTPS",
    "ResourcePath": "/health",
    "FullyQualifiedDomainName": "api-us-east-1.example.com",
    "Port": 443,
    "RequestInterval": 30,
    "FailureThreshold": 3,
    "MeasureLatency": true,
    "EnableSNI": true
  }' \
  --health-check-tags '[
    {"Key": "Name", "Value": "primary-api-health"},
    {"Key": "Region", "Value": "us-east-1"}
  ]'

# Create health check for secondary endpoint
aws route53 create-health-check \
  --caller-reference $(date +%s) \
  --health-check-config '{
    "Type": "HTTPS",
    "ResourcePath": "/health",
    "FullyQualifiedDomainName": "api-us-west-2.example.com",
    "Port": 443,
    "RequestInterval": 30,
    "FailureThreshold": 3,
    "MeasureLatency": true,
    "EnableSNI": true
  }' \
  --health-check-tags '[
    {"Key": "Name", "Value": "secondary-api-health"},
    {"Key": "Region", "Value": "us-west-2"}
  ]'

# Create failover DNS records
cat > dns-failover-config.json <<EOF
{
  "Changes": [
    {
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "api.example.com",
        "Type": "A",
        "SetIdentifier": "Primary-US-East-1",
        "Failover": "PRIMARY",
        "HealthCheckId": "PRIMARY_HEALTH_CHECK_ID",
        "AliasTarget": {
          "HostedZoneId": "Z1234567890ABC",
          "DNSName": "prod-alb-us-east-1.elb.amazonaws.com",
          "EvaluateTargetHealth": true
        }
      }
    },
    {
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "api.example.com",
        "Type": "A",
        "SetIdentifier": "Secondary-US-West-2",
        "Failover": "SECONDARY",
        "AliasTarget": {
          "HostedZoneId": "Z0987654321XYZ",
          "DNSName": "prod-alb-us-west-2.elb.amazonaws.com",
          "EvaluateTargetHealth": true
        }
      }
    }
  ]
}
EOF

aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --change-batch file://dns-failover-config.json
```

**Multi-Cloud DNS with Azure Traffic Manager:**

```bash
# Create Traffic Manager profile
az network traffic-manager profile create \
  --name prod-traffic-manager \
  --resource-group prod-rg-global \
  --routing-method Priority \
  --unique-dns-name prod-api-tm \
  --ttl 30 \
  --protocol HTTPS \
  --port 443 \
  --path /health \
  --interval 30 \
  --timeout 10 \
  --max-failures 3

# Add AWS endpoint (Priority 1)
az network traffic-manager endpoint create \
  --name aws-primary \
  --profile-name prod-traffic-manager \
  --resource-group prod-rg-global \
  --type externalEndpoints \
  --target api-us-east-1.example.com \
  --priority 1 \
  --endpoint-status Enabled

# Add Azure endpoint (Priority 2)
az network traffic-manager endpoint create \
  --name azure-secondary \
  --profile-name prod-traffic-manager \
  --resource-group prod-rg-global \
  --type externalEndpoints \
  --target api-eastus.example.com \
  --priority 2 \
  --endpoint-status Enabled

# Add GCP endpoint (Priority 3)
az network traffic-manager endpoint create \
  --name gcp-tertiary \
  --profile-name prod-traffic-manager \
  --resource-group prod-rg-global \
  --type externalEndpoints \
  --target api-us-central1.example.com \
  --priority 3 \
  --endpoint-status Enabled
```

### 5.4 Traffic Shifting Strategies

**Gradual Traffic Shift (Canary Deployment):**

```yaml
# k8s/canary-deployment.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: prod-ingress-canary
  annotations:
    nginx.ingress.kubernetes.io/canary: "true"
    nginx.ingress.kubernetes.io/canary-weight: "10"  # Start with 10% traffic
    nginx.ingress.kubernetes.io/canary-by-header: "X-Canary"
    nginx.ingress.kubernetes.io/canary-by-header-value: "always"
spec:
  ingressClassName: nginx
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-service-secondary
            port:
              number: 80
```

**Automated Traffic Shift Script:**

```bash
#!/bin/bash
# gradual-traffic-shift.sh

CURRENT_WEIGHT=0
TARGET_WEIGHT=100
INCREMENT=10
WAIT_TIME=300  # 5 minutes between increments

echo "Starting gradual traffic shift to secondary region..."

while [ $CURRENT_WEIGHT -lt $TARGET_WEIGHT ]; do
  CURRENT_WEIGHT=$((CURRENT_WEIGHT + INCREMENT))
  
  echo "Shifting traffic: ${CURRENT_WEIGHT}% to secondary"
  
  kubectl patch ingress prod-ingress-canary \
    -p "{\"metadata\":{\"annotations\":{\"nginx.ingress.kubernetes.io/canary-weight\":\"$CURRENT_WEIGHT\"}}}"
  
  # Monitor error rates
  echo "Monitoring error rates for $WAIT_TIME seconds..."
  ERROR_RATE=$(curl -s "http://prometheus:9090/api/v1/query?query=rate(http_requests_total{status=~\"5..\"}[5m])" | jq -r '.data.result[0].value[1]')
  
  if (( $(echo "$ERROR_RATE > 0.01" | bc -l) )); then
    echo "Error rate too high ($ERROR_RATE), rolling back!"
    kubectl patch ingress prod-ingress-canary \
      -p '{"metadata":{"annotations":{"nginx.ingress.kubernetes.io/canary-weight":"0"}}}'
    exit 1
  fi
  
  sleep $WAIT_TIME
done

echo "Traffic shift complete: 100% to secondary region"

# Remove canary annotation to finalize
kubectl patch ingress prod-ingress-canary \
  -p '{"metadata":{"annotations":{"nginx.ingress.kubernetes.io/canary":"false"}}}'
```

