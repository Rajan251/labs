# Dynamic Inventory Integration

## Table of Contents
- [Overview](#overview)
- [Static vs Dynamic Inventory](#static-vs-dynamic-inventory)
- [Method 1: Terraform-Generated Inventory](#method-1-terraform-generated-inventory)
- [Method 2: AWS EC2 Plugin](#method-2-aws-ec2-plugin)
- [Method 3: Custom Script](#method-3-custom-script)
- [Tag-Based Grouping](#tag-based-grouping)
- [Best Practices](#best-practices)

---

## Overview

Dynamic inventory allows Ansible to automatically discover hosts from cloud providers, eliminating manual inventory management.

**Benefits:**
- ✅ Always up-to-date with current infrastructure
- ✅ Automatic host discovery
- ✅ Tag-based grouping
- ✅ No manual updates needed
- ✅ Works with auto-scaling

---

## Static vs Dynamic Inventory

### Static Inventory

**File: `inventory/hosts.ini`**
```ini
[webservers]
web-1 ansible_host=54.123.45.67
web-2 ansible_host=54.123.45.68

[appservers]
app-1 ansible_host=54.123.45.69
```

**Pros:**
- Simple and readable
- Fast (no API calls)
- Works offline

**Cons:**
- Manual updates required
- Becomes stale quickly
- Doesn't work with auto-scaling

### Dynamic Inventory

**File: `inventory/aws_ec2.yml`**
```yaml
plugin: aws_ec2
regions:
  - us-east-1
filters:
  instance-state-name: running
```

**Pros:**
- Always current
- Automatic discovery
- Works with auto-scaling
- Tag-based grouping

**Cons:**
- Requires API access
- Slower (API calls)
- Requires internet connection

---

## Method 1: Terraform-Generated Inventory

### How It Works

1. **Terraform creates template** (`inventory_template.tpl`)
2. **Terraform populates template** with instance data
3. **Terraform writes file** (`inventory/hosts.ini`)
4. **Ansible reads file** as static inventory

### Implementation

**Template File:**
```hcl
[webservers]
%{ for instance in webservers ~}
${instance.tags.Name} ansible_host=${instance.public_ip}
%{ endfor ~}
```

**Terraform Resource:**
```hcl
resource "local_file" "ansible_inventory" {
  content = templatefile("inventory_template.tpl", {
    webservers = aws_instance.web
  })
  filename = "../ansible/inventory/hosts.ini"
}
```

**Usage:**
```bash
terraform apply  # Generates inventory
ansible-playbook -i inventory/hosts.ini setup.yml
```

---

## Method 2: AWS EC2 Plugin

### Configuration

**File: `inventory/aws_ec2.yml`**
```yaml
plugin: aws_ec2

# Regions to query
regions:
  - us-east-1

# Filters
filters:
  instance-state-name: running
  tag:Environment: production

# Group by tags
keyed_groups:
  - key: tags.Role
    prefix: role
  - key: tags.Environment
    prefix: env

# Hostname
hostnames:
  - tag:Name

# Compose variables
compose:
  ansible_host: public_ip_address
```

### Usage

```bash
# Test inventory
ansible-inventory -i inventory/aws_ec2.yml --list

# Use with playbook
ansible-playbook -i inventory/aws_ec2.yml setup.yml
```

### Example Output

```json
{
  "role_webserver": {
    "hosts": [
      "web-1",
      "web-2"
    ]
  },
  "env_production": {
    "hosts": [
      "web-1",
      "web-2",
      "app-1"
    ]
  }
}
```

---

## Method 3: Custom Script

### Python Script

**File: `inventory/ec2.py`**
```python
#!/usr/bin/env python3
import json
import boto3

def get_inventory():
    ec2 = boto3.client('ec2', region_name='us-east-1')
    
    response = ec2.describe_instances(
        Filters=[
            {'Name': 'instance-state-name', 'Values': ['running']},
            {'Name': 'tag:ManagedBy', 'Values': ['Terraform']}
        ]
    )
    
    inventory = {
        '_meta': {'hostvars': {}},
        'all': {'hosts': []},
        'webservers': {'hosts': []},
        'appservers': {'hosts': []}
    }
    
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            name = next((tag['Value'] for tag in instance.get('Tags', []) 
                        if tag['Key'] == 'Name'), instance['InstanceId'])
            role = next((tag['Value'] for tag in instance.get('Tags', []) 
                        if tag['Key'] == 'Role'), 'unknown')
            
            inventory['all']['hosts'].append(name)
            
            if role == 'webserver':
                inventory['webservers']['hosts'].append(name)
            elif role == 'appserver':
                inventory['appservers']['hosts'].append(name)
            
            inventory['_meta']['hostvars'][name] = {
                'ansible_host': instance.get('PublicIpAddress', instance.get('PrivateIpAddress')),
                'ansible_user': 'ubuntu',
                'ec2_instance_id': instance['InstanceId'],
                'ec2_instance_type': instance['InstanceType']
            }
    
    return inventory

if __name__ == '__main__':
    print(json.dumps(get_inventory(), indent=2))
```

### Usage

```bash
# Make executable
chmod +x inventory/ec2.py

# Test
./inventory/ec2.py --list

# Use with Ansible
ansible-playbook -i inventory/ec2.py setup.yml
```

---

## Tag-Based Grouping

### Terraform Tags

```hcl
resource "aws_instance" "web" {
  # ... other config
  
  tags = {
    Name        = "web-${count.index + 1}"
    Role        = "webserver"
    Environment = "production"
    Tier        = "frontend"
    Application = "myapp"
  }
}
```

### Dynamic Grouping

**AWS EC2 Plugin:**
```yaml
keyed_groups:
  # Group by Role: role_webserver, role_appserver
  - key: tags.Role
    prefix: role
  
  # Group by Environment: env_production, env_staging
  - key: tags.Environment
    prefix: env
  
  # Group by Tier: tier_frontend, tier_backend
  - key: tags.Tier
    prefix: tier
```

### Using Groups in Playbooks

```yaml
---
- name: Configure frontend servers
  hosts: tier_frontend
  roles:
    - nginx

- name: Configure backend servers
  hosts: tier_backend
  roles:
    - docker
    - app-deploy

- name: Configure all production servers
  hosts: env_production
  roles:
    - monitoring
```

---

## Best Practices

### 1. Use Consistent Tagging

```hcl
locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_instance" "web" {
  tags = merge(local.common_tags, {
    Name = "web-${count.index + 1}"
    Role = "webserver"
  })
}
```

### 2. Cache Dynamic Inventory

```yaml
# In aws_ec2.yml
cache: yes
cache_plugin: jsonfile
cache_timeout: 300
cache_connection: /tmp/ansible_inventory_cache
```

### 3. Filter Appropriately

```yaml
filters:
  # Only running instances
  instance-state-name: running
  
  # Only Terraform-managed
  tag:ManagedBy: Terraform
  
  # Specific environment
  tag:Environment: production
```

### 4. Use Multiple Inventory Sources

```bash
# Ansible can use multiple inventories
ansible-playbook -i inventory/hosts.ini -i inventory/aws_ec2.yml setup.yml
```

### 5. Verify Inventory

```bash
# List all hosts
ansible-inventory -i inventory/aws_ec2.yml --list

# Graph view
ansible-inventory -i inventory/aws_ec2.yml --graph

# Specific host details
ansible-inventory -i inventory/aws_ec2.yml --host web-1
```

---

## Troubleshooting

### Issue: No hosts found

**Check:**
```bash
# Verify AWS credentials
aws ec2 describe-instances --region us-east-1

# Test inventory plugin
ansible-inventory -i inventory/aws_ec2.yml --list

# Check filters
ansible-inventory -i inventory/aws_ec2.yml --list | jq '.all.hosts'
```

### Issue: Wrong IP addresses

**Solution:** Adjust compose section
```yaml
compose:
  # Use public IP for external access
  ansible_host: public_ip_address
  
  # Or use private IP for VPN/internal access
  # ansible_host: private_ip_address
```

### Issue: Permission denied

**Solution:** Check IAM permissions
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeTags"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## Summary

**Choose the right method:**

- **Terraform-Generated**: Best for simple setups, fast execution
- **AWS EC2 Plugin**: Best for auto-scaling, complex filtering
- **Custom Script**: Best for custom logic, multiple providers

**Recommended Approach:**
Use Terraform-generated inventory for initial deployment, then switch to AWS EC2 plugin for ongoing management.

---

[← Previous: Integration Workflow](05-integration-workflow.md) | [Next: Use Cases →](07-use-cases.md)
