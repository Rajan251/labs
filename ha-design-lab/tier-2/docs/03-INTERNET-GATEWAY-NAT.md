# 🌐 Step 3: Internet Gateway & NAT Gateway - Web UI Guide

> **Enabling Internet Connectivity for Public and Private Subnets**

---

## 📋 What We'll Create

- ✅ Internet Gateway (IGW) for public subnet internet access
- ✅ Elastic IP address for NAT Gateway
- ✅ NAT Gateway in Public Subnet 1 for private subnet outbound internet

---

## 🎯 Overview

### Internet Gateway (IGW)
- Allows resources in **public subnets** to access the internet
- Allows internet to access resources in public subnets
- Horizontally scaled, redundant, and highly available
- **Free** - no charges

### NAT Gateway
- Allows resources in **private subnets** to access the internet (outbound only)
- Prevents internet from initiating connections to private resources
- Managed by AWS, highly available within an AZ
- **Paid** - ~$32/month + data transfer charges

```
Internet
   ↕
Internet Gateway (IGW)
   ↕
Public Subnets (10.0.1.0/24, 10.0.2.0/24)
   ↕
NAT Gateway (in Public Subnet 1)
   ↕
Private Subnets (10.0.3.0/24, 10.0.4.0/24)
```

---

## 🚀 Part 1: Create Internet Gateway

### Step 3.1: Navigate to Internet Gateways

1. **Open VPC Dashboard**
   - Go to https://console.aws.amazon.com/vpc/
   - Ensure you're in **us-east-1** region

2. **Access Internet Gateways**
   - In the left sidebar, click **"Internet gateways"**

---

### Step 3.2: Create Internet Gateway

1. **Start Creation**
   - Click **"Create internet gateway"** button (orange, top-right)

2. **Configure IGW**
   - **Name tag**: `tier2-igw`
   - **Tags (optional)**:
     - **Key**: `Environment`, **Value**: `production`
     - **Key**: `Project`, **Value**: `tier2-architecture`

3. **Create**
   - Click **"Create internet gateway"**
   - You should see: **"Internet gateway created successfully"**
   - Note the **Internet Gateway ID**: `igw-xxxxxxxxxxxxxxxxx`

