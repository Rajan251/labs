# Troubleshooting Guide

## Common Problems and Solutions

### Terraform Issues

#### 1. Error: "No valid credential sources found"

**Symptom:**
```
Error: No valid credential sources found for AWS Provider
```

**Cause:** AWS credentials not configured

**Solutions:**
```bash
# Option 1: AWS CLI
aws configure

# Option 2: Environment variables
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_DEFAULT_REGION="us-east-1"

# Option 3: Terraform variables (not recommended for production)
# In terraform.tfvars
aws_access_key = "your-key"
aws_secret_key = "your-secret"
```

#### 2. Error: "InvalidKeyPair.NotFound"

**Symptom:**
```
Error launching source instance: InvalidKeyPair.NotFound: The key pair 'terraform-key' does not exist
```

**Cause:** SSH public key file not found or not uploaded

**Solutions:**
```bash
# Generate SSH key pair
ssh-keygen -t rsa -b 4096 -f ~/.ssh/terraform-key -N ""

# Verify files exist
ls -la ~/.ssh/terraform-key*

# Update terraform.tfvars
ssh_public_key_path = "~/.ssh/terraform-key.pub"
```

#### 3. Error: "VpcLimitExceeded"

**Symptom:**
```
Error creating VPC: VpcLimitExceeded: The maximum number of VPCs has been reached
```

**Cause:** AWS account VPC limit reached (default: 5 per region)

**Solutions:**
```bash
# List existing VPCs
aws ec2 describe-vpcs --region us-east-1

# Delete unused VPCs
aws ec2 delete-vpc --vpc-id vpc-xxx

# Or request limit increase from AWS Support
# Or use different region
```

#### 4. Error: "Resource already exists"

**Symptom:**
```
Error: Error creating security group: InvalidGroup.Duplicate
```

**Cause:** Resource with same name already exists

**Solutions:**
```bash
# Import existing resource
terraform import aws_security_group.web sg-xxx

# Or change resource name in variables
project_name = "terraform-ansible-v2"

# Or destroy and recreate
terraform destroy
terraform apply
```

---

### Ansible Issues

#### 5. Error: "Failed to connect to the host via ssh"

**Symptom:**
```
fatal: [web-1]: UNREACHABLE! => {"changed": false, "msg": "Failed to connect to the host via ssh"}
```

**Causes & Solutions:**

**A. SSH key permissions**
```bash
# Fix permissions
chmod 400 ~/.ssh/terraform-key

# Verify
ls -la ~/.ssh/terraform-key
# Should show: -r-------- 1 user user
```

**B. Wrong SSH key path**
```bash
# Check inventory
cat ansible/inventory/hosts.ini

# Should have correct path
ansible_ssh_private_key_file=~/.ssh/terraform-key
```

**C. Security group doesn't allow SSH**
```bash
# Check security group
aws ec2 describe-security-groups --group-ids sg-xxx

# Should have rule allowing port 22 from your IP
```

**D. Instance not ready**
```bash
# Wait for instance to be fully ready
sleep 60

# Test SSH manually
ssh -i ~/.ssh/terraform-key ubuntu@<instance-ip>
```

#### 6. Error: "Permission denied (publickey)"

**Symptom:**
```
Permission denied (publickey,gssapi-keyex,gssapi-with-mic)
```

**Solutions:**
```bash
# Verify correct user
# For Ubuntu AMI, use 'ubuntu'
# For Amazon Linux, use 'ec2-user'

# Check inventory
ansible_user=ubuntu

# Test manually
ssh -i ~/.ssh/terraform-key ubuntu@<ip>

# Enable verbose SSH debugging
ssh -vvv -i ~/.ssh/terraform-key ubuntu@<ip>
```

#### 7. Error: "Ansible module not found"

**Symptom:**
```
ERROR! couldn't resolve module/action 'docker_container'
```

**Cause:** Missing Ansible collection

**Solutions:**
```bash
# Install required collections
ansible-galaxy collection install community.docker
ansible-galaxy collection install community.general
ansible-galaxy collection install ansible.posix

# Or install all from requirements
ansible-galaxy collection install -r requirements.yml
```

#### 8. Error: "sudo: a password is required"

**Symptom:**
```
fatal: [web-1]: FAILED! => {"msg": "Missing sudo password"}
```

