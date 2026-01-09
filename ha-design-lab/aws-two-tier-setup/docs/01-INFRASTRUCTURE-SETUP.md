# 🏗️ Step 1: Infrastructure Setup - Two-Tier Architecture

> **Creating VPC, Subnets, Security Groups, Load Balancer, and Network Components**

---

## 📋 What We'll Create

- ✅ VPC (Virtual Private Cloud)
- ✅ 4 Subnets (2 public for web/app, 2 private for database)
- ✅ Internet Gateway
- ✅ Route Tables
- ✅ Security Groups (3 groups)
- ✅ Application Load Balancer
- ✅ Target Groups

---

## 🎯 Infrastructure Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                    VPC: 10.0.0.0/16                            │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              Internet Gateway                            │  │
│  └─────────────────────┬───────────────────────────────────┘  │
│                        │                                        │
│  ┌─────────────────────┴───────────────────────────────────┐  │
│  │         Application Load Balancer (ALB)                  │  │
│  └─────────────────────┬───────────────────────────────────┘  │
│                        │                                        │
│  ┌─────────────────────┴───────────────────────────────────┐  │
│  │         PUBLIC SUBNETS (Web/App Tier)                    │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │  AZ-1 (us-east-1a)          AZ-2 (us-east-1b)          │  │
│  │  10.0.1.0/24                10.0.2.0/24                 │  │
│  │  ┌─────────────┐            ┌─────────────┐            │  │
│  │  │ Web/App     │            │ Web/App     │            │  │
│  │  │ Servers     │            │ Servers     │            │  │
│  │  │ (NGINX +    │            │ (NGINX +    │            │  │
│  │  │  Node.js)   │            │  Node.js)   │            │  │
│  │  └─────────────┘            └─────────────┘            │  │
│  └─────────────────────────────────────────────────────────┘  │
│                        │                                        │
│  ┌─────────────────────┴───────────────────────────────────┐  │
│  │         PRIVATE SUBNETS (Database Tier)                  │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │  AZ-1 (us-east-1a)          AZ-2 (us-east-1b)          │  │
│  │  10.0.11.0/24               10.0.12.0/24                │  │
│  │  ┌─────────────┐            ┌─────────────┐            │  │
│  │  │ MongoDB     │◄──────────►│ MongoDB     │            │  │
│  │  │ PRIMARY     │ Replication│ SECONDARY   │            │  │
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
export VPC_NAME="two-tier-vpc"
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
  --tag-specifications "ResourceType=internet-gateway,Tags=[{Key=Name,Value=two-tier-igw}]" \
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

#### Public Subnets (Web/App Tier)

```bash
# ============================================
# RUN ON: Your Local Machine
# ============================================

# Public Subnet 1 (AZ-1)
PUBLIC_SUBNET_1=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.1.0/24 \
  --availability-zone us-east-1a \
  --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=public-webapp-subnet-1}]" \
  --query 'Subnet.SubnetId' \
  --output text)

echo "✅ Public Subnet 1 Created: $PUBLIC_SUBNET_1"

# Public Subnet 2 (AZ-2)
PUBLIC_SUBNET_2=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.2.0/24 \
  --availability-zone us-east-1b \
  --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=public-webapp-subnet-2}]" \
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

#### Private Subnets (Database Tier)

```bash
# ============================================
# RUN ON: Your Local Machine
# ============================================

# Private DB Subnet 1 (AZ-1)
PRIVATE_DB_SUBNET_1=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.11.0/24 \
  --availability-zone us-east-1a \
  --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=private-db-subnet-1}]" \
  --query 'Subnet.SubnetId' \
  --output text)

echo "✅ Private DB Subnet 1 Created: $PRIVATE_DB_SUBNET_1"

# Private DB Subnet 2 (AZ-2)
PRIVATE_DB_SUBNET_2=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.12.0/24 \
  --availability-zone us-east-1b \
  --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=private-db-subnet-2}]" \
  --query 'Subnet.SubnetId' \
  --output text)

