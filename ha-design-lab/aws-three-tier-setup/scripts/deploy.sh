#!/bin/bash

# ============================================
# AWS Three-Tier Architecture - Automated Deployment
# ============================================
# This script automates the complete deployment
# ============================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
AWS_REGION=${AWS_REGION:-us-east-1}
VPC_CIDR="10.0.0.0/16"
ENVIRONMENT=${ENVIRONMENT:-production}

echo -e "${PURPLE}============================================${NC}"
echo -e "${PURPLE}AWS Three-Tier Architecture Deployment${NC}"
echo -e "${PURPLE}============================================${NC}\n"

# Check prerequisites
echo -e "${CYAN}📋 Checking prerequisites...${NC}"

if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found. Please install it first.${NC}"
    exit 1
fi

if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS credentials not configured. Run 'aws configure'${NC}"
    exit 1
fi

echo -e "${GREEN}✅ AWS CLI configured${NC}"
echo -e "${GREEN}✅ Region: $AWS_REGION${NC}"
echo -e "${GREEN}✅ Environment: $ENVIRONMENT${NC}\n"

# Confirm deployment
read -p "$(echo -e ${YELLOW}Continue with deployment? [y/N]: ${NC})" -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}Deployment cancelled${NC}"
    exit 1
fi

# ============================================
# STEP 1: Create VPC and Network Infrastructure
# ============================================

echo -e "\n${BLUE}============================================${NC}"
echo -e "${BLUE}STEP 1: Creating VPC and Network${NC}"
echo -e "${BLUE}============================================${NC}\n"

echo -e "${CYAN}Creating VPC...${NC}"
VPC_ID=$(aws ec2 create-vpc \
  --cidr-block $VPC_CIDR \
  --region $AWS_REGION \
  --tag-specifications "ResourceType=vpc,Tags=[{Key=Name,Value=three-tier-vpc-$ENVIRONMENT}]" \
  --query 'Vpc.VpcId' \
  --output text)

echo -e "${GREEN}✅ VPC Created: $VPC_ID${NC}"

# Enable DNS
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-hostnames
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-support

# Create Internet Gateway
echo -e "${CYAN}Creating Internet Gateway...${NC}"
IGW_ID=$(aws ec2 create-internet-gateway \
  --tag-specifications "ResourceType=internet-gateway,Tags=[{Key=Name,Value=three-tier-igw}]" \
  --query 'InternetGateway.InternetGatewayId' \
  --output text)

aws ec2 attach-internet-gateway --internet-gateway-id $IGW_ID --vpc-id $VPC_ID
echo -e "${GREEN}✅ Internet Gateway Created: $IGW_ID${NC}"

# Create Subnets
echo -e "${CYAN}Creating Subnets...${NC}"

PUBLIC_SUBNET_1=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.1.0/24 \
  --availability-zone ${AWS_REGION}a \
  --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=public-subnet-1}]" \
  --query 'Subnet.SubnetId' \
  --output text)

PUBLIC_SUBNET_2=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.2.0/24 \
  --availability-zone ${AWS_REGION}b \
  --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=public-subnet-2}]" \
  --query 'Subnet.SubnetId' \
  --output text)

PRIVATE_APP_SUBNET_1=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.11.0/24 \
  --availability-zone ${AWS_REGION}a \
  --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=private-app-subnet-1}]" \
  --query 'Subnet.SubnetId' \
  --output text)

PRIVATE_APP_SUBNET_2=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.12.0/24 \
  --availability-zone ${AWS_REGION}b \
  --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=private-app-subnet-2}]" \
  --query 'Subnet.SubnetId' \
  --output text)

PRIVATE_DB_SUBNET_1=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.21.0/24 \
  --availability-zone ${AWS_REGION}a \
  --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=private-db-subnet-1}]" \
  --query 'Subnet.SubnetId' \
  --output text)

PRIVATE_DB_SUBNET_2=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.22.0/24 \
  --availability-zone ${AWS_REGION}b \
  --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=private-db-subnet-2}]" \
  --query 'Subnet.SubnetId' \
  --output text)

echo -e "${GREEN}✅ 6 Subnets Created${NC}"

# Enable auto-assign public IP for public subnets
aws ec2 modify-subnet-attribute --subnet-id $PUBLIC_SUBNET_1 --map-public-ip-on-launch
aws ec2 modify-subnet-attribute --subnet-id $PUBLIC_SUBNET_2 --map-public-ip-on-launch

# Create NAT Gateways
echo -e "${CYAN}Creating NAT Gateways (this takes 2-3 minutes)...${NC}"

EIP_1=$(aws ec2 allocate-address --domain vpc --query 'AllocationId' --output text)
EIP_2=$(aws ec2 allocate-address --domain vpc --query 'AllocationId' --output text)

NAT_GW_1=$(aws ec2 create-nat-gateway \
  --subnet-id $PUBLIC_SUBNET_1 \
  --allocation-id $EIP_1 \
  --query 'NatGateway.NatGatewayId' \
  --output text)

NAT_GW_2=$(aws ec2 create-nat-gateway \
  --subnet-id $PUBLIC_SUBNET_2 \
  --allocation-id $EIP_2 \
  --query 'NatGateway.NatGatewayId' \
  --output text)

echo -e "${YELLOW}⏳ Waiting for NAT Gateways to become available...${NC}"
aws ec2 wait nat-gateway-available --nat-gateway-ids $NAT_GW_1 $NAT_GW_2
echo -e "${GREEN}✅ NAT Gateways Created${NC}"

