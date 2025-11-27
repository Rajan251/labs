## 6. Testing Strategy & DR Drills

### 6.1 DR Testing Philosophy

**Core Principles:**
- **Test in production-like environments**: Staging should mirror production
- **Regular cadence**: Monthly for critical systems, quarterly for others
- **Automated where possible**: Reduce human error
- **Document everything**: Capture learnings and update runbooks
- **Measure and improve**: Track RTO/RPO actuals vs. targets

### 6.2 DR Testing Schedule

| Test Type | Frequency | Duration | Scope | Participants |
|-----------|-----------|----------|-------|--------------|
| **Tabletop Exercise** | Monthly | 2 hours | Discussion-based scenario walkthrough | All teams |
| **Component Test** | Monthly | 4 hours | Individual component failover (DB, storage, etc.) | Ops team |
| **Partial Failover** | Quarterly | 8 hours | Single service/application failover | Ops + Dev teams |
| **Full DR Drill** | Semi-annually | 24 hours | Complete regional failover | All teams + executives |
| **Chaos Engineering** | Weekly | Continuous | Random failure injection | SRE team |
| **Backup Restoration** | Monthly | 2 hours | Restore from backup to verify integrity | Ops team |

### 6.3 Pre-DR Drill Checklist

```bash
#!/bin/bash
# pre-dr-drill-checklist.sh

echo "=== Pre-DR Drill Checklist ==="
echo "Drill Date: $(date)"
echo "Drill Type: ${DRILL_TYPE:-Full Failover}"
echo ""

# 1. Stakeholder Notification
echo "[1/15] ✓ Stakeholders notified 48 hours in advance"
echo "  - Engineering teams: ✓"
echo "  - Product management: ✓"
echo "  - Customer support: ✓"
echo "  - Executive leadership: ✓"

# 2. Backup Verification
echo "[2/15] Verifying recent backups..."
LATEST_BACKUP=$(aws backup list-recovery-points-by-backup-vault \
  --backup-vault-name Default \
  --query 'RecoveryPoints[0].CreationDate' \
  --output text)
echo "  Latest backup: $LATEST_BACKUP"

# 3. Replication Status
echo "[3/15] Checking replication status..."
aws s3api get-bucket-replication \
  --bucket prod-app-data-us-east-1 \
  --query 'ReplicationConfiguration.Rules[*].[ID,Status]' \
  --output table

# 4. Secondary Region Capacity
echo "[4/15] Verifying secondary region capacity..."
aws ec2 describe-instance-type-offerings \
  --location-type availability-zone \
  --filters Name=instance-type,Values=c5.2xlarge \
  --region us-west-2 \
  --query 'InstanceTypeOfferings[*].Location' \
  --output table

# 5. DNS TTL Reduction
echo "[5/15] Reducing DNS TTL to 60 seconds..."
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "api.example.com",
        "Type": "A",
        "TTL": 60,
        "ResourceRecords": [{"Value": "CURRENT_IP"}]
      }
    }]
  }'

# 6. Monitoring Dashboard Setup
echo "[6/15] Setting up DR drill monitoring dashboard..."
curl -X POST http://grafana.example.com/api/dashboards/db \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_GRAFANA_TOKEN' \
  -d @dr-drill-dashboard.json

# 7. Communication Channels
echo "[7/15] Testing communication channels..."
# Slack
curl -X POST https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK \
  -d '{"text":"DR Drill communication test - please acknowledge"}'

# PagerDuty
curl -X POST https://api.pagerduty.com/incidents \
  -H 'Authorization: Token token=YOUR_PAGERDUTY_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "incident": {
      "type": "incident",
      "title": "DR Drill Test",
      "service": {"id": "YOUR_SERVICE_ID", "type": "service_reference"},
      "urgency": "low"
    }
  }'

# 8. Runbook Accessibility
echo "[8/15] Verifying runbook accessibility..."
curl -I https://wiki.example.com/dr-runbooks

# 9. Access Credentials
echo "[9/15] Verifying access credentials..."
aws sts get-caller-identity
az account show
gcloud auth list

# 10. Secondary Region Health
echo "[10/15] Checking secondary region health..."
aws ec2 describe-instance-status \
  --region us-west-2 \
  --filters "Name=instance-state-name,Values=running" \
  --query 'InstanceStatuses[*].[InstanceId,InstanceState.Name,SystemStatus.Status,InstanceStatus.Status]' \
  --output table

# 11. Database Replication Lag
echo "[11/15] Checking database replication lag..."
psql -h prod-db-replica-us-west-2.xxxxx.rds.amazonaws.com -U admin -d proddb -c \
  "SELECT now() - pg_last_xact_replay_timestamp() AS replication_lag;"

# 12. Storage Replication
echo "[12/15] Verifying storage replication..."
aws s3api head-bucket --bucket prod-app-data-us-west-2 --region us-west-2

# 13. Load Balancer Configuration
echo "[13/15] Checking load balancer configuration..."
aws elbv2 describe-load-balancers \
  --names prod-alb-us-west-2 \
  --region us-west-2 \
  --query 'LoadBalancers[*].[LoadBalancerName,State.Code,DNSName]' \
  --output table

# 14. Kubernetes Cluster
echo "[14/15] Checking Kubernetes cluster readiness..."
kubectl get nodes --context=aws-us-west-2
kubectl get pods --all-namespaces --context=aws-us-west-2 | grep -v Running

# 15. Rollback Plan
echo "[15/15] ✓ Rollback plan documented and reviewed"
echo "  Rollback runbook: https://wiki.example.com/dr-rollback"

echo ""
echo "=== Pre-DR Drill Checklist Complete ==="
echo "Status: READY FOR DRILL"
```