echo "✅ Private DB Subnet 2 Created: $PRIVATE_DB_SUBNET_2"
```

---

### 📍 **STEP 1.4: Create Route Tables**

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

#### Private Route Table (Database Tier - No Internet)

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

# Associate with private DB subnets (NO Internet Gateway - isolated)
aws ec2 associate-route-table \
  --route-table-id $PRIVATE_DB_RT \
  --subnet-id $PRIVATE_DB_SUBNET_1

aws ec2 associate-route-table \
  --route-table-id $PRIVATE_DB_RT \
  --subnet-id $PRIVATE_DB_SUBNET_2

echo "✅ Private DB subnets configured (isolated, no internet)"
```

---

### 📍 **STEP 1.5: Create Security Groups**

#### ALB Security Group

```bash
# ============================================
# RUN ON: Your Local Machine
# ============================================

# Create ALB Security Group
ALB_SG=$(aws ec2 create-security-group \
  --group-name alb-sg \
  --description "Security group for Application Load Balancer" \
  --vpc-id $VPC_ID \
  --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=alb-sg}]" \
  --query 'GroupId' \
  --output text)

echo "✅ ALB Security Group Created: $ALB_SG"

# Allow HTTP from anywhere
aws ec2 authorize-security-group-ingress \
  --group-id $ALB_SG \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0

# Allow HTTPS from anywhere
aws ec2 authorize-security-group-ingress \
  --group-id $ALB_SG \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0

echo "✅ ALB Security Group rules configured"
```

#### Web/App Tier Security Group

```bash
# ============================================
# RUN ON: Your Local Machine
# ============================================

# Create Web/App Security Group
WEBAPP_SG=$(aws ec2 create-security-group \
  --group-name webapp-tier-sg \
  --description "Security group for web/application tier" \
  --vpc-id $VPC_ID \
  --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=webapp-tier-sg}]" \
  --query 'GroupId' \
  --output text)

echo "✅ Web/App Security Group Created: $WEBAPP_SG"

# Allow HTTP from ALB
aws ec2 authorize-security-group-ingress \
  --group-id $WEBAPP_SG \
  --protocol tcp \
  --port 80 \
  --source-group $ALB_SG

# Allow HTTPS from ALB
aws ec2 authorize-security-group-ingress \
  --group-id $WEBAPP_SG \
  --protocol tcp \
  --port 443 \
  --source-group $ALB_SG

# Allow Node.js port from ALB
aws ec2 authorize-security-group-ingress \
  --group-id $WEBAPP_SG \
  --protocol tcp \
  --port 3000 \
  --source-group $ALB_SG

# Allow SSH from your IP (CHANGE THIS)
YOUR_IP="YOUR_PUBLIC_IP/32"  # Get from: curl ifconfig.me
aws ec2 authorize-security-group-ingress \
  --group-id $WEBAPP_SG \
  --protocol tcp \
  --port 22 \
  --cidr $YOUR_IP

echo "✅ Web/App Security Group rules configured"
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

# Allow MongoDB traffic from Web/App Tier
aws ec2 authorize-security-group-ingress \
  --group-id $DB_SG \
  --protocol tcp \
  --port 27017 \
  --source-group $WEBAPP_SG

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

### 📍 **STEP 1.6: Create Application Load Balancer**

```bash
# ============================================
# RUN ON: Your Local Machine
# ============================================

# Create Application Load Balancer
ALB_ARN=$(aws elbv2 create-load-balancer \
  --name two-tier-alb \
  --subnets $PUBLIC_SUBNET_1 $PUBLIC_SUBNET_2 \
  --security-groups $ALB_SG \
  --scheme internet-facing \
  --type application \
  --ip-address-type ipv4 \
  --tags Key=Name,Value=two-tier-alb \
  --query 'LoadBalancers[0].LoadBalancerArn' \
  --output text)

echo "✅ Application Load Balancer Created: $ALB_ARN"

# Get ALB DNS name
ALB_DNS=$(aws elbv2 describe-load-balancers \
  --load-balancer-arns $ALB_ARN \
  --query 'LoadBalancers[0].DNSName' \
  --output text)

