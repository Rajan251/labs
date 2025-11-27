# 3-Tier Application Deployment Example

## Architecture

This example demonstrates deploying a 3-tier web application:
- **Web Tier**: 2x Nginx servers (load balanced)
- **App Tier**: 2x Application servers (Docker containers)
- **Database Tier**: 1x RDS MySQL database

## Quick Start

```bash
cd examples/3-tier-app

# Deploy infrastructure
terraform -chdir=terraform init
terraform -chdir=terraform apply

# Configure servers
ansible-playbook -i ansible/inventory/hosts.ini ansible/deploy-app.yml

# Access application
terraform -chdir=terraform output -raw load_balancer_dns
```

## Components

### Terraform Configuration

**Additional resources beyond base setup:**
- Application Load Balancer (ALB)
- Target Groups for web and app tiers
- RDS MySQL instance
- Additional security groups for database access

### Ansible Playbooks

**deploy-app.yml**: Deploys the application
- Configures Nginx as reverse proxy
- Deploys Docker containers on app servers
- Configures database connection

## Architecture Diagram

```
Internet
    │
    ▼
┌───────────────────┐
│  Application      │
│  Load Balancer    │
└────────┬──────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼────┐
│ Nginx │ │ Nginx │  (Web Tier - Public Subnet)
│ :80   │ │ :80   │
└───┬───┘ └──┬────┘
    │         │
    └────┬────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼────┐
│ App   │ │ App   │  (App Tier - Private Subnet)
│ :8080 │ │ :8080 │
└───┬───┘ └──┬────┘
    │         │
    └────┬────┘
         │
    ┌────▼────┐
    │  MySQL  │      (Database Tier - Private Subnet)
    │  RDS    │
    └─────────┘
```

## Benefits

- **High Availability**: Multiple instances in each tier
- **Security**: Database in private subnet, not internet-accessible
- **Scalability**: Easy to add more instances to any tier
- **Load Balancing**: Traffic distributed across web servers
- **Separation of Concerns**: Each tier has specific responsibility

## Customization

Edit `terraform/terraform.tfvars`:
```hcl
web_instance_count = 2
app_instance_count = 2
db_instance_class  = "db.t3.micro"
db_allocated_storage = 20
```

## Cleanup

```bash
terraform -chdir=terraform destroy
```
