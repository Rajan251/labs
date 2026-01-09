# 📊 Step 12: Scaling Policies - Web UI Guide

> **Configuring Automatic Scaling Based on Metrics**

---

## 📋 What We'll Create

- ✅ Target tracking scaling policy (CPU-based)
- ✅ Target tracking scaling policy (ALB request count)
- ✅ Step scaling policy (advanced)
- ✅ CloudWatch alarms for scaling
- ✅ Scaling cooldowns

---

## 🎯 Overview

**Scaling Policies** define when and how Auto Scaling should add or remove instances:

### Policy Types

1. **Target Tracking**: Maintain a specific metric value (recommended)
   - Example: Keep CPU at 70%
   
2. **Step Scaling**: Scale based on alarm thresholds
   - Example: Add 2 instances if CPU > 80%

3. **Simple Scaling**: Add/remove fixed number of instances
   - Example: Always add 1 instance when alarm triggers

4. **Scheduled Scaling**: Scale at specific times
   - Example: Scale up at 9 AM, scale down at 6 PM

---

## 🚀 Part 1: Target Tracking - CPU Based

### Step 12.1: Create CPU-Based Scaling Policy

1. **Navigate to Auto Scaling Group**
   - Go to EC2 → Auto Scaling Groups
   - Select **tier2-asg**

2. **Go to Automatic Scaling Tab**
   - Click the **"Automatic scaling"** tab
   - Click **"Create dynamic scaling policy"**

3. **Configure Policy**

   **Policy type:**
   - Select **"Target tracking scaling"**

   **Scaling policy name:**
   - `tier2-cpu-target-tracking`

   **Metric type:**
   - Select **"Average CPU utilization"**

   **Target value:**
   - Enter `70` (maintain 70% CPU utilization)

   **Instance warmup:**
   - `300` seconds (5 minutes)
   - Allows new instances to warm up before receiving full traffic

   **Disable scale-in** (optional):
   - Leave unchecked (allow automatic scale-in)

4. **Create Policy**
   - Click **"Create"**
   - Policy will be created with CloudWatch alarms automatically

---

## 🚀 Part 2: Target Tracking - Request Count

### Step 12.2: Create Request-Based Scaling Policy

1. **Create Another Policy**
   - In **Automatic scaling** tab
   - Click **"Create dynamic scaling policy"**

2. **Configure Policy**

   **Policy type:**
   - Select **"Target tracking scaling"**

   **Scaling policy name:**
   - `tier2-request-target-tracking`

   **Metric type:**
   - Select **"Application Load Balancer request count per target"**

   **Target group:**
   - Select **tier2-tg**

   **Target value:**
   - Enter `1000` (1000 requests per minute per instance)

   **Instance warmup:**
   - `300` seconds

3. **Create Policy**
   - Click **"Create"**

---

## 🚀 Part 3: Step Scaling Policy (Advanced)

### Step 12.3: Create CloudWatch Alarm

First, create a CloudWatch alarm for high CPU:

1. **Open CloudWatch**
   - Go to https://console.aws.amazon.com/cloudwatch/

2. **Create Alarm**
   - Click **"Alarms"** → **"All alarms"**
   - Click **"Create alarm"**

3. **Select Metric**
   - Click **"Select metric"**
   - Choose **"EC2"** → **"By Auto Scaling Group"**
   - Select **CPUUtilization** for **tier2-asg**
   - Click **"Select metric"**

4. **Configure Alarm**
   - **Statistic**: Average
   - **Period**: 1 minute
   - **Threshold type**: Static
   - **Whenever CPUUtilization is**: Greater than `80`
   - Click **"Next"**

5. **Configure Actions**
   - **Alarm state trigger**: In alarm
   - **Send notification**: Skip for now (or configure SNS)
   - Click **"Next"**

6. **Name Alarm**
   - **Alarm name**: `tier2-high-cpu-alarm`
   - Click **"Next"** → **"Create alarm"**

---

### Step 12.4: Create Step Scaling Policy

1. **Back to Auto Scaling Group**
   - Go to **tier2-asg** → **Automatic scaling** tab
   - Click **"Create dynamic scaling policy"**

2. **Configure Step Scaling**

   **Policy type:**
   - Select **"Step scaling"**

   **Scaling policy name:**
   - `tier2-step-scale-out`

   **CloudWatch alarm:**
   - Select **tier2-high-cpu-alarm**

   **Take the action:**
   - **Add** `2` **capacity units** when `80 <= CPUUtilization < +infinity`

   **Instance warmup:**
   - `300` seconds

