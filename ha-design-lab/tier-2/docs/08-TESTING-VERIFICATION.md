# ✅ Step 8: Testing & Verification - Complete Guide

> **Comprehensive Testing of Tier-2 Architecture**

---

## 📋 What We'll Test

- ✅ Network connectivity (VPC, subnets, routing)
- ✅ Internet access via NAT Gateway
- ✅ VPN connectivity and SSH access
- ✅ Security group rules
- ✅ Multi-AZ deployment
- ✅ DNS resolution

---

## 🎯 Testing Overview

This guide provides step-by-step tests to verify every component of your tier-2 architecture is working correctly.

---

## 🧪 Test 1: VPC and Subnet Configuration

### Verify VPC

```bash
# AWS CLI command
aws ec2 describe-vpcs --vpc-ids <your-vpc-id> --query 'Vpcs[0].[VpcId,CidrBlock,State]' --output table

# Expected output:
# vpc-xxx | 10.0.0.0/16 | available
```

**Web UI Verification**:
1. Go to VPC Dashboard → Your VPCs
2. Find **tier2-vpc**
3. Verify:
   - ✅ CIDR: 10.0.0.0/16
   - ✅ DNS resolution: Enabled
   - ✅ DNS hostnames: Enabled
   - ✅ State: Available

---

### Verify Subnets

```bash
# List all subnets in VPC
aws ec2 describe-subnets --filters "Name=vpc-id,Values=<your-vpc-id>" \
  --query 'Subnets[*].[SubnetId,CidrBlock,AvailabilityZone,MapPublicIpOnLaunch]' \
  --output table
```

**Expected**:
- tier2-public-subnet-1: 10.0.1.0/24, us-east-1a, Auto-IP: Yes
- tier2-public-subnet-2: 10.0.2.0/24, us-east-1b, Auto-IP: Yes
- tier2-private-subnet-1: 10.0.3.0/24, us-east-1a, Auto-IP: No
- tier2-private-subnet-2: 10.0.4.0/24, us-east-1b, Auto-IP: No

---

## 🧪 Test 2: Internet Gateway and NAT Gateway

### Verify Internet Gateway

```bash
# Check IGW
aws ec2 describe-internet-gateways --filters "Name=attachment.vpc-id,Values=<your-vpc-id>"

# Expected: State = attached
```

**Web UI**:
1. VPC → Internet Gateways
2. Find **tier2-igw**
3. Verify: State = **Attached**, VPC = tier2-vpc

---

### Verify NAT Gateway

```bash
# Check NAT Gateway
aws ec2 describe-nat-gateways --filter "Name=vpc-id,Values=<your-vpc-id>"

# Expected: State = available
```

**Web UI**:
1. VPC → NAT Gateways
2. Find **tier2-nat-gw**
3. Verify:
   - ✅ State: **Available**
   - ✅ Subnet: tier2-public-subnet-1
   - ✅ Elastic IP: Assigned

---

## 🧪 Test 3: Route Tables

### Verify Public Route Table

```bash
# Check public route table
aws ec2 describe-route-tables --filters "Name=tag:Name,Values=tier2-public-rt"
```

**Web UI**:
1. VPC → Route Tables → tier2-public-rt
2. **Routes** tab - verify:
   - ✅ 10.0.0.0/16 → local
   - ✅ 0.0.0.0/0 → igw-xxx
3. **Subnet associations** tab - verify:
   - ✅ tier2-public-subnet-1
   - ✅ tier2-public-subnet-2

---

### Verify Private Route Table

**Web UI**:
1. VPC → Route Tables → tier2-private-rt
2. **Routes** tab - verify:
   - ✅ 10.0.0.0/16 → local
   - ✅ 0.0.0.0/0 → nat-xxx
3. **Subnet associations** tab - verify:
   - ✅ tier2-private-subnet-1
   - ✅ tier2-private-subnet-2

---

## 🧪 Test 4: Security Groups

### Verify EC2 Security Group

```bash
# Check security group
aws ec2 describe-security-groups --group-ids <your-sg-id>
```

**Web UI**:
1. VPC → Security Groups → tier2-ec2-sg
2. **Inbound rules** - verify:
   - ✅ SSH (22) from 10.0.0.0/16
   - ✅ HTTP (80) from 0.0.0.0/0
   - ✅ HTTPS (443) from 0.0.0.0/0
3. **Outbound rules** - verify:
   - ✅ All traffic to 0.0.0.0/0

---

## 🧪 Test 5: EC2 Instances

### Verify Instance Status

```bash
# Check instances
aws ec2 describe-instances --filters "Name=vpc-id,Values=<your-vpc-id>" \
  --query 'Reservations[*].Instances[*].[InstanceId,State.Name,PrivateIpAddress,SubnetId]' \
  --output table
```

**Web UI**:
1. EC2 → Instances
2. Verify both instances:
   - ✅ State: **Running**
   - ✅ Instance 1: Private IP in 10.0.3.x range
   - ✅ Instance 2: Private IP in 10.0.4.x range
   - ✅ No public IPs
   - ✅ Security group: tier2-ec2-sg

