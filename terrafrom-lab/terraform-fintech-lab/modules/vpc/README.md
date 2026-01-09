# VPC Module

This module creates a production-grade VPC with public, private, and database subnets across multiple availability zones.

## Features

- Multi-AZ VPC with configurable CIDR
- Public subnets with internet gateway
- Private subnets with NAT gateway
- Database subnets (isolated)
- VPC Flow Logs
- DNS support enabled

## Usage

```hcl
module "vpc" {
  source = "../../modules/vpc"

  environment        = "production"
  vpc_cidr           = "10.0.0.0/16"
  availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]
  
  # NAT Gateway configuration
  enable_nat_gateway     = true
  single_nat_gateway     = false
  one_nat_gateway_per_az = true
  
  # Flow logs
  enable_flow_logs = true
  
  tags = {
    Project   = "PayFlow"
    ManagedBy = "Terraform"
  }
}
```

## Outputs

- `vpc_id` - ID of the VPC
- `vpc_cidr` - CIDR block of the VPC
- `public_subnet_ids` - List of public subnet IDs
- `private_subnet_ids` - List of private subnet IDs
- `database_subnet_ids` - List of database subnet IDs
- `nat_gateway_ids` - List of NAT Gateway IDs
- `internet_gateway_id` - ID of the Internet Gateway
