# 🧪 Step 6: Testing & Verification

> **Comprehensive Testing and Validation of Two-Tier Architecture**

---

## 📋 Testing Overview

This guide covers:
- Functional testing
- Load testing
- Failover testing
- Security testing
- Performance monitoring

---

## ✅ Functional Testing

### Test 1: Health Check Endpoint

```bash
# Test ALB health endpoint
curl http://$ALB_DNS/health

# Expected output:
{
  "status": "UP",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "uptime": 3600,
  "mongodb": "connected",
  "hostname": "ip-10-0-1-123"
}
```

### Test 2: Application Endpoints

```bash
# Test root endpoint
curl http://$ALB_DNS/

# Create test data
curl -X POST http://$ALB_DNS/api/items \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Item",
    "description": "Testing MongoDB integration",
    "price": 99.99
  }'

# Retrieve data
curl http://$ALB_DNS/api/items

# Test multiple times to verify load balancing
for i in {1..10}; do
  curl -s http://$ALB_DNS/ | jq '.hostname'
done
```

---

## 🔥 Load Testing

### Setup Load Testing Tools

```bash
# Install Apache Bench
sudo yum install -y httpd-tools

# Install wrk (advanced)
sudo yum install -y git gcc make
git clone https://github.com/wg/wrk.git
cd wrk
make
sudo cp wrk /usr/local/bin/
```

### Test 1: Basic Load Test (Apache Bench)

```bash
# 10,000 requests, 100 concurrent
ab -n 10000 -c 100 http://$ALB_DNS/

# Results to look for:
# - Requests per second
# - Time per request
# - Failed requests (should be 0)
```

### Test 2: Sustained Load Test (wrk)

```bash
# 12 threads, 400 connections, 30 seconds
wrk -t12 -c400 -d30s http://$ALB_DNS/

# Monitor auto-scaling during test
watch -n 5 'aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names webapp-asg \
  --query "AutoScalingGroups[0].[DesiredCapacity,Instances[].InstanceId]"'
```

### Test 3: Gradual Load Increase

```bash
#!/bin/bash
# gradual-load-test.sh

ALB_DNS="your-alb-dns-here"

for connections in 50 100 200 400 800; do
  echo "Testing with $connections connections..."
  wrk -t12 -c$connections -d60s http://$ALB_DNS/
  echo "Waiting 2 minutes for metrics..."
  sleep 120
done
```

---

## 🔄 Failover Testing

### Test 1: Instance Failure

```bash
# Get current instances
aws autoscaling describe-auto-scaling-instances \
  --query "AutoScalingInstances[?AutoScalingGroupName=='webapp-asg'].[InstanceId,HealthStatus]"

# Terminate one instance
INSTANCE_ID=$(aws autoscaling describe-auto-scaling-instances \
  --query "AutoScalingInstances[?AutoScalingGroupName=='webapp-asg'][0].InstanceId" \
  --output text)

aws ec2 terminate-instances --instance-ids $INSTANCE_ID

# Monitor replacement
watch -n 10 'aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names webapp-asg \
  --query "AutoScalingGroups[0].Instances[*].[InstanceId,LifecycleState,HealthStatus]"'

# Verify application still accessible
while true; do
  curl -s http://$ALB_DNS/health && echo " ✅" || echo " ❌"
  sleep 2
done
```

### Test 2: Database Failover

```bash
# Connect to MongoDB primary
mongosh "mongodb://$MONGO_PRIMARY_IP:27017" \
  -u admin -p YourPassword --authenticationDatabase admin

# Check replica set status
rs.status()

# Simulate primary failure (DO NOT DO IN PRODUCTION)
# Stop MongoDB on primary
sudo systemctl stop mongod

# Monitor secondary promotion (from another terminal)
watch -n 5 'mongosh "mongodb://$MONGO_SECONDARY_IP:27017" \
  -u admin -p YourPassword --authenticationDatabase admin \
  --eval "rs.isMaster()"'

# Verify application still works
curl http://$ALB_DNS/api/items
```

### Test 3: Availability Zone Failure

```bash
# Simulate AZ failure by stopping all instances in AZ-1
AZ1_INSTANCES=$(aws ec2 describe-instances \
  --filters \
    "Name=tag:aws:autoscaling:groupName,Values=webapp-asg" \
    "Name=availability-zone,Values=us-east-1a" \
    "Name=instance-state-name,Values=running" \
  --query "Reservations[].Instances[].InstanceId" \
  --output text)

echo "Stopping instances in AZ-1: $AZ1_INSTANCES"
aws ec2 stop-instances --instance-ids $AZ1_INSTANCES

# Monitor auto-scaling response
watch -n 10 'aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names webapp-asg \
  --query "AutoScalingGroups[0].Instances[*].[AvailabilityZone,InstanceId,HealthStatus]"'

# Verify application accessibility
for i in {1..60}; do
  curl -s http://$ALB_DNS/health && echo " ✅ $(date)" || echo " ❌ $(date)"
  sleep 5
done
```

---

## 🔒 Security Testing

### Test 1: Security Group Rules

```bash
# Test that database is NOT accessible from internet
timeout 5 nc -zv $MONGO_PRIMARY_IP 27017
# Should timeout (no connection)

# Test that database IS accessible from app tier
# SSH to app instance first
ssh -i mongodb-key.pem ec2-user@$APP_INSTANCE_IP
nc -zv $MONGO_PRIMARY_IP 27017
# Should succeed
```

### Test 2: SSL/TLS (if configured)

```bash
# Test HTTPS (if SSL certificate is configured)
curl -v https://$ALB_DNS/

# Check certificate details
openssl s_client -connect $ALB_DNS:443 -servername $ALB_DNS
```