4. **Check Status**
   - State should be **"Detached"** (we'll attach it next)

---

### Step 3.3: Attach Internet Gateway to VPC

1. **Select IGW**
   - Find **tier2-igw** in the list
   - Click the checkbox next to it (or click on the name)

2. **Attach to VPC**
   - Click **"Actions"** dropdown
   - Select **"Attach to VPC"**

3. **Select VPC**
   - **Available VPCs**: Select **tier2-vpc** from dropdown
   - Click **"Attach internet gateway"**

4. **Verify Attachment**
   - State should change to **"Attached"**
   - VPC ID should show your tier2-vpc ID

---

## 🚀 Part 2: Create Elastic IP for NAT Gateway

### Step 3.4: Allocate Elastic IP

1. **Navigate to Elastic IPs**
   - In the left sidebar, click **"Elastic IPs"**

2. **Allocate New Address**
   - Click **"Allocate Elastic IP address"** button

3. **Configure Elastic IP**
   - **Network Border Group**: Leave as default (us-east-1)
   - **Public IPv4 address pool**: Select **"Amazon's pool of IPv4 addresses"**
   - **Tags (optional)**:
     - **Key**: `Name`, **Value**: `tier2-nat-eip`
     - **Key**: `Purpose`, **Value**: `NAT Gateway`

4. **Allocate**
   - Click **"Allocate"**
   - You should see: **"Elastic IP address allocated successfully"**

5. **Note the Details**
   - **Allocation ID**: `eipalloc-xxxxxxxxxxxxxxxxx`
   - **Allocated IPv4 address**: `x.x.x.x` (e.g., 54.123.45.67)
   - Save this IP address - this will be the public IP for all outbound traffic from private subnets

---

## 🚀 Part 3: Create NAT Gateway

### Step 3.5: Navigate to NAT Gateways

1. **Access NAT Gateways**
   - In the left sidebar, click **"NAT gateways"**

---

### Step 3.6: Create NAT Gateway

1. **Start Creation**
   - Click **"Create NAT gateway"** button

2. **Configure NAT Gateway**

   **Name:**
   - **Name**: `tier2-nat-gw`

   **Subnet:**
   - **Subnet**: Select **tier2-public-subnet-1** from dropdown
   - ⚠️ **Important**: Must be a PUBLIC subnet (10.0.1.0/24)

   **Connectivity type:**
   - Select **"Public"** (allows private subnets to access internet)

   **Elastic IP allocation ID:**
   - Select the Elastic IP you just created: **tier2-nat-eip**
   - Should show the allocation ID and IP address

   **Tags (optional):**
   - **Key**: `Environment`, **Value**: `production`

3. **Create NAT Gateway**
   - Click **"Create NAT gateway"**
   - You should see: **"NAT gateway created successfully"**

4. **Note NAT Gateway ID**
   - **NAT Gateway ID**: `nat-xxxxxxxxxxxxxxxxx`
   - **Status**: Will show **"Pending"** initially

5. **Wait for Availability**
   - Status will change from **"Pending"** to **"Available"**
   - This takes about **2-5 minutes**
   - ☕ You can proceed to the next step while waiting, but don't configure route tables until NAT Gateway is **"Available"**

---

## ✅ Verification Checklist

### Internet Gateway
- [ ] IGW created with name **tier2-igw**
- [ ] IGW ID noted: `igw-xxxxxxxxxxxxxxxxx`
- [ ] State: **Attached**
- [ ] Attached to: **tier2-vpc**

### Elastic IP
- [ ] Elastic IP allocated
- [ ] Allocation ID noted: `eipalloc-xxxxxxxxxxxxxxxxx`
- [ ] Public IP address noted: `x.x.x.x`
- [ ] Associated with: **tier2-nat-gw** (will show after NAT Gateway creation)

### NAT Gateway
- [ ] NAT Gateway created with name **tier2-nat-gw**
- [ ] NAT Gateway ID noted: `nat-xxxxxxxxxxxxxxxxx`
- [ ] Subnet: **tier2-public-subnet-1** (10.0.1.0/24)
- [ ] Elastic IP: Attached
- [ ] Status: **Available** (wait if still Pending)

---

## 📊 What We Created

```
┌─────────────────────────────────────────────────────────────┐
│                        Internet                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↕
┌────────────────────────┴────────────────────────────────────┐
│              Internet Gateway (tier2-igw)                   │
│              Attached to: tier2-vpc                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↕
┌────────────────────────────────────────────────────────────┐
│                  Public Subnet 1                           │
│                  10.0.1.0/24 (us-east-1a)                  │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │         NAT Gateway (tier2-nat-gw)                   │ │
│  │         Elastic IP: x.x.x.x                          │ │
│  │         Status: Available                            │ │
│  └──────────────────────┬───────────────────────────────┘ │
└─────────────────────────┼──────────────────────────────────┘
                          │
                          ↕
┌─────────────────────────┴──────────────────────────────────┐
│              Private Subnets                               │
│              10.0.3.0/24, 10.0.4.0/24                      │
│              (Outbound internet via NAT)                   │
└────────────────────────────────────────────────────────────┘
```

---

## 🔧 Troubleshooting

### Issue: "Cannot attach Internet Gateway to VPC"

**Cause**: VPC already has an IGW attached (limit: 1 IGW per VPC).

**Solution**:
1. Check if VPC already has an IGW
2. Detach old IGW if needed
3. Attach new IGW

### Issue: "Elastic IP limit exceeded"

**Cause**: Default limit is 5 Elastic IPs per region.

**Solution**:
1. Release unused Elastic IPs
2. Request limit increase via Service Quotas
3. Use a different region

### Issue: "NAT Gateway creation failed"

**Cause**: Usually subnet or Elastic IP issues.

**Solution**:
1. Ensure subnet is PUBLIC (has route to IGW)
2. Ensure Elastic IP is allocated and not in use
3. Verify you have permissions
4. Try a different public subnet

### Issue: "NAT Gateway stuck in Pending"

**Cause**: Normal - takes 2-5 minutes.

**Solution**:
1. Wait up to 5 minutes
2. Refresh the page
3. If still pending after 10 minutes, delete and recreate

### Issue: "NAT Gateway shows 'Failed' status"

**Cause**: Configuration error during creation.

**Solution**:
1. Delete the failed NAT Gateway
2. Verify Elastic IP is available
3. Verify subnet is public
4. Create new NAT Gateway

---

## 💡 Best Practices

### Internet Gateway
- ✅ One IGW per VPC is sufficient
- ✅ IGW is free and highly available
- ✅ No configuration needed after attachment
- ✅ Automatically scales

### NAT Gateway
- ✅ Place in public subnet (with IGW route)
- ✅ Use Elastic IP for consistent outbound IP
- ✅ For high availability, create NAT Gateway in each AZ
  - We're using 1 NAT Gateway to save costs (~$32/month per NAT)
  - For production, consider NAT Gateway in both AZs
- ✅ Monitor data transfer costs
- ✅ Consider VPC endpoints for AWS services to avoid NAT charges

### Cost Optimization
- 💰 NAT Gateway costs:
  - **Hourly**: $0.045/hour (~$32/month)
  - **Data**: $0.045/GB processed
- 💡 Delete NAT Gateway when not in use (testing environments)
- 💡 Use VPC endpoints for S3, DynamoDB to avoid NAT charges
- 💡 Consider NAT instances for lower cost (but more management)

---

## 📝 Save Your Configuration

```
Gateway Configuration - Tier 2 Architecture
============================================

Internet Gateway:
  Name:     tier2-igw
  ID:       igw-xxxxxxxxxxxxxxxxx
  VPC:      tier2-vpc
  State:    Attached

Elastic IP:
  Name:     tier2-nat-eip
  ID:       eipalloc-xxxxxxxxxxxxxxxxx
  IP:       x.x.x.x
  Usage:    NAT Gateway

NAT Gateway:
  Name:     tier2-nat-gw
  ID:       nat-xxxxxxxxxxxxxxxxx
  Subnet:   tier2-public-subnet-1 (10.0.1.0/24)
  EIP:      x.x.x.x
  Status:   Available
  AZ:       us-east-1a
```

Update the [Quick Reference](../QUICK_REFERENCE.md) with your gateway IDs.

---

## 🎯 Next Steps

✅ **Gateways are ready!**

Now proceed to:
- **[Step 4: Route Tables](./04-ROUTE-TABLES.md)** - Configure routing for public and private subnets

> **Important**: Wait for NAT Gateway status to be **"Available"** before configuring route tables!

---

## 📖 Additional Resources

- [Internet Gateway Documentation](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Internet_Gateway.html)
- [NAT Gateway Documentation](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html)
- [NAT Gateway vs NAT Instance](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-comparison.html)
- [Elastic IP Documentation](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/elastic-ip-addresses-eip.html)

---

**Gateway setup complete! 🎉 Continue to [Route Tables](./04-ROUTE-TABLES.md)**
