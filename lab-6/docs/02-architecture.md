# Architecture Overview

## Table of Contents
- [End-to-End Architecture Flow](#end-to-end-architecture-flow)
- [Component Interaction](#component-interaction)
- [Dynamic Inventory Generation](#dynamic-inventory-generation)
- [SSH Communication Flow](#ssh-communication-flow)
- [Ansible Galaxy Roles Integration](#ansible-galaxy-roles-integration)
- [Detailed Workflow](#detailed-workflow)

---

## End-to-End Architecture Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│                         DEVELOPER WORKSTATION                         │
│                                                                       │
│  ┌─────────────────┐              ┌──────────────────┐              │
│  │   Terraform     │              │     Ansible      │              │
│  │   Code (.tf)    │              │  Playbooks (.yml)│              │
│  └────────┬────────┘              └────────┬─────────┘              │
│           │                                 │                        │
└───────────┼─────────────────────────────────┼────────────────────────┘
            │                                 │
            │ 1. terraform apply              │
            ▼                                 │
┌──────────────────────────────────────────┐  │
│         AWS CLOUD PROVIDER               │  │
│                                          │  │
│  ┌────────────────────────────────┐     │  │
│  │  VPC (10.0.0.0/16)             │     │  │
│  │  ├─ Public Subnet (10.0.1.0/24)│     │  │
│  │  ├─ Private Subnet (10.0.2.0/24)    │  │
│  │  └─ Internet Gateway           │     │  │
│  └────────────────────────────────┘     │  │
│                                          │  │
│  ┌────────────────────────────────┐     │  │
│  │  Security Groups               │     │  │
│  │  ├─ SSH (22) from workstation  │     │  │
│  │  ├─ HTTP (80) from anywhere    │     │  │
│  │  └─ HTTPS (443) from anywhere  │     │  │
│  └────────────────────────────────┘     │  │
│                                          │  │
│  ┌────────────────────────────────┐     │  │
│  │  EC2 Instances                 │     │  │
│  │  ├─ web-1 (10.0.1.10)         │     │  │
│  │  ├─ web-2 (10.0.1.11)         │     │  │
│  │  ├─ app-1 (10.0.2.20)         │     │  │
│  │  └─ db-1 (10.0.2.30)          │     │  │
│  └────────────────────────────────┘     │  │
│                                          │  │
└──────────────┬───────────────────────────┘  │
               │                              │
               │ 2. Output: IPs, DNS names    │
               ▼                              │
┌──────────────────────────────────────────┐  │
│  LOCAL FILE: inventory/hosts.ini         │  │
│                                          │  │
│  [webservers]                            │  │
│  web-1 ansible_host=54.123.45.67        │  │
│  web-2 ansible_host=54.123.45.68        │  │
│                                          │  │
│  [appservers]                            │  │
│  app-1 ansible_host=10.0.2.20           │  │
│                                          │  │
│  [databases]                             │  │
│  db-1 ansible_host=10.0.2.30            │  │
└──────────────┬───────────────────────────┘  │
               │                              │
               │ 3. Inventory file created    │
               └──────────────────────────────┤
                                              │
                              4. ansible-playbook -i inventory/hosts.ini
                                              │
                                              ▼
                              ┌────────────────────────────┐
                              │  SSH Connection to Hosts   │
                              │  ├─ web-1: Configure Nginx │
                              │  ├─ web-2: Configure Nginx │
                              │  ├─ app-1: Install Docker  │
                              │  └─ db-1: Setup PostgreSQL │
                              └────────────────────────────┘
                                              │
                                              ▼
                              ┌────────────────────────────┐
                              │  Configured Infrastructure │
                              │  Ready for Production      │
                              └────────────────────────────┘
```

---

## Component Interaction

### Phase 1: Infrastructure Provisioning (Terraform)

```
┌─────────────────────────────────────────────────────────────┐
│                    TERRAFORM WORKFLOW                        │
└─────────────────────────────────────────────────────────────┘

Step 1: Initialize
┌──────────────────┐
│ terraform init   │ → Downloads AWS provider plugin
└──────────────────┘   Initializes backend (S3/local)
                       Sets up .terraform directory

Step 2: Plan
┌──────────────────┐
│ terraform plan   │ → Reads main.tf, variables.tf
└──────────────────┘   Compares with current state
                       Shows what will be created/changed
                       Preview before applying

Step 3: Apply
┌──────────────────┐
│ terraform apply  │ → Creates resources in order:
└──────────────────┘     1. VPC
                         2. Subnets
                         3. Internet Gateway
                         4. Route Tables
                         5. Security Groups
                         6. EC2 Key Pair
                         7. EC2 Instances
                       
                       Updates terraform.tfstate
                       
Step 4: Output
┌──────────────────┐
│ terraform output │ → Displays:
└──────────────────┘     - Instance IPs
                         - DNS names
                         - Instance IDs
                       
                       Generates inventory file
                       using local_file resource
```

### Phase 2: Configuration Management (Ansible)

```
┌─────────────────────────────────────────────────────────────┐
│                    ANSIBLE WORKFLOW                          │
└─────────────────────────────────────────────────────────────┘

Step 1: Read Inventory
┌──────────────────────────┐
│ ansible-playbook         │ → Reads inventory/hosts.ini
│ -i inventory/hosts.ini   │   Discovers host groups
│ setup.yml                │   Loads variables
└──────────────────────────┘

Step 2: Gather Facts
┌──────────────────────────┐
│ Fact Gathering           │ → Connects to each host via SSH
└──────────────────────────┘   Collects system information:
                                 - OS type and version
                                 - IP addresses
                                 - Disk space
                                 - Memory
                                 - CPU info

Step 3: Execute Roles
┌──────────────────────────┐
│ Role: common             │ → Update packages
└──────────────────────────┘   Create users
                               Configure firewall
                               Install base tools

┌──────────────────────────┐
│ Role: nginx              │ → Install Nginx
└──────────────────────────┘   Configure virtual hosts
                               Start service
                               Enable on boot

┌──────────────────────────┐
│ Role: docker             │ → Install Docker
└──────────────────────────┘   Add users to docker group
                               Start Docker daemon
                               Pull base images

┌──────────────────────────┐
│ Role: k8s-tools          │ → Install kubectl
└──────────────────────────┘   Install helm
                               Configure kubeconfig

Step 4: Handlers
┌──────────────────────────┐
│ Notify Handlers          │ → Restart services if config changed
└──────────────────────────┘   Reload Nginx
                               Restart Docker
```

---

## Dynamic Inventory Generation

### Method 1: Terraform local_file Resource

**How it works:**

1. **Terraform creates template file** (`inventory_template.tpl`):
```hcl
[webservers]
%{ for instance in webservers ~}
${instance.tags.Name} ansible_host=${instance.public_ip} ansible_user=ubuntu
%{ endfor ~}

[appservers]
%{ for instance in appservers ~}
${instance.tags.Name} ansible_host=${instance.private_ip} ansible_user=ubuntu
%{ endfor ~}

[all:vars]
ansible_ssh_private_key_file=~/.ssh/terraform-key.pem
ansible_ssh_common_args='-o StrictHostKeyChecking=no'
```

2. **Terraform generates inventory** using `local_file`:
```hcl
resource "local_file" "ansible_inventory" {
  content = templatefile("inventory_template.tpl", {
    webservers = aws_instance.web,
    appservers = aws_instance.app
  })
  filename = "../ansible/inventory/hosts.ini"
}
```

3. **Result**: `hosts.ini` file created automatically:
```ini
[webservers]
web-1 ansible_host=54.123.45.67 ansible_user=ubuntu
web-2 ansible_host=54.123.45.68 ansible_user=ubuntu

[appservers]
app-1 ansible_host=10.0.2.20 ansible_user=ubuntu

[all:vars]
ansible_ssh_private_key_file=~/.ssh/terraform-key.pem
ansible_ssh_common_args='-o StrictHostKeyChecking=no'
```

### Method 2: AWS EC2 Dynamic Inventory Plugin

**How it works:**

1. **Create plugin configuration** (`aws_ec2.yml`):
```yaml
plugin: aws_ec2
regions:
  - us-east-1
filters:
  tag:Environment: production
  instance-state-name: running
keyed_groups:
  - key: tags.Role
    prefix: role
  - key: tags.Environment
    prefix: env
hostnames:
  - ip-address
compose:
  ansible_host: public_ip_address
```

2. **Ansible queries AWS API** at runtime:
   - Discovers all EC2 instances in specified regions
   - Filters by tags and state
   - Groups instances automatically
   - No static file needed

3. **Use with playbook**:
```bash
ansible-playbook -i inventory/aws_ec2.yml setup.yml
```

### Method 3: Terraform Output + Script

**How it works:**

1. **Terraform outputs JSON**:
```hcl
output "instance_ips" {
  value = {
    for instance in aws_instance.web :
    instance.tags.Name => {
      public_ip  = instance.public_ip
      private_ip = instance.private_ip
      role       = instance.tags.Role
    }
  }
}
```

2. **Script converts to inventory**:
```bash
#!/bin/bash
terraform output -json instance_ips | jq -r '
  .value | to_entries[] | 
  "\(.value.role) ansible_host=\(.value.public_ip)"
' > ../ansible/inventory/hosts.ini
```

---

## SSH Communication Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    SSH CONNECTION FLOW                           │
└─────────────────────────────────────────────────────────────────┘

Developer Workstation                        EC2 Instance
┌──────────────────┐                        ┌──────────────────┐
│                  │                        │                  │
│  Ansible         │                        │  SSH Daemon      │
│  Control Node    │                        │  (Port 22)       │
│                  │                        │                  │
└────────┬─────────┘                        └────────┬─────────┘
         │                                           │
         │ 1. Read inventory/hosts.ini               │
         │    Get: ansible_host=54.123.45.67        │
         │         ansible_user=ubuntu               │
         │         ansible_ssh_private_key_file=key  │
         │                                           │
         │ 2. SSH Connection Request                 │
         ├──────────────────────────────────────────>│
         │    ssh -i key ubuntu@54.123.45.67        │
         │                                           │
         │                                           │ 3. Verify SSH key
         │                                           │    Check authorized_keys
         │                                           │
         │ 4. Connection Established                 │
         │<──────────────────────────────────────────┤
         │                                           │
         │ 5. Gather Facts (setup module)            │
         ├──────────────────────────────────────────>│
         │                                           │
         │                                           │ 6. Collect system info
         │                                           │    OS, memory, disk, etc.
         │                                           │
         │ 7. Facts returned                         │
         │<──────────────────────────────────────────┤
         │                                           │
         │ 8. Execute tasks                          │
         ├──────────────────────────────────────────>│
         │    - Install packages                     │
         │    - Copy files                           │
         │    - Start services                       │
         │                                           │
         │                                           │ 9. Execute commands
         │                                           │    Return results
         │                                           │
         │ 10. Task results                          │
         │<──────────────────────────────────────────┤
         │     changed: true/false                   │
         │     stdout: command output                │
         │                                           │
         │ 11. Close connection                      │
         ├──────────────────────────────────────────>│
         │                                           │
         ▼                                           ▼
```

### SSH Key Setup Process

**Terraform creates and distributes SSH keys:**

```hcl
# 1. Create key pair in AWS
resource "aws_key_pair" "deployer" {
  key_name   = "terraform-deployer-key"
  public_key = file("~/.ssh/terraform-key.pub")
}

# 2. Attach to EC2 instances
resource "aws_instance" "web" {
  key_name = aws_key_pair.deployer.key_name
  # ... other config
}
```

**On EC2 instance (automatic):**
```bash
# AWS adds public key to:
/home/ubuntu/.ssh/authorized_keys
```

**Ansible uses private key:**
```ini
[all:vars]
ansible_ssh_private_key_file=~/.ssh/terraform-key.pem
```

---

## Ansible Galaxy Roles Integration

### What are Galaxy Roles?

Pre-built, community-maintained Ansible roles from [galaxy.ansible.com](https://galaxy.ansible.com)

### Using Galaxy Roles in Our Setup

**1. Install roles from Galaxy:**
```bash
# Install specific role
ansible-galaxy install geerlingguy.nginx

# Install from requirements file
ansible-galaxy install -r requirements.yml
```

**2. Requirements file** (`requirements.yml`):
```yaml
roles:
  - name: geerlingguy.nginx
    version: 3.1.4
  
  - name: geerlingguy.docker
    version: 6.1.0
  
  - name: geerlingguy.kubernetes
    version: 6.0.0
```

**3. Use in playbook:**
```yaml
- name: Configure web servers
  hosts: webservers
  roles:
    - role: geerlingguy.nginx
      nginx_vhosts:
        - listen: "80"
          server_name: "example.com"
          root: "/var/www/html"
```

**4. Directory structure:**
```
ansible/
├── roles/
│   ├── geerlingguy.nginx/      # Downloaded from Galaxy
│   ├── geerlingguy.docker/     # Downloaded from Galaxy
│   ├── common/                 # Custom role
│   └── app-deploy/             # Custom role
├── requirements.yml
└── setup.yml
```

### Benefits of Galaxy Roles

- ✅ **Battle-tested**: Used by thousands of users
- ✅ **Well-documented**: Comprehensive README files
- ✅ **Maintained**: Regular updates and bug fixes
- ✅ **Customizable**: Override variables for your needs
- ✅ **Time-saving**: Don't reinvent the wheel

---

## Detailed Workflow

### Complete End-to-End Execution

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: DEVELOPER PREPARES CODE                                 │
└─────────────────────────────────────────────────────────────────┘

Developer edits:
├── terraform/variables.tf      (Set AWS region, instance types)
├── terraform/terraform.tfvars  (Provide AWS credentials)
├── ansible/group_vars/all.yml  (Set application variables)
└── ansible/setup.yml           (Define configuration tasks)

┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: TERRAFORM INITIALIZATION                                │
└─────────────────────────────────────────────────────────────────┘

$ cd terraform
$ terraform init

Actions:
├── Download AWS provider plugin (hashicorp/aws)
├── Initialize backend (local or S3)
├── Create .terraform/ directory
└── Lock provider versions (.terraform.lock.hcl)

┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: TERRAFORM PLAN                                          │
└─────────────────────────────────────────────────────────────────┘

$ terraform plan

Terraform analyzes:
├── Current state (terraform.tfstate)
├── Desired state (*.tf files)
└── Shows diff:
    ├── + Resources to create (VPC, EC2, etc.)
    ├── ~ Resources to modify
    └── - Resources to delete

┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: TERRAFORM APPLY                                         │
└─────────────────────────────────────────────────────────────────┘

$ terraform apply -auto-approve

Execution order (respects dependencies):
1. aws_vpc.main                    (VPC created)
2. aws_subnet.public               (Subnet created)
3. aws_internet_gateway.main       (IGW created)
4. aws_route_table.public          (Route table created)
5. aws_security_group.web          (Security group created)
6. aws_key_pair.deployer           (SSH key uploaded)
7. aws_instance.web[0]             (EC2 instance 1 launched)
8. aws_instance.web[1]             (EC2 instance 2 launched)
9. local_file.ansible_inventory    (Inventory file generated)

Result:
├── Infrastructure created in AWS
├── terraform.tfstate updated
└── ansible/inventory/hosts.ini generated

┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: WAIT FOR INSTANCES                                      │
└─────────────────────────────────────────────────────────────────┘

$ sleep 60  # Wait for SSH to be ready

EC2 instances:
├── Boot up (30-60 seconds)
├── SSH daemon starts
└── Ready to accept connections

┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: ANSIBLE EXECUTION                                       │
└─────────────────────────────────────────────────────────────────┘

$ cd ../ansible
$ ansible-playbook -i inventory/hosts.ini setup.yml

Ansible workflow:
1. Read inventory file
   ├── Discover hosts: web-1, web-2, app-1
   └── Load variables from group_vars/

2. Gather facts from all hosts
   ├── Connect via SSH
   ├── Collect system information
   └── Store in ansible_facts

3. Execute playbook tasks:
   
   Role: common (on all hosts)
   ├── Update apt cache
   ├── Upgrade packages
   ├── Install vim, curl, git
   ├── Create admin user
   └── Configure firewall
   
   Role: nginx (on webservers)
   ├── Install nginx package
   ├── Copy nginx.conf template
   ├── Create virtual host config
   ├── Start nginx service
   └── Enable nginx on boot
   
   Role: docker (on appservers)
   ├── Install Docker dependencies
   ├── Add Docker GPG key
   ├── Add Docker repository
   ├── Install docker-ce
   ├── Start Docker service
   └── Add user to docker group

4. Execute handlers (if notified)
   ├── Restart nginx (if config changed)
   └── Reload systemd (if units changed)

5. Report results
   ├── ok=45 changed=12 unreachable=0 failed=0
   └── Playbook execution time: 3m 24s

┌─────────────────────────────────────────────────────────────────┐
│ STEP 7: VERIFICATION                                            │
└─────────────────────────────────────────────────────────────────┘

$ curl http://$(terraform output -raw web_public_ip)
<!DOCTYPE html><html>Welcome to Nginx!</html>

$ ssh ubuntu@$(terraform output -raw web_public_ip) "docker --version"
Docker version 24.0.5, build ced0996

✅ Infrastructure provisioned and configured successfully!
```

---

## Data Flow Between Components

```
┌──────────────┐
│ variables.tf │ ──> Input variables
└──────┬───────┘     (region, instance_type, etc.)
       │
       ▼
┌──────────────┐
│   main.tf    │ ──> Creates resources
└──────┬───────┘     Uses variables
       │
       ▼
┌──────────────┐
│  outputs.tf  │ ──> Exports data
└──────┬───────┘     (IPs, DNS, IDs)
       │
       ▼
┌──────────────────┐
│ inventory_       │ ──> Template file
│ template.tpl     │     Uses output data
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ local_file       │ ──> Generates inventory
│ resource         │     Writes hosts.ini
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ inventory/       │ ──> Ansible reads this
│ hosts.ini        │     Discovers hosts
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ ansible.cfg      │ ──> Configuration
└──────┬───────────┘     (SSH settings, etc.)
       │
       ▼
┌──────────────────┐
│ setup.yml        │ ──> Main playbook
└──────┬───────────┘     Defines tasks
       │
       ▼
┌──────────────────┐
│ roles/           │ ──> Modular tasks
│ ├── common/      │     Reusable code
│ ├── nginx/       │
│ └── docker/      │
└──────────────────┘
```

---

## Summary

This architecture provides:

1. **Clear Separation**: Infrastructure (Terraform) vs Configuration (Ansible)
2. **Automation**: Dynamic inventory generation eliminates manual steps
3. **Scalability**: Add more instances, automatically included in inventory
4. **Reusability**: Terraform modules + Ansible roles
5. **Version Control**: Everything in Git
6. **Idempotency**: Safe to run multiple times

**Next Steps:**
- [Terraform Setup Guide](03-terraform-setup.md) - Learn to provision infrastructure
- [Ansible Setup Guide](04-ansible-setup.md) - Learn to configure servers

---

[← Previous: Introduction](01-introduction.md) | [Next: Terraform Setup →](03-terraform-setup.md)
