#!/bin/bash

# ============================================
# Network Verification Script
# Tier-2 AWS Architecture
# ============================================

set -e

echo "=================================================="
echo "Tier-2 Architecture - Network Verification Script"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print success
success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Function to print error
error() {
    echo -e "${RED}✗${NC} $1"
}

# Function to print warning
warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    error "AWS CLI is not installed. Please install it first."
    exit 1
fi
success "AWS CLI is installed"

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    error "AWS credentials not configured. Run 'aws configure'"
    exit 1
fi
success "AWS credentials configured"

echo ""
echo "Enter your VPC ID (e.g., vpc-xxxxxxxxxxxxxxxxx):"
read VPC_ID

if [ -z "$VPC_ID" ]; then
    error "VPC ID cannot be empty"
    exit 1
fi

echo ""
echo "Verifying VPC: $VPC_ID"
echo "=================================================="

# Verify VPC exists
echo ""
echo "1. Checking VPC..."
if aws ec2 describe-vpcs --vpc-ids "$VPC_ID" &> /dev/null; then
    VPC_CIDR=$(aws ec2 describe-vpcs --vpc-ids "$VPC_ID" --query 'Vpcs[0].CidrBlock' --output text)
    VPC_STATE=$(aws ec2 describe-vpcs --vpc-ids "$VPC_ID" --query 'Vpcs[0].State' --output text)
    
    if [ "$VPC_STATE" == "available" ]; then
        success "VPC is available (CIDR: $VPC_CIDR)"
    else
        error "VPC state is $VPC_STATE (expected: available)"
    fi
else
    error "VPC not found"
    exit 1
fi

# Check DNS settings
DNS_SUPPORT=$(aws ec2 describe-vpc-attribute --vpc-id "$VPC_ID" --attribute enableDnsSupport --query 'EnableDnsSupport.Value' --output text)
DNS_HOSTNAMES=$(aws ec2 describe-vpc-attribute --vpc-id "$VPC_ID" --attribute enableDnsHostnames --query 'EnableDnsHostnames.Value' --output text)

if [ "$DNS_SUPPORT" == "true" ]; then
    success "DNS resolution enabled"
else
    error "DNS resolution disabled"
fi

if [ "$DNS_HOSTNAMES" == "true" ]; then
    success "DNS hostnames enabled"
else
    error "DNS hostnames disabled"
fi

# Check subnets
echo ""
echo "2. Checking Subnets..."
SUBNET_COUNT=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query 'length(Subnets)' --output text)

if [ "$SUBNET_COUNT" -ge 4 ]; then
    success "Found $SUBNET_COUNT subnets (expected: 4+)"
    
    # List subnets
    aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" \
        --query 'Subnets[*].[Tags[?Key==`Name`].Value|[0],CidrBlock,AvailabilityZone,MapPublicIpOnLaunch]' \
        --output table
else
    warning "Found only $SUBNET_COUNT subnets (expected: 4)"
fi

# Check Internet Gateway
echo ""
echo "3. Checking Internet Gateway..."
IGW_ID=$(aws ec2 describe-internet-gateways --filters "Name=attachment.vpc-id,Values=$VPC_ID" --query 'InternetGateways[0].InternetGatewayId' --output text)

if [ "$IGW_ID" != "None" ] && [ ! -z "$IGW_ID" ]; then
    success "Internet Gateway found: $IGW_ID"
    
    IGW_STATE=$(aws ec2 describe-internet-gateways --internet-gateway-ids "$IGW_ID" --query 'InternetGateways[0].Attachments[0].State' --output text)
    if [ "$IGW_STATE" == "available" ]; then
        success "Internet Gateway is attached"
    else
        error "Internet Gateway state: $IGW_STATE"
    fi
else
    error "No Internet Gateway found"
fi

# Check NAT Gateways
echo ""
echo "4. Checking NAT Gateway..."
NAT_COUNT=$(aws ec2 describe-nat-gateways --filter "Name=vpc-id,Values=$VPC_ID" "Name=state,Values=available" --query 'length(NatGateways)' --output text)

if [ "$NAT_COUNT" -ge 1 ]; then
    success "Found $NAT_COUNT NAT Gateway(s)"
    
    # Get NAT Gateway details
    aws ec2 describe-nat-gateways --filter "Name=vpc-id,Values=$VPC_ID" "Name=state,Values=available" \
        --query 'NatGateways[*].[NatGatewayId,SubnetId,NatGatewayAddresses[0].PublicIp,State]' \
        --output table
