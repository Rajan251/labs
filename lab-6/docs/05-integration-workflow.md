# Integration Workflow & Automation

## Table of Contents
- [Overview](#overview)
- [Automation Methods](#automation-methods)
- [Method 1: Bash Script](#method-1-bash-script)
- [Method 2: Makefile](#method-2-makefile)
- [Method 3: Terraform Provisioner](#method-3-terraform-provisioner)
- [CI/CD Integration](#cicd-integration)
- [Best Practices](#best-practices)

---

## Overview

This guide explains different methods to automate the Terraform → Ansible workflow, ensuring seamless infrastructure provisioning and configuration.

**Workflow Steps:**
1. Terraform provisions infrastructure
2. Terraform generates Ansible inventory
3. Wait for instances to be ready
4. Ansible configures servers
5. Verification and testing

---

## Automation Methods

### Comparison

| Method | Pros | Cons | Best For |
|--------|------|------|----------|
| **Bash Script** | Full control, error handling, colored output | Requires bash, platform-specific | Local development, manual deployments |
| **Makefile** | Simple commands, IDE integration | Less error handling | Quick operations, developer workflow |
| **Terraform Provisioner** | Integrated with Terraform | Runs on every apply, harder to debug | Automated pipelines |
| **CI/CD Pipeline** | Fully automated, auditable | Requires CI/CD setup | Production deployments |

---

## Method 1: Bash Script

### Usage

```bash
# Full deployment
./scripts/deploy.sh

# Cleanup
./scripts/destroy.sh
```

### Script Features

✅ **Prerequisites Check**: Verifies terraform and ansible are installed  
✅ **Colored Output**: Easy-to-read status messages  
✅ **Error Handling**: Exits on first error  
✅ **SSH Wait Logic**: Waits for instances to be ready  
✅ **Verification**: Tests web servers after deployment  

### Example Output

```
============================================================================
Terraform + Ansible Deployment
============================================================================

============================================================================
Checking Prerequisites
============================================================================
✅ All prerequisites met

============================================================================
Provisioning Infrastructure with Terraform
============================================================================
ℹ️  Initializing Terraform...
ℹ️  Validating Terraform configuration...
ℹ️  Planning infrastructure changes...
ℹ️  Applying infrastructure changes...
✅ Infrastructure provisioned successfully

============================================================================
Waiting for Instances to be Ready
============================================================================
ℹ️  Checking 54.123.45.67...
✅ 54.123.45.67 is ready
✅ All instances are ready

============================================================================
Configuring Servers with Ansible
============================================================================
✅ All hosts are reachable
✅ Server configuration completed

============================================================================
Deployment Complete! 🎉
============================================================================
```

---

## Method 2: Makefile

### Available Targets

```bash
# View all available commands
make help

# Initialize Terraform
make init

# Plan changes
make plan

# Apply infrastructure
make apply

# Configure with Ansible
make configure

# Full deployment
make deploy

# Destroy infrastructure
make destroy

# Test connectivity
make ping

# SSH to web server
make ssh-web

# Format Terraform files
make fmt
```

### Example Workflow

```bash
# First time setup
make init

# Deploy infrastructure
make apply

# Configure servers
make configure

# Verify deployment
make verify

# Cleanup
make destroy
```

### Makefile Benefits

- ✅ **Tab Completion**: Works with shell completion
- ✅ **IDE Integration**: Most IDEs recognize Makefiles
- ✅ **Simple Commands**: Easy to remember
- ✅ **Dependency Management**: Targets can depend on others

---

## Method 3: Terraform Provisioner

### Local-exec Provisioner

Add to `terraform/main.tf`:

```hcl
resource "null_resource" "ansible_provisioning" {
  depends_on = [
    aws_instance.web,
    aws_instance.app,
    local_file.ansible_inventory
  ]

  # Trigger on instance changes
  triggers = {
    instance_ids = join(",", concat(
      aws_instance.web[*].id,
      aws_instance.app[*].id
    ))
  }

  # Wait for instances to be ready
  provisioner "local-exec" {
    command = <<-EOT
      echo "Waiting for instances to be ready..."
      sleep 60
    EOT
  }

  # Run Ansible playbook
  provisioner "local-exec" {
    command = <<-EOT
      cd ../ansible
      ansible-playbook -i inventory/hosts.ini setup.yml
    EOT
  }
}
```

### Usage

```bash
cd terraform
terraform apply
# Ansible runs automatically after infrastructure is created
```

### Pros and Cons

**Pros:**
- ✅ Fully integrated with Terraform
- ✅ Automatic execution
- ✅ Works in CI/CD pipelines

**Cons:**
- ❌ Runs on every `terraform apply`
- ❌ Harder to debug failures
- ❌ Less flexible than separate scripts

---

## CI/CD Integration

### GitHub Actions Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy Infrastructure

on:
  push:
    branches: [main]
  workflow_dispatch:

env:
  AWS_REGION: us-east-1
  TF_VERSION: 1.6.0
  ANSIBLE_VERSION: 2.9.0

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}
      
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v2
        with:
          terraform_version: ${{ env.TF_VERSION }}
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install Ansible
        run: |
          pip install ansible boto3 botocore
      
      - name: Terraform Init
        working-directory: terraform
        run: terraform init
      
      - name: Terraform Plan
        working-directory: terraform
        run: terraform plan
      
      - name: Terraform Apply
        working-directory: terraform
        run: terraform apply -auto-approve
      
      - name: Wait for instances
        run: sleep 60
      
      - name: Run Ansible
        working-directory: ansible
        run: ansible-playbook -i inventory/hosts.ini setup.yml
      
      - name: Verify deployment
        run: |
          cd terraform
          WEB_IP=$(terraform output -raw web_instance_public_ips | jq -r '.[0]')
          curl -f http://$WEB_IP || exit 1
```

### GitLab CI/CD

Create `.gitlab-ci.yml`:

```yaml
stages:
  - validate
  - plan
  - apply
  - configure
  - verify

variables:
  TF_ROOT: ${CI_PROJECT_DIR}/terraform
  ANSIBLE_ROOT: ${CI_PROJECT_DIR}/ansible

before_script:
  - apt-get update && apt-get install -y curl unzip python3-pip
  - curl -o terraform.zip https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
  - unzip terraform.zip && mv terraform /usr/local/bin/
  - pip3 install ansible boto3 botocore

validate:
  stage: validate
  script:
    - cd $TF_ROOT
    - terraform init
    - terraform validate

plan:
  stage: plan
  script:
    - cd $TF_ROOT
    - terraform init
    - terraform plan -out=tfplan
  artifacts:
    paths:
      - $TF_ROOT/tfplan

apply:
  stage: apply
  script:
    - cd $TF_ROOT
    - terraform init
    - terraform apply tfplan
  only:
    - main
  when: manual

configure:
  stage: configure
  script:
    - sleep 60
    - cd $ANSIBLE_ROOT
    - ansible-playbook -i inventory/hosts.ini setup.yml
  only:
    - main

verify:
  stage: verify
  script:
    - cd $TF_ROOT
    - WEB_IP=$(terraform output -json web_instance_public_ips | jq -r '.[0]')
    - curl -f http://$WEB_IP
  only:
    - main
```

---

## Best Practices

### 1. Use Remote State

**terraform/backend.tf:**

```hcl
terraform {
  backend "s3" {
    bucket         = "my-terraform-state"
    key            = "terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

### 2. Separate Environments

```bash
# Use Terraform workspaces
terraform workspace new dev
terraform workspace new staging
terraform workspace new prod

# Or separate directories
project/
├── environments/
│   ├── dev/
│   │   └── terraform.tfvars
│   ├── staging/
│   │   └── terraform.tfvars
│   └── prod/
│       └── terraform.tfvars
```

### 3. Use Ansible Vault for Secrets

```bash
# Create encrypted file
ansible-vault create ansible/group_vars/all/vault.yml

# Edit encrypted file
ansible-vault edit ansible/group_vars/all/vault.yml

# Run playbook with vault
ansible-playbook -i inventory/hosts.ini setup.yml --ask-vault-pass
```

### 4. Implement Health Checks

Add to deployment script:

```bash
verify_deployment() {
    local max_attempts=10
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://$WEB_IP/health; then
            echo "✅ Health check passed"
            return 0
        fi
        
        echo "Attempt $attempt/$max_attempts failed, retrying..."
        sleep 10
        ((attempt++))
    done
    
    echo "❌ Health check failed"
    return 1
}
```

### 5. Use Tags for Selective Execution

```yaml
# In playbook
- name: Install Nginx
  apt:
    name: nginx
  tags: [nginx, webserver]

# Run only nginx tasks
ansible-playbook setup.yml --tags nginx

# Skip nginx tasks
ansible-playbook setup.yml --skip-tags nginx
```

### 6. Implement Rollback Strategy

```bash
# Save current state before deployment
terraform state pull > terraform.tfstate.backup

# If deployment fails, restore state
terraform state push terraform.tfstate.backup
```

---

## Troubleshooting Workflows

### Issue: Ansible runs before instances are ready

**Solution**: Add proper wait logic

```bash
wait_for_ssh() {
    local host=$1
    local max_attempts=30
    
    for i in $(seq 1 $max_attempts); do
        if ssh -o ConnectTimeout=5 ubuntu@$host "exit" 2>/dev/null; then
            return 0
        fi
        sleep 10
    done
    
    return 1
}
```

### Issue: Inventory not generated

**Solution**: Check Terraform outputs

```bash
# Verify output exists
terraform output ansible_inventory_path

# Manually trigger inventory generation
terraform apply -refresh-only
```

### Issue: Ansible fails with "Unreachable host"

**Solution**: Check security groups and SSH keys

```bash
# Test SSH manually
ssh -i ~/.ssh/terraform-key ubuntu@$IP

# Check security group allows SSH from your IP
aws ec2 describe-security-groups --group-ids sg-xxx
```

---

## Summary

Choose the automation method that fits your needs:

- **Local Development**: Use bash scripts or Makefile
- **CI/CD Pipelines**: Use GitHub Actions or GitLab CI
- **Integrated Workflow**: Use Terraform provisioners
- **Production**: Combine multiple methods with proper error handling

**Next Steps:**
- [Dynamic Inventory Guide](06-dynamic-inventory.md)
- [Use Cases](07-use-cases.md)

---

[← Previous: Ansible Setup](04-ansible-setup.md) | [Next: Dynamic Inventory →](06-dynamic-inventory.md)
