# 🚀 Step 10: Launch Template - Web UI Guide

> **Creating Launch Template for Auto Scaling**

---

## 📋 What We'll Create

- ✅ Launch Template with EC2 configuration
- ✅ AMI selection and instance type
- ✅ User data for automatic application setup
- ✅ Network and security settings
- ✅ Storage configuration

---

## 🎯 Overview

A **Launch Template** defines the configuration for EC2 instances that will be launched by Auto Scaling. It includes:

- AMI (Amazon Machine Image)
- Instance type
- Security groups
- User data (startup scripts)
- Storage configuration
- Network settings

**Benefits**:
- Consistent instance configuration
- Version control
- Easy updates
- Reusable across Auto Scaling Groups

---

## 🚀 Create Launch Template

### Step 10.1: Navigate to Launch Templates

1. **Open EC2 Dashboard**
   - Go to https://console.aws.amazon.com/ec2/
   - In the left sidebar, under **"Instances"**
   - Click **"Launch Templates"**

---

### Step 10.2: Create Launch Template

1. **Start Creation**
   - Click **"Create launch template"**

2. **Launch Template Name and Description**
   - **Launch template name**: `tier2-launch-template`
   - **Template version description**: `Initial version for tier-2 architecture`
   - **Auto Scaling guidance**: Check **"Provide guidance to help me set up a template that I can use with EC2 Auto Scaling"**

---

### Step 10.3: Application and OS Images (AMI)

1. **Quick Start**
   - Select **"Amazon Linux"**
   - Choose **"Amazon Linux 2023 AMI"** (free tier eligible)
   - Architecture: **64-bit (x86)**

> **Alternative**: You can create a custom AMI from your configured instance and use that instead

---

### Step 10.4: Instance Type

- **Instance type**: `t3.micro` (or `t2.micro` for free tier)
- Click **"Compare instance types"** to see options

---

### Step 10.5: Key Pair

- **Key pair name**: Select **tier2-ec2-key** (existing key pair)

---

### Step 10.6: Network Settings

**Networking platform**:
- Select **"Virtual Private Cloud (VPC)"**

**Subnet**:
- **Don't include in launch template** (we'll specify in Auto Scaling Group)

**Firewall (security groups)**:
- Select **"Select existing security group"**
- Choose **tier2-ec2-sg**

**Advanced network configuration** (optional):
- **Auto-assign public IP**: **Disable** (instances will be in private subnets)

---

### Step 10.7: Configure Storage

**Volume 1 (Root volume)**:
- **Size**: `8` GiB
- **Volume type**: `gp3` (General Purpose SSD)
- **Delete on termination**: **Yes**
- **Encrypted**: **Yes** (recommended for production)

---

### Step 10.8: Resource Tags

Add tags that will be applied to instances:

- **Key**: `Name`, **Value**: `tier2-auto-instance`
- **Key**: `Environment`, **Value**: `production`
- **Key**: `ManagedBy`, **Value**: `AutoScaling`

**Resource types**: Select **"Instances"** and **"Volumes"**

---

### Step 10.9: Advanced Details

Expand **"Advanced details"** section:

**IAM instance profile** (optional):
- Leave blank or select if you have one

**Monitoring**:
- **Enable detailed monitoring**: Check this box (for better CloudWatch metrics)

**User data** (very important!):

```bash
#!/bin/bash
# Update system
yum update -y

# Install Apache web server
yum install -y httpd

# Get instance metadata
INSTANCE_ID=$(ec2-metadata --instance-id | cut -d " " -f 2)
AZ=$(ec2-metadata --availability-zone | cut -d " " -f 2)
PRIVATE_IP=$(ec2-metadata --local-ipv4 | cut -d " " -f 2)

# Create simple web page
cat > /var/www/html/index.html <<EOF
<!DOCTYPE html>
<html>
<head>
    <title>Tier-2 Auto Scaling Demo</title>
    <style>
        body { font-family: Arial; margin: 50px; background: #f0f0f0; }
        .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #FF9900; }
        .info { background: #232F3E; color: white; padding: 15px; border-radius: 5px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Tier-2 Auto Scaling Instance</h1>
        <div class="info">
            <p><strong>Instance ID:</strong> $INSTANCE_ID</p>
            <p><strong>Availability Zone:</strong> $AZ</p>
            <p><strong>Private IP:</strong> $PRIVATE_IP</p>
            <p><strong>Timestamp:</strong> $(date)</p>
        </div>
        <p>This instance was automatically launched by Auto Scaling!</p>
    </div>
</body>
</html>
EOF

# Create health check endpoint
echo "OK" > /var/www/html/health

# Start and enable Apache
systemctl start httpd
systemctl enable httpd

# Install CloudWatch agent (optional, for memory metrics)
wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
rpm -U ./amazon-cloudwatch-agent.rpm
```

---

### Step 10.10: Create Launch Template

1. **Review Configuration**
   - Scroll through all settings
   - Verify user data is correct
   - Check security group

2. **Create**
   - Click **"Create launch template"**
   - You should see: **"Launch template created successfully"**

3. **Note Template Details**
   - **Launch template ID**: `lt-xxxxxxxxxxxxxxxxx`
   - **Latest version**: `1`

---

## ✅ Verification Checklist