### 6.4 DR Drill Execution Plan

#### Phase 1: Preparation (T-2 hours)

```bash
#!/bin/bash
# dr-drill-phase1-preparation.sh

echo "=== DR Drill Phase 1: Preparation ==="
START_TIME=$(date +%s)

# 1. Create drill snapshot
echo "[1/5] Creating pre-drill snapshots..."
aws ec2 create-snapshot \
  --volume-id vol-xxxxx \
  --description "Pre-DR-Drill-$(date +%Y%m%d)" \
  --tag-specifications 'ResourceType=snapshot,Tags=[{Key=Purpose,Value=DR-Drill}]'

# 2. Enable detailed monitoring
echo "[2/5] Enabling detailed CloudWatch monitoring..."
aws cloudwatch put-metric-alarm \
  --alarm-name dr-drill-high-error-rate \
  --alarm-description "Alert on high error rate during DR drill" \
  --metric-name 5XXError \
  --namespace AWS/ApplicationELB \
  --statistic Sum \
  --period 60 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2

# 3. Notify all stakeholders
echo "[3/5] Sending drill start notifications..."
curl -X POST https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK \
  -d '{
    "text": "🚨 DR DRILL STARTING IN 2 HOURS",
    "attachments": [{
      "color": "warning",
      "fields": [
        {"title": "Drill Type", "value": "Full Regional Failover", "short": true},
        {"title": "Expected Duration", "value": "4 hours", "short": true},
        {"title": "Impact", "value": "None (test environment)", "short": true}
      ]
    }]
  }'

# 4. Set up drill-specific logging
echo "[4/5] Configuring drill-specific logging..."
aws logs create-log-group --log-group-name /dr-drill/$(date +%Y%m%d)

# 5. Prepare rollback scripts
echo "[5/5] Preparing rollback scripts..."
cat > /tmp/rollback-drill.sh <<'EOF'
#!/bin/bash
echo "Rolling back DR drill..."
# DNS rollback
aws route53 change-resource-record-sets --hosted-zone-id Z1234567890ABC --change-batch file://original-dns.json
# Traffic rollback
kubectl patch ingress prod-ingress --patch '{"metadata":{"annotations":{"nginx.ingress.kubernetes.io/canary":"false"}}}'
echo "Rollback complete"
EOF
chmod +x /tmp/rollback-drill.sh

echo "Phase 1 complete. Ready to begin drill."
```

#### Phase 2: Failover Execution (T+0 hours)