---

## 🧪 Test 6: Client VPN

### Verify VPN Endpoint

```bash
# Check VPN endpoint
aws ec2 describe-client-vpn-endpoints --client-vpn-endpoint-ids <your-vpn-id>
```

**Web UI**:
1. VPC → Client VPN Endpoints
2. Verify **tier2-vpn-endpoint**:
   - ✅ Status: **Available**
   - ✅ Client CIDR: 172.16.0.0/22
   - ✅ Target networks: Associated with subnets
   - ✅ Authorization rules: Active

---

### Test VPN Connection

1. **Connect to VPN**
   - Open AWS VPN Client
   - Connect to "Tier-2 VPN" profile
   - Verify: Status = **Connected**
   - Note your VPN IP: 172.16.0.x

2. **Test Connectivity**
   ```bash
   # Ping private instance
   ping -c 4 10.0.3.x  # Replace with your instance IP
   
   # Expected: Successful pings
   ```

---

## 🧪 Test 7: SSH Access to Private Instances

### SSH to Instance 1

```bash
# Ensure VPN is connected
# Replace with your instance IP
ssh -i ~/Downloads/tier2-ec2-key.pem ec2-user@10.0.3.x
```

**Expected Output**:
```
The authenticity of host '10.0.3.x' can't be established.
...
Are you sure you want to continue connecting (yes/no)? yes
...
[ec2-user@ip-10-0-3-x ~]$
```

**If successful**: ✅ SSH access working!

---

### SSH to Instance 2

```bash
ssh -i ~/Downloads/tier2-ec2-key.pem ec2-user@10.0.4.x
```

**Expected**: Same successful connection

---

## 🧪 Test 8: Internet Access from Private Instances

### Test Outbound Internet via NAT Gateway

