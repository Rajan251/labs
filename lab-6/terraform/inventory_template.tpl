# ============================================================================
# Ansible Inventory Template
# ============================================================================
# This template is used by Terraform to generate the Ansible inventory file.
# It uses Terraform's templatefile() function to populate dynamic values.
# ============================================================================

# ============================================================================
# Web Servers Group
# ============================================================================
[webservers]
%{ for instance in webservers ~}
${instance.tags.Name} ansible_host=${instance.public_ip} ansible_user=${ansible_user} ansible_ssh_private_key_file=${ssh_key_path}
%{ endfor ~}

# ============================================================================
# Application Servers Group
# ============================================================================
%{ if length(appservers) > 0 ~}
[appservers]
%{ for instance in appservers ~}
${instance.tags.Name} ansible_host=${instance.public_ip} ansible_user=${ansible_user} ansible_ssh_private_key_file=${ssh_key_path}
%{ endfor ~}
%{ endif ~}

# ============================================================================
# Group Variables for All Hosts
# ============================================================================
[all:vars]
ansible_python_interpreter=/usr/bin/python3
ansible_ssh_common_args='-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'

# ============================================================================
# Group of Groups (Optional)
# ============================================================================
%{ if length(appservers) > 0 ~}
[production:children]
webservers
appservers
%{ else ~}
[production:children]
webservers
%{ endif ~}
