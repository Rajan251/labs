# ============================================================================
# Terraform Outputs
# ============================================================================
# These values are displayed after 'terraform apply' and can be queried
# with 'terraform output <output_name>'
# ============================================================================

# ============================================================================
# VPC Outputs
# ============================================================================

output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "vpc_cidr" {
  description = "CIDR block of the VPC"
  value       = aws_vpc.main.cidr_block
}

output "subnet_ids" {
  description = "IDs of the public subnets"
  value       = aws_subnet.public[*].id
}

# ============================================================================
# Security Group Outputs
# ============================================================================

output "web_security_group_id" {
  description = "ID of the web server security group"
  value       = aws_security_group.web.id
}

output "app_security_group_id" {
  description = "ID of the app server security group"
  value       = aws_security_group.app.id
}

# ============================================================================
# EC2 Instance Outputs - Web Servers
# ============================================================================

output "web_instance_ids" {
  description = "IDs of web server instances"
  value       = aws_instance.web[*].id
}

output "web_instance_public_ips" {
  description = "Public IP addresses of web servers"
  value       = aws_instance.web[*].public_ip
}

output "web_instance_private_ips" {
  description = "Private IP addresses of web servers"
  value       = aws_instance.web[*].private_ip
}

output "web_instance_public_dns" {
  description = "Public DNS names of web servers"
  value       = aws_instance.web[*].public_dns
}

# ============================================================================
# EC2 Instance Outputs - App Servers
# ============================================================================

output "app_instance_ids" {
  description = "IDs of app server instances"
  value       = aws_instance.app[*].id
}

output "app_instance_public_ips" {
  description = "Public IP addresses of app servers"
  value       = aws_instance.app[*].public_ip
}

output "app_instance_private_ips" {
  description = "Private IP addresses of app servers"
  value       = aws_instance.app[*].private_ip
}

# ============================================================================
# Ansible Inventory Outputs
# ============================================================================

output "ansible_inventory_path" {
  description = "Path to generated Ansible inventory file"
  value       = local_file.ansible_inventory.filename
}

# ============================================================================
# Connection Information
# ============================================================================

output "ssh_connection_commands" {
  description = "SSH commands to connect to instances"
  value = {
    for idx, instance in aws_instance.web :
    instance.tags.Name => "ssh -i ${var.ssh_private_key_path} ${var.ansible_user}@${instance.public_ip}"
  }
}

# ============================================================================
# Summary Output
# ============================================================================

output "deployment_summary" {
  description = "Summary of deployed infrastructure"
  value = {
    vpc_id              = aws_vpc.main.id
    region              = var.aws_region
    environment         = var.environment
    web_servers_count   = var.web_instance_count
    app_servers_count   = var.app_instance_count
    inventory_generated = local_file.ansible_inventory.filename
  }
}

# ============================================================================
# Quick Access Commands
# ============================================================================

output "next_steps" {
  description = "Next steps to configure servers with Ansible"
  value = <<-EOT
  
  ✅ Infrastructure provisioned successfully!
  
  Next steps:
  
  1. Verify inventory file:
     cat ${local_file.ansible_inventory.filename}
  
  2. Test SSH connectivity:
     ssh -i ${var.ssh_private_key_path} ${var.ansible_user}@${try(aws_instance.web[0].public_ip, "N/A")}
  
  3. Run Ansible playbook:
     cd ../ansible
     ansible-playbook -i inventory/hosts.ini setup.yml
  
  4. Or use automation script:
     cd ..
     ./scripts/deploy.sh
  
  Web Server IPs: ${jsonencode(aws_instance.web[*].public_ip)}
  App Server IPs: ${jsonencode(aws_instance.app[*].public_ip)}
  
  EOT
}
