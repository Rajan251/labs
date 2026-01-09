# 🛣️ Step 4: Route Tables - Web UI Guide

> **Configuring Network Routing for Public and Private Subnets**

---

## 📋 What We'll Create

- ✅ Public Route Table (routes to Internet Gateway)
- ✅ Private Route Table (routes to NAT Gateway)
- ✅ Route table associations with subnets

---

## 🎯 Route Tables Overview

**Route Tables** control where network traffic is directed. Each subnet must be associated with a route table.

### Public Route Table
- Routes **0.0.0.0/0** (all internet traffic) to **Internet Gateway**
- Allows resources to communicate with the internet directly
- Used by: Public Subnet 1 & 2

### Private Route Table
- Routes **0.0.0.0/0** to **NAT Gateway**
- Allows outbound internet access only (no inbound from internet)
- Used by: Private Subnet 1 & 2

```
Public Subnets → Public RT → Internet Gateway → Internet
Private Subnets → Private RT → NAT Gateway → Internet Gateway → Internet
```

---

## 🚀 Part 1: Create Public Route Table

### Step 4.1: Navigate to Route Tables

1. **Open VPC Dashboard**
   - Go to https://console.aws.amazon.com/vpc/
   - Ensure you're in **us-east-1** region

2. **Access Route Tables**
   - In the left sidebar, click **"Route tables"**
   - You'll see the default route table for your VPC

---

### Step 4.2: Create Public Route Table

1. **Start Creation**
   - Click **"Create route table"** button (orange, top-right)

2. **Configure Route Table**
   - **Name**: `tier2-public-rt`
   - **VPC**: Select **tier2-vpc** from dropdown
   - **Tags (optional)**:
     - **Key**: `Type`, **Value**: `Public`
     - **Key**: `Environment`, **Value**: `production`

3. **Create**
   - Click **"Create route table"**
   - You should see: **"Route table created successfully"**
   - Note the **Route Table ID**: `rtb-xxxxxxxxxxxxxxxxx`

---

### Step 4.3: Add Internet Gateway Route to Public RT

1. **Select Public Route Table**
   - Find **tier2-public-rt** in the list
   - Click on the **Route Table ID** (or checkbox, then click on it)

2. **Edit Routes**
   - In the bottom panel, click the **"Routes"** tab
   - You should see one route: `10.0.0.0/16` → `local` (default VPC route)
   - Click **"Edit routes"** button

3. **Add Internet Route**
   - Click **"Add route"**
   - **Destination**: `0.0.0.0/0` (all internet traffic)
   - **Target**: 
     - Click the dropdown
     - Select **"Internet Gateway"**
     - Select **tier2-igw** from the list
   - Click **"Save changes"**

4. **Verify Routes**
   - You should now see 2 routes:
     - `10.0.0.0/16` → `local`
     - `0.0.0.0/0` → `igw-xxxxxxxxxxxxxxxxx`

---

### Step 4.4: Associate Public Subnets with Public RT

1. **Go to Subnet Associations**
   - Still in **tier2-public-rt** details
   - Click the **"Subnet associations"** tab
   - Click **"Edit subnet associations"**

2. **Select Public Subnets**
   - Check the boxes for:
     - ✅ **tier2-public-subnet-1** (10.0.1.0/24)
     - ✅ **tier2-public-subnet-2** (10.0.2.0/24)
   - Do NOT select private subnets
   - Click **"Save associations"**

3. **Verify Associations**
   - You should see 2 subnets associated:
     - tier2-public-subnet-1 (10.0.1.0/24)
     - tier2-public-subnet-2 (10.0.2.0/24)

---

## 🚀 Part 2: Create Private Route Table

### Step 4.5: Create Private Route Table

1. **Create New Route Table**
   - Click **"Create route table"** button again

2. **Configure Route Table**
   - **Name**: `tier2-private-rt`
   - **VPC**: Select **tier2-vpc**
   - **Tags (optional)**:
     - **Key**: `Type`, **Value**: `Private`
     - **Key**: `Environment`, **Value**: `production`

3. **Create**
   - Click **"Create route table"**
   - Note the **Route Table ID**: `rtb-xxxxxxxxxxxxxxxxx`

---

### Step 4.6: Add NAT Gateway Route to Private RT

> **Important**: Ensure your NAT Gateway status is **"Available"** before proceeding!

