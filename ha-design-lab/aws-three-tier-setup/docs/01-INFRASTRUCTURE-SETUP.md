# 🏗️ Step 1: Infrastructure Setup

> **Creating VPC, Subnets, Security Groups, and Network Components**

---

## 📋 What We'll Create

- ✅ VPC (Virtual Private Cloud)
- ✅ 6 Subnets (2 public, 2 private for app, 2 private for database)
- ✅ Internet Gateway
- ✅ NAT Gateways (2 for high availability)
- ✅ Route Tables
- ✅ Security Groups
- ✅ Network ACLs

---

## 🎯 Infrastructure Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                    VPC: 10.0.0.0/16                            │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │         PUBLIC SUBNETS (Internet Gateway)               │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │  AZ-1 (us-east-1a)          AZ-2 (us-east-1b)          │  │
│  │  10.0.1.0/24                10.0.2.0/24                 │  │
│  │  ┌─────────────┐            ┌─────────────┐            │  │
│  │  │ Web Servers │            │ Web Servers │            │  │
│  │  │ NAT Gateway │            │ NAT Gateway │            │  │
│  │  │ Bastion     │            │             │            │  │
│  │  └─────────────┘            └─────────────┘            │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │         PRIVATE SUBNETS - APP TIER                      │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │  AZ-1 (us-east-1a)          AZ-2 (us-east-1b)          │  │
│  │  10.0.11.0/24               10.0.12.0/24                │  │
│  │  ┌─────────────┐            ┌─────────────┐            │  │
│  │  │ App Servers │            │ App Servers │            │  │
│  │  └─────────────┘            └─────────────┘            │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │         PRIVATE SUBNETS - DATABASE TIER                 │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │  AZ-1 (us-east-1a)          AZ-2 (us-east-1b)          │  │
│  │  10.0.21.0/24               10.0.22.0/24                │  │
│  │  ┌─────────────┐            ┌─────────────┐            │  │
│  │  │ MongoDB     │            │ MongoDB     │            │  │
│  │  │ PRIMARY +   │            │ SECONDARY   │            │  │
│  │  │ SECONDARY   │            │             │            │  │
│  │  └─────────────┘            └─────────────┘            │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Step-by-Step Setup

### 📍 **STEP 1.1: Create VPC**

```bash
# ============================================
# RUN ON: Your Local Machine (AWS CLI)
# ============================================

# Set variables
export AWS_REGION=us-east-1
export VPC_NAME="three-tier-vpc"
export VPC_CIDR="10.0.0.0/16"

# Create VPC
VPC_ID=$(aws ec2 create-vpc \
  --cidr-block $VPC_CIDR \
  --region $AWS_REGION \
  --tag-specifications "ResourceType=vpc,Tags=[{Key=Name,Value=$VPC_NAME}]" \
  --query 'Vpc.VpcId' \
  --output text)

echo "✅ VPC Created: $VPC_ID"

# Enable DNS hostnames
aws ec2 modify-vpc-attribute \
  --vpc-id $VPC_ID \
  --enable-dns-hostnames

# Enable DNS support
aws ec2 modify-vpc-attribute \
  --vpc-id $VPC_ID \
  --enable-dns-support

echo "✅ DNS enabled for VPC"
```

**Expected Output:**
```
✅ VPC Created: vpc-0123456789abcdef0
✅ DNS enabled for VPC
```

---

### 📍 **STEP 1.2: Create Internet Gateway**

```bash
# ============================================
# RUN ON: Your Local Machine
# ============================================

# Create Internet Gateway
IGW_ID=$(aws ec2 create-internet-gateway \
  --tag-specifications "ResourceType=internet-gateway,Tags=[{Key=Name,Value=three-tier-igw}]" \
  --query 'InternetGateway.InternetGatewayId' \
  --output text)

echo "✅ Internet Gateway Created: $IGW_ID"

# Attach to VPC
aws ec2 attach-internet-gateway \
  --internet-gateway-id $IGW_ID \
  --vpc-id $VPC_ID

echo "✅ Internet Gateway attached to VPC"
```

---

### 📍 **STEP 1.3: Create Subnets**

#### Public Subnets (Web Tier)

```bash
# ============================================
# RUN ON: Your Local Machine
# ============================================

# Public Subnet 1 (AZ-1)
PUBLIC_SUBNET_1=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.1.0/24 \
  --availability-zone us-east-1a \
  --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=public-subnet-1}]" \
  --query 'Subnet.SubnetId' \
  --output text)

echo "✅ Public Subnet 1 Created: $PUBLIC_SUBNET_1"

# Public Subnet 2 (AZ-2)
PUBLIC_SUBNET_2=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.2.0/24 \
  --availability-zone us-east-1b \
  --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=public-subnet-2}]" \
  --query 'Subnet.SubnetId' \
  --output text)

echo "✅ Public Subnet 2 Created: $PUBLIC_SUBNET_2"

# Enable auto-assign public IP
aws ec2 modify-subnet-attribute \
  --subnet-id $PUBLIC_SUBNET_1 \
  --map-public-ip-on-launch

aws ec2 modify-subnet-attribute \
  --subnet-id $PUBLIC_SUBNET_2 \
  --map-public-ip-on-launch

echo "✅ Auto-assign public IP enabled"
```