### Launch Template
- [ ] Name: **tier2-launch-template**
- [ ] Template ID noted: `lt-xxxxxxxxxxxxxxxxx`
- [ ] Version: 1

### Configuration
- [ ] AMI: Amazon Linux 2023
- [ ] Instance type: t3.micro
- [ ] Key pair: tier2-ec2-key
- [ ] Security group: tier2-ec2-sg
- [ ] Storage: 8 GiB gp3, encrypted
- [ ] User data: Configured with web server setup
- [ ] Tags: Name, Environment, ManagedBy

---

## 📊 What We Created

```
┌─────────────────────────────────────────────────────────────┐
│         Launch Template: tier2-launch-template              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  AMI:              Amazon Linux 2023                        │
│  Instance Type:    t3.micro                                 │
│  Key Pair:         tier2-ec2-key                            │
│  Security Group:   tier2-ec2-sg                             │
│  Storage:          8 GiB gp3 (encrypted)                    │
│  User Data:        Web server auto-install                  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ User Data Script:                                      │ │
│  │ • Update system packages                               │ │
│  │ • Install Apache web server                            │ │
│  │ • Create custom web page with instance info            │ │
│  │ • Create /health endpoint                              │ │
│  │ • Start and enable Apache                              │ │
│  │ • Install CloudWatch agent (optional)                  │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Troubleshooting

### Issue: Cannot create launch template

**Cause**: Missing permissions or invalid configuration.

**Solution**:
1. Check IAM permissions (`ec2:CreateLaunchTemplate`)
2. Verify AMI ID is valid
3. Ensure security group exists in same VPC

---

### Issue: User data not executing

**Cause**: Script errors or permissions.

**Solution**:
1. Check user data logs on instance:
   ```bash
   # SSH to instance
   sudo cat /var/log/cloud-init-output.log
   ```
2. Verify script syntax (bash -n to check)
3. Ensure script starts with `#!/bin/bash`

---

### Issue: Web server not starting

**Cause**: User data script failed.

**Solution**:
```bash
# SSH to instance and check
sudo systemctl status httpd
sudo journalctl -u httpd

# Manually start if needed
sudo systemctl start httpd
```

---

## 💡 Best Practices

### Launch Template Design
- ✅ Use latest AMI for security patches
- ✅ Include comprehensive user data
- ✅ Enable detailed monitoring
- ✅ Encrypt EBS volumes
- ✅ Use appropriate instance types

### User Data
- ✅ Keep scripts idempotent (can run multiple times)
- ✅ Log all actions for debugging
- ✅ Install and configure application automatically
- ✅ Create health check endpoints
- ✅ Use CloudWatch agent for custom metrics

### Versioning
- ✅ Create new version for changes (don't modify existing)
- ✅ Test new versions before using in production
- ✅ Document version changes
- ✅ Set default version for Auto Scaling

### Security
- ✅ Never include secrets in user data (use Secrets Manager)
- ✅ Use IAM roles instead of access keys
- ✅ Encrypt EBS volumes
- ✅ Use minimal security group rules

---

## 🧪 Test Launch Template

### Step 10.11: Test Launch (Optional)

Before using with Auto Scaling, test the template:

1. **Launch Instance from Template**
   - In Launch Templates, select **tier2-launch-template**
   - Click **"Actions"** → **"Launch instance from template"**

2. **Configure Test Launch**
   - **Number of instances**: 1
   - **Network settings**: Select **tier2-private-subnet-1**
   - Click **"Launch instance"**

3. **Verify Instance**
   - Wait for instance to be running
   - Check user data executed:
     ```bash
     # SSH via VPN
     ssh -i tier2-ec2-key.pem ec2-user@10.0.3.x
     
     # Check web server
     curl localhost
     # Should show custom web page
     
     # Check health endpoint
     curl localhost/health
     # Should return "OK"
     ```

4. **Terminate Test Instance**
   - After verification, terminate the test instance
   - We'll use Auto Scaling to launch instances

---

## 📝 Save Your Configuration

```
Launch Template Configuration - Tier 2 Architecture
====================================================

Launch Template:
  Name:     tier2-launch-template
  ID:       lt-xxxxxxxxxxxxxxxxx
  Version:  1

Configuration:
  AMI:              Amazon Linux 2023
  Instance Type:    t3.micro
  Key Pair:         tier2-ec2-key
  Security Group:   tier2-ec2-sg
  Storage:          8 GiB gp3 (encrypted)
  Monitoring:       Detailed enabled

User Data Features:
  - System updates
  - Apache web server installation
  - Custom web page with instance info
  - Health check endpoint (/health)
  - CloudWatch agent installation

Tags:
  Name:       tier2-auto-instance
  Environment: production
  ManagedBy:  AutoScaling
```

Update the [Quick Reference](../QUICK_REFERENCE.md) with your launch template ID.

---

## 🎯 Next Steps

✅ **Launch Template is ready!**

Now proceed to:
- **[Step 11: Auto Scaling Group](./11-AUTO-SCALING-GROUP.md)** - Create Auto Scaling Group using this template

---

## 📖 Additional Resources

- [Launch Templates Documentation](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-launch-templates.html)
- [User Data Scripts](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/user-data.html)
- [CloudWatch Agent](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Install-CloudWatch-Agent.html)

---

**Launch Template complete! 🎉 Continue to [Auto Scaling Group](./11-AUTO-SCALING-GROUP.md)**
