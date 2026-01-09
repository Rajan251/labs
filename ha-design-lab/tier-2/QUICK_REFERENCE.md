# 📋 Quick Reference - Tier-2 Architecture

> **Quick lookup for network configuration, resource IDs, and common commands**

---

## 🌐 Network Configuration

### VPC Details
```
VPC CIDR:           10.0.0.0/16
VPC Name:           tier2-vpc
DNS Hostnames:      Enabled
DNS Resolution:     Enabled
```

### Subnet Configuration

| Subnet Name | CIDR Block | AZ | Type | Auto-assign Public IP |
|-------------|------------|-------|------|----------------------|
| tier2-public-subnet-1 | 10.0.1.0/24 | us-east-1a | Public | Yes |
| tier2-public-subnet-2 | 10.0.2.0/24 | us-east-1b | Public | Yes |
| tier2-private-subnet-1 | 10.0.3.0/24 | us-east-1a | Private | No |
| tier2-private-subnet-2 | 10.0.4.0/24 | us-east-1b | Private | No |

### IP Address Ranges

```
Public Subnet 1:    10.0.1.1 - 10.0.1.254  (251 usable IPs)
Public Subnet 2:    10.0.2.1 - 10.0.2.254  (251 usable IPs)
Private Subnet 1:   10.0.3.1 - 10.0.3.254  (251 usable IPs)
Private Subnet 2:   10.0.4.1 - 10.0.4.254  (251 usable IPs)
```

---

## 🆔 Resource IDs Tracker

### Core Network Resources

```bash
# VPC
VPC_ID=vpc-xxxxxxxxxxxxxxxxx

# Internet Gateway
IGW_ID=igw-xxxxxxxxxxxxxxxxx

# NAT Gateway
NAT_GW_ID=nat-xxxxxxxxxxxxxxxxx
ELASTIC_IP=eipalloc-xxxxxxxxxxxxxxxxx
ELASTIC_IP_ADDRESS=x.x.x.x

# Subnets
PUBLIC_SUBNET_1=subnet-xxxxxxxxxxxxxxxxx
PUBLIC_SUBNET_2=subnet-xxxxxxxxxxxxxxxxx
PRIVATE_SUBNET_1=subnet-xxxxxxxxxxxxxxxxx
PRIVATE_SUBNET_2=subnet-xxxxxxxxxxxxxxxxx

# Route Tables
PUBLIC_RT=rtb-xxxxxxxxxxxxxxxxx
PRIVATE_RT=rtb-xxxxxxxxxxxxxxxxx

# Security Groups
EC2_SG=sg-xxxxxxxxxxxxxxxxx
VPN_SG=sg-xxxxxxxxxxxxxxxxx

# EC2 Instances
EC2_PRIVATE_1=i-xxxxxxxxxxxxxxxxx
EC2_PRIVATE_2=i-xxxxxxxxxxxxxxxxx

# Client VPN
VPN_ENDPOINT_ID=cvpn-endpoint-xxxxxxxxxxxxxxxxx
```

---

## 🔐 Security Group Rules

### EC2 Security Group (tier2-ec2-sg)

#### Inbound Rules
| Type | Protocol | Port | Source | Description |
|------|----------|------|--------|-------------|
| SSH | TCP | 22 | VPN CIDR (10.0.0.0/16) | SSH from VPN |
| HTTP | TCP | 80 | 0.0.0.0/0 | Web traffic |
| HTTPS | TCP | 443 | 0.0.0.0/0 | Secure web traffic |
| Custom | TCP | 8080 | 10.0.0.0/16 | Application port |

#### Outbound Rules
| Type | Protocol | Port | Destination | Description |
|------|----------|------|-------------|-------------|
| All | All | All | 0.0.0.0/0 | Allow all outbound |

---

## 🛣️ Route Table Configuration

### Public Route Table (tier2-public-rt)

| Destination | Target | Status |
|-------------|--------|--------|
| 10.0.0.0/16 | local | Active |
| 0.0.0.0/0 | igw-xxx | Active |

**Associated Subnets:**
- tier2-public-subnet-1 (10.0.1.0/24)
- tier2-public-subnet-2 (10.0.2.0/24)

### Private Route Table (tier2-private-rt)

| Destination | Target | Status |
|-------------|--------|--------|
| 10.0.0.0/16 | local | Active |
| 0.0.0.0/0 | nat-xxx | Active |

**Associated Subnets:**
- tier2-private-subnet-1 (10.0.3.0/24)
- tier2-private-subnet-2 (10.0.4.0/24)

---

## 🔧 Common AWS CLI Commands

### VPC Commands

```bash
# Describe VPC
aws ec2 describe-vpcs --vpc-ids $VPC_ID

# List all subnets in VPC
aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID"

# Check route tables
aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$VPC_ID"
```

### NAT Gateway Commands

```bash
# Check NAT Gateway status
aws ec2 describe-nat-gateways --nat-gateway-ids $NAT_GW_ID

# Check Elastic IP
aws ec2 describe-addresses --allocation-ids $ELASTIC_IP
```

### EC2 Commands

```bash
# List EC2 instances
aws ec2 describe-instances --filters "Name=vpc-id,Values=$VPC_ID"

# Get instance private IP
aws ec2 describe-instances --instance-ids $EC2_PRIVATE_1 \
  --query 'Reservations[0].Instances[0].PrivateIpAddress' --output text

# Check instance status
aws ec2 describe-instance-status --instance-ids $EC2_PRIVATE_1
```

