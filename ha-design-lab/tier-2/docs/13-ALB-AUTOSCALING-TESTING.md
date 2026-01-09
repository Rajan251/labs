# ✅ Step 13: ALB & Auto Scaling Testing - Complete Guide

> **Comprehensive Testing of Load Balancing and Auto-Scaling**

---

## 📋 What We'll Test

- ✅ Application Load Balancer functionality
- ✅ Load distribution across instances
- ✅ Target health checks
- ✅ Auto Scaling scale-out events
- ✅ Auto Scaling scale-in events
- ✅ Instance replacement on failure
- ✅ Multi-AZ failover

---

## 🧪 Test 1: Load Balancer Functionality

### Verify ALB is Working

1. **Get ALB DNS Name**
   ```bash
   # From AWS Console: EC2 → Load Balancers → tier2-alb
   # Copy DNS name: tier2-alb-xxx.us-east-1.elb.amazonaws.com
   ```

2. **Test HTTP Access**
   ```bash
   # From your local machine
   curl http://tier2-alb-xxx.us-east-1.elb.amazonaws.com
   
   # Should return HTML with instance information
   ```

3. **Test in Browser**
   - Open: `http://tier2-alb-xxx.us-east-1.elb.amazonaws.com`
   - Should see web page with instance details
   - Refresh multiple times - should see different instances

---

## 🧪 Test 2: Load Distribution

### Verify Traffic is Balanced

```bash
# Run multiple requests and check which instance responds
for i in {1..20}; do
  curl -s http://tier2-alb-xxx.us-east-1.elb.amazonaws.com | grep -i "instance id"
done

# Expected: Should see responses from different instances
# Example output:
# Instance ID: i-0abc123
# Instance ID: i-0def456
# Instance ID: i-0abc123
# Instance ID: i-0def456
# ...
```

**Verification**:
- ✅ Requests distributed across all healthy instances
- ✅ Roughly equal distribution over time
- ✅ No single instance handling all requests

---

## 🧪 Test 3: Target Health Checks

### Verify Health Check Mechanism

1. **Check Current Health**
   - Go to: EC2 → Target Groups → tier2-tg → Targets tab
   - All targets should show "healthy"

2. **Simulate Unhealthy Instance**
   ```bash
   # SSH to one instance via VPN
   ssh -i tier2-ec2-key.pem ec2-user@10.0.3.x
   
   # Stop web server
   sudo systemctl stop httpd
   ```

3. **Monitor Health Check**
   - Wait 30-60 seconds
   - Refresh Targets tab
   - Instance should show "unhealthy"

4. **Verify Traffic Routing**
   ```bash
   # From local machine
   for i in {1..10}; do
     curl -s http://tier2-alb-xxx.us-east-1.elb.amazonaws.com | grep "Instance ID"
   done
   
   # Should only see healthy instance responding
   ```

5. **Restore Instance**
   ```bash
   # On the instance
   sudo systemctl start httpd
   
   # Wait 30-60 seconds
   # Instance should become healthy again
   ```

---

## 🧪 Test 4: Auto Scaling - Scale Out

### Trigger Scale-Out Event

**Method 1: CPU Load**

```bash
# SSH to instances and generate CPU load
ssh -i tier2-ec2-key.pem ec2-user@10.0.3.x

# Install stress tool
sudo yum install -y stress

# Generate high CPU load (90%+)
stress --cpu 2 --timeout 600
```

**Method 2: Load Testing with Apache Bench**

```bash
# From your local machine
# Install Apache Bench if needed
# Ubuntu: sudo apt-get install apache2-utils
# macOS: brew install httpd

# Generate sustained load
ab -n 100000 -c 100 http://tier2-alb-xxx.us-east-1.elb.amazonaws.com/
```

**Monitor Scaling**:

1. **CloudWatch Metrics**
   - Go to: CloudWatch → Metrics → EC2 → By Auto Scaling Group
   - Watch CPUUtilization increase above 70%

2. **Auto Scaling Activity**
   - Go to: EC2 → Auto Scaling Groups → tier2-asg → Activity tab
   - Should see: "Launching a new EC2 instance"
   - Status: "Successful"