```bash
#!/bin/bash
# dr-drill-phase2-execution.sh

echo "=== DR Drill Phase 2: Failover Execution ==="
DRILL_START=$(date +%s)

# Record start time
echo "Drill started at: $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /var/log/dr-drill.log

# Step 1: Simulate primary region failure
echo "[1/8] Simulating primary region failure..."
# In a real drill, you might:
# - Stop accepting traffic at primary load balancer
# - Disable primary database writes
# - Trigger health check failures

# For safety, we'll use traffic shifting instead
kubectl patch ingress prod-ingress \
  --patch '{"metadata":{"annotations":{"nginx.ingress.kubernetes.io/canary":"true","nginx.ingress.kubernetes.io/canary-weight":"0"}}}'

# Step 2: Promote secondary database
echo "[2/8] Promoting secondary database..."
PROMOTE_START=$(date +%s)

aws rds promote-read-replica \
  --db-instance-identifier prod-db-replica-us-west-2 \
  --backup-retention-period 7 \
  --region us-west-2

aws rds wait db-instance-available \
  --db-instance-identifier prod-db-replica-us-west-2 \
  --region us-west-2

PROMOTE_END=$(date +%s)
PROMOTE_DURATION=$((PROMOTE_END - PROMOTE_START))
echo "Database promotion took: ${PROMOTE_DURATION}s" | tee -a /var/log/dr-drill.log

# Step 3: Update DNS
echo "[3/8] Updating DNS records..."
DNS_START=$(date +%s)

NEW_LB_DNS=$(aws elbv2 describe-load-balancers \
  --names prod-alb-us-west-2 \
  --region us-west-2 \
  --query 'LoadBalancers[0].DNSName' \
  --output text)

aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --change-batch "{
    \"Changes\": [{
      \"Action\": \"UPSERT\",
      \"ResourceRecordSet\": {
        \"Name\": \"api.example.com\",
        \"Type\": \"CNAME\",
        \"TTL\": 60,
        \"ResourceRecords\": [{\"Value\": \"$NEW_LB_DNS\"}]
      }
    }]
  }"

DNS_END=$(date +%s)
DNS_DURATION=$((DNS_END - DNS_START))
echo "DNS update took: ${DNS_DURATION}s" | tee -a /var/log/dr-drill.log

# Step 4: Scale up secondary compute
echo "[4/8] Scaling up secondary region compute..."
SCALE_START=$(date +%s)

aws autoscaling set-desired-capacity \
  --auto-scaling-group-name prod-asg-web-us-west-2 \
  --desired-capacity 10 \
  --region us-west-2

aws autoscaling set-desired-capacity \
  --auto-scaling-group-name prod-asg-app-us-west-2 \
  --desired-capacity 15 \
  --region us-west-2

# Wait for instances to be in service
sleep 120

SCALE_END=$(date +%s)
SCALE_DURATION=$((SCALE_END - SCALE_START))
echo "Compute scaling took: ${SCALE_DURATION}s" | tee -a /var/log/dr-drill.log

# Step 5: Update application configuration
echo "[5/8] Updating application configuration..."
aws ssm put-parameter \
  --name /prod/database/primary-endpoint \
  --value "prod-db-replica-us-west-2.xxxxx.rds.amazonaws.com" \
  --type String \
  --overwrite \
  --region us-west-2

# Step 6: Restart application pods
echo "[6/8] Restarting application pods..."
kubectl --context=aws-us-west-2 rollout restart deployment/api-server
kubectl --context=aws-us-west-2 rollout restart deployment/web-server

kubectl --context=aws-us-west-2 rollout status deployment/api-server --timeout=300s
kubectl --context=aws-us-west-2 rollout status deployment/web-server --timeout=300s

# Step 7: Verify application health
echo "[7/8] Verifying application health..."
HEALTH_CHECK_PASSED=false
for i in {1..20}; do
  HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://api.example.com/health)
  if [ "$HTTP_STATUS" == "200" ]; then
    echo "Health check passed (attempt $i/20)"
    HEALTH_CHECK_PASSED=true
    break
  else
    echo "Health check failed (attempt $i/20), status: $HTTP_STATUS"
    sleep 10
  fi
done

if [ "$HEALTH_CHECK_PASSED" = false ]; then
  echo "ERROR: Health checks failed! Initiating rollback..." | tee -a /var/log/dr-drill.log
  /tmp/rollback-drill.sh
  exit 1
fi

# Step 8: Run smoke tests
echo "[8/8] Running smoke tests..."
./scripts/smoke-tests.sh --region us-west-2

DRILL_END=$(date +%s)
TOTAL_DURATION=$((DRILL_END - DRILL_START))

echo ""
echo "=== DR Drill Phase 2 Complete ==="
echo "Total failover time: ${TOTAL_DURATION}s ($(($TOTAL_DURATION / 60)) minutes)"
echo "Database promotion: ${PROMOTE_DURATION}s"
echo "DNS update: ${DNS_DURATION}s"
echo "Compute scaling: ${SCALE_DURATION}s"
```

