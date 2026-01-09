# 🏗️ Step 1: VPC Setup - Web UI Guide

> **Creating the Virtual Private Cloud (VPC) using AWS Console**

---

## 📋 What We'll Create

- ✅ VPC with CIDR block 10.0.0.0/16
- ✅ Enable DNS hostnames
- ✅ Enable DNS resolution
- ✅ Add tags for organization

---

## 🎯 VPC Overview

A **Virtual Private Cloud (VPC)** is your isolated network in AWS. Think of it as your own private data center in the cloud.

**Our VPC Configuration:**
- **CIDR Block**: 10.0.0.0/16 (65,536 IP addresses)
- **Region**: us-east-1 (N. Virginia)
- **Tenancy**: Default (shared hardware)

---

## 🚀 Step-by-Step Instructions

### Step 1.1: Navigate to VPC Dashboard

1. **Log in to AWS Management Console**
   - Go to https://console.aws.amazon.com
   - Sign in with your credentials

2. **Open VPC Service**
   - In the search bar at the top, type **"VPC"**
   - Click on **"VPC"** under Services
   - Or use the direct link: https://console.aws.amazon.com/vpc/

3. **Verify Region**
   - Check the region selector in the top-right corner
   - Ensure you're in **US East (N. Virginia) us-east-1**
   - If not, click the region dropdown and select **US East (N. Virginia)**

---

### Step 1.2: Create VPC

1. **Start VPC Creation**
   - In the left sidebar, click **"Your VPCs"**
   - Click the orange **"Create VPC"** button in the top-right

