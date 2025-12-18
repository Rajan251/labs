resource "aws_elasticache_subnet_group" "default" {
  name       = "${var.cluster_id}-subnet-group"
  subnet_ids = var.subnet_ids
}

resource "aws_elasticache_replication_group" "redis" {
  replication_group_id          = var.cluster_id
  replication_group_description = "Redis Cluster for ${var.cluster_id}"
  node_type                     = var.node_type
  port                          = 6379
  automatic_failover_enabled    = true
  multi_az_enabled              = true
  subnet_group_name             = aws_elasticache_subnet_group.default.name
  
  num_cache_clusters = var.num_cache_nodes # For non-cluster mode or disabled cluster mode
  
  # For Cluster Mode Enabled (Sharding)
  # num_node_groups         = 2
  # replicas_per_node_group = 1

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                 = var.auth_token
}

variable "cluster_id" { type = string }
variable "subnet_ids" { type = list(string) }
variable "node_type" { default = "cache.t3.medium" }
variable "num_cache_nodes" { default = 2 }
variable "auth_token" { type = string; sensitive = true }
