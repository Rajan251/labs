# 🌐 Step 2: Subnet Configuration - Web UI Guide

> **Creating Public and Private Subnets across Multiple Availability Zones**

---

## 📋 What We'll Create

- ✅ 2 Public Subnets (10.0.1.0/24, 10.0.2.0/24)
- ✅ 2 Private Subnets (10.0.3.0/24, 10.0.4.0/24)
- ✅ Multi-AZ deployment (us-east-1a, us-east-1b)
- ✅ Auto-assign public IP for public subnets

---

## 🎯 Subnet Overview

**Subnets** divide your VPC into smaller networks. We'll create:

| Subnet Name | CIDR | AZ | Type | Purpose |
|-------------|------|-----|------|---------|
| tier2-public-subnet-1 | 10.0.1.0/24 | us-east-1a | Public | NAT Gateway, public resources |
| tier2-public-subnet-2 | 10.0.2.0/24 | us-east-1b | Public | High availability |
| tier2-private-subnet-1 | 10.0.3.0/24 | us-east-1a | Private | EC2 instances |
| tier2-private-subnet-2 | 10.0.4.0/24 | us-east-1b | Private | EC2 instances |

**Each /24 subnet provides 251 usable IP addresses** (256 total - 5 reserved by AWS)

---

## 🚀 Step-by-Step Instructions

### Step 2.1: Navigate to Subnets

1. **Open VPC Dashboard**
   - Go to https://console.aws.amazon.com/vpc/
   - Ensure you're in **us-east-1** region

2. **Access Subnets**
   - In the left sidebar, click **"Subnets"**
   - You should see the default subnets (if any)

---

### Step 2.2: Create Public Subnet 1

1. **Start Subnet Creation**
   - Click **"Create subnet"** button (orange, top-right)

2. **VPC Selection**
   - **VPC ID**: Select **tier2-vpc** from the dropdown
   - The VPC CIDR (10.0.0.0/16) should appear below

3. **Subnet Settings**

   **Subnet 1 of 4:**
   - **Subnet name**: `tier2-public-subnet-1`
   - **Availability Zone**: Select **us-east-1a**
   - **IPv4 CIDR block**: `10.0.1.0/24`
   
   **Subnet tags (optional):**
   - **Key**: `Type`, **Value**: `Public`
   - **Key**: `Environment`, **Value**: `production`

4. **Add More Subnets**
   - Click **"Add new subnet"** button at the bottom
   - We'll create all 4 subnets in one go

---

### Step 2.3: Create Public Subnet 2

**Subnet 2 of 4:**
- **Subnet name**: `tier2-public-subnet-2`
- **Availability Zone**: Select **us-east-1b**
- **IPv4 CIDR block**: `10.0.2.0/24`

**Subnet tags:**
- **Key**: `Type`, **Value**: `Public`

Click **"Add new subnet"** again.

---

### Step 2.4: Create Private Subnet 1

**Subnet 3 of 4:**
- **Subnet name**: `tier2-private-subnet-1`
- **Availability Zone**: Select **us-east-1a**
- **IPv4 CIDR block**: `10.0.3.0/24`

**Subnet tags:**
- **Key**: `Type`, **Value**: `Private`

Click **"Add new subnet"** again.

---

### Step 2.5: Create Private Subnet 2

**Subnet 4 of 4:**
- **Subnet name**: `tier2-private-subnet-2`
- **Availability Zone**: Select **us-east-1b**
- **IPv4 CIDR block**: `10.0.4.0/24`

**Subnet tags:**
- **Key**: `Type`, **Value**: `Private`

---

### Step 2.6: Create All Subnets

1. **Review Configuration**
   - Scroll through all 4 subnets
   - Verify CIDR blocks don't overlap
   - Verify AZs are correct (2 in 1a, 2 in 1b)

2. **Create Subnets**
   - Click **"Create subnet"** button at the bottom
   - Wait for creation (should take a few seconds)

3. **Success Confirmation**
   - You should see: **"Successfully created 4 subnets"**
   - All 4 subnets should appear in the list

