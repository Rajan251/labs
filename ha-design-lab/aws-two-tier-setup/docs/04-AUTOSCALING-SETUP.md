# ⚡ Step 4: Auto-Scaling Configuration

> **Configuring Auto-Scaling Group with Dynamic Scaling Policies**

---

## 📋 What We'll Configure

- ✅ Auto-Scaling Group (ASG)
- ✅ Scaling policies (scale out/in)
- ✅ CloudWatch alarms
- ✅ Target tracking policies
- ✅ Health checks
- ✅ Lifecycle hooks

---

## 🎯 Auto-Scaling Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Auto-Scaling Group                                     │
│                                                           │
│  Min: 2  │  Desired: 2  │  Max: 10                      │
│                                                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Scaling Policies                               │   │
│  ├─────────────────────────────────────────────────┤   │
│  │                                                  │   │
│  │  📈 Scale Out Triggers:                         │   │
│  │  • CPU > 70% for 2 minutes                      │   │
│  │  • Memory > 75% for 2 minutes                   │   │
│  │  • Request count > 1000/min                     │   │
│  │  • Target response time > 2s                    │   │
│  │                                                  │   │
│  │  📉 Scale In Triggers:                          │   │
│  │  • CPU < 30% for 5 minutes                      │   │
│  │  • Memory < 35% for 5 minutes                   │   │
│  │  • Request count < 200/min                      │   │
│  │                                                  │   │
│  └─────────────────────────────────────────────────┘   │
│                                                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Health Checks                                  │   │
│  ├─────────────────────────────────────────────────┤   │
│  │  • ELB Health Check: /health (every 30s)        │   │
│  │  • EC2 Status Check: (every 60s)                │   │
│  │  • Grace Period: 300s                           │   │
│  │  • Unhealthy Threshold: 3 consecutive failures  │   │
│  └─────────────────────────────────────────────────┘   │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

---

## 🚀 Step-by-Step Setup

### 📍 **STEP 4.1: Create Auto-Scaling Group**

```bash
# ============================================
# RUN ON: Your Local Machine
# ============================================

# Load infrastructure IDs
source infrastructure-ids.txt

# Create Auto-Scaling Group
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name webapp-asg \
  --launch-template LaunchTemplateId=$LAUNCH_TEMPLATE_ID,Version='$Latest' \
  --min-size 2 \
  --max-size 10 \
  --desired-capacity 2 \
  --default-cooldown 300 \
  --health-check-type ELB \
  --health-check-grace-period 300 \
  --vpc-zone-identifier "$PUBLIC_SUBNET_1,$PUBLIC_SUBNET_2" \
  --target-group-arns $TG_ARN \
  --tags \
    "Key=Name,Value=webapp-asg-instance,PropagateAtLaunch=true" \
    "Key=Environment,Value=production,PropagateAtLaunch=true" \
    "Key=ManagedBy,Value=AutoScaling,PropagateAtLaunch=true"

echo "✅ Auto-Scaling Group created: webapp-asg"

# Wait for instances to launch
echo "⏳ Waiting for instances to launch..."
sleep 120

# Check ASG status
aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names webapp-asg
```

---

### 📍 **STEP 4.2: Create Target Tracking Scaling Policy (CPU)**

```bash
# ============================================
# RUN ON: Your Local Machine
# ============================================

# Create target tracking policy for CPU
cat > cpu-target-tracking-policy.json <<'EOF'
{
  "TargetValue": 70.0,
  "PredefinedMetricSpecification": {
    "PredefinedMetricType": "ASGAverageCPUUtilization"
  },
  "ScaleInCooldown": 300,
  "ScaleOutCooldown": 60
}
EOF

aws autoscaling put-scaling-policy \
  --auto-scaling-group-name webapp-asg \
  --policy-name cpu-target-tracking-policy \
  --policy-type TargetTrackingScaling \
  --target-tracking-configuration file://cpu-target-tracking-policy.json

echo "✅ CPU target tracking policy created"
```

---

### 📍 **STEP 4.3: Create Target Tracking Scaling Policy (ALB Request Count)**