2. **Configure VPC Settings**

   **Resources to create:**
   - Select **"VPC only"** (we'll create subnets separately for more control)

   **VPC settings:**
   - **Name tag**: `tier2-vpc`
   - **IPv4 CIDR block**: Select **"IPv4 CIDR manual input"**
   - **IPv4 CIDR**: `10.0.0.0/16`
   - **IPv6 CIDR block**: Select **"No IPv6 CIDR block"**
   - **Tenancy**: Select **"Default"**

   **Tags (optional but recommended):**
   - Click **"Add new tag"**
   - **Key**: `Environment`, **Value**: `production`
   - **Key**: `Project`, **Value**: `tier2-architecture`

3. **Create VPC**
   - Review all settings
   - Click **"Create VPC"** button at the bottom

4. **Confirmation**
   - You should see a success message: **"VPC created successfully"**
   - Note down the **VPC ID** (format: `vpc-xxxxxxxxxxxxxxxxx`)
   - Example: `vpc-0a1b2c3d4e5f6g7h8`

---

### Step 1.3: Enable DNS Settings

By default, DNS hostnames are disabled. We need to enable them for EC2 instances to get DNS names.

1. **Select Your VPC**
   - In the VPCs list, find **tier2-vpc**
   - Click the checkbox next to it

2. **Enable DNS Hostnames**
   - Click **"Actions"** dropdown at the top
   - Select **"Edit VPC settings"**
   - Scroll down to **DNS settings** section
   - Check the box for **"Enable DNS hostnames"**
   - **"Enable DNS resolution"** should already be checked (verify it is)

3. **Save Changes**
   - Click **"Save"** button
   - You should see: **"VPC settings updated successfully"**

---

### Step 1.4: Verify VPC Creation

1. **Check VPC Details**
   - Click on your **tier2-vpc** in the list
   - In the details pane below, verify:
     - **VPC ID**: vpc-xxxxxxxxxxxxxxxxx
     - **State**: Available
     - **IPv4 CIDR**: 10.0.0.0/16
     - **DNS resolution**: Enabled
     - **DNS hostnames**: Enabled
     - **Default VPC**: No

2. **Check Resource Map**
   - Click on the **"Resource map"** tab
   - You should see your VPC with no subnets yet (we'll add them next)

---

## ✅ Verification Checklist

Before proceeding to the next step, verify:

- [ ] VPC is created with name **tier2-vpc**
- [ ] VPC ID is noted down (vpc-xxxxxxxxxxxxxxxxx)
- [ ] IPv4 CIDR is **10.0.0.0/16**
- [ ] DNS resolution is **Enabled**
- [ ] DNS hostnames is **Enabled**
- [ ] VPC state is **Available**
- [ ] Region is **us-east-1**

---

## 📊 What We Created

```
┌─────────────────────────────────────────┐
│         VPC: tier2-vpc                  │
│         CIDR: 10.0.0.0/16               │
│         Region: us-east-1               │
│                                         │
│   ┌─────────────────────────────────┐  │
│   │   Available IP Range:           │  │
│   │   10.0.0.0 - 10.0.255.255       │  │
│   │   Total: 65,536 IPs             │  │
│   └─────────────────────────────────┘  │
│                                         │
│   DNS Settings:                         │
│   ✓ DNS Resolution: Enabled             │
│   ✓ DNS Hostnames: Enabled              │
└─────────────────────────────────────────┘
```

---

## 🔧 Troubleshooting

### Issue: "VPC limit exceeded"

**Cause**: AWS limits you to 5 VPCs per region by default.

**Solution**:
1. Go to **Service Quotas** in AWS Console
2. Search for **"VPC"**
3. Request a limit increase
4. Or delete unused VPCs

### Issue: "Invalid CIDR block"

**Cause**: CIDR block format is incorrect or conflicts with existing VPCs.

**Solution**:
1. Verify format: `10.0.0.0/16` (no spaces)
2. Check it doesn't overlap with existing VPCs
3. Use a different CIDR if needed (e.g., `172.16.0.0/16`)

### Issue: "Cannot enable DNS hostnames"

**Cause**: DNS resolution must be enabled first.

**Solution**:
1. Ensure **DNS resolution** is enabled
2. Then enable **DNS hostnames**

### Issue: "VPC creation failed"

**Cause**: Insufficient permissions or service issue.

**Solution**:
1. Check your IAM permissions (need `ec2:CreateVpc`)
2. Try a different region
3. Contact AWS support if issue persists

---

## 💡 Best Practices

### CIDR Block Selection
- ✅ Use private IP ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
- ✅ Plan for growth - /16 gives you 65,536 IPs
- ✅ Avoid overlapping with on-premises networks
- ✅ Document your CIDR allocation

### Tagging
- ✅ Always tag your resources
- ✅ Use consistent naming conventions
- ✅ Include: Name, Environment, Project, Owner
- ✅ Tags help with cost allocation and organization

### DNS Settings
- ✅ Always enable DNS resolution
- ✅ Enable DNS hostnames for EC2 instances
- ✅ Required for many AWS services to work properly

---

## 📝 Save Your Configuration

**Important**: Save these details in a safe place (e.g., password manager or documentation):

```
VPC Configuration - Tier 2 Architecture
========================================
VPC Name:           tier2-vpc
VPC ID:             vpc-xxxxxxxxxxxxxxxxx
Region:             us-east-1
IPv4 CIDR:          10.0.0.0/16
DNS Resolution:     Enabled
DNS Hostnames:      Enabled
Created:            2025-12-26
```

You can also use the [Quick Reference](../QUICK_REFERENCE.md) to track all resource IDs.

---

## 🎯 Next Steps

✅ **VPC is ready!**

Now proceed to:
- **[Step 2: Subnet Configuration](./02-SUBNET-CONFIGURATION.md)** - Create public and private subnets

---

## 📖 Additional Resources

- [AWS VPC Documentation](https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html)
- [VPC CIDR Blocks](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Subnets.html#VPC_Sizing)
- [VPC Limits](https://docs.aws.amazon.com/vpc/latest/userguide/amazon-vpc-limits.html)

---

**VPC setup complete! 🎉 Continue to [Subnet Configuration](./02-SUBNET-CONFIGURATION.md)**