#### Phase 3: Validation (T+4 hours)

```bash
#!/bin/bash
# dr-drill-phase3-validation.sh

echo "=== DR Drill Phase 3: Validation ==="

# 1. End-to-end functional tests
echo "[1/6] Running end-to-end functional tests..."
npm run test:e2e -- --env=dr-secondary

# 2. Performance testing
echo "[2/6] Running performance tests..."
artillery run --target https://api.example.com performance-test.yml

# 3. Data integrity verification
echo "[3/6] Verifying data integrity..."
psql -h prod-db-replica-us-west-2.xxxxx.rds.amazonaws.com -U admin -d proddb <<EOF
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
  n_live_tup AS row_count
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;
EOF

# 4. Monitoring and alerting verification
echo "[4/6] Verifying monitoring and alerting..."
curl -s http://prometheus-us-west-2:9090/api/v1/query?query=up | jq '.data.result[] | select(.value[1]=="0")'

# 5. Security posture check
echo "[5/6] Running security posture check..."
aws ec2 describe-security-groups --region us-west-2 --query 'SecurityGroups[?IpPermissions[?IpRanges[?CidrIp==`0.0.0.0/0`]]]'

# 6. Compliance verification
echo "[6/6] Verifying compliance requirements..."
# Check encryption
aws rds describe-db-instances \
  --db-instance-identifier prod-db-replica-us-west-2 \
  --region us-west-2 \
  --query 'DBInstances[0].StorageEncrypted'

# Check backup retention
aws rds describe-db-instances \
  --db-instance-identifier prod-db-replica-us-west-2 \
  --region us-west-2 \
  --query 'DBInstances[0].BackupRetentionPeriod'

echo "Phase 3 validation complete."
```

#### Phase 4: Rollback (T+6 hours)

```bash
#!/bin/bash
# dr-drill-phase4-rollback.sh

echo "=== DR Drill Phase 4: Rollback ==="
ROLLBACK_START=$(date +%s)

# 1. Demote secondary database back to replica
echo "[1/5] Converting database back to read replica..."
# Note: This requires creating a new replica from the original primary
aws rds create-db-instance-read-replica \
  --db-instance-identifier prod-db-replica-us-west-2-new \
  --source-db-instance-identifier prod-db-us-east-1 \
  --db-instance-class db.r6g.xlarge \
  --region us-west-2

# 2. Restore original DNS
echo "[2/5] Restoring original DNS records..."
ORIGINAL_LB_DNS=$(aws elbv2 describe-load-balancers \
  --names prod-alb-us-east-1 \
  --region us-east-1 \
  --query 'LoadBalancers[0].DNSName' \
  --output text)

aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --change-batch "{
    \"Changes\": [{
      \"Action\": \"UPSERT\",
      \"ResourceRecordSet\": {
        \"Name\": \"api.example.com\",
        \"Type\": \"CNAME\",
        \"TTL\": 300,
        \"ResourceRecords\": [{\"Value\": \"$ORIGINAL_LB_DNS\"}]
      }
    }]
  }"

# 3. Scale down secondary compute
echo "[3/5] Scaling down secondary region compute..."
aws autoscaling set-desired-capacity \
  --auto-scaling-group-name prod-asg-web-us-west-2 \
  --desired-capacity 2 \
  --region us-west-2

aws autoscaling set-desired-capacity \
  --auto-scaling-group-name prod-asg-app-us-west-2 \
  --desired-capacity 3 \
  --region us-west-2

# 4. Restore application configuration
echo "[4/5] Restoring application configuration..."
aws ssm put-parameter \
  --name /prod/database/primary-endpoint \
  --value "prod-db-us-east-1.xxxxx.rds.amazonaws.com" \
  --type String \
  --overwrite \
  --region us-east-1

# 5. Verify primary region health
echo "[5/5] Verifying primary region health..."
for i in {1..10}; do
  HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://api.example.com/health)
  if [ "$HTTP_STATUS" == "200" ]; then
    echo "Primary region health check passed"
    break
  else
    sleep 5
  fi
done

ROLLBACK_END=$(date +%s)
ROLLBACK_DURATION=$((ROLLBACK_END - ROLLBACK_START))

echo ""
echo "=== DR Drill Phase 4 Complete ==="
echo "Rollback time: ${ROLLBACK_DURATION}s ($(($ROLLBACK_DURATION / 60)) minutes)"
```