3. **Create Policy**
   - Click **"Create"**

---

## 🚀 Part 4: Scheduled Scaling (Optional)

### Step 12.5: Create Scheduled Action

For predictable traffic patterns:

1. **Go to Automatic Scaling Tab**
   - Click **"Create scheduled action"**

2. **Configure Schedule**

   **Name:**
   - `tier2-scale-up-morning`

   **Desired capacity:**
   - `4`

   **Min:**
   - `4`

   **Max:**
   - `10`

   **Recurrence:**
   - Select **"Cron"**
   - Enter: `0 9 * * MON-FRI` (9 AM weekdays)
   - Timezone: Select your timezone

3. **Create Scheduled Action**
   - Click **"Create"**

4. **Create Scale-Down Schedule**
   - Repeat for evening scale-down
   - Name: `tier2-scale-down-evening`
   - Desired: `2`, Min: `2`, Max: `10`
   - Cron: `0 18 * * MON-FRI` (6 PM weekdays)

---

## ✅ Verification Checklist

### Target Tracking Policies
- [ ] CPU-based policy created
  - Target: 70% CPU
  - Warmup: 300 seconds
- [ ] Request-based policy created
  - Target: 1000 requests/min/instance
  - Warmup: 300 seconds

### Step Scaling (Optional)
- [ ] CloudWatch alarm created
- [ ] Step scaling policy created
- [ ] Action: Add 2 instances when CPU > 80%

### Scheduled Scaling (Optional)
- [ ] Morning scale-up scheduled
- [ ] Evening scale-down scheduled

---

## 📊 What We Created

```
┌─────────────────────────────────────────────────────────────┐
│         Auto Scaling Policies: tier2-asg                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Target Tracking - CPU                                   │
│     ┌────────────────────────────────────────────────────┐  │
│     │ Policy: tier2-cpu-target-tracking                  │  │
│     │ Metric: Average CPU Utilization                    │  │
│     │ Target: 70%                                        │  │
│     │ Action: Scale out/in to maintain 70% CPU          │  │
│     └────────────────────────────────────────────────────┘  │
│                                                              │
│  2. Target Tracking - Requests                              │
│     ┌────────────────────────────────────────────────────┐  │
│     │ Policy: tier2-request-target-tracking             │  │
│     │ Metric: ALB Request Count per Target              │  │
│     │ Target: 1000 requests/min/instance                │  │
│     │ Action: Scale based on request load               │  │
│     └────────────────────────────────────────────────────┘  │
│                                                              │
│  3. Step Scaling (Optional)                                 │
│     ┌────────────────────────────────────────────────────┐  │
│     │ Policy: tier2-step-scale-out                      │  │
│     │ Alarm: tier2-high-cpu-alarm                       │  │
│     │ Threshold: CPU > 80%                              │  │
│     │ Action: Add 2 instances                           │  │
│     └────────────────────────────────────────────────────┘  │
│                                                              │
│  4. Scheduled Scaling (Optional)                            │
│     ┌────────────────────────────────────────────────────┐  │
│     │ Morning: Scale to 4 instances at 9 AM (weekdays)  │  │
│     │ Evening: Scale to 2 instances at 6 PM (weekdays)  │  │
│     └────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧪 Test Scaling Policies

### Test CPU-Based Scaling

1. **Generate CPU Load**

   SSH to one of the instances via VPN:
   ```bash
   ssh -i tier2-ec2-key.pem ec2-user@10.0.3.x
   
   # Install stress tool
   sudo yum install -y stress
   
   # Generate CPU load (use all cores for 10 minutes)
   stress --cpu 2 --timeout 600
   ```

2. **Monitor Scaling**
   - Go to ASG → **Monitoring** tab
   - Watch CPU utilization increase
   - When it exceeds 70%, scaling should trigger
   - Check **Activity** tab for scale-out events

3. **Verify New Instances**
   - New instances should launch
   - Check **Instance management** tab
   - Desired capacity should increase

4. **Stop Load**
   - Stop the stress command (Ctrl+C)
   - Wait 5-10 minutes
   - CPU should drop below 70%
   - ASG should scale in (terminate extra instances)

---

### Test Request-Based Scaling

1. **Generate Load with Apache Bench**

   From your local machine:
   ```bash
   # Install Apache Bench
   # Ubuntu/Debian: sudo apt-get install apache2-utils
   # macOS: brew install httpd (includes ab)
   
   # Generate load
   ab -n 100000 -c 100 http://tier2-alb-xxx.us-east-1.elb.amazonaws.com/
   ```

2. **Monitor**
   - Go to CloudWatch → Metrics
   - Check ALB request count
   - Watch ASG scale out when requests exceed threshold

---

## 🔧 Troubleshooting

### Issue: Scaling not triggering

**Possible causes**:
1. Metric not reaching threshold
2. Cooldown period active
3. Already at max capacity

**Solution**:
```bash
# Check CloudWatch metrics
# Go to CloudWatch → Metrics → EC2 → By Auto Scaling Group

