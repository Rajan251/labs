# 💻 Step 6: EC2 Deployment - Web UI Guide

> **Launching EC2 Instances in Private Subnets**

---

## 📋 What We'll Create

- ✅ SSH key pair for instance access
- ✅ 2 EC2 instances in private subnets (one per AZ)
- ✅ Proper instance configuration and tagging

---

## 🎯 Overview

We'll launch EC2 instances in **private subnets** (10.0.3.0/24 and 10.0.4.0/24). These instances:
- Have **no public IP** (private only)
- Access internet via **NAT Gateway** (outbound only)
- Accessible via **Client VPN** (we'll set up in next step)

---

## 🚀 Part 1: Create SSH Key Pair

### Step 6.1: Navigate to Key Pairs

1. **Open EC2 Dashboard**
   - Go to https://console.aws.amazon.com/ec2/
   - Ensure you're in **us-east-1** region

2. **Access Key Pairs**
   - In the left sidebar, under **"Network & Security"**
   - Click **"Key Pairs"**

---

### Step 6.2: Create Key Pair

1. **Start Creation**
   - Click **"Create key pair"** button (orange, top-right)

2. **Configure Key Pair**
   - **Name**: `tier2-ec2-key`
   - **Key pair type**: Select **RSA**
   - **Private key file format**: 
     - Select **.pem** (for Linux/Mac)
     - Or **.ppk** (for Windows/PuTTY)

3. **Create and Download**
   - Click **"Create key pair"**
   - The private key file will automatically download
   - **Save this file securely!** You cannot download it again

4. **Set Permissions (Linux/Mac)**
   ```bash
   chmod 400 ~/Downloads/tier2-ec2-key.pem
   ```

---

## 🚀 Part 2: Launch EC2 Instance in Private Subnet 1

### Step 6.3: Navigate to EC2 Instances

1. **Go to Instances**
   - In the left sidebar, click **"Instances"**
   - Click **"Launch instances"** button (orange, top-right)

---

### Step 6.4: Configure Instance 1

#### Name and Tags
- **Name**: `tier2-private-instance-1`
- **Additional tags** (optional):
  - **Key**: `Environment`, **Value**: `production`
  - **Key**: `Tier`, **Value**: `private`
  - **Key**: `AZ`, **Value**: `us-east-1a`

#### Application and OS Images (AMI)
- **Quick Start**: Select **Amazon Linux**
- **Amazon Machine Image (AMI)**: **Amazon Linux 2023 AMI** (free tier eligible)
- Architecture: **64-bit (x86)**

#### Instance Type
- **Instance type**: `t3.micro` (or `t2.micro` for free tier)
- Click **"Compare instance types"** to see options

#### Key Pair
- **Key pair name**: Select **tier2-ec2-key** (created earlier)

#### Network Settings
Click **"Edit"** to customize:

- **VPC**: Select **tier2-vpc**
- **Subnet**: Select **tier2-private-subnet-1** (10.0.3.0/24, us-east-1a)
- **Auto-assign public IP**: **Disable** (very important!)
- **Firewall (security groups)**: 
  - Select **"Select existing security group"**
  - Choose **tier2-ec2-sg**

#### Configure Storage
- **Size**: `8` GiB (default, sufficient for testing)
- **Volume type**: `gp3` (General Purpose SSD)
- **Encrypted**: Check this box for production
- **Delete on termination**: Checked (default)

#### Advanced Details (Optional but Recommended)

Expand **"Advanced details"** and configure:

- **IAM instance profile**: None (or create one if needed)
- **User data** (optional - for automatic setup):
  ```bash
  #!/bin/bash
  yum update -y
  yum install -y httpd
  systemctl start httpd
  systemctl enable httpd
  echo "<h1>Private Instance 1 - AZ: us-east-1a</h1>" > /var/www/html/index.html
  ```

---

### Step 6.5: Launch Instance 1

1. **Review Summary**
   - Check all settings in the right panel
   - Verify subnet is **tier2-private-subnet-1**
   - Verify **no public IP**

2. **Launch**
   - Click **"Launch instance"** button
   - You should see: **"Successfully initiated launch of instance"**

3. **View Instance**
   - Click **"View all instances"**
   - Wait for instance state to change from **"Pending"** to **"Running"**
   - This takes 1-2 minutes

4. **Note Instance Details**
   - **Instance ID**: `i-xxxxxxxxxxxxxxxxx`
   - **Private IPv4 address**: `10.0.3.x` (e.g., 10.0.3.45)
   - **Public IPv4 address**: Should be blank (none)

---

## 🚀 Part 3: Launch EC2 Instance in Private Subnet 2

### Step 6.6: Launch Instance 2

Repeat the same process for the second instance:

1. **Click "Launch instances"** again

2. **Configure Instance 2**:
   - **Name**: `tier2-private-instance-2`
   - **AMI**: Amazon Linux 2023 AMI
   - **Instance type**: t3.micro
   - **Key pair**: tier2-ec2-key
   - **VPC**: tier2-vpc
   - **Subnet**: **tier2-private-subnet-2** (10.0.4.0/24, us-east-1b) ⚠️
   - **Auto-assign public IP**: **Disable**
   - **Security group**: tier2-ec2-sg
   - **Storage**: 8 GiB gp3
   - **User data** (optional):
     ```bash
     #!/bin/bash
     yum update -y
     yum install -y httpd
     systemctl start httpd
     systemctl enable httpd
     echo "<h1>Private Instance 2 - AZ: us-east-1b</h1>" > /var/www/html/index.html
     ```

3. **Launch Instance 2**
   - Click **"Launch instance"**
   - Wait for state to become **"Running"**

4. **Note Instance Details**
   - **Instance ID**: `i-xxxxxxxxxxxxxxxxx`
   - **Private IPv4 address**: `10.0.4.x`
   - **Public IPv4 address**: None

---

## ✅ Verification Checklist

### Instance 1 (tier2-private-instance-1)
- [ ] Instance ID noted: `i-xxxxxxxxxxxxxxxxx`
- [ ] State: **Running**
- [ ] Subnet: **tier2-private-subnet-1** (10.0.3.0/24)
- [ ] AZ: **us-east-1a**
- [ ] Private IP: `10.0.3.x`
- [ ] Public IP: **None**
- [ ] Security group: **tier2-ec2-sg**
- [ ] Key pair: **tier2-ec2-key**

### Instance 2 (tier2-private-instance-2)
- [ ] Instance ID noted: `i-xxxxxxxxxxxxxxxxx`
- [ ] State: **Running**
- [ ] Subnet: **tier2-private-subnet-2** (10.0.4.0/24)
- [ ] AZ: **us-east-1b**
- [ ] Private IP: `10.0.4.x`
- [ ] Public IP: **None**
- [ ] Security group: **tier2-ec2-sg**
- [ ] Key pair: **tier2-ec2-key**

---

## 📊 What We Created

```
┌──────────────────────────────────────────────────────────────┐
│                    VPC: 10.0.0.0/16                          │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │         Private Subnet 1 (10.0.3.0/24)                 │  │
│  │         AZ: us-east-1a                                 │  │
│  │                                                        │  │
│  │  ┌──────────────────────────────────────────────────┐ │  │
│  │  │ EC2 Instance: tier2-private-instance-1          │ │  │
│  │  │ Instance ID: i-xxxxxxxxxxxxxxxxx                │ │  │
│  │  │ Private IP: 10.0.3.x                            │ │  │
│  │  │ Public IP: None                                 │ │  │
│  │  │ Security Group: tier2-ec2-sg                    │ │  │
│  │  └──────────────────────────────────────────────────┘ │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │         Private Subnet 2 (10.0.4.0/24)                 │  │
│  │         AZ: us-east-1b                                 │  │
│  │                                                        │  │
│  │  ┌──────────────────────────────────────────────────┐ │  │
│  │  │ EC2 Instance: tier2-private-instance-2          │ │  │
│  │  │ Instance ID: i-xxxxxxxxxxxxxxxxx                │ │  │
│  │  │ Private IP: 10.0.4.x                            │ │  │
│  │  │ Public IP: None                                 │ │  │
│  │  │ Security Group: tier2-ec2-sg                    │ │  │
│  │  └──────────────────────────────────────────────────┘ │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔧 Troubleshooting

### Issue: "Cannot launch instance - insufficient capacity"

**Cause**: AWS doesn't have available capacity for that instance type in that AZ.

**Solution**:
1. Try a different instance type (t2.micro instead of t3.micro)
2. Try a different AZ
3. Wait and try again later

### Issue: "Instance has public IP even though disabled"

**Cause**: Subnet has auto-assign public IP enabled.

**Solution**:
1. Terminate the instance
2. Go to Subnets → Edit subnet settings
3. Disable "Auto-assign public IPv4 address"
4. Launch instance again

### Issue: "Cannot connect to instance"

**Cause**: Instance is in private subnet with no public access.

**Solution**:
- This is expected! You need to set up Client VPN (next step)
- Or use AWS Systems Manager Session Manager
- Cannot SSH directly from internet

### Issue: "Instance stuck in 'Pending' state"

**Cause**: Usually normal, but could be an issue.

**Solution**:
1. Wait 2-3 minutes
2. Refresh the page
3. If stuck for >5 minutes, check AWS Service Health Dashboard
4. Try terminating and relaunching

---

## 💡 Best Practices

### Instance Placement
- ✅ Distribute instances across multiple AZs for high availability
- ✅ Use private subnets for application/database tiers
- ✅ Use public subnets only for load balancers, NAT gateways

### Security
- ✅ Never launch instances with default security groups
- ✅ Disable auto-assign public IP for private instances
- ✅ Use IAM roles instead of embedding credentials
- ✅ Enable encryption for EBS volumes in production
- ✅ Protect SSH keys (chmod 400)

### Tagging
- ✅ Always tag instances with Name, Environment, Purpose
- ✅ Use consistent naming conventions
- ✅ Tags help with cost allocation and automation

### Instance Sizing
- 💡 Start small (t3.micro) for testing
- 💡 Monitor CPU/memory usage
- 💡 Scale up as needed
- 💡 Use Auto Scaling for production

---

## 📝 Save Your Configuration

```
EC2 Instance Configuration - Tier 2 Architecture
=================================================

SSH Key Pair:
  Name:     tier2-ec2-key
  Type:     RSA
  Format:   .pem
  Location: ~/Downloads/tier2-ec2-key.pem

Instance 1:
  Name:         tier2-private-instance-1
  ID:           i-xxxxxxxxxxxxxxxxx
  Type:         t3.micro
  AMI:          Amazon Linux 2023
  Subnet:       tier2-private-subnet-1 (10.0.3.0/24)
  AZ:           us-east-1a
  Private IP:   10.0.3.x
  Public IP:    None
  Security Group: tier2-ec2-sg
  Key Pair:     tier2-ec2-key

Instance 2:
  Name:         tier2-private-instance-2
  ID:           i-xxxxxxxxxxxxxxxxx
  Type:         t3.micro
  AMI:          Amazon Linux 2023
  Subnet:       tier2-private-subnet-2 (10.0.4.0/24)
  AZ:           us-east-1b
  Private IP:   10.0.4.x
  Public IP:    None
  Security Group: tier2-ec2-sg
  Key Pair:     tier2-ec2-key
```

Update the [Quick Reference](../QUICK_REFERENCE.md) with your instance IDs and IPs.

---

## 🎯 Next Steps

✅ **EC2 instances are running!**

Now proceed to:
- **[Step 7: Client VPN Setup](./07-CLIENT-VPN-SETUP.md)** - Set up VPN for SSH access to private instances

> **Note**: You cannot SSH to these instances yet! They're in private subnets with no public IPs. The next step will set up Client VPN for secure access.

---

## 📖 Additional Resources

- [EC2 User Guide](https://docs.aws.amazon.com/ec2/index.html)
- [EC2 Instance Types](https://aws.amazon.com/ec2/instance-types/)
- [Amazon Linux 2023](https://aws.amazon.com/linux/amazon-linux-2023/)
- [EC2 Key Pairs](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html)

---

**EC2 deployment complete! 🎉 Continue to [Client VPN Setup](./07-CLIENT-VPN-SETUP.md)**