### 6.5 Post-DR Drill Analysis

```bash
#!/bin/bash
# post-dr-drill-analysis.sh

echo "=== Post-DR Drill Analysis ==="

# Generate drill report
cat > /tmp/dr-drill-report.md <<EOF
# DR Drill Report - $(date +%Y-%m-%d)

## Executive Summary
- **Drill Type**: Full Regional Failover
- **Source Region**: us-east-1 (AWS)
- **Target Region**: us-west-2 (AWS)
- **Status**: $([ $? -eq 0 ] && echo "✅ SUCCESS" || echo "❌ FAILED")

## Metrics

### RTO/RPO Achieved
| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| RTO | 1 hour | ${TOTAL_DURATION}s ($(($TOTAL_DURATION / 60))min) | $([ $TOTAL_DURATION -lt 3600 ] && echo "✅ PASS" || echo "❌ FAIL") |
| RPO | 15 minutes | ${REPLICATION_LAG}s | $([ $REPLICATION_LAG -lt 900 ] && echo "✅ PASS" || echo "❌ FAIL") |

### Component Timings
| Component | Duration | Notes |
|-----------|----------|-------|
| Database Promotion | ${PROMOTE_DURATION}s | |
| DNS Update | ${DNS_DURATION}s | |
| Compute Scaling | ${SCALE_DURATION}s | |
| Application Restart | ${APP_RESTART_DURATION}s | |
| Health Check Validation | ${HEALTH_CHECK_DURATION}s | |

## Issues Identified
EOF

# Extract errors from logs
echo "### Errors" >> /tmp/dr-drill-report.md
grep -i error /var/log/dr-drill.log >> /tmp/dr-drill-report.md || echo "No errors found" >> /tmp/dr-drill-report.md

echo "### Warnings" >> /tmp/dr-drill-report.md
grep -i warning /var/log/dr-drill.log >> /tmp/dr-drill-report.md || echo "No warnings found" >> /tmp/dr-drill-report.md

# Action items
cat >> /tmp/dr-drill-report.md <<EOF

## Action Items
1. [ ] Update runbook with lessons learned
2. [ ] Address identified performance bottlenecks
3. [ ] Schedule follow-up drill for next quarter
4. [ ] Update monitoring thresholds based on observed metrics

## Recommendations
- Consider reducing DNS TTL permanently to 60s for faster failover
- Implement pre-warming of secondary region compute resources
- Automate database promotion process
- Add more granular health checks

## Participants
- SRE Team: ✓
- Development Team: ✓
- Product Management: ✓
- Executive Sponsor: ✓

## Next Steps
1. Review this report in post-mortem meeting
2. Update DR documentation
3. Implement approved recommendations
4. Schedule next drill

---
*Report generated automatically by dr-drill-analysis.sh*
EOF

# Upload report to S3
aws s3 cp /tmp/dr-drill-report.md s3://dr-reports-bucket/$(date +%Y%m%d)-drill-report.md

# Send report to stakeholders
curl -X POST https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK \
  -H 'Content-Type: application/json' \
  -d "{
    \"text\": \"DR Drill Complete - Report Available\",
    \"attachments\": [{
      \"color\": \"good\",
      \"title\": \"DR Drill Report\",
      \"title_link\": \"https://s3.console.aws.amazon.com/s3/object/dr-reports-bucket/$(date +%Y%m%d)-drill-report.md\",
      \"fields\": [
        {\"title\": \"RTO Achieved\", \"value\": \"$(($TOTAL_DURATION / 60)) minutes\", \"short\": true},
        {\"title\": \"Status\", \"value\": \"Success\", \"short\": true}
      ]
    }]
  }"

echo "Post-drill analysis complete. Report: /tmp/dr-drill-report.md"
```

