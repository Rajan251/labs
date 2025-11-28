# Dynamic Inventory

This document explains how to use dynamic inventory in Ansible, including static inventory, Terraform-generated inventory, and cloud provider dynamic plugins.

## Table of Contents

1. [Static Inventory](#static-inventory)
2. [Dynamic Inventory Concepts](#dynamic-inventory-concepts)
3. [Terraform-Generated Inventory](#terraform-generated-inventory)
4. [AWS Dynamic Inventory](#aws-dynamic-inventory)
5. [GCP Dynamic Inventory](#gcp-dynamic-inventory)
6. [Azure Dynamic Inventory](#azure-dynamic-inventory)
7. [Custom Dynamic Inventory Scripts](#custom-dynamic-inventory-scripts)
8. [Best Practices](#best-practices)

---

## Static Inventory

### INI Format

```ini
# inventories/production/hosts

# Individual hosts
web01.example.com ansible_host=192.168.1.10
web02.example.com ansible_host=192.168.1.11

# Groups
[webservers]
web01.example.com
web02.example.com
web03.example.com

[databases]
db01.example.com ansible_host=192.168.1.20
db02.example.com ansible_host=192.168.1.21

[loadbalancers]
lb01.example.com ansible_host=192.168.1.30

# Group of groups
[production:children]
webservers
databases
loadbalancers

# Group variables
[webservers:vars]
nginx_port=80
app_env=production

[databases:vars]
db_port=5432
db_max_connections=200

# All hosts variables
[all:vars]
ansible_user=ansible
ansible_ssh_private_key_file=~/.ssh/ansible_key
ansible_python_interpreter=/usr/bin/python3
```

### YAML Format

```yaml
# inventories/production/hosts.yml
all:
  vars:
    ansible_user: ansible
    ansible_ssh_private_key_file: ~/.ssh/ansible_key
    ansible_python_interpreter: /usr/bin/python3
  
  children:
    webservers:
      hosts:
        web01.example.com:
          ansible_host: 192.168.1.10
        web02.example.com:
          ansible_host: 192.168.1.11
        web03.example.com:
          ansible_host: 192.168.1.12
      vars:
        nginx_port: 80
        app_env: production
    
    databases:
      hosts:
        db01.example.com:
          ansible_host: 192.168.1.20
          db_role: primary
        db02.example.com:
          ansible_host: 192.168.1.21
          db_role: replica
      vars:
        db_port: 5432
        db_max_connections: 200
    
    loadbalancers:
      hosts:
        lb01.example.com:
          ansible_host: 192.168.1.30
    
    production:
      children:
        webservers:
        databases:
        loadbalancers:
```

---

## Dynamic Inventory Concepts

### What is Dynamic Inventory?

Dynamic inventory allows Ansible to query external sources (cloud providers, CMDBs, etc.) to get the list of hosts and their properties in real-time.

### Benefits

- **Always up-to-date**: Reflects current infrastructure state
- **No manual updates**: Automatically discovers new/removed hosts
- **Metadata-rich**: Includes tags, properties from cloud providers
- **Scalable**: Works with large, dynamic environments

### How It Works

```
┌─────────────┐
│   Ansible   │
└──────┬──────┘
       │
       │ 1. Request inventory
       ▼
┌─────────────────────┐
│ Dynamic Inventory   │
│ Script/Plugin       │
└──────┬──────────────┘
       │
       │ 2. Query API
       ▼
┌─────────────────────┐
│ Cloud Provider API  │
│ (AWS/GCP/Azure)     │
└──────┬──────────────┘
       │
       │ 3. Return JSON
       ▼
┌─────────────────────┐
│ Ansible processes   │
│ inventory data      │
└─────────────────────┘
```

---

## Terraform-Generated Inventory

### Terraform Output

```hcl
# terraform/outputs.tf
output "ansible_inventory" {
  value = {
    webservers = {
      hosts = {
        for instance in aws_instance.web :
        instance.tags.Name => {
          ansible_host = instance.public_ip
          private_ip   = instance.private_ip
          instance_id  = instance.id
          instance_type = instance.instance_type
        }
      }
    }
    
    databases = {
      hosts = {
        for instance in aws_instance.db :
        instance.tags.Name => {
          ansible_host = instance.private_ip
          instance_id  = instance.id
        }
      }
    }
    
    all = {
      vars = {
        ansible_user = "ubuntu"
        ansible_ssh_private_key_file = "~/.ssh/terraform-key.pem"
      }
    }
  }
}

# Generate inventory file
resource "local_file" "ansible_inventory" {
  content = templatefile("${path.module}/templates/inventory.tpl", {
    webservers = aws_instance.web
    databases  = aws_instance.db
  })
  filename = "${path.module}/../ansible/inventories/terraform/hosts.yml"
}
```

### Inventory Template

```jinja2
# terraform/templates/inventory.tpl
all:
  vars:
    ansible_user: ubuntu
    ansible_ssh_private_key_file: ~/.ssh/terraform-key.pem
  
  children:
    webservers:
      hosts:
%{ for instance in webservers ~}
        ${instance.tags.Name}:
          ansible_host: ${instance.public_ip}
          private_ip: ${instance.private_ip}
          instance_id: ${instance.id}
%{ endfor ~}
    
    databases:
      hosts:
%{ for instance in databases ~}
        ${instance.tags.Name}:
          ansible_host: ${instance.private_ip}
          instance_id: ${instance.id}
%{ endfor ~}
```

### Generate Inventory

```bash
# After terraform apply
terraform output -json ansible_inventory > ../ansible/inventories/terraform/inventory.json

# Or use the generated YAML file
cd ../ansible
ansible-playbook -i inventories/terraform/hosts.yml playbooks/site.yml
```

---

## AWS Dynamic Inventory

### Using AWS EC2 Plugin

#### Install Requirements

```bash
pip install boto3 botocore
```

#### Configure AWS Credentials

```bash
# ~/.aws/credentials
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY

# Or use environment variables
export AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY
export AWS_SECRET_ACCESS_KEY=YOUR_SECRET_KEY
export AWS_DEFAULT_REGION=us-east-1
```

#### Create Inventory Plugin Configuration

```yaml
# inventories/aws_ec2.yml
plugin: amazon.aws.aws_ec2

regions:
  - us-east-1
  - us-west-2

filters:
  # Only running instances
  instance-state-name: running
  
  # Filter by tag
  tag:Environment: production

keyed_groups:
  # Group by instance type
  - key: instance_type
    prefix: instance_type
  
  # Group by availability zone
  - key: placement.availability_zone
    prefix: az
  
  # Group by tag
  - key: tags.Role
    prefix: role
  
  # Group by VPC
  - key: vpc_id
    prefix: vpc

hostnames:
  # Use tag Name as hostname
  - tag:Name
  - dns-name
  - private-ip-address

compose:
  # Set ansible_host to public IP if available, else private IP
  ansible_host: public_ip_address | default(private_ip_address)
  
  # Custom variables from tags
  environment: tags.Environment
  application: tags.Application
  
  # Instance metadata
  instance_id: instance_id
  instance_type: instance_type
  availability_zone: placement.availability_zone
```

#### Use AWS Dynamic Inventory

```bash
# List inventory
ansible-inventory -i inventories/aws_ec2.yml --list

# Graph inventory
ansible-inventory -i inventories/aws_ec2.yml --graph

# Run playbook
ansible-playbook -i inventories/aws_ec2.yml playbooks/site.yml

# Target specific group
ansible-playbook -i inventories/aws_ec2.yml playbooks/site.yml --limit role_webserver
```

### Advanced AWS Configuration

```yaml
# inventories/aws_ec2_advanced.yml
plugin: amazon.aws.aws_ec2

regions:
  - us-east-1
  - us-west-2
  - eu-west-1

# Use IAM role instead of credentials
iam_role_arn: arn:aws:iam::123456789012:role/AnsibleInventoryRole

filters:
  instance-state-name: running
  tag:Managed: ansible

# Cache inventory for 5 minutes
cache: yes
cache_plugin: jsonfile
cache_timeout: 300
cache_connection: /tmp/ansible_inventory_cache

keyed_groups:
  # Group by multiple tags
  - key: tags.Environment
    prefix: env
  - key: tags.Application
    prefix: app
  - key: tags.Role
    prefix: role
  - key: tags.Team
    prefix: team
  
  # Group by instance attributes
  - key: instance_type
    prefix: type
  - key: placement.availability_zone
    prefix: az
  - key: vpc_id
    prefix: vpc
  - key: subnet_id
    prefix: subnet

# Construct groups based on conditions
groups:
  # Production webservers
  production_web: tags.Environment == 'production' and tags.Role == 'webserver'
  
  # Development databases
  dev_db: tags.Environment == 'development' and tags.Role == 'database'
  
  # Large instances
  large_instances: instance_type.startswith('m5.large') or instance_type.startswith('c5.large')

compose:
  ansible_host: public_ip_address | default(private_ip_address)
  ansible_user: tags.SSHUser | default('ubuntu')
  
  # Custom facts
  ec2_region: placement.region
  ec2_az: placement.availability_zone
  ec2_instance_id: instance_id
  ec2_instance_type: instance_type
  ec2_vpc_id: vpc_id
  ec2_subnet_id: subnet_id
  
  # Application-specific variables
  app_environment: tags.Environment
  app_name: tags.Application
  app_version: tags.Version | default('latest')
```

---

## GCP Dynamic Inventory

### Using GCP Compute Plugin

#### Install Requirements

```bash
pip install google-auth requests
```

#### Create Service Account

```bash
# Create service account
gcloud iam service-accounts create ansible-inventory \
  --display-name="Ansible Inventory"

# Grant permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:ansible-inventory@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/compute.viewer"

# Create and download key
gcloud iam service-accounts keys create ~/ansible-gcp-key.json \
  --iam-account=ansible-inventory@PROJECT_ID.iam.gserviceaccount.com
```

#### Configure GCP Inventory

```yaml
# inventories/gcp_compute.yml
plugin: google.cloud.gcp_compute

projects:
  - my-project-id

auth_kind: serviceaccount
service_account_file: ~/ansible-gcp-key.json

filters:
  - status = RUNNING
  - labels.environment = production

keyed_groups:
  # Group by zone
  - key: zone
    prefix: zone
  
  # Group by machine type
  - key: machineType
    prefix: machine_type
  
  # Group by labels
  - key: labels.role
    prefix: role
  - key: labels.environment
    prefix: env

hostnames:
  - name
  - public_ip
  - private_ip

compose:
  ansible_host: networkInterfaces[0].accessConfigs[0].natIP | default(networkInterfaces[0].networkIP)
  ansible_user: labels.ssh_user | default('ansible')
  
  # Custom variables
  gcp_zone: zone
  gcp_machine_type: machineType
  gcp_instance_id: id
  environment: labels.environment
  application: labels.application
```

---

## Azure Dynamic Inventory

### Using Azure RM Plugin

#### Install Requirements

```bash
pip install azure-cli azure-identity
```

#### Authenticate with Azure

```bash
# Login to Azure
az login

# Set subscription
az account set --subscription "SUBSCRIPTION_ID"
```

#### Configure Azure Inventory

```yaml
# inventories/azure_rm.yml
plugin: azure.azcollection.azure_rm

auth_source: auto

include_vm_resource_groups:
  - production-rg
  - staging-rg

conditional_groups:
  # Group by resource group
  production: resource_group == "production-rg"
  staging: resource_group == "staging-rg"
  
  # Group by tags
  webservers: tags.role == "webserver"
  databases: tags.role == "database"

keyed_groups:
  # Group by location
  - key: location
    prefix: location
  
  # Group by tags
  - key: tags.environment
    prefix: env
  - key: tags.role
    prefix: role

hostnames:
  - name
  - public_ipv4_addresses
  - private_ipv4_addresses

compose:
  ansible_host: public_ipv4_addresses[0] | default(private_ipv4_addresses[0])
  ansible_user: tags.ssh_user | default('azureuser')
  
  # Custom variables
  azure_location: location
  azure_vm_size: vm_size
  azure_resource_group: resource_group
  environment: tags.environment
```

---

## Custom Dynamic Inventory Scripts

### Python Script Example

```python
#!/usr/bin/env python3
# inventories/custom_inventory.py

import json
import argparse
import requests

def get_inventory():
    """Fetch inventory from custom API"""
    
    # Query your CMDB/API
    response = requests.get('https://api.example.com/inventory')
    data = response.json()
    
    inventory = {
        '_meta': {
            'hostvars': {}
        },
        'all': {
            'children': ['webservers', 'databases']
        },
        'webservers': {
            'hosts': [],
            'vars': {
                'nginx_port': 80
            }
        },
        'databases': {
            'hosts': [],
            'vars': {
                'db_port': 5432
            }
        }
    }
    
    # Process API data
    for server in data['servers']:
        if server['role'] == 'web':
            inventory['webservers']['hosts'].append(server['hostname'])
        elif server['role'] == 'db':
            inventory['databases']['hosts'].append(server['hostname'])
        
        # Add host variables
        inventory['_meta']['hostvars'][server['hostname']] = {
            'ansible_host': server['ip_address'],
            'ansible_user': server.get('ssh_user', 'ansible'),
            'environment': server.get('environment', 'production')
        }
    
    return inventory

def get_host(hostname):
    """Get specific host variables"""
    inventory = get_inventory()
    return inventory['_meta']['hostvars'].get(hostname, {})

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--list', action='store_true')
    parser.add_argument('--host', action='store')
    args = parser.parse_args()
    
    if args.list:
        inventory = get_inventory()
        print(json.dumps(inventory, indent=2))
    elif args.host:
        hostvars = get_host(args.host)
        print(json.dumps(hostvars, indent=2))
    else:
        print(json.dumps({}))

if __name__ == '__main__':
    main()
```

### Make Script Executable

```bash
chmod +x inventories/custom_inventory.py

# Test inventory
./inventories/custom_inventory.py --list

# Use with ansible
ansible-playbook -i inventories/custom_inventory.py playbooks/site.yml
```

---

## Best Practices

### 1. Use Inventory Plugins Over Scripts

**Modern Approach:**
```yaml
# Use inventory plugins (preferred)
plugin: amazon.aws.aws_ec2
```

**Legacy Approach:**
```bash
# Old dynamic inventory scripts (deprecated)
./ec2.py --list
```

### 2. Cache Inventory for Performance

```yaml
# Enable caching
cache: yes
cache_plugin: jsonfile
cache_timeout: 300
cache_connection: /tmp/ansible_inventory_cache
```

### 3. Use Filters to Limit Scope

```yaml
filters:
  instance-state-name: running
  tag:Environment: production
  tag:Managed: ansible
```

### 4. Organize with Groups

```yaml
keyed_groups:
  - key: tags.Environment
    prefix: env
  - key: tags.Role
    prefix: role
  - key: tags.Application
    prefix: app
```

### 5. Test Inventory Before Use

```bash
# List all hosts
ansible-inventory -i inventories/aws_ec2.yml --list

# Show inventory graph
ansible-inventory -i inventories/aws_ec2.yml --graph

# Test connectivity
ansible all -i inventories/aws_ec2.yml -m ping
```

### 6. Combine Multiple Sources

```yaml
# ansible.cfg
[defaults]
inventory = inventories/

# Directory structure
inventories/
├── static_hosts.yml
├── aws_ec2.yml
├── gcp_compute.yml
└── azure_rm.yml
```

### 7. Use Environment-Specific Inventories

```
inventories/
├── production/
│   ├── aws_ec2.yml
│   └── group_vars/
├── staging/
│   ├── aws_ec2.yml
│   └── group_vars/
└── development/
    ├── static_hosts.yml
    └── group_vars/
```

---

## Quick Reference

| Inventory Type | Configuration File | Command |
|---------------|-------------------|---------|
| Static INI | `hosts` | `ansible-playbook -i hosts playbook.yml` |
| Static YAML | `hosts.yml` | `ansible-playbook -i hosts.yml playbook.yml` |
| AWS EC2 | `aws_ec2.yml` | `ansible-playbook -i aws_ec2.yml playbook.yml` |
| GCP Compute | `gcp_compute.yml` | `ansible-playbook -i gcp_compute.yml playbook.yml` |
| Azure RM | `azure_rm.yml` | `ansible-playbook -i azure_rm.yml playbook.yml` |
| Custom Script | `script.py` | `ansible-playbook -i script.py playbook.yml` |

---

**Next**: [Best Practices →](05-best-practices.md)