4. **Note Subnet IDs**
   - Click on each subnet and note its ID:
     - `tier2-public-subnet-1`: subnet-xxxxxxxxxxxxxxxxx
     - `tier2-public-subnet-2`: subnet-xxxxxxxxxxxxxxxxx
     - `tier2-private-subnet-1`: subnet-xxxxxxxxxxxxxxxxx
     - `tier2-private-subnet-2`: subnet-xxxxxxxxxxxxxxxxx

---

### Step 2.7: Enable Auto-Assign Public IP (Public Subnets Only)

We need to enable auto-assign public IP for public subnets so EC2 instances automatically get public IPs.

#### For Public Subnet 1:

1. **Select Subnet**
   - Find **tier2-public-subnet-1** in the list
   - Click the checkbox next to it

2. **Edit Settings**
   - Click **"Actions"** dropdown
   - Select **"Edit subnet settings"**

3. **Enable Auto-Assign**
   - Check the box: **"Enable auto-assign public IPv4 address"**
   - Click **"Save"**

4. **Verify**
   - You should see: **"Subnet settings updated successfully"**
   - The **"Auto-assign public IPv4 address"** column should show **"Yes"**

#### For Public Subnet 2:

Repeat the same steps for **tier2-public-subnet-2**:
1. Select the subnet
2. Actions → Edit subnet settings
3. Enable auto-assign public IPv4 address
4. Save

> **Important**: Do NOT enable auto-assign public IP for private subnets (tier2-private-subnet-1 and tier2-private-subnet-2). They should remain **"No"**.

---

## ✅ Verification Checklist

Verify all subnets are created correctly:

### Public Subnet 1
- [ ] Name: **tier2-public-subnet-1**
- [ ] CIDR: **10.0.1.0/24**
- [ ] AZ: **us-east-1a**
- [ ] Auto-assign public IP: **Yes**
- [ ] Available IPs: **251**

### Public Subnet 2
- [ ] Name: **tier2-public-subnet-2**
- [ ] CIDR: **10.0.2.0/24**
- [ ] AZ: **us-east-1b**
- [ ] Auto-assign public IP: **Yes**
- [ ] Available IPs: **251**

### Private Subnet 1
- [ ] Name: **tier2-private-subnet-1**
- [ ] CIDR: **10.0.3.0/24**
- [ ] AZ: **us-east-1a**
- [ ] Auto-assign public IP: **No**
- [ ] Available IPs: **251**

### Private Subnet 2
- [ ] Name: **tier2-private-subnet-2**
- [ ] CIDR: **10.0.4.0/24**
- [ ] AZ: **us-east-1b**
- [ ] Auto-assign public IP: **No**
- [ ] Available IPs: **251**

---

## 📊 What We Created

