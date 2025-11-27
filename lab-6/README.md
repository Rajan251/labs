                                                                                                                                                                                                                                        # Terraform + Ansible Integration Guide

A comprehensive, production-ready guide for integrating Terraform infrastructure provisioning with Ansible configuration management.

## 🎯 Overview

This project demonstrates how to combine **Terraform** (Infrastructure as Code) with **Ansible** (Configuration Management) to create a complete automation workflow for cloud infrastructure deployment and server configuration.

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│  Terraform  │ ───> │   Dynamic    │ ───> │   Ansible   │
│ Provisions  │      │  Inventory   │      │ Configures  │
│    AWS      │      │  Generated   │      │   Servers   │
└─────────────┘      └──────────────┘      └─────────────┘
```

## 📚 Documentation Structure

1. **[Introduction](docs/01-introduction.md)** - Why Terraform + Ansible, use cases, benefits
2. **[Architecture](docs/02-architecture.md)** - End-to-end flow, diagrams, component interaction
3. **[Terraform Setup](docs/03-terraform-setup.md)** - Infrastructure provisioning guide
4. **[Ansible Setup](docs/04-ansible-setup.md)** - Configuration management guide
5. **[Integration Workflow](docs/05-integration-workflow.md)** - Automation scripts and workflows
6. **[Dynamic Inventory](docs/06-dynamic-inventory.md)** - Dynamic inventory integration
7. **[Use Cases](docs/07-use-cases.md)** - Real-world examples and scenarios
8. **[Troubleshooting](docs/08-troubleshooting.md)** - Common problems and solutions
9. **[Best Practices](docs/09-best-practices.md)** - Advanced tips and recommendations

## 🚀 Quick Start

### Prerequisites

- AWS Account with appropriate credentials
- Terraform >= 1.0
- Ansible >= 2.9
- Python 3.8+
- SSH key pair for EC2 access

### Installation

```bash
# Install Terraform
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/

# Install Ansible
pip3 install ansible boto3 botocore

# Clone this repository
git clone <your-repo>
cd lab-6
```

### Basic Usage

#### Option 1: Using Automation Script (Recommended)

```bash
# Deploy infrastructure and configure servers
./scripts/deploy.sh

# Destroy infrastructure
./scripts/destroy.sh
```

#### Option 2: Using Makefile

```bash
# Initialize and deploy
make init
make deploy

# Configure servers only
make configure

# Destroy infrastructure
make destroy
```

#### Option 3: Manual Execution

```bash
# Step 1: Provision infrastructure with Terraform
cd terraform
terraform init
terraform plan
terraform apply -auto-approve

# Step 2: Configure servers with Ansible
cd ../ansible
ansible-playbook -i inventory/hosts.ini setup.yml

# Step 3: Cleanup
cd ../terraform
terraform destroy -auto-approve
```

## 📁 Project Structure

```
lab-6/
├── README.md                          # This file
├── Makefile                           # Automation targets
├── requirements.txt                   # Python dependencies
├── .gitignore                         # Git ignore rules
│
├── docs/                              # Documentation
│   ├── 01-introduction.md
│   ├── 02-architecture.md
│   ├── 03-terraform-setup.md
│   ├── 04-ansible-setup.md
│   ├── 05-integration-workflow.md
│   ├── 06-dynamic-inventory.md
│   ├── 07-use-cases.md
│   ├── 08-troubleshooting.md
│   └── 09-best-practices.md
│
├── terraform/                         # Terraform infrastructure code
│   ├── main.tf                        # Main configuration
│   ├── variables.tf                   # Variable definitions
│   ├── outputs.tf                     # Output definitions
│   ├── terraform.tfvars.example       # Example variables
│   └── inventory_template.tpl         # Ansible inventory template
│
├── ansible/                           # Ansible configuration
│   ├── ansible.cfg                    # Ansible configuration
│   ├── setup.yml                      # Main playbook
│   ├── inventory/
│   │   ├── hosts.ini.example          # Static inventory example
│   │   └── aws_ec2.yml                # Dynamic inventory config
│   ├── roles/
│   │   ├── common/                    # Common system setup
│   │   ├── nginx/                     # Nginx web server
│   │   ├── docker/                    # Docker installation
│   │   └── k8s-tools/                 # Kubernetes tools
│   └── group_vars/
│       ├── all.yml                    # Global variables
│       └── webservers.yml             # Web server variables
│
├── scripts/                           # Automation scripts
│   ├── deploy.sh                      # Deployment script
│   └── destroy.sh                     # Cleanup script
│
└── examples/                          # Real-world examples
    ├── 3-tier-app/                    # 3-tier application
    ├── kubernetes-cluster/            # K8s cluster setup
    └── ci-cd-pipeline/                # CI/CD integration
