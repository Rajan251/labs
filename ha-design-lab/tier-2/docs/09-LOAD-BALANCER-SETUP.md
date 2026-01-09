# ⚖️ Step 9: Load Balancer Setup - Web UI Guide

> **Creating Application Load Balancer and Target Groups**

---

## 📋 What We'll Create

- ✅ Security group for Application Load Balancer
- ✅ Target Group with health checks
- ✅ Application Load Balancer in public subnets
- ✅ HTTP/HTTPS listeners
- ✅ Register EC2 instances with Target Group

---

## 🎯 Overview

**Application Load Balancer (ALB)** distributes incoming traffic across multiple EC2 instances in different availability zones, providing:

- **High Availability**: Traffic distributed across multiple AZs
- **Health Checks**: Automatic detection and routing around unhealthy instances
- **SSL/TLS Termination**: Handle HTTPS at the load balancer
- **Path-Based Routing**: Route requests based on URL paths

**Cost**: ~$16/month + $0.008/LCU-hour

---

## 🚀 Part 1: Create ALB Security Group

### Step 9.1: Navigate to Security Groups

1. **Open VPC Dashboard**
   - Go to https://console.aws.amazon.com/vpc/
   - Ensure you're in **us-east-1** region

2. **Access Security Groups**
   - In the left sidebar, click **"Security groups"**

---

### Step 9.2: Create ALB Security Group

1. **Start Creation**
   - Click **"Create security group"**

2. **Basic Details**
   - **Security group name**: `tier2-alb-sg`
   - **Description**: `Security group for Application Load Balancer`
   - **VPC**: Select **tier2-vpc**

3. **Inbound Rules**

   **Rule 1: HTTP**
   - **Type**: HTTP
   - **Port**: 80
   - **Source**: `0.0.0.0/0` (anywhere)
   - **Description**: `HTTP from internet`

   **Rule 2: HTTPS**
   - **Type**: HTTPS
   - **Port**: 443
   - **Source**: `0.0.0.0/0`
   - **Description**: `HTTPS from internet`

4. **Outbound Rules**
   - Keep default: All traffic to 0.0.0.0/0

5. **Create**
   - Click **"Create security group"**
   - Note the **Security Group ID**: `sg-xxxxxxxxxxxxxxxxx`

---

### Step 9.3: Update EC2 Security Group

We need to allow traffic from ALB to EC2 instances.

1. **Open EC2 Security Group**
   - Find **tier2-ec2-sg**
   - Click on it

2. **Edit Inbound Rules**
   - Click **"Edit inbound rules"**
   - Click **"Add rule"**

3. **Add ALB Rule**
   - **Type**: HTTP
   - **Port**: 80
   - **Source**: Custom
     - Select **tier2-alb-sg** (the ALB security group)
   - **Description**: `HTTP from ALB`

4. **Save Rules**
   - Click **"Save rules"**

---

## 🚀 Part 2: Create Target Group

### Step 9.4: Navigate to Target Groups

1. **Open EC2 Dashboard**
   - Go to https://console.aws.amazon.com/ec2/
   - In the left sidebar, scroll to **"Load Balancing"**
   - Click **"Target Groups"**

---

### Step 9.5: Create Target Group

1. **Start Creation**
   - Click **"Create target group"**

2. **Choose Target Type**
   - Select **"Instances"**
   - Click **"Next"**

3. **Configure Target Group**

   **Basic configuration:**
   - **Target group name**: `tier2-tg`
   - **Protocol**: HTTP
   - **Port**: 80
   - **VPC**: Select **tier2-vpc**
   - **Protocol version**: HTTP1

   **Health checks:**
   - **Health check protocol**: HTTP
   - **Health check path**: `/` (or `/health` if you have a health endpoint)
   - **Advanced health check settings**:
     - **Port**: Traffic port
     - **Healthy threshold**: 2
     - **Unhealthy threshold**: 3
     - **Timeout**: 5 seconds
     - **Interval**: 30 seconds
     - **Success codes**: 200

   **Tags (optional):**
   - **Key**: `Name`, **Value**: `tier2-tg`

4. **Register Targets**
   - Select your EC2 instances:
     - ✅ **tier2-private-instance-1**
     - ✅ **tier2-private-instance-2**
   - **Ports for the selected instances**: 80
   - Click **"Include as pending below"**

5. **Create Target Group**
   - Review settings
   - Click **"Create target group"**
   - You should see: **"Target group created successfully"**

6. **Note Target Group ARN**
   - **Target Group ARN**: `arn:aws:elasticloadbalancing:us-east-1:xxxx:targetgroup/tier2-tg/xxxx`

---

### Step 9.6: Verify Target Health

1. **Select Target Group**
   - Click on **tier2-tg**