# Create Route Tables
echo -e "${CYAN}Creating Route Tables...${NC}"

PUBLIC_RT=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --tag-specifications "ResourceType=route-table,Tags=[{Key=Name,Value=public-rt}]" \
  --query 'RouteTable.RouteTableId' \
  --output text)

aws ec2 create-route --route-table-id $PUBLIC_RT --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW_ID
aws ec2 associate-route-table --route-table-id $PUBLIC_RT --subnet-id $PUBLIC_SUBNET_1
aws ec2 associate-route-table --route-table-id $PUBLIC_RT --subnet-id $PUBLIC_SUBNET_2

echo -e "${GREEN}✅ Route Tables Configured${NC}"

# ============================================
# STEP 2: Create Security Groups
# ============================================

echo -e "\n${BLUE}============================================${NC}"
echo -e "${BLUE}STEP 2: Creating Security Groups${NC}"
echo -e "${BLUE}============================================${NC}\n"

# Get your public IP
YOUR_IP=$(curl -s ifconfig.me)/32
echo -e "${CYAN}Your public IP: $YOUR_IP${NC}"

# Web Security Group
WEB_SG=$(aws ec2 create-security-group \
  --group-name web-tier-sg \
  --description "Security group for web tier" \
  --vpc-id $VPC_ID \
  --query 'GroupId' \
  --output text)

aws ec2 authorize-security-group-ingress --group-id $WEB_SG --protocol tcp --port 80 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $WEB_SG --protocol tcp --port 443 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $WEB_SG --protocol tcp --port 22 --cidr $YOUR_IP

echo -e "${GREEN}✅ Web Security Group Created: $WEB_SG${NC}"

# App Security Group
APP_SG=$(aws ec2 create-security-group \
  --group-name app-tier-sg \
  --description "Security group for application tier" \
  --vpc-id $VPC_ID \
  --query 'GroupId' \
  --output text)

aws ec2 authorize-security-group-ingress --group-id $APP_SG --protocol tcp --port 3000 --source-group $WEB_SG
aws ec2 authorize-security-group-ingress --group-id $APP_SG --protocol tcp --port 8000 --source-group $WEB_SG
aws ec2 authorize-security-group-ingress --group-id $APP_SG --protocol tcp --port 22 --cidr $YOUR_IP

echo -e "${GREEN}✅ App Security Group Created: $APP_SG${NC}"

# DB Security Group
DB_SG=$(aws ec2 create-security-group \
  --group-name db-tier-sg \
  --description "Security group for database tier" \
  --vpc-id $VPC_ID \
  --query 'GroupId' \
  --output text)

aws ec2 authorize-security-group-ingress --group-id $DB_SG --protocol tcp --port 27017 --source-group $APP_SG
aws ec2 authorize-security-group-ingress --group-id $DB_SG --protocol tcp --port 27017 --source-group $DB_SG
aws ec2 authorize-security-group-ingress --group-id $DB_SG --protocol tcp --port 22 --cidr $YOUR_IP

echo -e "${GREEN}✅ DB Security Group Created: $DB_SG${NC}"

# ============================================
# STEP 3: Save Configuration
# ============================================

echo -e "\n${BLUE}============================================${NC}"
echo -e "${BLUE}STEP 3: Saving Configuration${NC}"
echo -e "${BLUE}============================================${NC}\n"

cat > infrastructure-ids.txt <<EOF
# AWS Three-Tier Infrastructure IDs
# Generated: $(date)
# Region: $AWS_REGION
# Environment: $ENVIRONMENT

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
YOUR_IP=$YOUR_IP
EOF

echo -e "${GREEN}✅ Configuration saved to infrastructure-ids.txt${NC}"

# ============================================
# DEPLOYMENT SUMMARY
# ============================================

echo -e "\n${PURPLE}============================================${NC}"
echo -e "${PURPLE}DEPLOYMENT SUMMARY${NC}"
echo -e "${PURPLE}============================================${NC}\n"

echo -e "${GREEN}✅ VPC Created:${NC} $VPC_ID"
echo -e "${GREEN}✅ Subnets Created:${NC} 6 (2 public, 2 private app, 2 private DB)"
echo -e "${GREEN}✅ NAT Gateways:${NC} 2 (high availability)"
echo -e "${GREEN}✅ Security Groups:${NC} 3 (web, app, database)"
echo -e "${GREEN}✅ Configuration Saved:${NC} infrastructure-ids.txt"

echo -e "\n${YELLOW}📋 NEXT STEPS:${NC}"
echo -e "1. Review infrastructure-ids.txt"
echo -e "2. Create SSH key pair: ${CYAN}aws ec2 create-key-pair --key-name mongodb-key${NC}"
echo -e "3. Deploy database tier: ${CYAN}Follow docs/02-DATABASE-TIER-SETUP.md${NC}"
echo -e "4. Deploy application tier: ${CYAN}Follow docs/03-APPLICATION-TIER-SETUP.md${NC}"
echo -e "5. Deploy web tier: ${CYAN}Follow docs/04-WEB-TIER-SETUP.md${NC}"

echo -e "\n${PURPLE}============================================${NC}"
echo -e "${GREEN}Infrastructure deployment complete! 🎉${NC}"
echo -e "${PURPLE}============================================${NC}\n"
