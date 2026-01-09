output "mongodb_primary_id" {
  description = "ID of MongoDB primary instance"
  value       = aws_instance.mongodb_primary.id
}

output "mongodb_primary_private_ip" {
  description = "Private IP of MongoDB primary"
  value       = aws_instance.mongodb_primary.private_ip
}

output "mongodb_secondary_id" {
  description = "ID of MongoDB secondary instance"
  value       = aws_instance.mongodb_secondary.id
}

output "mongodb_secondary_private_ip" {
  description = "Private IP of MongoDB secondary"
  value       = aws_instance.mongodb_secondary.private_ip
}