1. **Select Private Route Table**
   - Find **tier2-private-rt** in the list
   - Click on the **Route Table ID**

2. **Edit Routes**
   - Click the **"Routes"** tab
   - You should see one route: `10.0.0.0/16` → `local`
   - Click **"Edit routes"**

3. **Add NAT Gateway Route**
   - Click **"Add route"**
   - **Destination**: `0.0.0.0/0`
   - **Target**:
     - Click the dropdown
     - Select **"NAT Gateway"**
     - Select **tier2-nat-gw** from the list
     - Should show: `nat-xxxxxxxxxxxxxxxxx`
   - Click **"Save changes"**

4. **Verify Routes**
   - You should now see 2 routes:
     - `10.0.0.0/16` → `local`
     - `0.0.0.0/0` → `nat-xxxxxxxxxxxxxxxxx`

---

### Step 4.7: Associate Private Subnets with Private RT

1. **Go to Subnet Associations**
   - Still in **tier2-private-rt** details
   - Click the **"Subnet associations"** tab
   - Click **"Edit subnet associations"**

2. **Select Private Subnets**
   - Check the boxes for:
     - ✅ **tier2-private-subnet-1** (10.0.3.0/24)
     - ✅ **tier2-private-subnet-2** (10.0.4.0/24)
   - Do NOT select public subnets
   - Click **"Save associations"**

3. **Verify Associations**
   - You should see 2 subnets associated:
     - tier2-private-subnet-1 (10.0.3.0/24)
     - tier2-private-subnet-2 (10.0.4.0/24)

---

## ✅ Verification Checklist

### Public Route Table (tier2-public-rt)
- [ ] Route Table ID noted: `rtb-xxxxxxxxxxxxxxxxx`
- [ ] Routes configured:
  - [ ] `10.0.0.0/16` → `local`
  - [ ] `0.0.0.0/0` → `igw-xxx` (Internet Gateway)
- [ ] Subnets associated:
  - [ ] tier2-public-subnet-1 (10.0.1.0/24)
  - [ ] tier2-public-subnet-2 (10.0.2.0/24)

### Private Route Table (tier2-private-rt)
- [ ] Route Table ID noted: `rtb-xxxxxxxxxxxxxxxxx`
- [ ] Routes configured:
  - [ ] `10.0.0.0/16` → `local`
  - [ ] `0.0.0.0/0` → `nat-xxx` (NAT Gateway)
- [ ] Subnets associated:
  - [ ] tier2-private-subnet-1 (10.0.3.0/24)
  - [ ] tier2-private-subnet-2 (10.0.4.0/24)

---

## 📊 What We Created

```
┌──────────────────────────────────────────────────────────────┐
│                    VPC: 10.0.0.0/16                          │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │         Public Route Table (tier2-public-rt)           │  │
│  ├────────────────────────────────────────────────────────┤  │
│  │  Routes:                                               │  │
│  │  • 10.0.0.0/16 → local                                 │  │
│  │  • 0.0.0.0/0 → Internet Gateway (igw-xxx)             │  │
│  │                                                        │  │
│  │  Associated Subnets:                                   │  │
│  │  • tier2-public-subnet-1 (10.0.1.0/24)                │  │
│  │  • tier2-public-subnet-2 (10.0.2.0/24)                │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │         Private Route Table (tier2-private-rt)         │  │
│  ├────────────────────────────────────────────────────────┤  │
│  │  Routes:                                               │  │
│  │  • 10.0.0.0/16 → local                                 │  │
│  │  • 0.0.0.0/0 → NAT Gateway (nat-xxx)                  │  │
│  │                                                        │  │
│  │  Associated Subnets:                                   │  │
│  │  • tier2-private-subnet-1 (10.0.3.0/24)               │  │
│  │  • tier2-private-subnet-2 (10.0.4.0/24)               │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
└──────────────────────────────────────────────────────────────┘

Traffic Flow:
=============
Public Subnet → Public RT → IGW → Internet
Private Subnet → Private RT → NAT GW → IGW → Internet
```

---

## 🔧 Troubleshooting

### Issue: "Cannot add route - target not found"

**Cause**: Internet Gateway or NAT Gateway not created/attached.

**Solution**:
1. Verify IGW is attached to VPC
2. Verify NAT Gateway status is "Available"
3. Refresh the page and try again

### Issue: "Route already exists"

**Cause**: Trying to add duplicate route.

