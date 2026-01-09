output "vpn_security_group_id" {
  description = "ID of VPN security group"
  value       = aws_security_group.vpn.id
}

output "alb_security_group_id" {
  description = "ID of ALB security group"
  value       = aws_security_group.alb.id
}

output "app_security_group_id" {
  description = "ID of application server security group"
  value       = aws_security_group.app.id
}

output "db_security_group_id" {
  description = "ID of database server security group"
  value       = aws_security_group.db.id
}

output "public_nacl_id" {
  description = "ID of public subnet NACL"
  value       = aws_network_acl.public.id
}

output "private_app_nacl_id" {
  description = "ID of private application subnet NACL"
  value       = aws_network_acl.private_app.id
}

output "private_db_nacl_id" {
  description = "ID of private database subnet NACL"
  value       = aws_network_acl.private_db.id
}
