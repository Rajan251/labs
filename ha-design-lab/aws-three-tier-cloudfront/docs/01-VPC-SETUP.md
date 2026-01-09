# VPC Setup Guide

## Overview

This guide walks you through setting up a Virtual Private Cloud (VPC) for the three-tier architecture using both the AWS Web Console and Terraform.

## Architecture

The VPC includes:
- **CIDR Block**: 10.0.0.0/16 (65,536 IP addresses)
- **Availability Zones**: 2 AZs for high availability
- **Subnets**: 6 subnets (2 public, 2 private app, 2 private DB)
- **DNS**: Enabled for hostname resolution

## Web Console Setup

### Step 1: Create VPC

1. Navigate to **VPC Dashboard** in AWS Console
2. Click **Create VPC**
3. Configure:
   - **Name**: `three-tier-app-dev-vpc`
   - **IPv4 CIDR block**: `10.0.0.0/16`
   - **IPv6 CIDR block**: No IPv6
   - **Tenancy**: Default
   - **Enable DNS resolution**: Yes
   - **Enable DNS hostnames**: Yes
4. Click **Create VPC**

### Step 2: Create Subnets

#### Public Subnet 1 (AZ-A)
1. Click **Subnets** → **Create subnet**
2. Configure:
   - **VPC**: Select your VPC
   - **Subnet name**: `three-tier-app-dev-public-us-east-1a`
   - **Availability Zone**: `us-east-1a`
   - **IPv4 CIDR block**: `10.0.1.0/24`
3. Click **Create subnet**

#### Public Subnet 2 (AZ-B)
- **Subnet name**: `three-tier-app-dev-public-us-east-1b`
- **Availability Zone**: `us-east-1b`
- **IPv4 CIDR block**: `10.0.2.0/24`

#### Private App Subnet 1 (AZ-A)
- **Subnet name**: `three-tier-app-dev-private-app-us-east-1a`
- **Availability Zone**: `us-east-1a`
- **IPv4 CIDR block**: `10.0.11.0/24`

#### Private App Subnet 2 (AZ-B)
- **Subnet name**: `three-tier-app-dev-private-app-us-east-1b`
- **Availability Zone**: `us-east-1b`
- **IPv4 CIDR block**: `10.0.12.0/24`

#### Private DB Subnet 1 (AZ-A)
- **Subnet name**: `three-tier-app-dev-private-db-us-east-1a`
- **Availability Zone**: `us-east-1a`
- **IPv4 CIDR block**: `10.0.21.0/24`

#### Private DB Subnet 2 (AZ-B)
- **Subnet name**: `three-tier-app-dev-private-db-us-east-1b`
- **Availability Zone**: `us-east-1b`
- **IPv4 CIDR block**: `10.0.22.0/24`

### Step 3: Enable Auto-assign Public IP for Public Subnets

1. Select each public subnet
2. Click **Actions** → **Edit subnet settings**
3. Check **Enable auto-assign public IPv4 address**
4. Click **Save**

## Terraform Setup

The VPC is automatically created using the networking module:

```hcl
module "networking" {
  source = "../../modules/networking"

  project_name       = "three-tier-app"
  environment        = "dev"
  vpc_cidr           = "10.0.0.0/16"
  availability_zones = ["us-east-1a", "us-east-1b"]
}
```

### Deploy with Terraform

```bash
cd terraform/environments/dev
terraform init
terraform plan
terraform apply
```

## Verification

### Console Verification
1. Go to **VPC Dashboard**
2. Verify VPC is created with correct CIDR
3. Check **Subnets** - should see 6 subnets
4. Verify each subnet has correct CIDR and AZ

### CLI Verification

```bash
# List VPCs
aws ec2 describe-vpcs --filters "Name=tag:Name,Values=three-tier-app-dev-vpc"

# List subnets
aws ec2 describe-subnets --filters "Name=vpc-id,Values=<vpc-id>"

# Verify CIDR blocks
aws ec2 describe-subnets --query 'Subnets[*].[SubnetId,CidrBlock,AvailabilityZone,Tags[?Key==`Name`].Value|[0]]' --output table
```

### Terraform Verification

```bash
terraform output vpc_id
terraform output public_subnet_ids
terraform output private_app_subnet_ids
terraform output private_db_subnet_ids
```

## Best Practices

1. **CIDR Planning**: Use non-overlapping CIDR blocks
2. **Multi-AZ**: Always use at least 2 AZs for HA
3. **Subnet Sizing**: Use /24 for subnets (251 usable IPs)
4. **DNS**: Enable DNS hostnames for EC2 instances
5. **Tagging**: Use consistent naming and tagging

## Troubleshooting

### Issue: VPC creation fails
**Solution**: Check if you've reached VPC limit (default: 5 per region)

### Issue: Subnet CIDR conflicts
**Solution**: Ensure subnet CIDRs don't overlap and are within VPC CIDR

### Issue: Can't create resources in VPC
**Solution**: Verify VPC state is "available"

## Next Steps

- [Internet Gateway & NAT Setup](03-INTERNET-GATEWAY-NAT.md)
- [Security Groups Configuration](04-SECURITY-GROUPS.md)
- [Subnets & Routing](02-SUBNETS-ROUTING.md)