#### Private Subnets (Application Tier)

```bash
# ============================================
# RUN ON: Your Local Machine
# ============================================

# Private App Subnet 1 (AZ-1)
PRIVATE_APP_SUBNET_1=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.11.0/24 \
  --availability-zone us-east-1a \
  --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=private-app-subnet-1}]" \
  --query 'Subnet.SubnetId' \
  --output text)

echo "✅ Private App Subnet 1 Created: $PRIVATE_APP_SUBNET_1"

# Private App Subnet 2 (AZ-2)
PRIVATE_APP_SUBNET_2=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.12.0/24 \
  --availability-zone us-east-1b \
  --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=private-app-subnet-2}]" \
  --query 'Subnet.SubnetId' \
  --output text)

echo "✅ Private App Subnet 2 Created: $PRIVATE_APP_SUBNET_2"
```

#### Private Subnets (Database Tier)

```bash
# ============================================
# RUN ON: Your Local Machine
# ============================================

# Private DB Subnet 1 (AZ-1)
PRIVATE_DB_SUBNET_1=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.21.0/24 \
  --availability-zone us-east-1a \
  --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=private-db-subnet-1}]" \
  --query 'Subnet.SubnetId' \
  --output text)

echo "✅ Private DB Subnet 1 Created: $PRIVATE_DB_SUBNET_1"

# Private DB Subnet 2 (AZ-2)
PRIVATE_DB_SUBNET_2=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.22.0/24 \
  --availability-zone us-east-1b \
  --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=private-db-subnet-2}]" \
  --query 'Subnet.SubnetId' \
  --output text)

echo "✅ Private DB Subnet 2 Created: $PRIVATE_DB_SUBNET_2"
```

---

### 📍 **STEP 1.4: Create NAT Gateways**

```bash
# ============================================
# RUN ON: Your Local Machine
# ============================================

# Allocate Elastic IPs for NAT Gateways
EIP_1=$(aws ec2 allocate-address \
  --domain vpc \
  --tag-specifications "ResourceType=elastic-ip,Tags=[{Key=Name,Value=nat-eip-1}]" \
  --query 'AllocationId' \
  --output text)

echo "✅ Elastic IP 1 Created: $EIP_1"

EIP_2=$(aws ec2 allocate-address \
  --domain vpc \
  --tag-specifications "ResourceType=elastic-ip,Tags=[{Key=Name,Value=nat-eip-2}]" \
  --query 'AllocationId' \
  --output text)

echo "✅ Elastic IP 2 Created: $EIP_2"

# Create NAT Gateway 1 (in Public Subnet 1)
NAT_GW_1=$(aws ec2 create-nat-gateway \
  --subnet-id $PUBLIC_SUBNET_1 \
  --allocation-id $EIP_1 \
  --tag-specifications "ResourceType=natgateway,Tags=[{Key=Name,Value=nat-gateway-1}]" \
  --query 'NatGateway.NatGatewayId' \
  --output text)

echo "✅ NAT Gateway 1 Created: $NAT_GW_1"

# Create NAT Gateway 2 (in Public Subnet 2)
NAT_GW_2=$(aws ec2 create-nat-gateway \
  --subnet-id $PUBLIC_SUBNET_2 \
  --allocation-id $EIP_2 \
  --tag-specifications "ResourceType=natgateway,Tags=[{Key=Name,Value=nat-gateway-2}]" \
  --query 'NatGateway.NatGatewayId' \
  --output text)

echo "✅ NAT Gateway 2 Created: $NAT_GW_2"

# Wait for NAT Gateways to become available (takes 2-3 minutes)
echo "⏳ Waiting for NAT Gateways to become available..."
aws ec2 wait nat-gateway-available --nat-gateway-ids $NAT_GW_1 $NAT_GW_2
echo "✅ NAT Gateways are now available"
```

---

### 📍 **STEP 1.5: Create Route Tables**

#### Public Route Table

