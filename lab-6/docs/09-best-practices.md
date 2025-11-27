# Best Practices & Advanced Tips

## Terraform Best Practices

### 1. Use Remote State

```hcl
terraform {
  backend "s3" {
    bucket         = "my-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

### 2. Use Modules

```hcl
module "vpc" {
  source = "./modules/vpc"
  
  vpc_cidr     = var.vpc_cidr
  project_name = var.project_name
}

module "ec2" {
  source = "./modules/ec2"
  
  vpc_id       = module.vpc.vpc_id
  subnet_ids   = module.vpc.subnet_ids
}
```

### 3. Use Workspaces for Environments

```bash
terraform workspace new dev
terraform workspace new staging
terraform workspace new prod

terraform workspace select dev
terraform apply -var-file=dev.tfvars
```

### 4. Pin Provider Versions

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0.0"  # Pin to specific version
    }
  }
}
```

---

## Ansible Best Practices

### 1. Use Ansible Vault for Secrets

```bash
# Create encrypted file
ansible-vault create group_vars/all/vault.yml

# Content:
vault_db_password: "super-secret"
vault_api_key: "api-key-here"

# Use in playbooks
db_password: "{{ vault_db_password }}"
```

### 2. Use Roles for Reusability

```yaml
# Good structure
roles/
├── common/
├── nginx/
├── docker/
└── app-deploy/

# Use in playbook
- hosts: webservers
  roles:
    - common
    - nginx
    - app-deploy
```

### 3. Use Tags for Selective Execution

```yaml
- name: Install Nginx
  apt:
    name: nginx
  tags: [nginx, webserver, packages]

# Run only nginx tasks
ansible-playbook setup.yml --tags nginx
```

### 4. Implement Idempotency

```yaml
# Bad - always changes
- name: Add line to file
  shell: echo "text" >> /etc/file

# Good - idempotent
- name: Add line to file
  lineinfile:
    path: /etc/file
    line: "text"
    state: present
```

---

## Security Best Practices

### 1. Never Commit Secrets

```gitignore
# .gitignore
*.tfvars
!terraform.tfvars.example
*.pem
*.key
vault.yml
```

### 2. Use IAM Roles for EC2

```hcl
resource "aws_iam_role" "ec2_role" {
  name = "ec2-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })
}

resource "aws_instance" "web" {
  iam_instance_profile = aws_iam_instance_profile.ec2_profile.name
}
```

### 3. Implement Least Privilege

```hcl
resource "aws_security_group" "web" {
  # Only allow SSH from specific IP
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["203.0.113.0/32"]  # Your IP only
  }
}
```

---

## Performance Optimization

### 1. Use Pipelining (Ansible)

```ini
[ssh_connection]
pipelining = True
```

### 2. Increase Parallelism (Terraform)

```bash
terraform apply -parallelism=20
```

### 3. Cache Facts (Ansible)

```ini
[defaults]
gathering = smart
fact_caching = jsonfile
fact_caching_timeout = 3600
```

---

## Monitoring and Logging

### 1. Enable CloudWatch

```hcl
resource "aws_cloudwatch_log_group" "app_logs" {
  name              = "/aws/ec2/${var.project_name}"
  retention_in_days = 30
}
```

### 2. Ansible Logging

```ini
[defaults]
log_path = ./ansible.log
```

---

## Cost Optimization

### 1. Use Spot Instances for Dev

```hcl
resource "aws_instance" "dev" {
  instance_market_options {
    market_type = "spot"
  }
}
```

### 2. Auto-Stop Dev Instances

```bash
# Cron job to stop instances at night
0 20 * * * aws ec2 stop-instances --instance-ids $(terraform output -raw dev_instance_ids)
```

---

[← Previous: Troubleshooting](08-troubleshooting.md) | [Back to README](../README.md)