echo "✅ ALB DNS Name: $ALB_DNS"
```

---

### 📍 **STEP 1.7: Create Target Group**

```bash
# ============================================
# RUN ON: Your Local Machine
# ============================================

# Create Target Group
TG_ARN=$(aws elbv2 create-target-group \
  --name webapp-target-group \
  --protocol HTTP \
  --port 80 \
  --vpc-id $VPC_ID \
  --health-check-enabled \
  --health-check-protocol HTTP \
  --health-check-path /health \
  --health-check-interval-seconds 30 \
  --health-check-timeout-seconds 5 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3 \
  --matcher HttpCode=200 \
  --tags Key=Name,Value=webapp-target-group \
  --query 'TargetGroups[0].TargetGroupArn' \
  --output text)

echo "✅ Target Group Created: $TG_ARN"

# Create Listener (HTTP)
LISTENER_ARN=$(aws elbv2 create-listener \
  --load-balancer-arn $ALB_ARN \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=forward,TargetGroupArn=$TG_ARN \
  --query 'Listeners[0].ListenerArn' \
  --output text)

echo "✅ Listener Created: $LISTENER_ARN"
```

---

### 📍 **STEP 1.8: Save Configuration**

```bash
# ============================================
# RUN ON: Your Local Machine
# ============================================

# Save all IDs to a file for later use
cat > infrastructure-ids.txt <<EOF
# Two-Tier Infrastructure IDs
# Generated: $(date)

VPC_ID=$VPC_ID
IGW_ID=$IGW_ID
PUBLIC_SUBNET_1=$PUBLIC_SUBNET_1
PUBLIC_SUBNET_2=$PUBLIC_SUBNET_2
PRIVATE_DB_SUBNET_1=$PRIVATE_DB_SUBNET_1
PRIVATE_DB_SUBNET_2=$PRIVATE_DB_SUBNET_2
PUBLIC_RT=$PUBLIC_RT
PRIVATE_DB_RT=$PRIVATE_DB_RT
ALB_SG=$ALB_SG
WEBAPP_SG=$WEBAPP_SG
DB_SG=$DB_SG
ALB_ARN=$ALB_ARN
ALB_DNS=$ALB_DNS
TG_ARN=$TG_ARN
LISTENER_ARN=$LISTENER_ARN
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

### Check Load Balancer

```bash
aws elbv2 describe-load-balancers --load-balancer-arns $ALB_ARN
```

### Check Target Group

```bash
aws elbv2 describe-target-groups --target-group-arns $TG_ARN
```

### Test ALB DNS (should return 503 until targets are registered)

```bash
curl http://$ALB_DNS
```

---

## 📊 Infrastructure Summary

| Component | Count | Details |
|-----------|-------|---------|
| **VPC** | 1 | 10.0.0.0/16 |
| **Subnets** | 4 | 2 public, 2 private |
| **Availability Zones** | 2 | us-east-1a, us-east-1b |
| **Internet Gateway** | 1 | For public subnets |
| **Route Tables** | 2 | 1 public, 1 private |
| **Security Groups** | 3 | ALB, Web/App, Database |
| **Load Balancer** | 1 | Application Load Balancer |
| **Target Groups** | 1 | For web/app instances |

---

## 🎯 Next Steps

✅ **Infrastructure is ready!**

Now proceed to:
1. **[Database Tier Setup](./02-DATABASE-TIER-SETUP.md)** - Deploy MongoDB replica set
2. **[Web/App Tier Setup](./03-WEBAPP-TIER-SETUP.md)** - Deploy application servers
3. **[Auto-Scaling Setup](./04-AUTOSCALING-SETUP.md)** - Configure auto-scaling

---

## 🔧 Troubleshooting

### Issue: "VPC limit exceeded"
**Solution**: Request limit increase in AWS Service Quotas

### Issue: "Subnet CIDR conflict"
**Solution**: Ensure CIDR blocks don't overlap

### Issue: "ALB creation failed"
**Solution**: Ensure you have at least 2 subnets in different AZs

### Issue: "Security group rule limit"
**Solution**: Consolidate rules or request limit increase

---

**Infrastructure setup complete! 🎉**