2. **Check Targets Tab**
   - Click the **"Targets"** tab
   - Wait 1-2 minutes for initial health check
   - **Status** should change from **"initial"** to **"healthy"**

> **Note**: If instances show "unhealthy", ensure:
> - Instances are running
> - Security group allows HTTP from ALB
> - Web server is running on port 80
> - Health check path returns 200 OK

---

## 🚀 Part 3: Create Application Load Balancer

### Step 9.7: Navigate to Load Balancers

1. **In EC2 Dashboard**
   - Left sidebar → **"Load Balancers"** (under Load Balancing)
   - Click **"Create load balancer"**

---

### Step 9.8: Select Load Balancer Type

1. **Choose Type**
   - Find **"Application Load Balancer"**
   - Click **"Create"**

---

### Step 9.9: Configure Load Balancer

**Basic configuration:**
- **Load balancer name**: `tier2-alb`
- **Scheme**: **Internet-facing** (for public access)
- **IP address type**: IPv4

**Network mapping:**
- **VPC**: Select **tier2-vpc**
- **Mappings**: Select **both** availability zones
  - ✅ **us-east-1a**: Select **tier2-public-subnet-1**
  - ✅ **us-east-1b**: Select **tier2-public-subnet-2**

> **Important**: ALB must be in public subnets!

**Security groups:**
- Remove default security group
- Select **tier2-alb-sg**

**Listeners and routing:**
- **Protocol**: HTTP
- **Port**: 80
- **Default action**: Forward to **tier2-tg**

**Tags (optional):**
- **Key**: `Environment`, **Value**: `production`

---

### Step 9.10: Create Load Balancer

1. **Review Configuration**
   - Scroll through all settings
   - Verify public subnets selected
   - Verify correct security group

2. **Create**
   - Click **"Create load balancer"**
   - You should see: **"Load balancer created successfully"**

3. **View Load Balancer**
   - Click **"View load balancer"**
   - Wait for **State** to change from **"provisioning"** to **"active"**
   - This takes 2-5 minutes ☕

4. **Note ALB Details**
   - **Load Balancer ARN**: `arn:aws:elasticloadbalancing:us-east-1:xxxx:loadbalancer/app/tier2-alb/xxxx`
   - **DNS name**: `tier2-alb-xxxxxxxxxx.us-east-1.elb.amazonaws.com`

---

## 🧪 Test Load Balancer

### Step 9.11: Test HTTP Access

1. **Get ALB DNS Name**
   - Copy the **DNS name** from ALB details

2. **Test in Browser**
   ```
   http://tier2-alb-xxxxxxxxxx.us-east-1.elb.amazonaws.com
   ```

3. **Expected Result**
   - You should see the web page from one of your EC2 instances
   - Refresh multiple times to see load balancing in action
   - Different instances should respond

4. **Test with curl**
   ```bash
   # From your local machine
   curl http://tier2-alb-xxxxxxxxxx.us-east-1.elb.amazonaws.com
   
   # Multiple requests to see load balancing
   for i in {1..10}; do
     curl -s http://tier2-alb-xxxxxxxxxx.us-east-1.elb.amazonaws.com | grep -i "instance"
   done
   ```

---

## 🔒 Optional: Add HTTPS Listener

### Step 9.12: Request SSL Certificate (Optional)

If you have a domain name:

1. **Open AWS Certificate Manager**
   - Go to https://console.aws.amazon.com/acm/

2. **Request Certificate**
   - Click **"Request certificate"**
   - Select **"Request a public certificate"**
   - Enter your domain name
   - Choose DNS or Email validation
   - Complete validation

3. **Note Certificate ARN**

---

### Step 9.13: Add HTTPS Listener (Optional)

1. **Select ALB**
   - Go to Load Balancers → **tier2-alb**

2. **Add Listener**
   - Click **"Listeners"** tab
   - Click **"Add listener"**

3. **Configure HTTPS Listener**
   - **Protocol**: HTTPS
   - **Port**: 443
   - **Default action**: Forward to **tier2-tg**
   - **Security policy**: ELBSecurityPolicy-2016-08
   - **Default SSL certificate**: Select your certificate

4. **Save**
   - Click **"Add"**

---

## ✅ Verification Checklist

### ALB Security Group
- [ ] Name: **tier2-alb-sg**
- [ ] Inbound: HTTP (80) and HTTPS (443) from 0.0.0.0/0
- [ ] Outbound: All traffic

### EC2 Security Group Updated
- [ ] Added rule: HTTP from tier2-alb-sg

### Target Group
- [ ] Name: **tier2-tg**
- [ ] Protocol: HTTP, Port: 80
- [ ] Health check path: `/`
- [ ] Targets: 2 instances registered
- [ ] Target health: **healthy**