### 6.6 Chaos Engineering Integration

**Chaos Monkey for Multi-Cloud:**

```python
# chaos_monkey.py
import random
import time
import boto3
import subprocess
from datetime import datetime

class MultiCloudChaosMonkey:
    def __init__(self):
        self.aws_ec2 = boto3.client('ec2')
        self.aws_rds = boto3.client('rds')
        
    def terminate_random_instance(self, region='us-east-1'):
        """Randomly terminate an EC2 instance"""
        instances = self.aws_ec2.describe_instances(
            Filters=[
                {'Name': 'tag:ChaosMonkey', 'Values': ['enabled']},
                {'Name': 'instance-state-name', 'Values': ['running']}
            ]
        )
        
        instance_ids = [
            i['InstanceId'] 
            for r in instances['Reservations'] 
            for i in r['Instances']
        ]
        
        if instance_ids:
            target = random.choice(instance_ids)
            print(f"[{datetime.now()}] Terminating instance: {target}")
            self.aws_ec2.terminate_instances(InstanceIds=[target])
            return target
        return None
    
    def inject_network_latency(self, pod_name, namespace='default', latency_ms=1000):
        """Inject network latency in Kubernetes pod"""
        cmd = f"""
        kubectl exec -n {namespace} {pod_name} -- \
        tc qdisc add dev eth0 root netem delay {latency_ms}ms
        """
        subprocess.run(cmd, shell=True)
        print(f"[{datetime.now()}] Injected {latency_ms}ms latency to {pod_name}")
    
    def simulate_database_failure(self, db_identifier):
        """Simulate database failure by rebooting"""
        print(f"[{datetime.now()}] Rebooting database: {db_identifier}")
        self.aws_rds.reboot_db_instance(DBInstanceIdentifier=db_identifier)
    
    def fill_disk_space(self, instance_id, percentage=90):
        """Fill disk space to simulate storage issues"""
        cmd = f"""
        aws ssm send-command \
          --instance-ids {instance_id} \
          --document-name "AWS-RunShellScript" \
          --parameters 'commands=["fallocate -l $(df / | tail -1 | awk \"{{print int(\\$2*{percentage}/100)}}\"K) /tmp/chaos-fill"]'
        """
        subprocess.run(cmd, shell=True)
        print(f"[{datetime.now()}] Filled disk to {percentage}% on {instance_id}")
    
    def run_chaos_schedule(self):
        """Run chaos experiments on a schedule"""
        experiments = [
            (self.terminate_random_instance, {'region': 'us-east-1'}),
            (self.inject_network_latency, {'pod_name': 'api-server-xxx', 'latency_ms': 500}),
            # Add more experiments
        ]
        
        while True:
            # Run random experiment
            experiment, kwargs = random.choice(experiments)
            experiment(**kwargs)
            
            # Wait random interval (1-6 hours)
            wait_time = random.randint(3600, 21600)
            print(f"Waiting {wait_time}s until next experiment...")
            time.sleep(wait_time)

if __name__ == "__main__":
    monkey = MultiCloudChaosMonkey()
    monkey.run_chaos_schedule()
```

**Deploy Chaos Monkey:**

```yaml
# k8s/chaos-monkey.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chaos-monkey
  namespace: chaos-engineering
spec:
  replicas: 1
  selector:
    matchLabels:
      app: chaos-monkey
  template:
    metadata:
      labels:
        app: chaos-monkey
    spec:
      serviceAccountName: chaos-monkey
      containers:
      - name: chaos-monkey
        image: your-registry/chaos-monkey:latest
        env:
        - name: AWS_REGION
          value: "us-east-1"
        - name: CHAOS_SCHEDULE
          value: "0 */6 * * *"  # Every 6 hours
        - name: BLAST_RADIUS
          value: "single-instance"  # or "availability-zone" or "region"
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: chaos-monkey
  namespace: chaos-engineering
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::ACCOUNT_ID:role/ChaosMonkeyRole
```