```bash
# ============================================
# RUN ON: Your Local Machine
# ============================================

# Create Public Route Table
PUBLIC_RT=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --tag-specifications "ResourceType=route-table,Tags=[{Key=Name,Value=public-rt}]" \
  --query 'RouteTable.RouteTableId' \
  --output text)

echo "✅ Public Route Table Created: $PUBLIC_RT"

# Add route to Internet Gateway
aws ec2 create-route \
  --route-table-id $PUBLIC_RT \
  --destination-cidr-block 0.0.0.0/0 \
  --gateway-id $IGW_ID

echo "✅ Route to Internet Gateway added"

# Associate with public subnets
aws ec2 associate-route-table \
  --route-table-id $PUBLIC_RT \
  --subnet-id $PUBLIC_SUBNET_1

aws ec2 associate-route-table \
  --route-table-id $PUBLIC_RT \
  --subnet-id $PUBLIC_SUBNET_2

echo "✅ Public subnets associated with route table"
```

#### Private Route Tables (for App Tier)

```bash
# ============================================
# RUN ON: Your Local Machine
# ============================================

# Private Route Table 1 (AZ-1)
PRIVATE_APP_RT_1=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --tag-specifications "ResourceType=route-table,Tags=[{Key=Name,Value=private-app-rt-1}]" \
  --query 'RouteTable.RouteTableId' \
  --output text)

echo "✅ Private App Route Table 1 Created: $PRIVATE_APP_RT_1"

# Add route to NAT Gateway 1
aws ec2 create-route \
  --route-table-id $PRIVATE_APP_RT_1 \
  --destination-cidr-block 0.0.0.0/0 \
  --nat-gateway-id $NAT_GW_1

# Associate with private app subnet 1
aws ec2 associate-route-table \
  --route-table-id $PRIVATE_APP_RT_1 \
  --subnet-id $PRIVATE_APP_SUBNET_1

echo "✅ Private App Subnet 1 configured with NAT Gateway 1"

# Private Route Table 2 (AZ-2)
PRIVATE_APP_RT_2=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --tag-specifications "ResourceType=route-table,Tags=[{Key=Name,Value=private-app-rt-2}]" \
  --query 'RouteTable.RouteTableId' \
  --output text)

echo "✅ Private App Route Table 2 Created: $PRIVATE_APP_RT_2"

# Add route to NAT Gateway 2
aws ec2 create-route \
  --route-table-id $PRIVATE_APP_RT_2 \
  --destination-cidr-block 0.0.0.0/0 \
  --nat-gateway-id $NAT_GW_2

# Associate with private app subnet 2
aws ec2 associate-route-table \
  --route-table-id $PRIVATE_APP_RT_2 \
  --subnet-id $PRIVATE_APP_SUBNET_2

echo "✅ Private App Subnet 2 configured with NAT Gateway 2"
```

#### Private Route Tables (for Database Tier)

```bash
# ============================================
# RUN ON: Your Local Machine
# ============================================

# Private DB Route Table (no internet access)
PRIVATE_DB_RT=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --tag-specifications "ResourceType=route-table,Tags=[{Key=Name,Value=private-db-rt}]" \
  --query 'RouteTable.RouteTableId' \
  --output text)

echo "✅ Private DB Route Table Created: $PRIVATE_DB_RT"

# Associate with private DB subnets (NO NAT Gateway - isolated)
aws ec2 associate-route-table \
  --route-table-id $PRIVATE_DB_RT \
  --subnet-id $PRIVATE_DB_SUBNET_1

aws ec2 associate-route-table \
  --route-table-id $PRIVATE_DB_RT \
  --subnet-id $PRIVATE_DB_SUBNET_2

echo "✅ Private DB subnets configured (isolated, no internet)"
```

---

### 📍 **STEP 1.6: Create Security Groups**

#### Web Tier Security Group

```bash
# ============================================
# RUN ON: Your Local Machine
# ============================================

# Create Web Security Group
WEB_SG=$(aws ec2 create-security-group \
  --group-name web-tier-sg \
  --description "Security group for web tier" \
  --vpc-id $VPC_ID \
  --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=web-tier-sg}]" \
  --query 'GroupId' \
  --output text)

echo "✅ Web Security Group Created: $WEB_SG"

# Allow HTTP from anywhere
aws ec2 authorize-security-group-ingress \
  --group-id $WEB_SG \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0

# Allow HTTPS from anywhere
aws ec2 authorize-security-group-ingress \
  --group-id $WEB_SG \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0

# Allow SSH from your IP (CHANGE THIS)
YOUR_IP="YOUR_PUBLIC_IP/32"  # Get from: curl ifconfig.me
aws ec2 authorize-security-group-ingress \
  --group-id $WEB_SG \
  --protocol tcp \
  --port 22 \
  --cidr $YOUR_IP

echo "✅ Web Security Group rules configured"
```

#### Application Tier Security Group