### Application Load Balancer
- [ ] Name: **tier2-alb**
- [ ] State: **active**
- [ ] Scheme: Internet-facing
- [ ] Subnets: tier2-public-subnet-1 and tier2-public-subnet-2
- [ ] Security group: tier2-alb-sg
- [ ] Listener: HTTP:80 → tier2-tg
- [ ] DNS name noted

### Testing
- [ ] Can access ALB via HTTP
- [ ] Load balancing works (traffic distributed)
- [ ] Both instances responding
- [ ] Health checks passing

---

## 📊 What We Created

```
┌─────────────────────────────────────────────────────────────┐
│                        Internet                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌────────────────────────────────────────────────────────────┐
│         Application Load Balancer (tier2-alb)              │
│         DNS: tier2-alb-xxx.us-east-1.elb.amazonaws.com     │
│         Listener: HTTP:80                                  │
│         Security Group: tier2-alb-sg                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌────────────────────────────────────────────────────────────┐
│              Target Group (tier2-tg)                       │
│              Health Check: HTTP:80 /                       │
└────────────┬───────────────────────────┬────────────────────┘
             │                           │
             ↓                           ↓
┌─────────────────────┐      ┌─────────────────────┐
│ EC2 Instance 1      │      │ EC2 Instance 2      │
│ Private Subnet 1    │      │ Private Subnet 2    │
│ AZ: us-east-1a      │      │ AZ: us-east-1b      │
│ Status: healthy     │      │ Status: healthy     │
└─────────────────────┘      └─────────────────────┘
```

---

## 🔧 Troubleshooting

### Issue: Targets showing "unhealthy"

**Possible causes**:
1. Web server not running on instances
2. Security group blocking traffic
3. Health check path incorrect

**Solution**:
```bash
# SSH to instance via VPN
ssh -i tier2-ec2-key.pem ec2-user@10.0.3.x

# Install and start web server
sudo yum install -y httpd
sudo systemctl start httpd
sudo systemctl enable httpd
echo "<h1>Instance $(hostname)</h1>" | sudo tee /var/www/html/index.html

# Check if web server is running
curl localhost
```

---

### Issue: Cannot access ALB

**Checklist**:
1. ✅ ALB state is "active"?
2. ✅ ALB in public subnets?
3. ✅ ALB security group allows HTTP from 0.0.0.0/0?
4. ✅ At least one target is healthy?
5. ✅ Using correct DNS name?

---

### Issue: "503 Service Unavailable"

**Cause**: No healthy targets

**Solution**:
1. Check target health in Target Group
2. Fix unhealthy instances
3. Wait for health checks to pass

---

## 💡 Best Practices

### Load Balancer
- ✅ Always use at least 2 AZs
- ✅ Place ALB in public subnets
- ✅ Use HTTPS in production
- ✅ Enable access logs for troubleshooting
- ✅ Use WAF for additional security

### Target Group
- ✅ Configure appropriate health check path
- ✅ Set reasonable timeout and interval
- ✅ Use deregistration delay (default: 300s)
- ✅ Enable stickiness if needed

### Security
- ✅ Use security group references (ALB SG → EC2 SG)
- ✅ Restrict EC2 to only accept traffic from ALB
- ✅ Use SSL/TLS certificates in production
- ✅ Enable deletion protection on ALB

---

## 📝 Save Your Configuration

```
Load Balancer Configuration - Tier 2 Architecture
==================================================

ALB Security Group:
  Name:     tier2-alb-sg
  ID:       sg-xxxxxxxxxxxxxxxxx
  Inbound:  HTTP (80), HTTPS (443) from 0.0.0.0/0

Target Group:
  Name:     tier2-tg
  ARN:      arn:aws:elasticloadbalancing:...
  Protocol: HTTP:80
  Health:   / every 30s, timeout 5s
  Targets:  2 instances

Application Load Balancer:
  Name:     tier2-alb
  ARN:      arn:aws:elasticloadbalancing:...
  DNS:      tier2-alb-xxx.us-east-1.elb.amazonaws.com
  Scheme:   Internet-facing
  Subnets:  tier2-public-subnet-1, tier2-public-subnet-2
  Listener: HTTP:80 → tier2-tg
  State:    active
```

Update the [Quick Reference](../QUICK_REFERENCE.md) with your ALB details.

---

## 🎯 Next Steps

✅ **Load Balancer is configured!**

Now proceed to:
- **[Step 10: Launch Template](./10-LAUNCH-TEMPLATE.md)** - Create template for Auto Scaling

---

## 📖 Additional Resources

- [Application Load Balancer Documentation](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/)
- [Target Groups](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-target-groups.html)
- [Health Checks](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/target-group-health-checks.html)

---

**Load Balancer setup complete! 🎉 Continue to [Launch Template](./10-LAUNCH-TEMPLATE.md)**
