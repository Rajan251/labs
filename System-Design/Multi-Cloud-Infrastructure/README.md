# Cloud-Native HA Infrastructure (AWS Terraform Modules)

This library provides production-ready Terraform modules for deploying a high-availability architecture on AWS, suitable for the "Cloud-Native HA" and "Enterprise Reference" projects defined in this lab.

## Directory Structure
```
Multi-Cloud-Infrastructure/aws/
├── modules/
│   ├── networking/  # VPC, Multi-AZ Subnets, HA NAT Gateways
│   ├── compute/     # EKS Cluster, Managed Node Groups, IAM
│   ├── database/    # Aurora PostgreSQL (Multi-AZ Encrypted)
│   ├── cache/       # ElastiCache Redis (Cluster Mode Enabled)
│   ├── messaging/   # MSK (Managed Kafka) 3 Brokers
│   ├── lb/          # ALB with HTTP->HTTPS Redirect & Health Checks
│   ├── cdn/         # CloudFront Distribution (Global)
│   └── monitoring/  # CloudWatch Dashboards & Alarms
```

## Module Usage Examples

### 1. Networking (Base Layer)
```hcl
module "networking" {
  source             = "./modules/networking"
  environment        = "prod"
  vpc_cidr           = "10.0.0.0/16"
  availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]
}
```

### 2. Compute (EKS)
```hcl
module "compute" {
  source             = "./modules/compute"
  cluster_name       = "prod-eks"
  private_subnet_ids = module.networking.private_subnets
}
```

### 3. Database (Aurora)
```hcl
module "database" {
  source             = "./modules/database"
  cluster_identifier = "prod-aurora-cluster"
  db_name            = "order_db"
  master_password    = var.db_password
  subnet_ids         = module.networking.private_subnets
  availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]
}
```

## Disaster Recovery (DR) Strategy
To enable DR to a secondary region (e.g., `us-west-2`):
1.  Deploy the same stack in `us-west-2` using a distinct `environment` variable (e.g., `dr`).
2.  **Database**: Enable `global_cluster_identifier` in the `database` module variables to replicate data globally.
3.  **DNS**: Use Route53 (outside these modules) to failover traffic from ALB-East to ALB-West.

## Estimated Monthly Cost (US-East-1)

| Resource | Size/Config | Approx. Cost |
| :--- | :--- | :--- |
| **EKS Cluster** | Control Plane | $73.00 |
| **EKS Nodes** | 2x t3.medium | $60.00 |
| **Aurora DB** | db.r6g.large (Multi-AZ) | $400.00 |
| **ElastiCache**| 2x cache.t3.medium | $70.00 |
| **MSK Kafka** | 3x kafka.t3.small | $150.00 |
| **NAT Gateway**| 3x (High Availability) | $100.00 |
| **ALB** | 1 LCU | $20.00 |
| **Total** | | **~$873/mo** |

> [!WARNING]
> This configuration assumes a high-availability production setup. For personal labs, reduce `instance_count`, use Single-AZ, and disable MSK/Aurora Multi-AZ.