3. **Instance Count**
   - Go to: Instance management tab
   - Desired capacity should increase (e.g., 2 → 3 or 4)
   - New instances should appear with status "InService"

4. **Target Group**
   - Go to: Target Groups → tier2-tg → Targets tab
   - New instances should be registered
   - Health status: "healthy" (after warmup period)

**Expected Timeline**:
- **0-2 min**: CPU exceeds threshold
- **2-3 min**: Scaling policy triggers
- **3-5 min**: New instances launching
- **5-10 min**: Instances pass health checks and receive traffic

---

## 🧪 Test 5: Auto Scaling - Scale In

### Trigger Scale-In Event

1. **Stop Load Generation**
   - Stop stress command (Ctrl+C)
   - Stop Apache Bench

2. **Wait for Cool Down**
   - Wait 10-15 minutes
   - CPU should drop below 70%

3. **Monitor Scale-In**
   - Go to: ASG → Activity tab
   - Should see: "Terminating EC2 instance"
   - Oldest instances terminated first

4. **Verify Capacity**
   - Desired capacity should decrease back to minimum (2)
   - Extra instances should be terminated

**Expected Timeline**:
- **0-5 min**: CPU drops below threshold
- **5-10 min**: Scale-in cooldown period
- **10-15 min**: Instances begin terminating
- **15-20 min**: Back to minimum capacity

---

## 🧪 Test 6: Instance Replacement

### Test Automatic Instance Replacement

1. **Terminate an Instance Manually**
   - Go to: EC2 → Instances
   - Select one ASG instance
   - Actions → Instance State → Terminate

2. **Monitor Replacement**
   - Go to: ASG → Activity tab
   - Should see:
     - "Terminating EC2 instance" (the one you terminated)
     - "Launching a new EC2 instance" (replacement)

3. **Verify Capacity Maintained**
   - Desired capacity should remain the same
   - New instance launched to replace terminated one
   - Total instances = desired capacity

---

## 🧪 Test 7: Multi-AZ Failover

### Verify Multi-AZ Distribution

1. **Check Instance Distribution**
   ```bash
   # AWS CLI
   aws ec2 describe-instances \
     --filters "Name=tag:aws:autoscaling:groupName,Values=tier2-asg" \
     --query 'Reservations[*].Instances[*].[InstanceId,Placement.AvailabilityZone,State.Name]' \
     --output table
   ```

2. **Expected Distribution**
   - Instances should be roughly evenly distributed
   - Example: 2 in us-east-1a, 2 in us-east-1b

3. **Simulate AZ Failure**
   - Terminate all instances in one AZ
   - ASG should launch replacements in both AZs
   - Distribution should rebalance

---

## 🧪 Test 8: Load Testing

### Comprehensive Load Test

**Using Apache Bench**:

```bash
# Light load (baseline)
ab -n 1000 -c 10 http://tier2-alb-xxx.us-east-1.elb.amazonaws.com/

# Medium load
ab -n 10000 -c 50 http://tier2-alb-xxx.us-east-1.elb.amazonaws.com/

# Heavy load (should trigger scaling)
ab -n 100000 -c 200 http://tier2-alb-xxx.us-east-1.elb.amazonaws.com/
```

**Monitor During Load Test**:
1. ALB metrics (requests, response time)
2. Target health (should remain healthy)
3. Auto Scaling activity (scale out if needed)
4. CloudWatch metrics (CPU, network, requests)

---

## ✅ Complete Verification Checklist

### Load Balancer
- [ ] ALB accessible via DNS name
- [ ] Traffic distributed across instances
- [ ] Health checks working
- [ ] Unhealthy instances removed from rotation
- [ ] Instances automatically re-added when healthy

### Auto Scaling - Scale Out
- [ ] Scales out when CPU > 70%
- [ ] Scales out when requests exceed threshold
- [ ] New instances launch successfully
- [ ] New instances pass health checks
- [ ] New instances receive traffic

### Auto Scaling - Scale In
- [ ] Scales in when load decreases
- [ ] Respects minimum capacity
- [ ] Terminates oldest instances first
- [ ] Gradual scale-in (not all at once)

### Instance Management
- [ ] Failed instances automatically replaced
- [ ] Capacity maintained at desired level
- [ ] Multi-AZ distribution maintained
- [ ] Instances properly tagged

