# PayFlow Terraform Project

## Quick Start

```bash
# 1. Clone the repository
cd /home/rk/Documents/labs/terrafrom-lab/terraform-fintech-lab

# 2. Choose an environment
cd environments/dev

# 3. Copy and customize variables
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

# 4. Initialize Terraform
terraform init

# 5. Plan infrastructure
terraform plan

# 6. Apply configuration
terraform apply
```

## Project Structure

```
terraform-fintech-lab/
├── modules/              # Reusable Terraform modules
│   ├── vpc/             # VPC, subnets, routing
│   └── security/        # Security groups
├── environments/         # Environment-specific configs
│   ├── dev/             # Development
│   ├── staging/         # Staging
│   └── prod/            # Production
├── labs/                # Hands-on lab exercises
│   └── 01-vpc-networking/
├── docs/                # Documentation
└── scripts/             # Helper scripts
```

## Environments

### Development
- **VPC CIDR**: 10.0.0.0/16
- **NAT Gateways**: 1 (cost optimized)
- **Availability Zones**: 2
- **Flow Logs**: Disabled

### Staging
- **VPC CIDR**: 10.1.0.0/16
- **NAT Gateways**: 2 (moderate HA)
- **Availability Zones**: 2
- **Flow Logs**: Enabled (7 days retention)

### Production
- **VPC CIDR**: 10.2.0.0/16
- **NAT Gateways**: 3 (full HA)
- **Availability Zones**: 3
- **Flow Logs**: Enabled (30 days retention)

## Documentation

- [Architecture](docs/architecture.md)
- [Business Requirements](docs/business-requirements.md)
- [Security Best Practices](docs/security-best-practices.md)
- [Terraform Workflow Diagrams](docs/terraform-workflow-diagrams.md)
- [Terraform Capabilities](docs/terraform-capabilities.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Use Cases](docs/use-cases.md)

## Labs

Start with [Lab 01: VPC and Networking](labs/01-vpc-networking/README.md)

## License

MIT
