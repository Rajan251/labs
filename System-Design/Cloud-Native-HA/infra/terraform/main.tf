provider "aws" {
  region = "us-east-1"
}

# 1. VPC Network (Multi-AZ)
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  name   = "ha-vpc"
  cidr   = "10.0.0.0/16"

  azs             = ["us-east-1a", "us-east-1b", "us-east-1c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = false  # Multi-AZ NAT for high availability
  one_nat_gateway_per_az = true
}

# 2. EKS Cluster
module "eks" {
  source          = "terraform-aws-modules/eks/aws"
  cluster_name    = "ha-cluster"
  cluster_version = "1.27"
  vpc_id          = module.vpc.vpc_id
  subnet_ids      = module.vpc.private_subnets

  eks_managed_node_groups = {
    general = {
      min_size     = 3
      max_size     = 10
      desired_size = 3

      instance_types = ["t3.medium"]
      capacity_type  = "ON_DEMAND"
    }
  }
}

# 3. RDS Aurora PostgreSQL (Multi-AZ)
module "aurora" {
  source         = "terraform-aws-modules/rds-aurora/aws"
  name           = "ha-db"
  engine         = "aurora-postgresql"
  engine_version = "14.5"
  
  vpc_id                = module.vpc.vpc_id
  subnets               = module.vpc.private_subnets
  create_security_group = true
  
  replica_count         = 2  # 1 Writer + 2 Readers
  instance_type         = "db.r6g.large"
  storage_encrypted     = true
  
  monitoring_interval = 60
}

# 4. ElastiCache Redis (Cluster Mode Enabled)
resource "aws_elasticache_replication_group" "ha_redis" {
  replication_group_id          = "ha-redis-cluster"
  replication_group_description = "HA Redis Cluster"
  node_type                     = "cache.t3.medium"
  port                          = 6379
  automatic_failover_enabled    = true
  multi_az_enabled              = true
  num_cache_clusters            = 3 # Spread across AZs
  subnet_group_name             = aws_elasticache_subnet_group.redis_subnet.name
}

resource "aws_elasticache_subnet_group" "redis_subnet" {
  name       = "ha-redis-subnet"
  subnet_ids = module.vpc.private_subnets
}