**Solution**:
1. Check existing routes in the route table
2. Edit existing route instead of adding new one
3. Delete conflicting route if needed

### Issue: "Cannot associate subnet - already associated"

**Cause**: Subnet is already associated with another route table.

**Solution**:
1. Each subnet can only be associated with ONE route table
2. Disassociate from old route table first
3. Then associate with new route table

### Issue: "NAT Gateway not available in dropdown"

**Cause**: NAT Gateway not in "Available" state.

**Solution**:
1. Go to NAT Gateways page
2. Check status - must be "Available"
3. Wait if still "Pending" (2-5 minutes)
4. If "Failed", delete and recreate

### Issue: "Routes not working - no internet access"

**Cause**: Multiple possible causes.

**Solution**:
1. Verify route table associations are correct
2. Check security group rules (must allow outbound)
3. Verify NAT Gateway is in public subnet
4. Check NACL rules (should allow all by default)
5. Test with `ping 8.8.8.8` from instance

---

## 💡 Best Practices

### Route Table Design
- ✅ Create separate route tables for public and private subnets
- ✅ Use descriptive names (include "public" or "private")
- ✅ Document route purposes with tags
- ✅ Minimize number of route tables for simplicity

### Route Configuration
- ✅ Always have local route (automatic)
- ✅ Public subnets: 0.0.0.0/0 → IGW
- ✅ Private subnets: 0.0.0.0/0 → NAT Gateway
- ✅ Add specific routes only when needed

### Subnet Associations
- ✅ Verify each subnet is associated with correct route table
- ✅ Public subnets → Public RT
- ✅ Private subnets → Private RT
- ✅ Use explicit associations (don't rely on main route table)

### High Availability
- 💡 For production, consider:
  - NAT Gateway in each AZ
  - Separate private route table per AZ
  - Each AZ's private RT points to its own NAT Gateway
- 💰 This costs more (~$32/month per NAT) but provides better availability

---

## 🧪 Testing Route Configuration

### Test Public Subnet Routing

```bash
# From an EC2 instance in public subnet:
ping -c 4 8.8.8.8
curl http://checkip.amazonaws.com
# Should return the instance's public IP
```

### Test Private Subnet Routing

```bash
# From an EC2 instance in private subnet:
ping -c 4 8.8.8.8
curl http://checkip.amazonaws.com
# Should return the NAT Gateway's Elastic IP (not instance IP)
```

### Verify Route Table Associations

```bash
# AWS CLI command to check route table associations:
aws ec2 describe-route-tables \
  --filters "Name=vpc-id,Values=<your-vpc-id>" \
  --query 'RouteTables[*].[RouteTableId,Tags[?Key==`Name`].Value|[0],Associations[*].SubnetId]' \
  --output table
```

---

## 📝 Save Your Configuration

```
Route Table Configuration - Tier 2 Architecture
================================================

Public Route Table:
  Name:     tier2-public-rt
  ID:       rtb-xxxxxxxxxxxxxxxxx
  Routes:
    - 10.0.0.0/16 → local
    - 0.0.0.0/0 → igw-xxxxxxxxxxxxxxxxx
  Subnets:
    - tier2-public-subnet-1 (10.0.1.0/24)
    - tier2-public-subnet-2 (10.0.2.0/24)

Private Route Table:
  Name:     tier2-private-rt
  ID:       rtb-xxxxxxxxxxxxxxxxx
  Routes:
    - 10.0.0.0/16 → local
    - 0.0.0.0/0 → nat-xxxxxxxxxxxxxxxxx
  Subnets:
    - tier2-private-subnet-1 (10.0.3.0/24)
    - tier2-private-subnet-2 (10.0.4.0/24)
```

Update the [Quick Reference](../QUICK_REFERENCE.md) with your route table IDs.

---

## 🎯 Next Steps

✅ **Route tables are configured!**

Now proceed to:
- **[Step 5: Security Groups](./05-SECURITY-GROUPS.md)** - Configure firewall rules for EC2 instances

---

## 📖 Additional Resources

- [Route Tables Documentation](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Route_Tables.html)
- [Route Table Best Practices](https://docs.aws.amazon.com/vpc/latest/userguide/route-table-options.html)
- [Troubleshooting Route Tables](https://docs.aws.amazon.com/vpc/latest/userguide/route-table-troubleshooting.html)

---

**Route table configuration complete! 🎉 Continue to [Security Groups](./05-SECURITY-GROUPS.md)**
