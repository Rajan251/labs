provider "aws" {
  region = var.region
}

# VPC
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  name   = "video-platform-vpc"
  cidr   = "10.0.0.0/16"

  azs             = ["us-east-1a", "us-east-1b"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]

  enable_nat_gateway = true
}

# EKS Cluster
module "eks" {
  source          = "terraform-aws-modules/eks/aws"
  cluster_name    = "video-platform-cluster"
  cluster_version = "1.27"
  subnet_ids      = module.vpc.private_subnets
  vpc_id          = module.vpc.vpc_id

  eks_managed_node_groups = {
    general = {
      desired_size = 2
      max_size     = 3
      min_size     = 1
      instance_types = ["t3.medium"]
    }
    video_processing = {
      desired_size = 1
      max_size     = 5
      min_size     = 0
      instance_types = ["c5.xlarge"]
      labels = {
        workload = "transcoding"
      }
    }
  }
}

# S3 Bucket for Videos
resource "aws_s3_bucket" "videos" {
  bucket = "video-platform-storage-${var.environment}"
}

# RDS Postgres
resource "aws_db_instance" "default" {
  allocated_storage    = 20
  engine               = "postgres"
  engine_version       = "15.3"
  instance_class       = "db.t3.micro"
  db_name              = "videodb"
  username             = "dbadmin"
  password             = "securepassword"
  skip_final_snapshot  = true
}
