resource "aws_msk_cluster" "kafka" {
  cluster_name           = "${var.environment}-kafka"
  kafka_version          = "3.2.0"
  number_of_broker_nodes = 3

  broker_node_group_info {
    instance_type   = "kafka.t3.small"
    client_subnets  = var.subnets
    security_groups = var.security_groups
    storage_info {
      ebs_storage_info {
        volume_size = 100
      }
    }
  }

  encryption_info {
    encryption_in_transit {
      client_broker = "TLS"
      in_cluster    = true
    }
  }

  configuration_info {
    arn      = aws_msk_configuration.config.arn
    revision = aws_msk_configuration.config.latest_revision
  }

  tags = { Name = "${var.environment}-kafka" }
}

resource "aws_msk_configuration" "config" {
  kafka_versions = ["3.2.0"]
  name           = "${var.environment}-kafka-config"

  server_properties = <<PROPERTIES
auto.create.topics.enable = true
delete.topic.enable = true
PROPERTIES
}

variable "environment" { type = string }
variable "subnets" { type = list(string) }
variable "security_groups" { type = list(string) }

output "bootstrap_brokers" {
  value = aws_msk_cluster.kafka.bootstrap_brokers_tls
}