### Test 3: Authentication

```bash
# Test MongoDB authentication
mongosh "mongodb://$MONGO_PRIMARY_IP:27017" --eval "db.adminCommand('ping')"
# Should fail without credentials

mongosh "mongodb://admin:YourPassword@$MONGO_PRIMARY_IP:27017/?authSource=admin" \
  --eval "db.adminCommand('ping')"
# Should succeed
```

---

## 📊 Performance Monitoring

### CloudWatch Metrics to Monitor

```bash
# CPU Utilization
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=AutoScalingGroupName,Value=webapp-asg \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum

# ALB Request Count
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name RequestCount \
  --dimensions Name=LoadBalancer,Value=app/$ALB_FULL_NAME \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum

# Target Response Time
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name TargetResponseTime \
  --dimensions Name=LoadBalancer,Value=app/$ALB_FULL_NAME \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum
```

### Create Monitoring Script

```bash
cat > monitor-performance.sh <<'EOF'
#!/bin/bash

ALB_DNS="your-alb-dns"
INTERVAL=10

echo "Monitoring Two-Tier Application Performance"
echo "==========================================="

while true; do
  # Get timestamp
  TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
  
  # Test response time
  RESPONSE_TIME=$(curl -o /dev/null -s -w '%{time_total}\n' http://$ALB_DNS/)
  
  # Test health
  HEALTH=$(curl -s http://$ALB_DNS/health | jq -r '.status')
  
  # Get instance count
  INSTANCE_COUNT=$(aws autoscaling describe-auto-scaling-groups \
    --auto-scaling-group-names webapp-asg \
    --query 'AutoScalingGroups[0].Instances | length(@)' \
    --output text)
  
  # Display
  echo "[$TIMESTAMP] Response: ${RESPONSE_TIME}s | Health: $HEALTH | Instances: $INSTANCE_COUNT"
  
  sleep $INTERVAL
done
EOF

chmod +x monitor-performance.sh
./monitor-performance.sh
```

---

## 🎯 Acceptance Criteria

### ✅ Functional Requirements

- [ ] All endpoints return 200 OK
- [ ] Health check passes consistently
- [ ] Data persists in MongoDB
- [ ] Load balancer distributes traffic evenly
- [ ] Auto-scaling group maintains desired capacity

### ✅ Performance Requirements

- [ ] Response time < 500ms (95th percentile)
- [ ] Handles 1000+ requests/second
- [ ] Zero downtime during instance replacement
- [ ] Auto-scaling triggers within 2 minutes
- [ ] Database replication lag < 1 second

### ✅ Availability Requirements

- [ ] Application accessible 99.9% of time
- [ ] Survives single instance failure
- [ ] Survives single AZ failure
- [ ] Database failover < 60 seconds
- [ ] No data loss during failover

### ✅ Security Requirements

- [ ] Database not accessible from internet
- [ ] MongoDB authentication enabled
- [ ] EBS volumes encrypted
- [ ] Security groups follow least privilege
- [ ] No sensitive data in logs

---

## 🔧 Troubleshooting

### Issue: High Response Times

```bash
# Check target health
aws elbv2 describe-target-health --target-group-arn $TG_ARN

# Check instance CPU
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=AutoScalingGroupName,Value=webapp-asg \
  --start-time $(date -u -d '10 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Average

# Check application logs
ssh -i mongodb-key.pem ec2-user@$INSTANCE_IP
sudo journalctl -u webapp -f
```

### Issue: Failed Health Checks

```bash
# Check health endpoint directly
curl http://$INSTANCE_IP/health

# Check NGINX status
ssh -i mongodb-key.pem ec2-user@$INSTANCE_IP
sudo systemctl status nginx
sudo systemctl status webapp

# Check logs
sudo tail -f /var/log/nginx/error.log
```

### Issue: Database Connection Failures

```bash
# Test MongoDB connectivity
mongosh "mongodb://$MONGO_PRIMARY_IP:27017" \
  -u appuser -p AppPassword --authenticationDatabase myapp \
  --eval "db.adminCommand('ping')"

# Check replica set status
mongosh "mongodb://$MONGO_PRIMARY_IP:27017" \
  -u admin -p AdminPassword --authenticationDatabase admin \
  --eval "rs.status()"

# Check MongoDB logs
ssh -i mongodb-key.pem ec2-user@$MONGO_PRIMARY_IP
sudo tail -f /var/log/mongodb/mongod.log
```

---

## 📈 Performance Benchmarks

### Expected Results

| Metric | Target | Acceptable | Poor |
|--------|--------|------------|------|
| Response Time (avg) | < 200ms | < 500ms | > 500ms |
| Response Time (p95) | < 500ms | < 1000ms | > 1000ms |
| Requests/sec | > 1000 | > 500 | < 500 |
| Error Rate | < 0.1% | < 1% | > 1% |
| CPU Utilization | 40-60% | 60-80% | > 80% |
| Memory Utilization | 40-60% | 60-80% | > 80% |

---

## 🎯 Next Steps

After successful testing:

1. **Production Deployment**
   - Configure SSL/TLS certificates
   - Set up CloudWatch alarms with SNS notifications
   - Configure automated backups
   - Implement CI/CD pipeline

2. **Monitoring & Alerting**
   - Create CloudWatch dashboards
   - Set up log aggregation
   - Configure PagerDuty/Slack alerts
   - Implement APM (Application Performance Monitoring)

3. **Optimization**
   - Fine-tune auto-scaling policies
   - Optimize database queries
   - Implement caching (Redis/ElastiCache)
   - CDN for static assets

---

**Testing complete! Ready for production! 🚀**
