resource "aws_db_subnet_group" "default" {
  name       = "${var.cluster_identifier}-subnet-group"
  subnet_ids = var.subnet_ids
}

resource "aws_rds_cluster" "postgresql" {
  cluster_identifier      = var.cluster_identifier
  engine                  = "aurora-postgresql"
  engine_version          = "14.5"
  availability_zones      = var.availability_zones
  database_name           = var.db_name
  master_username         = var.master_username
  master_password         = var.master_password
  backup_retention_period = 7
  preferred_backup_window = "07:00-09:00"
  storage_encrypted       = true
  db_subnet_group_name    = aws_db_subnet_group.default.name
  
  # Global Cluster (DR) support
  # global_cluster_identifier = var.global_cluster_identifier 

  tags = {
    Name = "${var.cluster_identifier}"
  }
}

resource "aws_rds_cluster_instance" "postgresql_instances" {
  count              = var.instance_count
  identifier         = "${var.cluster_identifier}-${count.index}"
  cluster_identifier = aws_rds_cluster.postgresql.id
  instance_class     = var.instance_class
  engine             = aws_rds_cluster.postgresql.engine
  engine_version     = aws_rds_cluster.postgresql.engine_version
  
  publicly_accessible = false
}
