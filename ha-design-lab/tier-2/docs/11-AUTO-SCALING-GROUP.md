# 📈 Step 11: Auto Scaling Group - Web UI Guide

> **Creating Auto Scaling Group for Automatic Capacity Management**

---

## 📋 What We'll Create

- ✅ Auto Scaling Group with 2-10 instances
- ✅ Multi-AZ distribution
- ✅ Integration with Target Group
- ✅ Health checks configuration
- ✅ Termination policies

---

## 🎯 Overview

An **Auto Scaling Group (ASG)** automatically adjusts the number of EC2 instances based on demand:

- **Scale Out**: Add instances when load increases
- **Scale In**: Remove instances when load decreases
- **Health Checks**: Replace unhealthy instances automatically
- **Multi-AZ**: Distribute instances across availability zones

**Benefits**:
- High availability
- Cost optimization
- Automatic recovery
- Consistent capacity

---

## 🚀 Create Auto Scaling Group

### Step 11.1: Navigate to Auto Scaling Groups

1. **Open EC2 Dashboard**
   - Go to https://console.aws.amazon.com/ec2/
   - In the left sidebar, under **"Auto Scaling"**
   - Click **"Auto Scaling Groups"**

---

### Step 11.2: Create Auto Scaling Group

1. **Start Creation**
   - Click **"Create Auto Scaling group"**

---

### Step 11.3: Choose Launch Template

**Step 1: Choose launch template or configuration**

- **Auto Scaling group name**: `tier2-asg`
- **Launch template**: Select **tier2-launch-template**
- **Version**: **Latest** (or select specific version)

Click **"Next"**

---

### Step 11.4: Choose Instance Launch Options

**Step 2: Choose instance launch options**

**Network:**
- **VPC**: **tier2-vpc** (auto-selected)
- **Availability Zones and subnets**: Select **both private subnets**
  - ✅ **tier2-private-subnet-1** (10.0.3.0/24, us-east-1a)
  - ✅ **tier2-private-subnet-2** (10.0.4.0/24, us-east-1b)

> **Important**: Select private subnets, not public!

**Instance type requirements** (optional):
- Leave as default (uses launch template settings)

Click **"Next"**

---

### Step 11.5: Configure Advanced Options

**Step 3: Configure advanced options**

**Load balancing:**
- Select **"Attach to an existing load balancer"**
- **Choose from your load balancer target groups**
- Select **tier2-tg** from the dropdown

**Health checks:**
- **Health check type**: Select **both**
  - ✅ **EC2** (default)
  - ✅ **ELB** (recommended for load balanced applications)
- **Health check grace period**: `300` seconds (5 minutes)
  - This allows time for instances to start and pass health checks

**Additional settings:**
- **Enable group metrics collection within CloudWatch**: ✅ Check this
- **Enable default instance warmup**: Check and set to `300` seconds

Click **"Next"**

---

### Step 11.6: Configure Group Size and Scaling

**Step 4: Configure group size and scaling policies**

**Group size:**
- **Desired capacity**: `2` (start with 2 instances)
- **Minimum capacity**: `2` (always have at least 2)
- **Maximum capacity**: `10` (scale up to 10 instances)