```bash
# ============================================
# RUN ON: Your Local Machine
# ============================================

# Get ALB full name
ALB_FULL_NAME=$(aws elbv2 describe-load-balancers \
  --load-balancer-arns $ALB_ARN \
  --query 'LoadBalancers[0].LoadBalancerName' \
  --output text)

# Get target group full name
TG_FULL_NAME=$(aws elbv2 describe-target-groups \
  --target-group-arns $TG_ARN \
  --query 'TargetGroups[0].TargetGroupName' \
  --output text)

# Create target tracking policy for request count
cat > request-count-target-tracking-policy.json <<EOF
{
  "TargetValue": 1000.0,
  "PredefinedMetricSpecification": {
    "PredefinedMetricType": "ALBRequestCountPerTarget",
    "ResourceLabel": "app/$ALB_FULL_NAME/targetgroup/$TG_FULL_NAME"
  },
  "ScaleInCooldown": 300,
  "ScaleOutCooldown": 60
}
EOF

aws autoscaling put-scaling-policy \
  --auto-scaling-group-name webapp-asg \
  --policy-name request-count-target-tracking-policy \
  --policy-type TargetTrackingScaling \
  --target-tracking-configuration file://request-count-target-tracking-policy.json

echo "✅ Request count target tracking policy created"
```

---

### 📍 **STEP 4.4: Create Step Scaling Policy (Memory)**

```bash
# ============================================
# RUN ON: Your Local Machine
# ============================================

# Create CloudWatch alarm for high memory
aws cloudwatch put-metric-alarm \
  --alarm-name webapp-high-memory \
  --alarm-description "Trigger when memory utilization is high" \
  --metric-name MemoryUtilization \
  --namespace WebApp \
  --statistic Average \
  --period 120 \
  --evaluation-periods 2 \
  --threshold 75 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=AutoScalingGroupName,Value=webapp-asg

echo "✅ High memory alarm created"

# Create CloudWatch alarm for low memory
aws cloudwatch put-metric-alarm \
  --alarm-name webapp-low-memory \
  --alarm-description "Trigger when memory utilization is low" \
  --metric-name MemoryUtilization \
  --namespace WebApp \
  --statistic Average \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 35 \
  --comparison-operator LessThanThreshold \
  --dimensions Name=AutoScalingGroupName,Value=webapp-asg

echo "✅ Low memory alarm created"

# Create step scaling policy for scale out
cat > scale-out-policy.json <<'EOF'
{
  "AdjustmentType": "ChangeInCapacity",
  "StepAdjustments": [
    {
      "MetricIntervalLowerBound": 0,
      "MetricIntervalUpperBound": 10,
      "ScalingAdjustment": 1
    },
    {
      "MetricIntervalLowerBound": 10,
      "ScalingAdjustment": 2
    }
  ],
  "MetricAggregationType": "Average"
}
EOF

SCALE_OUT_POLICY_ARN=$(aws autoscaling put-scaling-policy \
  --auto-scaling-group-name webapp-asg \
  --policy-name memory-scale-out-policy \
  --policy-type StepScaling \
  --adjustment-type ChangeInCapacity \
  --step-adjustments file://scale-out-policy.json \
  --query 'PolicyARN' \
  --output text)

echo "✅ Scale out policy created: $SCALE_OUT_POLICY_ARN"

# Create step scaling policy for scale in
cat > scale-in-policy.json <<'EOF'
{
  "AdjustmentType": "ChangeInCapacity",
  "StepAdjustments": [
    {
      "MetricIntervalUpperBound": 0,
      "ScalingAdjustment": -1
    }
  ],
  "MetricAggregationType": "Average"
}
EOF

SCALE_IN_POLICY_ARN=$(aws autoscaling put-scaling-policy \
  --auto-scaling-group-name webapp-asg \
  --policy-name memory-scale-in-policy \
  --policy-type StepScaling \
  --adjustment-type ChangeInCapacity \
  --step-adjustments file://scale-in-policy.json \
  --query 'PolicyARN' \
  --output text)

echo "✅ Scale in policy created: $SCALE_IN_POLICY_ARN"

# Link alarms to policies
aws cloudwatch put-metric-alarm \
  --alarm-name webapp-high-memory \
  --alarm-actions $SCALE_OUT_POLICY_ARN

aws cloudwatch put-metric-alarm \
  --alarm-name webapp-low-memory \
  --alarm-actions $SCALE_IN_POLICY_ARN

echo "✅ Alarms linked to scaling policies"
```

---

### 📍 **STEP 4.5: Create Additional CloudWatch Alarms**