### Performance
- [ ] Response time acceptable under load
- [ ] No 503 errors during scaling
- [ ] Smooth transitions during scaling events
- [ ] Health checks don't cause false positives

---

## 📊 Monitoring Dashboard

### Key Metrics to Monitor

**CloudWatch Metrics**:
1. **ALB Metrics**:
   - TargetResponseTime
   - RequestCount
   - HealthyHostCount
   - UnHealthyHostCount
   - HTTPCode_Target_2XX_Count

2. **Auto Scaling Metrics**:
   - GroupDesiredCapacity
   - GroupInServiceInstances
   - GroupTotalInstances

3. **EC2 Metrics**:
   - CPUUtilization
   - NetworkIn/NetworkOut
   - StatusCheckFailed

---

## 🔧 Troubleshooting

### Issue: Scaling not triggering

**Debug Steps**:
```bash
# 1. Check CloudWatch alarms
# Go to CloudWatch → Alarms
# Verify alarms are in "In alarm" state

# 2. Check scaling policies
# Go to ASG → Automatic scaling tab
# Verify policies are enabled

# 3. Check if at max capacity
# Go to ASG → Details
# Current capacity = max capacity?

# 4. Check cooldown period
# Recent scaling activity may have triggered cooldown
```

---

### Issue: Instances unhealthy in target group

**Debug Steps**:
```bash
# SSH to instance
ssh -i tier2-ec2-key.pem ec2-user@10.0.3.x

# Check web server status
sudo systemctl status httpd

# Test locally
curl localhost
curl localhost/health

# Check security group
# Verify ALB can reach instance on port 80
```

---

### Issue: 503 Service Unavailable

**Causes**:
1. No healthy targets
2. All instances at capacity
3. Health check failing

**Solution**:
1. Check target health
2. Increase desired capacity manually
3. Fix health check endpoint
4. Verify security groups

---

## 📝 Test Results Template

```
Load Balancing & Auto Scaling Test Results
===========================================
Date: 2025-12-26
Tester: [Your Name]

Load Balancer Tests:
  ✅ ALB accessible
  ✅ Load distribution working
  ✅ Health checks functioning
  ✅ Unhealthy instance removal
  ✅ Instance re-addition

Auto Scaling Tests:
  ✅ Scale-out triggered (CPU > 70%)
  ✅ New instances launched: 2 → 4
  ✅ Scale-out time: ~5 minutes
  ✅ Scale-in triggered (CPU < 70%)
  ✅ Instances terminated: 4 → 2
  ✅ Scale-in time: ~15 minutes

Instance Management:
  ✅ Automatic replacement working
  ✅ Multi-AZ distribution maintained
  ✅ Capacity maintained at desired level

Load Testing:
  - Concurrent users tested: 200
  - Total requests: 100,000
  - Success rate: 99.9%
  - Average response time: 45ms
  - Max instances reached: 6

Issues Found:
  - None / [List any issues]

Overall Status: ✅ PASS

Notes:
  [Any additional observations]
```

---

## 🎯 Next Steps

✅ **All tests passed? Excellent!**

Your tier-2 architecture with load balancing and auto-scaling is fully functional!

### Recommended Actions:

1. **Set Up Monitoring**
   - Create CloudWatch dashboards
   - Set up SNS notifications for scaling events
   - Configure billing alerts

2. **Optimize Costs**
   - Review scaling policies
   - Adjust min/max capacity based on actual usage
   - Consider Reserved Instances or Savings Plans

3. **Production Readiness**
   - Enable ALB access logs
   - Set up WAF rules
   - Configure SSL/TLS certificates
   - Enable deletion protection

4. **Documentation**
   - Document your specific configuration
   - Create runbooks for common operations
   - Train team on scaling behavior

---

## 📖 Additional Resources

- [Load Testing Best Practices](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-testing.html)
- [Auto Scaling Monitoring](https://docs.aws.amazon.com/autoscaling/ec2/userguide/as-monitoring-features.html)
- [CloudWatch Dashboards](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Dashboards.html)

---

**Testing complete! 🎉 Your architecture is production-ready!**

Return to [Main README](../README.md) for overview.
