# 🔒 Step 5: Security Groups - Web UI Guide

> **Configuring Firewall Rules for EC2 Instances**

---

## 📋 What We'll Create

- ✅ Security Group for EC2 instances in private subnets
- ✅ Inbound rules (SSH, HTTP, HTTPS, custom ports)
- ✅ Outbound rules (allow all)

---

## 🎯 Security Groups Overview

**Security Groups** act as virtual firewalls for your EC2 instances. They control inbound and outbound traffic at the instance level.

### Key Concepts
- **Stateful**: If you allow inbound traffic, response traffic is automatically allowed
- **Default Deny**: All inbound traffic is denied by default
- **Default Allow**: All outbound traffic is allowed by default
- **Rules**: Define allowed traffic by protocol, port, and source/destination

---

## 🚀 Create EC2 Security Group

### Step 5.1: Navigate to Security Groups

1. **Open VPC Dashboard**
   - Go to https://console.aws.amazon.com/vpc/
   - Ensure you're in **us-east-1** region

2. **Access Security Groups**
   - In the left sidebar, click **"Security groups"**

---

### Step 5.2: Create Security Group

1. **Start Creation**
   - Click **"Create security group"** button (orange, top-right)

2. **Basic Details**
   - **Security group name**: `tier2-ec2-sg`
   - **Description**: `Security group for EC2 instances in private subnets`
   - **VPC**: Select **tier2-vpc** from dropdown

---

### Step 5.3: Configure Inbound Rules

Click **"Add rule"** for each of the following:

#### Rule 1: SSH (for VPN access)
- **Type**: SSH
- **Protocol**: TCP (auto-filled)
- **Port range**: 22 (auto-filled)
- **Source**: Custom
  - Enter: `10.0.0.0/16` (entire VPC CIDR)
  - This allows SSH from VPN clients
- **Description**: `SSH from VPN`

#### Rule 2: HTTP
- **Type**: HTTP
- **Protocol**: TCP
- **Port range**: 80
- **Source**: Custom
  - Enter: `0.0.0.0/0` (anywhere)
  - Or use `10.0.0.0/16` for VPC-only access
- **Description**: `HTTP web traffic`

#### Rule 3: HTTPS
- **Type**: HTTPS
- **Protocol**: TCP
- **Port range**: 443
- **Source**: Custom
  - Enter: `0.0.0.0/0`
- **Description**: `HTTPS web traffic`

#### Rule 4: Custom Application Port (optional)
- **Type**: Custom TCP
- **Protocol**: TCP
- **Port range**: `8080` (or your application port)
- **Source**: Custom
  - Enter: `10.0.0.0/16` (VPC only)
- **Description**: `Application port`

#### Rule 5: ICMP (for ping testing)
- **Type**: All ICMP - IPv4
- **Protocol**: ICMP (auto-filled)
- **Port range**: All (auto-filled)
- **Source**: Custom
  - Enter: `10.0.0.0/16`
- **Description**: `Ping for testing`

---

### Step 5.4: Configure Outbound Rules

**Default Outbound Rule** (already present):
- **Type**: All traffic
- **Protocol**: All
- **Port range**: All
- **Destination**: `0.0.0.0/0`
- **Description**: `Allow all outbound traffic`

> **Note**: Keep this default rule. It allows instances to access the internet via NAT Gateway for updates, downloads, etc.

---

### Step 5.5: Add Tags (Optional)

- **Key**: `Environment`, **Value**: `production`
- **Key**: `Purpose`, **Value**: `EC2 instances`

---

### Step 5.6: Create Security Group

1. **Review Configuration**
   - Scroll through all inbound rules
   - Verify VPC is correct
   - Check port numbers

2. **Create**
   - Click **"Create security group"** button at the bottom
   - You should see: **"Security group created successfully"**

3. **Note Security Group ID**
   - **Security Group ID**: `sg-xxxxxxxxxxxxxxxxx`
   - Save this ID for EC2 instance creation

---

## ✅ Verification Checklist

### Security Group Details
- [ ] Name: **tier2-ec2-sg**
- [ ] VPC: **tier2-vpc**
- [ ] Security Group ID noted: `sg-xxxxxxxxxxxxxxxxx`

### Inbound Rules
- [ ] SSH (22) from 10.0.0.0/16
- [ ] HTTP (80) from 0.0.0.0/0 or 10.0.0.0/16
- [ ] HTTPS (443) from 0.0.0.0/0 or 10.0.0.0/16
- [ ] Custom TCP (8080) from 10.0.0.0/16 (optional)
- [ ] ICMP from 10.0.0.0/16 (optional)

### Outbound Rules
- [ ] All traffic to 0.0.0.0/0

---

## 📊 Security Group Configuration