**Solutions:**
```bash
# Option 1: Use --ask-become-pass
ansible-playbook -i inventory/hosts.ini setup.yml --ask-become-pass

# Option 2: Configure passwordless sudo on instances
# (Already configured for ubuntu user on Ubuntu AMI)

# Option 3: Check ansible.cfg
[privilege_escalation]
become = True
become_method = sudo
become_user = root
become_ask_pass = False
```

---

### Integration Issues

#### 9. Inventory file not generated

**Symptom:**
Ansible inventory file `hosts.ini` doesn't exist after Terraform apply

**Solutions:**
```bash
# Check Terraform output
cd terraform
terraform output ansible_inventory_path

# Verify local_file resource
terraform state list | grep local_file

# Manually trigger
terraform apply -refresh-only

# Check template file exists
ls -la inventory_template.tpl

# Debug template rendering
terraform console
> templatefile("inventory_template.tpl", {webservers = aws_instance.web})
```

#### 10. Ansible runs before instances are ready

**Symptom:**
Ansible fails with "Connection timeout" immediately after Terraform apply

**Solutions:**
```bash
# Add wait time in deployment script
sleep 60

# Or use Ansible wait_for module
- name: Wait for SSH
  wait_for_connection:
    timeout: 300
    delay: 5

# Or check instance status
aws ec2 describe-instance-status --instance-ids i-xxx
```

#### 11. Wrong IP addresses in inventory

**Symptom:**
Inventory has private IPs but you need public IPs (or vice versa)

**Solutions:**
```hcl
# In inventory_template.tpl
# For public IPs:
ansible_host=${instance.public_ip}

# For private IPs (VPN/internal access):
ansible_host=${instance.private_ip}

# In outputs.tf
output "web_instance_public_ips" {
  value = aws_instance.web[*].public_ip
}
```

---

### AWS-Specific Issues

#### 12. Error: "UnauthorizedOperation"

**Symptom:**
```
Error: UnauthorizedOperation: You are not authorized to perform this operation
```

**Cause:** IAM permissions insufficient

**Solution:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:*",
        "vpc:*"
      ],
      "Resource": "*"
    }
  ]
}
```

#### 13. Error: "InvalidAMIID.NotFound"

**Symptom:**
```
Error: Error launching source instance: InvalidAMIID.NotFound
```

**Cause:** AMI not available in selected region

**Solutions:**
```hcl
# Use data source to find latest AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical
  
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

# Or check AMI availability
aws ec2 describe-images --image-ids ami-xxx --region us-east-1
```

---

## Debugging Techniques

### 1. Enable Verbose Output

**Terraform:**
```bash
export TF_LOG=DEBUG
terraform apply

# Or specific component
export TF_LOG_PATH=./terraform.log
```

**Ansible:**
```bash
# Verbose levels: -v, -vv, -vvv, -vvvv
ansible-playbook -i inventory/hosts.ini setup.yml -vvv
```

### 2. Test Components Individually

```bash
# Test Terraform
cd terraform
terraform plan
terraform validate

# Test Ansible connectivity
cd ansible
ansible all -i inventory/hosts.ini -m ping

# Test specific role
ansible-playbook -i inventory/hosts.ini setup.yml --tags nginx --check
```

### 3. Use Check Mode

```bash
# Terraform plan (dry run)
terraform plan

# Ansible check mode (dry run)
ansible-playbook -i inventory/hosts.ini setup.yml --check
```

### 4. Inspect State

```bash
# Terraform state
terraform show
terraform state list
terraform state show aws_instance.web[0]

# Ansible facts
ansible web-1 -i inventory/hosts.ini -m setup
```

---

## Performance Issues

### Slow Terraform Apply

**Solutions:**
```bash
# Use parallelism
terraform apply -parallelism=20

# Reduce resource count for testing
web_instance_count = 1
```

### Slow Ansible Execution

**Solutions:**
```ini
# In ansible.cfg
[defaults]
forks = 20
gathering = smart
fact_caching = jsonfile

[ssh_connection]
pipelining = True
ssh_args = -o ControlMaster=auto -o ControlPersist=60s
```

---

## Prevention Best Practices

1. **Always run `terraform plan` before `apply`**
2. **Use `--check` mode for Ansible before actual run**
3. **Keep backups of state files**
4. **Use version control for all code**
5. **Test in dev environment first**
6. **Monitor AWS costs**
7. **Use tags for resource organization**
8. **Document custom configurations**

---

[← Previous: Dynamic Inventory](06-dynamic-inventory.md) | [Next: Best Practices →](09-best-practices.md)