# Check scaling activities
# Go to ASG → Activity tab
# Look for "WaitingForInstanceWarmup" or "InProgress"

# Check if at max capacity
# Go to ASG → Details tab
# Verify current capacity < max capacity
```

---

### Issue: Scaling too aggressive

**Solution**:
1. Increase target value (e.g., 70% → 80%)
2. Increase warmup period (300s → 600s)
3. Adjust alarm evaluation periods

---

### Issue: Instances terminating too quickly

**Solution**:
1. Increase scale-in cooldown
2. Enable scale-in protection for critical instances
3. Adjust target value to be less sensitive

---

## 💡 Best Practices

### Policy Selection
- ✅ Use target tracking for most cases (simplest)
- ✅ Use step scaling for fine-grained control
- ✅ Combine multiple policies (CPU + requests)
- ✅ Use scheduled scaling for predictable patterns

### Target Values
- ✅ CPU: 60-80% (allows headroom for spikes)
- ✅ Requests: Based on application capacity testing
- ✅ Start conservative, adjust based on monitoring
- ✅ Consider application-specific metrics

### Cooldowns and Warmup
- ✅ Set warmup = time for instance to be fully ready
- ✅ Default cooldown: 300 seconds (5 minutes)
- ✅ Longer cooldowns prevent thrashing
- ✅ Shorter cooldowns for faster response

### Monitoring
- ✅ Set up CloudWatch dashboards
- ✅ Create alarms for unusual scaling
- ✅ Monitor scaling activities regularly
- ✅ Review and adjust policies based on patterns

### Cost Optimization
- ✅ Set appropriate max capacity
- ✅ Use scheduled scaling to reduce off-peak costs
- ✅ Monitor actual usage vs. capacity
- ✅ Consider Savings Plans or Reserved Instances

---

## 📝 Save Your Configuration

```
Scaling Policies Configuration - Tier 2 Architecture
=====================================================

Target Tracking Policies:
  1. CPU-Based:
     Name:     tier2-cpu-target-tracking
     Metric:   Average CPU Utilization
     Target:   70%
     Warmup:   300 seconds

  2. Request-Based:
     Name:     tier2-request-target-tracking
     Metric:   ALB Request Count per Target
     Target:   1000 requests/min/instance
     Warmup:   300 seconds

Step Scaling (Optional):
  Policy:   tier2-step-scale-out
  Alarm:    tier2-high-cpu-alarm
  Trigger:  CPU > 80%
  Action:   Add 2 instances

Scheduled Scaling (Optional):
  Morning:  Scale to 4 at 9 AM (weekdays)
  Evening:  Scale to 2 at 6 PM (weekdays)

Capacity Limits:
  Minimum:  2 instances
  Desired:  2 instances (adjusted by policies)
  Maximum:  10 instances
```

Update the [Quick Reference](../QUICK_REFERENCE.md) with your scaling policies.

---

## 🎯 Next Steps

✅ **Scaling policies are configured!**

Now proceed to:
- **[Step 13: ALB & Auto Scaling Testing](./13-ALB-AUTOSCALING-TESTING.md)** - Comprehensive testing of load balancing and auto-scaling

---

## 📖 Additional Resources

- [Target Tracking Scaling](https://docs.aws.amazon.com/autoscaling/ec2/userguide/as-scaling-target-tracking.html)
- [Step Scaling](https://docs.aws.amazon.com/autoscaling/ec2/userguide/as-scaling-simple-step.html)
- [Scheduled Scaling](https://docs.aws.amazon.com/autoscaling/ec2/userguide/schedule_time.html)
- [Scaling Cooldowns](https://docs.aws.amazon.com/autoscaling/ec2/userguide/Cooldown.html)

---

**Scaling policies complete! 🎉 Continue to [ALB & Auto Scaling Testing](./13-ALB-AUTOSCALING-TESTING.md)**