```
┌─────────────────────────────────────────────────────────────┐
│         Security Group: tier2-ec2-sg                        │
│         VPC: tier2-vpc (10.0.0.0/16)                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  INBOUND RULES:                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Type     │ Protocol │ Port │ Source        │ Desc   │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │ SSH      │ TCP      │ 22   │ 10.0.0.0/16   │ VPN    │  │
│  │ HTTP     │ TCP      │ 80   │ 0.0.0.0/0     │ Web    │  │
│  │ HTTPS    │ TCP      │ 443  │ 0.0.0.0/0     │ Web    │  │
│  │ Custom   │ TCP      │ 8080 │ 10.0.0.0/16   │ App    │  │
│  │ ICMP     │ ICMP     │ All  │ 10.0.0.0/16   │ Ping   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  OUTBOUND RULES:                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Type     │ Protocol │ Port │ Destination   │ Desc   │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │ All      │ All      │ All  │ 0.0.0.0/0     │ All    │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Troubleshooting

### Issue: "Cannot create security group"

**Cause**: VPC not selected or permission issues.

**Solution**:
1. Ensure VPC is selected
2. Check IAM permissions (`ec2:CreateSecurityGroup`)
3. Verify security group limit (default: 2500 per VPC)

### Issue: "Invalid CIDR block in rule"

**Cause**: Incorrect CIDR format.

**Solution**:
1. Use format: `x.x.x.x/x` (e.g., `10.0.0.0/16`)
2. For single IP: `x.x.x.x/32`
3. For all IPs: `0.0.0.0/0`

### Issue: "Cannot SSH to instance"

**Cause**: Security group doesn't allow SSH or wrong source.

**Solution**:
1. Verify SSH rule exists (port 22)
2. Check source CIDR includes your VPN IP range
3. Verify instance is in correct security group
4. Check NACL rules (should allow by default)

### Issue: "Cannot access internet from instance"

**Cause**: Outbound rules blocking traffic.

**Solution**:
1. Ensure outbound rule allows all traffic (0.0.0.0/0)
2. Check route table has NAT Gateway route
3. Verify NAT Gateway is available

---

## 💡 Best Practices

### Security Group Design
- ✅ Create separate security groups for different tiers
- ✅ Use descriptive names and descriptions
- ✅ Follow principle of least privilege
- ✅ Document rules with descriptions

### Inbound Rules
- ✅ Only allow necessary ports
- ✅ Restrict sources to specific CIDR blocks when possible
- ✅ Avoid 0.0.0.0/0 for SSH (use VPN CIDR instead)
- ✅ Use security group IDs as sources for inter-tier communication

### Outbound Rules
- ✅ Default "allow all" is usually fine
- ✅ Restrict if you need tight egress control
- ✅ Consider VPC endpoints to avoid internet egress

### SSH Access
- 🔒 **Never** allow SSH from 0.0.0.0/0 in production
- ✅ Use VPN or bastion host
- ✅ Our setup: SSH only from VPN (10.0.0.0/16)
- ✅ Consider AWS Systems Manager Session Manager as alternative

---

## 🔐 Security Hardening

### Additional Security Measures

1. **Use Security Group References**
   ```
   Instead of: Source = 10.0.0.0/16
   Use: Source = sg-xxxxxxxxx (another security group)
   ```

2. **Implement Defense in Depth**
   - Security Groups (instance level)
   - Network ACLs (subnet level)
   - Host-based firewalls (iptables, firewalld)
   - Application-level security

3. **Regular Audits**
   - Review security group rules quarterly
   - Remove unused rules
   - Check for overly permissive rules (0.0.0.0/0)

4. **Monitoring**
   - Enable VPC Flow Logs
   - Monitor rejected connections
   - Set up CloudWatch alarms for unusual traffic

---

## 📝 Save Your Configuration

```
Security Group Configuration - Tier 2 Architecture
===================================================

EC2 Security Group:
  Name:     tier2-ec2-sg
  ID:       sg-xxxxxxxxxxxxxxxxx
  VPC:      tier2-vpc

Inbound Rules:
  1. SSH (22) from 10.0.0.0/16
  2. HTTP (80) from 0.0.0.0/0
  3. HTTPS (443) from 0.0.0.0/0
  4. TCP (8080) from 10.0.0.0/16
  5. ICMP from 10.0.0.0/16

Outbound Rules:
  1. All traffic to 0.0.0.0/0
```

Update the [Quick Reference](../QUICK_REFERENCE.md) with your security group ID.

---

## 🎯 Next Steps

✅ **Security group is configured!**

Now proceed to:
- **[Step 6: EC2 Deployment](./06-EC2-DEPLOYMENT.md)** - Launch EC2 instances in private subnets

---

## 📖 Additional Resources

- [Security Groups Documentation](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html)
- [Security Group Rules Reference](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/security-group-rules-reference.html)
- [Security Best Practices](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-best-practices.html)

---

**Security group setup complete! 🎉 Continue to [EC2 Deployment](./06-EC2-DEPLOYMENT.md)**