else
    error "No NAT Gateway found in available state"
fi

# Check Route Tables
echo ""
echo "5. Checking Route Tables..."
RT_COUNT=$(aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$VPC_ID" --query 'length(RouteTables)' --output text)

if [ "$RT_COUNT" -ge 2 ]; then
    success "Found $RT_COUNT route tables"
    
    # Check for IGW routes
    IGW_ROUTES=$(aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$VPC_ID" --query 'RouteTables[*].Routes[?GatewayId!=`null` && starts_with(GatewayId, `igw-`)]' --output text)
    
    if [ ! -z "$IGW_ROUTES" ]; then
        success "Found route(s) to Internet Gateway"
    else
        warning "No routes to Internet Gateway found"
    fi
    
    # Check for NAT routes
    NAT_ROUTES=$(aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$VPC_ID" --query 'RouteTables[*].Routes[?NatGatewayId!=`null`]' --output text)
    
    if [ ! -z "$NAT_ROUTES" ]; then
        success "Found route(s) to NAT Gateway"
    else
        warning "No routes to NAT Gateway found"
    fi
else
    warning "Found only $RT_COUNT route tables (expected: 2+)"
fi

# Check Security Groups
echo ""
echo "6. Checking Security Groups..."
SG_COUNT=$(aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$VPC_ID" --query 'length(SecurityGroups)' --output text)

if [ "$SG_COUNT" -ge 1 ]; then
    success "Found $SG_COUNT security group(s)"
    
    # List security groups
    aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$VPC_ID" \
        --query 'SecurityGroups[*].[GroupId,GroupName,Description]' \
        --output table
else
    warning "No custom security groups found"
fi

# Check EC2 Instances
echo ""
echo "7. Checking EC2 Instances..."
INSTANCE_COUNT=$(aws ec2 describe-instances --filters "Name=vpc-id,Values=$VPC_ID" "Name=instance-state-name,Values=running" --query 'length(Reservations[*].Instances[])' --output text)

if [ "$INSTANCE_COUNT" -ge 1 ]; then
    success "Found $INSTANCE_COUNT running instance(s)"
    
    # List instances
    aws ec2 describe-instances --filters "Name=vpc-id,Values=$VPC_ID" "Name=instance-state-name,Values=running" \
        --query 'Reservations[*].Instances[*].[InstanceId,Tags[?Key==`Name`].Value|[0],PrivateIpAddress,PublicIpAddress,SubnetId]' \
        --output table
else
    warning "No running instances found"
fi

# Check Client VPN Endpoints
echo ""
echo "8. Checking Client VPN Endpoints..."
VPN_COUNT=$(aws ec2 describe-client-vpn-endpoints --query "length(ClientVpnEndpoints[?VpcId=='$VPC_ID'])" --output text)

if [ "$VPN_COUNT" -ge 1 ]; then
    success "Found $VPN_COUNT Client VPN endpoint(s)"
    
    # List VPN endpoints
    aws ec2 describe-client-vpn-endpoints --query "ClientVpnEndpoints[?VpcId=='$VPC_ID'].[ClientVpnEndpointId,Status.Code,ClientCidrBlock]" --output table
else
    warning "No Client VPN endpoints found"
fi

# Summary
echo ""
echo "=================================================="
echo "Verification Summary"
echo "=================================================="
echo ""
echo "VPC Configuration:"
echo "  VPC ID: $VPC_ID"
echo "  CIDR: $VPC_CIDR"
echo "  State: $VPC_STATE"
echo "  DNS Support: $DNS_SUPPORT"
echo "  DNS Hostnames: $DNS_HOSTNAMES"
echo ""
echo "Resources:"
echo "  Subnets: $SUBNET_COUNT"
echo "  NAT Gateways: $NAT_COUNT"
echo "  Route Tables: $RT_COUNT"
echo "  Security Groups: $SG_COUNT"
echo "  Running Instances: $INSTANCE_COUNT"
echo "  VPN Endpoints: $VPN_COUNT"
echo ""
echo "=================================================="
echo "Verification Complete!"
echo "=================================================="