```bash
# ============================================
# RUN ON: Your Local Machine
# ============================================

# Alarm for unhealthy targets
aws cloudwatch put-metric-alarm \
  --alarm-name webapp-unhealthy-targets \
  --alarm-description "Alert when targets are unhealthy" \
  --metric-name UnHealthyHostCount \
  --namespace AWS/ApplicationELB \
  --statistic Average \
  --period 60 \
  --evaluation-periods 2 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --dimensions \
    Name=LoadBalancer,Value=app/$ALB_FULL_NAME \
    Name=TargetGroup,Value=targetgroup/$TG_FULL_NAME

echo "✅ Unhealthy targets alarm created"

# Alarm for high response time
aws cloudwatch put-metric-alarm \
  --alarm-name webapp-high-response-time \
  --alarm-description "Alert when response time is high" \
  --metric-name TargetResponseTime \
  --namespace AWS/ApplicationELB \
  --statistic Average \
  --period 60 \
  --evaluation-periods 3 \
  --threshold 2.0 \
  --comparison-operator GreaterThanThreshold \
  --dimensions \
    Name=LoadBalancer,Value=app/$ALB_FULL_NAME \
    Name=TargetGroup,Value=targetgroup/$TG_FULL_NAME

echo "✅ High response time alarm created"

# Alarm for 5xx errors
aws cloudwatch put-metric-alarm \
  --alarm-name webapp-5xx-errors \
  --alarm-description "Alert on 5xx errors" \
  --metric-name HTTPCode_Target_5XX_Count \
  --namespace AWS/ApplicationELB \
  --statistic Sum \
  --period 60 \
  --evaluation-periods 2 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --dimensions \
    Name=LoadBalancer,Value=app/$ALB_FULL_NAME \
    Name=TargetGroup,Value=targetgroup/$TG_FULL_NAME

echo "✅ 5xx errors alarm created"
```

---

### 📍 **STEP 4.6: Configure Lifecycle Hooks**

```bash
# ============================================
# RUN ON: Your Local Machine
# ============================================

# Create lifecycle hook for instance launch
aws autoscaling put-lifecycle-hook \
  --lifecycle-hook-name webapp-launch-hook \
  --auto-scaling-group-name webapp-asg \
  --lifecycle-transition autoscaling:EC2_INSTANCE_LAUNCHING \
  --default-result CONTINUE \
  --heartbeat-timeout 300 \
  --notification-metadata "Launching new instance"

echo "✅ Launch lifecycle hook created"

# Create lifecycle hook for instance termination
aws autoscaling put-lifecycle-hook \
  --lifecycle-hook-name webapp-terminate-hook \
  --auto-scaling-group-name webapp-asg \
  --lifecycle-transition autoscaling:EC2_INSTANCE_TERMINATING \
  --default-result CONTINUE \
  --heartbeat-timeout 120 \
  --notification-metadata "Terminating instance"

echo "✅ Terminate lifecycle hook created"
```

---

### 📍 **STEP 4.7: Configure Scheduled Scaling (Optional)**

```bash
# ============================================
# RUN ON: Your Local Machine
# ============================================

# Scale up during business hours (8 AM UTC)
aws autoscaling put-scheduled-action \
  --auto-scaling-group-name webapp-asg \
  --scheduled-action-name scale-up-business-hours \
  --recurrence "0 8 * * MON-FRI" \
  --min-size 4 \
  --max-size 10 \
  --desired-capacity 4

echo "✅ Business hours scale-up scheduled"

# Scale down after business hours (6 PM UTC)
aws autoscaling put-scheduled-action \
  --auto-scaling-group-name webapp-asg \
  --scheduled-action-name scale-down-after-hours \
  --recurrence "0 18 * * MON-FRI" \
  --min-size 2 \
  --max-size 10 \
  --desired-capacity 2

echo "✅ After hours scale-down scheduled"
```

---

## ✅ Verification

### Check Auto-Scaling Group

```bash
# Describe ASG
aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names webapp-asg

# List instances in ASG
aws autoscaling describe-auto-scaling-instances \
  --query "AutoScalingInstances[?AutoScalingGroupName=='webapp-asg']"
```

### Check Scaling Policies

```bash
# List all policies
aws autoscaling describe-policies \
  --auto-scaling-group-name webapp-asg

# Check target tracking policies
aws autoscaling describe-policies \
  --auto-scaling-group-name webapp-asg \
  --policy-types TargetTrackingScaling
```

### Check CloudWatch Alarms