### Security Group Commands

```bash
# Describe security group
aws ec2 describe-security-groups --group-ids $EC2_SG

# List all security groups in VPC
aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$VPC_ID"
```

### Client VPN Commands

```bash
# Describe VPN endpoint
aws ec2 describe-client-vpn-endpoints --client-vpn-endpoint-ids $VPN_ENDPOINT_ID

# List VPN connections
aws ec2 describe-client-vpn-connections --client-vpn-endpoint-id $VPN_ENDPOINT_ID

# Check VPN authorization rules
aws ec2 describe-client-vpn-authorization-rules --client-vpn-endpoint-id $VPN_ENDPOINT_ID
```

---

## 🧪 Testing Commands

### Test Internet Connectivity from Private Instance

```bash
# SSH to private instance via VPN, then:
ping -c 4 8.8.8.8
curl -I https://www.google.com
curl ifconfig.me  # Should show NAT Gateway's Elastic IP
```

### Test VPN Connectivity

```bash
# From your local machine after connecting to VPN
ping 10.0.3.10  # Private instance IP
ssh -i your-key.pem ec2-user@10.0.3.10
```

### Verify NAT Gateway

```bash
# From private instance
curl http://checkip.amazonaws.com
# Should return the Elastic IP of NAT Gateway
```

### Check DNS Resolution

```bash
# From private instance
nslookup amazon.com
dig google.com
```

---

## 📊 Monitoring Commands

### CloudWatch Metrics

```bash
# NAT Gateway metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/NATGateway \
  --metric-name BytesOutToDestination \
  --dimensions Name=NatGatewayId,Value=$NAT_GW_ID \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-01T23:59:59Z \
  --period 3600 \
  --statistics Sum

# VPN connection metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ClientVPN \
  --metric-name ActiveConnectionsCount \
  --dimensions Name=Endpoint,Value=$VPN_ENDPOINT_ID \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-01T23:59:59Z \
  --period 300 \
  --statistics Average
```

---

## 🔍 Troubleshooting Quick Checks

### Cannot SSH to Private Instance

```bash
# 1. Check VPN connection status
# 2. Verify security group allows SSH from VPN CIDR
aws ec2 describe-security-groups --group-ids $EC2_SG

# 3. Check instance is running
aws ec2 describe-instance-status --instance-ids $EC2_PRIVATE_1

# 4. Verify route table has VPN route
aws ec2 describe-route-tables --route-table-ids $PRIVATE_RT
```

### Private Instance Cannot Access Internet

```bash
# 1. Check NAT Gateway status
aws ec2 describe-nat-gateways --nat-gateway-ids $NAT_GW_ID

# 2. Verify route table has NAT route
aws ec2 describe-route-tables --route-table-ids $PRIVATE_RT

# 3. Check security group outbound rules
aws ec2 describe-security-groups --group-ids $EC2_SG

# 4. Test from instance
ping -c 4 8.8.8.8
```

### VPN Connection Issues

```bash
# 1. Check VPN endpoint status
aws ec2 describe-client-vpn-endpoints --client-vpn-endpoint-ids $VPN_ENDPOINT_ID

# 2. Verify authorization rules
aws ec2 describe-client-vpn-authorization-rules --client-vpn-endpoint-id $VPN_ENDPOINT_ID

# 3. Check VPN security group
aws ec2 describe-security-groups --group-ids $VPN_SG
```

---

## 📝 Resource Naming Convention

```
Format: tier2-<resource-type>-<purpose>-<number>

Examples:
- tier2-vpc
- tier2-public-subnet-1
- tier2-private-subnet-1
- tier2-igw
- tier2-nat-gw
- tier2-public-rt
- tier2-private-rt
- tier2-ec2-sg
- tier2-vpn-endpoint
```

---

## 💡 Quick Tips

### Cost Saving
```bash
# Stop NAT Gateway when not in use (saves ~$32/month)
# Note: You'll need to recreate it when needed

# Stop EC2 instances when not testing
aws ec2 stop-instances --instance-ids $EC2_PRIVATE_1 $EC2_PRIVATE_2

# Disconnect VPN when not in use (saves hourly charges)
```

### Performance
```bash
# Use t3.micro for testing (cheapest)
# Upgrade to t3.small or larger for production

# Monitor NAT Gateway data transfer costs
# Consider VPC endpoints for AWS services to avoid NAT charges
```

### Security
```bash
# Regularly rotate SSH keys
# Use Systems Manager Session Manager as VPN alternative
# Enable VPC Flow Logs for network monitoring
# Use AWS Config for compliance checking
```

---

## 📚 Related Documentation

- [VPC Setup Guide](./docs/01-VPC-SETUP.md)
- [Subnet Configuration](./docs/02-SUBNET-CONFIGURATION.md)
- [NAT Gateway Setup](./docs/03-INTERNET-GATEWAY-NAT.md)
- [Route Tables](./docs/04-ROUTE-TABLES.md)
- [Security Groups](./docs/05-SECURITY-GROUPS.md)
- [EC2 Deployment](./docs/06-EC2-DEPLOYMENT.md)
- [Client VPN Setup](./docs/07-CLIENT-VPN-SETUP.md)
- [Testing Guide](./docs/08-TESTING-VERIFICATION.md)

---

**Last Updated**: 2025-12-26