**From Instance 1** (SSH'd in):

```bash
# Test DNS resolution
nslookup google.com

# Expected:
# Server:    10.0.0.2
# Address:   10.0.0.2#53
# Non-authoritative answer:
# Name:   google.com
# Address: 142.250.x.x
```

```bash
# Test internet connectivity
ping -c 4 8.8.8.8

# Expected: Successful pings
```

```bash
# Check public IP (should be NAT Gateway's Elastic IP)
curl http://checkip.amazonaws.com

# Expected: Your NAT Gateway's Elastic IP (not instance IP)
```

```bash
# Test HTTPS
curl -I https://www.google.com

# Expected: HTTP/2 200 response
```

**Repeat for Instance 2**

---

## 🧪 Test 9: Multi-AZ Deployment

### Verify High Availability Setup

**Check Instances in Different AZs**:
```bash
aws ec2 describe-instances --filters "Name=vpc-id,Values=<your-vpc-id>" \
  --query 'Reservations[*].Instances[*].[Tags[?Key==`Name`].Value|[0],Placement.AvailabilityZone]' \
  --output table
```

**Expected**:
- Instance 1: us-east-1a
- Instance 2: us-east-1b

**Verify Subnets in Different AZs**:
- Public Subnet 1: us-east-1a
- Public Subnet 2: us-east-1b
- Private Subnet 1: us-east-1a
- Private Subnet 2: us-east-1b

✅ **Multi-AZ deployment confirmed!**

---

## 🧪 Test 10: Network Isolation

### Verify Private Instances Have No Public Access

**Test 1: No Public IP**
```bash
aws ec2 describe-instances --instance-ids <instance-id> \
  --query 'Reservations[0].Instances[0].PublicIpAddress'

# Expected: null or empty
```

**Test 2: Cannot Access from Internet**
```bash
# From your local machine (NOT connected to VPN)
# Try to SSH to private IP
ssh -i tier2-ec2-key.pem ec2-user@10.0.3.x

# Expected: Connection timeout (no route to host)
```

**Test 3: Only Accessible via VPN**
```bash
# Connect to VPN first
# Then SSH
ssh -i tier2-ec2-key.pem ec2-user@10.0.3.x

# Expected: Successful connection
```

✅ **Network isolation working correctly!**

---

## 🧪 Test 11: DNS Resolution

### Test VPC DNS

**From Private Instance**:
```bash
# Test AWS internal DNS
nslookup ec2.amazonaws.com

# Expected: Resolves to AWS IP addresses
```

```bash
# Test external DNS
nslookup google.com

# Expected: Resolves correctly
```

```bash
# Check DNS server
cat /etc/resolv.conf

# Expected: nameserver 10.0.0.2 (VPC DNS)
```

---

## 🧪 Test 12: Security Group Rules

### Test SSH Access

**From VPN (10.0.0.0/16)**:
```bash
ssh -i tier2-ec2-key.pem ec2-user@10.0.3.x
# Expected: ✅ Success
```

**From Internet (without VPN)**:
```bash
ssh -i tier2-ec2-key.pem ec2-user@<public-ip>
# Expected: ❌ Timeout (no public IP anyway)
```

---

### Test HTTP/HTTPS (if web server installed)

**From Private Instance**:
```bash
# Start simple web server
sudo python3 -m http.server 80

# From another terminal (via VPN)
curl http://10.0.3.x

# Expected: HTML response
```

---

## 📊 Complete Verification Checklist

### Infrastructure
- [ ] VPC created with 10.0.0.0/16 CIDR
- [ ] 4 subnets created (2 public, 2 private)
- [ ] Subnets in 2 different AZs
- [ ] Internet Gateway attached
- [ ] NAT Gateway created and available
- [ ] Elastic IP allocated to NAT Gateway

### Routing
- [ ] Public route table routes to IGW
- [ ] Private route table routes to NAT Gateway
- [ ] Subnets associated with correct route tables

### Security
- [ ] Security group created with proper rules
- [ ] SSH allowed from VPN CIDR only
- [ ] Outbound traffic allowed

### Compute
- [ ] 2 EC2 instances running
- [ ] Instances in private subnets
- [ ] No public IPs assigned
- [ ] Instances in different AZs

### VPN
- [ ] Client VPN endpoint created
- [ ] VPN status: Available
- [ ] Subnet associations configured
- [ ] Authorization rules active
- [ ] VPN client connected successfully

### Connectivity Tests
- [ ] Can connect to VPN
- [ ] Can SSH to private instances via VPN
- [ ] Cannot SSH without VPN
- [ ] Private instances can access internet
- [ ] Internet traffic goes through NAT Gateway
- [ ] DNS resolution works
- [ ] Ping works between instances

---

## 🔧 Troubleshooting Common Issues

### Issue: Cannot SSH to Instance

**Checklist**:
1. ✅ VPN connected?
2. ✅ Correct private IP?
3. ✅ Key file permissions: `chmod 400 key.pem`
4. ✅ Security group allows SSH from 10.0.0.0/16?
5. ✅ Instance is running?

**Debug**:
```bash
# Verbose SSH
ssh -v -i tier2-ec2-key.pem ec2-user@10.0.3.x

# Test connectivity
ping 10.0.3.x
telnet 10.0.3.x 22
```

---

### Issue: No Internet Access from Instance

**Checklist**:
1. ✅ NAT Gateway status: Available?
2. ✅ Private route table has NAT route?
3. ✅ Security group allows outbound?
4. ✅ Instance in private subnet?

**Debug**:
```bash
# From instance
ping 8.8.8.8
traceroute 8.8.8.8
curl -v http://google.com
```

---

### Issue: VPN Connection Fails

**Checklist**:
1. ✅ VPN endpoint status: Available?
2. ✅ Client config has certificates embedded?
3. ✅ Authorization rules active?
4. ✅ Subnet associations configured?

**Debug**:
- Check VPN client logs
- Verify certificate validity
- Try different transport protocol (TCP/UDP)

---

## 📝 Test Results Template

```
Tier-2 Architecture Test Results
=================================
Date: 2025-12-26
Tester: [Your Name]

Infrastructure Tests:
  ✅ VPC Configuration
  ✅ Subnet Configuration
  ✅ Internet Gateway
  ✅ NAT Gateway
  ✅ Route Tables
  ✅ Security Groups

Instance Tests:
  ✅ EC2 Instance 1 Running
  ✅ EC2 Instance 2 Running
  ✅ Multi-AZ Deployment
  ✅ No Public IPs

VPN Tests:
  ✅ VPN Endpoint Available
  ✅ VPN Connection Successful
  ✅ VPN IP Assigned: 172.16.0.x

Connectivity Tests:
  ✅ SSH to Instance 1
  ✅ SSH to Instance 2
  ✅ Internet Access via NAT
  ✅ DNS Resolution
  ✅ Network Isolation

Performance Tests:
  - Ping latency: X ms
  - Download speed: X Mbps
  - SSH connection time: X seconds

Issues Found:
  - None / [List any issues]

Overall Status: ✅ PASS / ❌ FAIL

Notes:
  [Any additional notes]
```

---

## 🎯 Next Steps

✅ **All tests passed? Congratulations!**

Your tier-2 architecture is fully functional and ready for use!

### Recommended Next Steps:

1. **Monitor Costs**
   - Set up billing alerts
   - Monitor NAT Gateway data transfer
   - Track VPN connection hours

2. **Enable Monitoring**
   - Set up CloudWatch dashboards
   - Create alarms for instance health
   - Enable VPC Flow Logs

3. **Backup and Documentation**
   - Document all resource IDs
   - Take snapshots of instances
   - Export VPC configuration

4. **Security Hardening**
   - Enable AWS Config
   - Set up GuardDuty
   - Review IAM policies
   - Enable CloudTrail

5. **Automation**
   - Create Terraform/CloudFormation templates
   - Set up CI/CD pipelines
   - Automate backups

---

## 📖 Additional Resources

- [VPC Testing Best Practices](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-testing.html)
- [Troubleshooting VPC](https://docs.aws.amazon.com/vpc/latest/userguide/troubleshooting.html)
- [Network Performance Testing](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/monitoring-network-performance.html)

---

**Testing complete! 🎉 Your tier-2 architecture is production-ready!**

Return to [Main README](../README.md) for overview and next steps.