```bash
# List all alarms
aws cloudwatch describe-alarms \
  --alarm-name-prefix webapp-

# Check alarm history
aws cloudwatch describe-alarm-history \
  --alarm-name webapp-high-memory \
  --max-records 10
```

### Monitor Scaling Activities

```bash
# View scaling activities
aws autoscaling describe-scaling-activities \
  --auto-scaling-group-name webapp-asg \
  --max-records 20

# Watch in real-time
watch -n 10 'aws autoscaling describe-scaling-activities \
  --auto-scaling-group-name webapp-asg \
  --max-records 5'
```

---

## 🧪 Testing Auto-Scaling

### Test 1: CPU-Based Scaling

```bash
# SSH to an instance
INSTANCE_ID=$(aws autoscaling describe-auto-scaling-instances \
  --query "AutoScalingInstances[?AutoScalingGroupName=='webapp-asg'][0].InstanceId" \
  --output text)

INSTANCE_IP=$(aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)

ssh -i mongodb-key.pem ec2-user@$INSTANCE_IP

# Generate CPU load
sudo yum install -y stress
stress --cpu 4 --timeout 600s

# Monitor from local machine
watch -n 10 'aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=AutoScalingGroupName,Value=webapp-asg \
  --start-time $(date -u -d "10 minutes ago" +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Average'
```

### Test 2: Load Testing

```bash
# Install Apache Bench
sudo yum install -y httpd-tools

# Run load test
ab -n 10000 -c 100 http://$ALB_DNS/

# Or use wrk for more advanced testing
sudo yum install -y git gcc make
git clone https://github.com/wg/wrk.git
cd wrk
make
sudo cp wrk /usr/local/bin/

# Run wrk test
wrk -t12 -c400 -d30s http://$ALB_DNS/
```

### Test 3: Manual Scaling

```bash
# Manually set desired capacity
aws autoscaling set-desired-capacity \
  --auto-scaling-group-name webapp-asg \
  --desired-capacity 5

# Wait and verify
sleep 120
aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names webapp-asg \
  --query 'AutoScalingGroups[0].[MinSize,DesiredCapacity,MaxSize,Instances[].InstanceId]'
```

---

## 📊 Auto-Scaling Configuration Summary

| Parameter | Value |
|-----------|-------|
| **Min Size** | 2 |
| **Max Size** | 10 |
| **Desired Capacity** | 2 |
| **Health Check Grace Period** | 300 seconds |
| **Default Cooldown** | 300 seconds |
| **Health Check Type** | ELB |
| **Scaling Policies** | 3 (CPU, Request Count, Memory) |
| **CloudWatch Alarms** | 5 |

### Scaling Triggers

| Metric | Scale Out | Scale In |
|--------|-----------|----------|
| **CPU** | > 70% | < 30% |
| **Memory** | > 75% | < 35% |
| **Requests/Target** | > 1000 | < 200 |
| **Response Time** | > 2s | N/A |

---

## 🎯 Best Practices

### 1. Cooldown Periods
- **Scale Out**: 60 seconds (quick response)
- **Scale In**: 300 seconds (prevent flapping)

### 2. Health Checks
- Use ELB health checks for application-level monitoring
- Set appropriate grace period (300s for initialization)

### 3. Monitoring
- Monitor scaling activities regularly
- Set up SNS notifications for scaling events
- Review CloudWatch metrics daily

### 4. Cost Optimization
- Use scheduled scaling for predictable patterns
- Set appropriate max size to control costs
- Monitor unused capacity

---

## 🔧 Troubleshooting

### Issue: "Instances not scaling out"
**Solution**: 
- Check CloudWatch alarms are in ALARM state
- Verify scaling policies are attached
- Check if max capacity is reached

### Issue: "Instances scaling in too quickly"
**Solution**: 
- Increase scale-in cooldown period
- Adjust threshold values
- Review metric data points

### Issue: "Health checks failing"
**Solution**: 
- Verify /health endpoint is responding
- Check security group rules
- Increase health check grace period

### Issue: "New instances not receiving traffic"
**Solution**: 
- Verify target group registration
- Check health check configuration
- Review ALB listener rules

---

## 🎯 Next Steps

✅ **Auto-scaling is configured!**

Now proceed to:
1. **[Web UI Setup Steps](./05-WEB-UI-STEPS.md)** - AWS Console guide
2. **[Testing & Verification](./06-TESTING-VERIFICATION.md)** - Comprehensive testing

---

**Auto-scaling configuration complete! 🎉**