```

## 🎓 What You'll Learn

- ✅ How to provision AWS infrastructure with Terraform
- ✅ How to generate dynamic Ansible inventory from Terraform
- ✅ How to configure servers automatically with Ansible
- ✅ How to create end-to-end automation workflows
- ✅ How to integrate with CI/CD pipelines
- ✅ How to troubleshoot common issues
- ✅ Production-ready best practices

## 🔧 Key Features

- **Complete Infrastructure as Code**: VPC, subnets, security groups, EC2 instances
- **Dynamic Inventory Generation**: Automatic host discovery from Terraform outputs
- **Modular Ansible Roles**: Reusable roles for common configurations
- **Automation Scripts**: One-command deployment and destruction
- **Real-World Examples**: 3-tier apps, Kubernetes, multi-cloud
- **CI/CD Integration**: GitHub Actions workflow examples
- **Comprehensive Troubleshooting**: Common problems and solutions

## 🌟 Use Cases

1. **DevOps Automation**: Automated infrastructure deployment and configuration
2. **Cloud Migration**: Lift-and-shift applications to AWS
3. **Disaster Recovery**: Quick infrastructure recreation
4. **Development Environments**: Spin up/down dev/test environments
5. **Kubernetes Clusters**: Automated K8s node provisioning and setup
6. **Multi-Cloud Deployments**: Consistent configuration across providers

## 📊 Architecture Flow

```
Developer
    │
    ├─> terraform apply
    │       │
    │       ├─> Creates VPC, Subnets, Security Groups
    │       ├─> Launches EC2 Instances
    │       ├─> Generates inventory/hosts.ini
    │       └─> Outputs instance IPs
    │
    └─> ansible-playbook setup.yml
            │
            ├─> Reads inventory/hosts.ini
            ├─> Connects via SSH
            ├─> Applies roles:
            │       ├─> common (updates, users)
            │       ├─> nginx (web server)
            │       ├─> docker (containers)
            │       └─> k8s-tools (kubectl, helm)
            │
            └─> Configured Infrastructure Ready
```

## 🔐 Security Considerations

- SSH keys are managed securely
- Security groups follow least privilege principle
- Sensitive data stored in `.tfvars` (gitignored)
- Ansible vault for secrets management
- IAM roles for EC2 instances

## 🤝 Contributing

This is a learning resource. Feel free to:
- Report issues
- Suggest improvements
- Add new examples
- Share your use cases

## 📝 License

MIT License - Feel free to use for learning and production

## 🆘 Need Help?

- Check [Troubleshooting Guide](docs/08-troubleshooting.md)
- Review [Best Practices](docs/09-best-practices.md)
- See [Real-World Examples](docs/07-use-cases.md)

## 🚦 Next Steps

1. Read the [Introduction](docs/01-introduction.md) to understand the concepts
2. Review the [Architecture](docs/02-architecture.md) to see how components interact
3. Follow the [Terraform Setup](docs/03-terraform-setup.md) to provision infrastructure
4. Configure servers with [Ansible Setup](docs/04-ansible-setup.md)
5. Explore [Use Cases](docs/07-use-cases.md) for real-world scenarios

---

**Happy Automating! 🚀**
