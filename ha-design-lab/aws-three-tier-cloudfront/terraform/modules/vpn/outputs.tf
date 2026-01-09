output "vpn_instance_id" {
  description = "ID of the VPN server instance"
  value       = aws_instance.vpn.id
}

output "vpn_private_ip" {
  description = "Private IP of the VPN server"
  value       = aws_instance.vpn.private_ip
}

output "vpn_public_ip" {
  description = "Public IP of the VPN server"
  value       = aws_eip.vpn.public_ip
}

output "vpn_eip_id" {
  description = "ID of the Elastic IP"
  value       = aws_eip.vpn.id
}