```
┌──────────────────────────────────────────────────────────────┐
│                    VPC: 10.0.0.0/16                          │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              PUBLIC SUBNETS                            │  │
│  ├────────────────────────────────────────────────────────┤  │
│  │  AZ: us-east-1a              AZ: us-east-1b           │  │
│  │  ┌─────────────────┐          ┌─────────────────┐     │  │
│  │  │ Public Subnet 1 │          │ Public Subnet 2 │     │  │
│  │  │ 10.0.1.0/24     │          │ 10.0.2.0/24     │     │  │
│  │  │ Auto-IP: Yes    │          │ Auto-IP: Yes    │     │  │
│  │  │ IPs: 251        │          │ IPs: 251        │     │  │
│  │  └─────────────────┘          └─────────────────┘     │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              PRIVATE SUBNETS                           │  │
│  ├────────────────────────────────────────────────────────┤  │
│  │  AZ: us-east-1a              AZ: us-east-1b           │  │
│  │  ┌─────────────────┐          ┌─────────────────┐     │  │
│  │  │ Private Subnet 1│          │ Private Subnet 2│     │  │
│  │  │ 10.0.3.0/24     │          │ 10.0.4.0/24     │     │  │
│  │  │ Auto-IP: No     │          │ Auto-IP: No     │     │  │
│  │  │ IPs: 251        │          │ IPs: 251        │     │  │
│  │  └─────────────────┘          └─────────────────┘     │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔧 Troubleshooting

### Issue: "CIDR block overlaps with existing subnet"

**Cause**: CIDR blocks must not overlap.

**Solution**:
1. Check existing subnets in the VPC
2. Use non-overlapping CIDR blocks
3. Our configuration (10.0.1.0/24, 10.0.2.0/24, 10.0.3.0/24, 10.0.4.0/24) doesn't overlap

### Issue: "CIDR block is outside VPC CIDR range"

**Cause**: Subnet CIDR must be within VPC CIDR (10.0.0.0/16).

**Solution**:
1. Verify VPC CIDR is 10.0.0.0/16
2. All our subnets (10.0.1.0/24 through 10.0.4.0/24) are within this range

### Issue: "Availability Zone not available"

**Cause**: Some AZs may not be available in your account.

**Solution**:
1. Use available AZs shown in the dropdown
2. If us-east-1a/1b not available, use 1c/1d or other available AZs
3. Just ensure you use 2 different AZs for high availability

### Issue: "Cannot enable auto-assign public IP"

**Cause**: May be a permission issue or subnet type.

**Solution**:
1. Ensure you have `ec2:ModifySubnetAttribute` permission
2. Only enable for public subnets
3. Try refreshing the page and trying again

### Issue: "Only 251 IPs available instead of 256"

**Explanation**: This is normal. AWS reserves 5 IPs in each subnet:
- `.0` - Network address
- `.1` - VPC router
- `.2` - DNS server
- `.3` - Future use
- `.255` - Broadcast address

---

## 💡 Best Practices

### Subnet Sizing
- ✅ Use /24 for most use cases (251 IPs)
- ✅ Use /25 or /26 for smaller subnets
- ✅ Use /23 or /22 for larger subnets
- ✅ Plan for growth - don't make subnets too small

### Multi-AZ Deployment
- ✅ Always use at least 2 AZs for high availability
- ✅ Distribute resources evenly across AZs
- ✅ Public and private subnets in same AZ for lower latency

### Naming Convention
- ✅ Include VPC name, type, and number
- ✅ Example: `tier2-public-subnet-1`
- ✅ Consistent naming helps with automation

### IP Address Planning
- ✅ Leave gaps between subnets for future expansion
- ✅ Document your IP allocation
- ✅ Use tags to identify subnet types

---

## 📝 Save Your Configuration

```
Subnet Configuration - Tier 2 Architecture
===========================================

Public Subnet 1:
  Name:     tier2-public-subnet-1
  ID:       subnet-xxxxxxxxxxxxxxxxx
  CIDR:     10.0.1.0/24
  AZ:       us-east-1a
  Auto-IP:  Yes

Public Subnet 2:
  Name:     tier2-public-subnet-2
  ID:       subnet-xxxxxxxxxxxxxxxxx
  CIDR:     10.0.2.0/24
  AZ:       us-east-1b
  Auto-IP:  Yes

Private Subnet 1:
  Name:     tier2-private-subnet-1
  ID:       subnet-xxxxxxxxxxxxxxxxx
  CIDR:     10.0.3.0/24
  AZ:       us-east-1a
  Auto-IP:  No

Private Subnet 2:
  Name:     tier2-private-subnet-2
  ID:       subnet-xxxxxxxxxxxxxxxxx
  CIDR:     10.0.4.0/24
  AZ:       us-east-1b
  Auto-IP:  No
```

Update the [Quick Reference](../QUICK_REFERENCE.md) with your subnet IDs.

---

## 🎯 Next Steps

✅ **Subnets are ready!**

Now proceed to:
- **[Step 3: Internet Gateway & NAT Gateway](./03-INTERNET-GATEWAY-NAT.md)** - Enable internet connectivity

---

## 📖 Additional Resources

- [AWS Subnet Documentation](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Subnets.html)
- [Subnet Sizing](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Subnets.html#VPC_Sizing)
- [Multi-AZ Best Practices](https://docs.aws.amazon.com/whitepapers/latest/real-time-communication-on-aws/high-availability-and-scalability-on-aws.html)

---

**Subnet configuration complete! 🎉 Continue to [Internet Gateway & NAT Gateway](./03-INTERNET-GATEWAY-NAT.md)**
