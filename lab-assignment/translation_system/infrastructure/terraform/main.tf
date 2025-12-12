provider "aws" {
  region = "us-west-2"
}

locals {
  cluster_name = "translation-system-cluster"
}

module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  version = "5.0.0"

  name = "translation-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["us-west-2a", "us-west-2b"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = true
}

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "19.15.3"

  cluster_name    = local.cluster_name
  cluster_version = "1.27"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  cluster_endpoint_public_access = true

  # Node Groups
  eks_managed_node_groups = {
    # 1. System Node Group (CoreDNS, Kube-Proxy, Autoscaler, Ingress)
    system = {
      name = "system-node-group"
      instance_types = ["t3.medium"]
      min_size     = 2
      max_size     = 3
      desired_size = 2
      labels = {
        role = "system"
      }
    }

    # 2. Priority GPU Workers (On-Demand, Warm Pool)
    priority_gpu = {
      name = "priority-gpu-group"
      instance_types = ["g5.12xlarge"] # 4x A10G
      
      # Keep 1 warm for SLA, scale up to 5
      min_size     = 1
      max_size     = 5
      desired_size = 1
      
      capacity_type = "ON_DEMAND"
      
      labels = {
        role = "worker"
        tier = "priority"
        accelerator = "nvidia-gpu"
      }
      
      taints = {
        dedicated = {
          key    = "tier"
          value  = "priority"
          effect = "NO_SCHEDULE"
        }
      }
    }

    # 3. Standard GPU Workers (Spot, Scale-to-Zero)
    standard_gpu = {
      name = "standard-gpu-group"
      instance_types = ["g5.12xlarge"]
      
      # Scale to zero allowed
      min_size     = 0
      max_size     = 10
      desired_size = 0
      
      capacity_type = "SPOT"
      
      labels = {
        role = "worker"
        tier = "standard"
        accelerator = "nvidia-gpu"
      }
      
      taints = {
        dedicated = {
          key    = "tier"
          value  = "standard"
          effect = "NO_SCHEDULE"
        }
      }
    }
  }
}