```bash
# ============================================
# RUN ON: Your Local Machine
# ============================================

# Create App Security Group
APP_SG=$(aws ec2 create-security-group \
  --group-name app-tier-sg \
  --description "Security group for application tier" \
  --vpc-id $VPC_ID \
  --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=app-tier-sg}]" \
  --query 'GroupId' \
  --output text)

echo "✅ App Security Group Created: $APP_SG"

# Allow traffic from Web Tier on port 3000 (Node.js)
aws ec2 authorize-security-group-ingress \
  --group-id $APP_SG \
  --protocol tcp \
  --port 3000 \
  --source-group $WEB_SG

# Allow traffic from Web Tier on port 8000 (Python)
aws ec2 authorize-security-group-ingress \
  --group-id $APP_SG \
  --protocol tcp \
  --port 8000 \
  --source-group $WEB_SG

# Allow SSH from Bastion (we'll create bastion later)
# For now, allow from your IP
aws ec2 authorize-security-group-ingress \
  --group-id $APP_SG \
  --protocol tcp \
  --port 22 \
  --cidr $YOUR_IP

echo "✅ App Security Group rules configured"
```

#### Database Tier Security Group

```bash
# ============================================
# RUN ON: Your Local Machine
# ============================================

# Create DB Security Group
DB_SG=$(aws ec2 create-security-group \
  --group-name db-tier-sg \
  --description "Security group for database tier" \
  --vpc-id $VPC_ID \
  --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=db-tier-sg}]" \
  --query 'GroupId' \
  --output text)

echo "✅ DB Security Group Created: $DB_SG"

# Allow MongoDB traffic from App Tier
aws ec2 authorize-security-group-ingress \
  --group-id $DB_SG \
  --protocol tcp \
  --port 27017 \
  --source-group $APP_SG

# Allow MongoDB traffic between DB instances (for replication)
aws ec2 authorize-security-group-ingress \
  --group-id $DB_SG \
  --protocol tcp \
  --port 27017 \
  --source-group $DB_SG

# Allow SSH from your IP (for initial setup)
aws ec2 authorize-security-group-ingress \
  --group-id $DB_SG \
  --protocol tcp \
  --port 22 \
  --cidr $YOUR_IP

echo "✅ DB Security Group rules configured"
```

---

### 📍 **STEP 1.7: Save Configuration**

```bash
# ============================================
# RUN ON: Your Local Machine
# ============================================

# Save all IDs to a file for later use
cat > infrastructure-ids.txt <<EOF
VPC_ID=$VPC_ID
IGW_ID=$IGW_ID
PUBLIC_SUBNET_1=$PUBLIC_SUBNET_1
PUBLIC_SUBNET_2=$PUBLIC_SUBNET_2
PRIVATE_APP_SUBNET_1=$PRIVATE_APP_SUBNET_1
PRIVATE_APP_SUBNET_2=$PRIVATE_APP_SUBNET_2
PRIVATE_DB_SUBNET_1=$PRIVATE_DB_SUBNET_1
PRIVATE_DB_SUBNET_2=$PRIVATE_DB_SUBNET_2
NAT_GW_1=$NAT_GW_1
NAT_GW_2=$NAT_GW_2
WEB_SG=$WEB_SG
APP_SG=$APP_SG
DB_SG=$DB_SG
EOF

echo "✅ Configuration saved to infrastructure-ids.txt"
cat infrastructure-ids.txt
```

---

## ✅ Verification

### Check VPC

```bash
aws ec2 describe-vpcs --vpc-ids $VPC_ID
```

### Check Subnets

```bash
aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID"
```

### Check Security Groups

```bash
aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$VPC_ID"
```

### Check NAT Gateways

```bash
aws ec2 describe-nat-gateways --filter "Name=vpc-id,Values=$VPC_ID"
```

---

## 📊 Infrastructure Summary

| Component | Count | Details |
|-----------|-------|---------|
| **VPC** | 1 | 10.0.0.0/16 |
| **Subnets** | 6 | 2 public, 2 private app, 2 private DB |
| **Availability Zones** | 2 | us-east-1a, us-east-1b |
| **Internet Gateway** | 1 | For public subnets |
| **NAT Gateways** | 2 | One per AZ for HA |
| **Route Tables** | 4 | 1 public, 2 private app, 1 private DB |
| **Security Groups** | 3 | Web, App, Database |

---

## 🎯 Next Steps

✅ **Infrastructure is ready!**

Now proceed to:
1. **[Database Tier Setup](./02-DATABASE-TIER-SETUP.md)** - Deploy MongoDB replica set
2. **[Application Tier Setup](./03-APPLICATION-TIER-SETUP.md)** - Deploy app servers
3. **[Web Tier Setup](./04-WEB-TIER-SETUP.md)** - Deploy NGINX servers

---

## 🔧 Troubleshooting

### Issue: "VPC limit exceeded"
**Solution**: Request limit increase in AWS Service Quotas

### Issue: "NAT Gateway creation failed"
**Solution**: Check Elastic IP limits, wait a few minutes and retry

### Issue: "Subnet CIDR conflict"
**Solution**: Ensure CIDR blocks don't overlap

---

**Infrastructure setup complete! 🎉**