**Scaling policies:**
- Select **"Target tracking scaling policy"** (we'll configure this in next step)
- For now, select **"None"** (we'll add policies later)

**Instance scale-in protection:**
- Leave unchecked (allow instances to be terminated)

Click **"Next"**

---

### Step 11.7: Add Notifications (Optional)

**Step 5: Add notifications**

You can configure SNS notifications for scaling events:
- Launch
- Terminate
- Fail to launch
- Fail to terminate

For now, click **"Skip to review"** or **"Next"**

---

### Step 11.8: Add Tags

**Step 6: Add tags**

Tags will be applied to instances launched by ASG:

- **Key**: `Name`, **Value**: `tier2-asg-instance`
- **Key**: `Environment`, **Value**: `production`
- **Key**: `ManagedBy`, **Value**: `AutoScaling`

**Tag new instances**: ✅ Check this

Click **"Next"**

---

### Step 11.9: Review and Create

**Step 7: Review**

1. **Review all settings**:
   - Auto Scaling group name: tier2-asg
   - Launch template: tier2-launch-template
   - Subnets: 2 private subnets
   - Load balancer: tier2-tg
   - Capacity: 2/2/10 (desired/min/max)

2. **Create Auto Scaling Group**
   - Click **"Create Auto Scaling group"**
   - You should see: **"Auto Scaling group created successfully"**

---

## 🔍 Monitor Auto Scaling Group

### Step 11.10: View ASG Details

1. **Select ASG**
   - Click on **tier2-asg**

2. **Check Activity Tab**
   - Click **"Activity"** tab
   - You should see launch activities
   - Status will show "Successful" when instances are launched

3. **Check Instance Management Tab**
   - Click **"Instance management"** tab
   - You should see 2 instances being launched
   - **Lifecycle**: InService
   - **Health status**: Healthy (after grace period)

4. **Check Monitoring Tab**
   - Click **"Monitoring"** tab
   - View metrics like:
     - Group desired capacity
     - Group in-service instances
     - Group total instances

---

### Step 11.11: Verify Instances

1. **Go to EC2 Instances**
   - Navigate to EC2 → Instances
   - You should see new instances with names: **tier2-asg-instance**

2. **Check Instance Details**
   - Instances should be in private subnets
   - Distributed across both AZs
   - Security group: tier2-ec2-sg

3. **Verify Target Group**
   - Go to Target Groups → tier2-tg
   - Click **"Targets"** tab
   - You should see ASG instances registered
   - Health status should be "healthy" (after health check grace period)

---

## ✅ Verification Checklist

### Auto Scaling Group
- [ ] Name: **tier2-asg**
- [ ] Launch template: tier2-launch-template
- [ ] VPC: tier2-vpc
- [ ] Subnets: tier2-private-subnet-1 and tier2-private-subnet-2
- [ ] Capacity: 2 desired, 2 min, 10 max

### Load Balancer Integration
- [ ] Attached to target group: tier2-tg
- [ ] Health check type: EC2 + ELB
- [ ] Health check grace period: 300 seconds

### Instances
- [ ] 2 instances launched
- [ ] Instances in InService state
- [ ] Instances distributed across 2 AZs
- [ ] Instances registered with target group
- [ ] Target health: healthy

### Monitoring
- [ ] CloudWatch metrics enabled
- [ ] Activity history shows successful launches

---

## 📊 What We Created

```
┌─────────────────────────────────────────────────────────────┐
│         Auto Scaling Group: tier2-asg                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Configuration:                                             │
│  • Launch Template: tier2-launch-template                   │
│  • Desired Capacity: 2 instances                            │
│  • Minimum: 2, Maximum: 10                                  │
│  • Health Check: EC2 + ELB                                  │
│  • Grace Period: 300 seconds                                │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Load Balancer Integration                 │ │
│  │              Target Group: tier2-tg                    │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         AZ: us-east-1a              AZ: us-east-1b     │ │
│  │  ┌──────────────────┐        ┌──────────────────┐     │ │
│  │  │ ASG Instance 1   │        │ ASG Instance 2   │     │ │
│  │  │ Private Subnet 1 │        │ Private Subnet 2 │     │ │
│  │  │ Status: InService│        │ Status: InService│     │ │
│  │  └──────────────────┘        └──────────────────┘     │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  Scaling Policies: (to be added in next step)              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Troubleshooting

### Issue: Instances not launching

**Possible causes**:
1. Launch template issues
2. Subnet configuration
3. Insufficient capacity

**Solution**:
```bash
# Check Activity history
# Go to ASG → Activity tab
# Look for error messages

# Common errors:
# - "Invalid subnet": Check subnet IDs
# - "Insufficient capacity": Try different instance type or AZ
# - "Security group not found": Verify security group exists
```

---

### Issue: Instances unhealthy in target group

**Cause**: Health check failing

**Solution**:
1. Increase health check grace period (e.g., 600 seconds)
2. Verify web server is running on instances
3. Check security group allows traffic from ALB
4. SSH to instance and test:
   ```bash
   curl localhost
   curl localhost/health
   ```

---

### Issue: Instances not distributed across AZs

**Cause**: ASG balancing

**Solution**:
- ASG automatically balances across AZs
- Wait a few minutes for distribution
- If persistent, check subnet availability

---

## 💡 Best Practices

### Capacity Planning
- ✅ Set minimum = desired for consistent capacity
- ✅ Set maximum high enough for peak load
- ✅ Start conservative, adjust based on metrics
- ✅ Consider cost vs. performance trade-offs

### Health Checks
- ✅ Use both EC2 and ELB health checks
- ✅ Set appropriate grace period (5-10 minutes)
- ✅ Create dedicated health check endpoint
- ✅ Monitor health check failures

### Multi-AZ Distribution
- ✅ Always use at least 2 AZs
- ✅ Ensure equal subnet sizes
- ✅ Let ASG balance automatically
- ✅ Don't manually interfere with distribution

### Termination Policies
Default order (can be customized):
1. Oldest launch template
2. Closest to next billing hour
3. Random selection

### Instance Protection
- Use for critical instances
- Prevent accidental termination
- Remove protection before scaling in

---

## 🧪 Test Auto Scaling

### Manual Scaling Test

1. **Increase Desired Capacity**
   - Go to ASG → **tier2-asg**
   - Click **"Edit"** (in Details tab)
   - Change **Desired capacity** to `4`
   - Click **"Update"**

2. **Watch Scaling**
   - Go to **Activity** tab
   - You should see 2 new launch activities
   - Wait 2-3 minutes for instances to launch

3. **Verify**
   - Check **Instance management** tab
   - Should show 4 instances InService
   - Check Target Group - should have 4 healthy targets

4. **Scale Back**
   - Edit desired capacity back to `2`
   - Watch instances terminate
   - ASG will terminate oldest instances first

---

## 📝 Save Your Configuration

```
Auto Scaling Group Configuration - Tier 2 Architecture
=======================================================

Auto Scaling Group:
  Name:             tier2-asg
  Launch Template:  tier2-launch-template (latest)
  VPC:              tier2-vpc

Capacity:
  Desired:  2
  Minimum:  2
  Maximum:  10

Network:
  Subnets:
    - tier2-private-subnet-1 (10.0.3.0/24, us-east-1a)
    - tier2-private-subnet-2 (10.0.4.0/24, us-east-1b)

Load Balancing:
  Target Group:     tier2-tg
  Health Check:     EC2 + ELB
  Grace Period:     300 seconds

Monitoring:
  CloudWatch:       Enabled
  Metrics:          Group metrics enabled
  Instance Warmup:  300 seconds

Tags:
  Name:        tier2-asg-instance
  Environment: production
  ManagedBy:   AutoScaling
```

Update the [Quick Reference](../QUICK_REFERENCE.md) with your ASG details.

---

## 🎯 Next Steps

✅ **Auto Scaling Group is configured!**

Now proceed to:
- **[Step 12: Scaling Policies](./12-SCALING-POLICIES.md)** - Configure automatic scaling based on metrics

---

## 📖 Additional Resources

- [Auto Scaling Groups Documentation](https://docs.aws.amazon.com/autoscaling/ec2/userguide/AutoScalingGroup.html)
- [Health Checks](https://docs.aws.amazon.com/autoscaling/ec2/userguide/healthcheck.html)
- [Termination Policies](https://docs.aws.amazon.com/autoscaling/ec2/userguide/as-instance-termination.html)

---

**Auto Scaling Group complete! 🎉 Continue to [Scaling Policies](./12-SCALING-POLICIES.md)**
