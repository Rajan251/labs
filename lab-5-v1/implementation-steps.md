## 4. Detailed Implementation Steps

### Phase 1: Networking Setup

#### Step 1.1: AWS VPC and Transit Gateway Configuration

**Objective:** Create isolated network environments with cross-region and cross-cloud connectivity.

**AWS Primary Region (us-east-1):**

```bash
# Create VPC
aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=prod-vpc-us-east-1}]' \
  --region us-east-1

# Create subnets (Multi-AZ)
# Public Subnet AZ-1
aws ec2 create-subnet \
  --vpc-id vpc-xxxxx \
  --cidr-block 10.0.1.0/24 \
  --availability-zone us-east-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=public-subnet-1a}]'

# Public Subnet AZ-2
aws ec2 create-subnet \
  --vpc-id vpc-xxxxx \
  --cidr-block 10.0.2.0/24 \
  --availability-zone us-east-1b \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=public-subnet-1b}]'

# Private Subnet AZ-1
aws ec2 create-subnet \
  --vpc-id vpc-xxxxx \
  --cidr-block 10.0.10.0/24 \
  --availability-zone us-east-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=private-subnet-1a}]'

# Private Subnet AZ-2
aws ec2 create-subnet \
  --vpc-id vpc-xxxxx \
  --cidr-block 10.0.11.0/24 \
  --availability-zone us-east-1b \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=private-subnet-1b}]'

# Database Subnet AZ-1
aws ec2 create-subnet \
  --vpc-id vpc-xxxxx \
  --cidr-block 10.0.20.0/24 \
  --availability-zone us-east-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=db-subnet-1a}]'

# Database Subnet AZ-2
aws ec2 create-subnet \
  --vpc-id vpc-xxxxx \
  --cidr-block 10.0.21.0/24 \
  --availability-zone us-east-1b \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=db-subnet-1b}]'

# Create Internet Gateway
aws ec2 create-internet-gateway \
  --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=prod-igw}]'

aws ec2 attach-internet-gateway \
  --vpc-id vpc-xxxxx \
  --internet-gateway-id igw-xxxxx

# Create NAT Gateways (one per AZ for HA)
aws ec2 allocate-address --domain vpc
aws ec2 create-nat-gateway \
  --subnet-id subnet-public-1a \
  --allocation-id eipalloc-xxxxx \
  --tag-specifications 'ResourceType=nat-gateway,Tags=[{Key=Name,Value=nat-gw-1a}]'

# Create Transit Gateway
aws ec2 create-transit-gateway \
  --description "Multi-cloud transit gateway" \
  --options "AmazonSideAsn=64512,AutoAcceptSharedAttachments=enable,DefaultRouteTableAssociation=enable,DefaultRouteTablePropagation=enable,DnsSupport=enable,VpnEcmpSupport=enable" \
  --tag-specifications 'ResourceType=transit-gateway,Tags=[{Key=Name,Value=prod-tgw}]'

# Attach VPC to Transit Gateway
aws ec2 create-transit-gateway-vpc-attachment \
  --transit-gateway-id tgw-xxxxx \
  --vpc-id vpc-xxxxx \
  --subnet-ids subnet-private-1a subnet-private-1b
```

**Terraform Alternative (Recommended):**

```hcl
# terraform/aws/networking/main.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    bucket         = "terraform-state-prod"
    key            = "networking/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.primary_region
  alias  = "primary"
}

provider "aws" {
  region = var.secondary_region
  alias  = "secondary"
}

module "vpc_primary" {
  source = "terraform-aws-modules/vpc/aws"
  version = "5.1.2"

  name = "prod-vpc-${var.primary_region}"
  cidr = "10.0.0.0/16"

  azs              = ["${var.primary_region}a", "${var.primary_region}b", "${var.primary_region}c"]
  public_subnets   = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  private_subnets  = ["10.0.10.0/24", "10.0.11.0/24", "10.0.12.0/24"]
  database_subnets = ["10.0.20.0/24", "10.0.21.0/24", "10.0.22.0/24"]

  enable_nat_gateway   = true
  enable_vpn_gateway   = false
  enable_dns_hostnames = true
  enable_dns_support   = true

  # One NAT Gateway per AZ for HA
  single_nat_gateway = false
  one_nat_gateway_per_az = true

  # Enable VPC Flow Logs
  enable_flow_log                      = true
  create_flow_log_cloudwatch_iam_role  = true
  create_flow_log_cloudwatch_log_group = true

  tags = {
    Environment = "production"
    Terraform   = "true"
    DR_Tier     = "primary"
  }
}

resource "aws_ec2_transit_gateway" "main" {
  description                     = "Multi-cloud transit gateway"
  amazon_side_asn                 = 64512
  auto_accept_shared_attachments  = "enable"
  default_route_table_association = "enable"
  default_route_table_propagation = "enable"
  dns_support                     = "enable"
  vpn_ecmp_support               = "enable"

  tags = {
    Name = "prod-tgw"
  }
}

resource "aws_ec2_transit_gateway_vpc_attachment" "primary" {
  subnet_ids         = module.vpc_primary.private_subnets
  transit_gateway_id = aws_ec2_transit_gateway.main.id
  vpc_id             = module.vpc_primary.vpc_id

  tags = {
    Name = "tgw-attachment-primary"
  }
}
```

#### Step 1.2: Azure VNet and VPN Gateway Configuration

```bash
# Create Resource Group
az group create \
  --name prod-rg-eastus \
  --location eastus

# Create VNet
az network vnet create \
  --resource-group prod-rg-eastus \
  --name prod-vnet-eastus \
  --address-prefix 10.1.0.0/16 \
  --location eastus

# Create Subnets
az network vnet subnet create \
  --resource-group prod-rg-eastus \
  --vnet-name prod-vnet-eastus \
  --name frontend-subnet \
  --address-prefixes 10.1.1.0/24

az network vnet subnet create \
  --resource-group prod-rg-eastus \
  --vnet-name prod-vnet-eastus \
  --name backend-subnet \
  --address-prefixes 10.1.10.0/24

az network vnet subnet create \
  --resource-group prod-rg-eastus \
  --vnet-name prod-vnet-eastus \
  --name database-subnet \
  --address-prefixes 10.1.20.0/24

# Create Gateway Subnet (required for VPN Gateway)
az network vnet subnet create \
  --resource-group prod-rg-eastus \
  --vnet-name prod-vnet-eastus \
  --name GatewaySubnet \
  --address-prefixes 10.1.255.0/27

# Create Public IP for VPN Gateway
az network public-ip create \
  --resource-group prod-rg-eastus \
  --name vpn-gateway-pip \
  --allocation-method Static \
  --sku Standard

# Create VPN Gateway (takes 30-45 minutes)
az network vnet-gateway create \
  --resource-group prod-rg-eastus \
  --name prod-vpn-gateway \
  --public-ip-address vpn-gateway-pip \
  --vnet prod-vnet-eastus \
  --gateway-type Vpn \
  --vpn-type RouteBased \
  --sku VpnGw2 \
  --no-wait
```

**Terraform for Azure:**

```hcl
# terraform/azure/networking/main.tf
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "main" {
  name     = "prod-rg-${var.azure_region}"
  location = var.azure_region
}

resource "azurerm_virtual_network" "main" {
  name                = "prod-vnet-${var.azure_region}"
  address_space       = ["10.1.0.0/16"]
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  tags = {
    Environment = "production"
    DR_Tier     = "secondary"
  }
}

resource "azurerm_subnet" "frontend" {
  name                 = "frontend-subnet"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.1.1.0/24"]
}

resource "azurerm_subnet" "backend" {
  name                 = "backend-subnet"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.1.10.0/24"]
}

resource "azurerm_subnet" "database" {
  name                 = "database-subnet"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.1.20.0/24"]
  
  delegation {
    name = "sql-delegation"
    service_delegation {
      name = "Microsoft.Sql/managedInstances"
      actions = [
        "Microsoft.Network/virtualNetworks/subnets/join/action",
        "Microsoft.Network/virtualNetworks/subnets/prepareNetworkPolicies/action",
      ]
    }
  }
}

resource "azurerm_subnet" "gateway" {
  name                 = "GatewaySubnet"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.1.255.0/27"]
}

resource "azurerm_public_ip" "vpn_gateway" {
  name                = "vpn-gateway-pip"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  allocation_method   = "Static"
  sku                 = "Standard"
}

resource "azurerm_virtual_network_gateway" "vpn" {
  name                = "prod-vpn-gateway"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  type     = "Vpn"
  vpn_type = "RouteBased"

  active_active = false
  enable_bgp    = true
  sku           = "VpnGw2"

  ip_configuration {
    name                          = "vnetGatewayConfig"
    public_ip_address_id          = azurerm_public_ip.vpn_gateway.id
    private_ip_address_allocation = "Dynamic"
    subnet_id                     = azurerm_subnet.gateway.id
  }

  bgp_settings {
    asn = 65515
  }
}
```

#### Step 1.3: GCP VPC and Cloud Interconnect Configuration

```bash
# Create VPC
gcloud compute networks create prod-vpc \
  --subnet-mode=custom \
  --bgp-routing-mode=global

# Create Subnets
gcloud compute networks subnets create public-subnet \
  --network=prod-vpc \
  --region=us-central1 \
  --range=10.2.1.0/24

gcloud compute networks subnets create private-subnet \
  --network=prod-vpc \
  --region=us-central1 \
  --range=10.2.10.0/24 \
  --enable-private-ip-google-access

gcloud compute networks subnets create db-subnet \
  --network=prod-vpc \
  --region=us-central1 \
  --range=10.2.20.0/24 \
  --enable-private-ip-google-access

# Create Cloud Router
gcloud compute routers create prod-router \
  --network=prod-vpc \
  --region=us-central1 \
  --asn=64513

# Create Cloud NAT
gcloud compute routers nats create prod-nat \
  --router=prod-router \
  --region=us-central1 \
  --nat-all-subnet-ip-ranges \
  --auto-allocate-nat-external-ips

# Create VPN Gateway for AWS connectivity
gcloud compute vpn-gateways create aws-vpn-gateway \
  --network=prod-vpc \
  --region=us-central1

# Create VPN Gateway for Azure connectivity
gcloud compute vpn-gateways create azure-vpn-gateway \
  --network=prod-vpc \
  --region=us-central1
```

**Terraform for GCP:**

```hcl
# terraform/gcp/networking/main.tf
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.gcp_region
}

resource "google_compute_network" "main" {
  name                    = "prod-vpc"
  auto_create_subnetworks = false
  routing_mode            = "GLOBAL"
}

resource "google_compute_subnetwork" "public" {
  name          = "public-subnet"
  ip_cidr_range = "10.2.1.0/24"
  region        = var.gcp_region
  network       = google_compute_network.main.id

  log_config {
    aggregation_interval = "INTERVAL_10_MIN"
    flow_sampling        = 0.5
    metadata             = "INCLUDE_ALL_METADATA"
  }
}

resource "google_compute_subnetwork" "private" {
  name          = "private-subnet"
  ip_cidr_range = "10.2.10.0/24"
  region        = var.gcp_region
  network       = google_compute_network.main.id

  private_ip_google_access = true

  log_config {
    aggregation_interval = "INTERVAL_10_MIN"
    flow_sampling        = 0.5
    metadata             = "INCLUDE_ALL_METADATA"
  }
}

resource "google_compute_subnetwork" "database" {
  name          = "db-subnet"
  ip_cidr_range = "10.2.20.0/24"
  region        = var.gcp_region
  network       = google_compute_network.main.id

  private_ip_google_access = true
}

resource "google_compute_router" "main" {
  name    = "prod-router"
  region  = var.gcp_region
  network = google_compute_network.main.id

  bgp {
    asn = 64513
  }
}

resource "google_compute_router_nat" "main" {
  name                               = "prod-nat"
  router                             = google_compute_router.main.name
  region                             = google_compute_router.main.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}
```

#### Step 1.4: Cross-Cloud VPN Connectivity

**AWS to Azure VPN Connection:**

```bash
# On AWS side - Create Customer Gateway (Azure VPN Gateway IP)
aws ec2 create-customer-gateway \
  --type ipsec.1 \
  --public-ip <AZURE_VPN_GATEWAY_IP> \
  --bgp-asn 65515 \
  --tag-specifications 'ResourceType=customer-gateway,Tags=[{Key=Name,Value=azure-cgw}]'

# Create VPN Connection
aws ec2 create-vpn-connection \
  --type ipsec.1 \
  --customer-gateway-id cgw-xxxxx \
  --transit-gateway-id tgw-xxxxx \
  --options TunnelOptions='[{TunnelInsideCidr=169.254.21.0/30,PreSharedKey=MySecureKey123},{TunnelInsideCidr=169.254.22.0/30,PreSharedKey=MySecureKey456}]'

# On Azure side - Create Local Network Gateway (AWS endpoint)
az network local-gateway create \
  --resource-group prod-rg-eastus \
  --name aws-local-gateway \
  --gateway-ip-address <AWS_VPN_ENDPOINT_IP> \
  --local-address-prefixes 10.0.0.0/16

# Create VPN Connection
az network vpn-connection create \
  --resource-group prod-rg-eastus \
  --name azure-to-aws-vpn \
  --vnet-gateway1 prod-vpn-gateway \
  --local-gateway2 aws-local-gateway \
  --shared-key MySecureKey123 \
  --connection-protocol IKEv2
```

**AWS to GCP VPN Connection:**

```bash
# On GCP side - Create VPN tunnels to AWS
gcloud compute vpn-tunnels create aws-tunnel-1 \
  --peer-address=<AWS_VPN_ENDPOINT_1_IP> \
  --shared-secret=MySecureKey789 \
  --ike-version=2 \
  --vpn-gateway=aws-vpn-gateway \
  --interface=0 \
  --region=us-central1

gcloud compute vpn-tunnels create aws-tunnel-2 \
  --peer-address=<AWS_VPN_ENDPOINT_2_IP> \
  --shared-secret=MySecureKey012 \
  --ike-version=2 \
  --vpn-gateway=aws-vpn-gateway \
  --interface=1 \
  --region=us-central1

# Create BGP sessions
gcloud compute routers add-bgp-peer prod-router \
  --peer-name=aws-peer-1 \
  --peer-asn=64512 \
  --interface=aws-tunnel-1-interface \
  --region=us-central1
```

**Complete Multi-Cloud Networking Terraform Module:**

```hcl
# terraform/multi-cloud-networking/main.tf
module "aws_networking" {
  source = "./modules/aws"
  
  primary_region   = "us-east-1"
  secondary_region = "us-west-2"
  vpc_cidr         = "10.0.0.0/16"
}

module "azure_networking" {
  source = "./modules/azure"
  
  azure_region = "eastus"
  vnet_cidr    = "10.1.0.0/16"
}

module "gcp_networking" {
  source = "./modules/gcp"
  
  project_id = var.gcp_project_id
  gcp_region = "us-central1"
  vpc_cidr   = "10.2.0.0/16"
}

module "cross_cloud_vpn" {
  source = "./modules/vpn"
  
  aws_transit_gateway_id = module.aws_networking.transit_gateway_id
  azure_vpn_gateway_id   = module.azure_networking.vpn_gateway_id
  gcp_vpn_gateway_id     = module.gcp_networking.vpn_gateway_id
  
  shared_secrets = {
    aws_azure = var.aws_azure_vpn_key
    aws_gcp   = var.aws_gcp_vpn_key
    azure_gcp = var.azure_gcp_vpn_key
  }
}
```

---

### Phase 2: Data Synchronization

#### Step 2.1: Object Storage Replication (S3 ↔ Azure Blob ↔ GCS)

**AWS S3 Cross-Region Replication:**

```bash
# Enable versioning (required for CRR)
aws s3api put-bucket-versioning \
  --bucket prod-app-data-us-east-1 \
  --versioning-configuration Status=Enabled

# Create replication role
cat > s3-replication-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Service": "s3.amazonaws.com"
    },
    "Action": "sts:AssumeRole"
  }]
}
EOF

aws iam create-role \
  --role-name S3ReplicationRole \
  --assume-role-policy-document file://s3-replication-policy.json

# Attach replication policy
cat > s3-replication-permissions.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "s3:GetReplicationConfiguration",
      "s3:ListBucket"
    ],
    "Resource": "arn:aws:s3:::prod-app-data-us-east-1"
  }, {
    "Effect": "Allow",
    "Action": [
      "s3:GetObjectVersionForReplication",
      "s3:GetObjectVersionAcl"
    ],
    "Resource": "arn:aws:s3:::prod-app-data-us-east-1/*"
  }, {
    "Effect": "Allow",
    "Action": [
      "s3:ReplicateObject",
      "s3:ReplicateDelete"
    ],
    "Resource": "arn:aws:s3:::prod-app-data-us-west-2/*"
  }]
}
EOF

aws iam put-role-policy \
  --role-name S3ReplicationRole \
  --policy-name S3ReplicationPolicy \
  --policy-document file://s3-replication-permissions.json

# Configure replication
cat > replication-config.json <<EOF
{
  "Role": "arn:aws:iam::ACCOUNT_ID:role/S3ReplicationRole",
  "Rules": [{
    "Status": "Enabled",
    "Priority": 1,
    "DeleteMarkerReplication": { "Status": "Enabled" },
    "Filter": {},
    "Destination": {
      "Bucket": "arn:aws:s3:::prod-app-data-us-west-2",
      "ReplicationTime": {
        "Status": "Enabled",
        "Time": {
          "Minutes": 15
        }
      },
      "Metrics": {
        "Status": "Enabled",
        "EventThreshold": {
          "Minutes": 15
        }
      }
    }
  }]
}
EOF

aws s3api put-bucket-replication \
  --bucket prod-app-data-us-east-1 \
  --replication-configuration file://replication-config.json
```

**S3 to Azure Blob Sync using AWS DataSync:**

```bash
# Create DataSync location for S3
aws datasync create-location-s3 \
  --s3-bucket-arn arn:aws:s3:::prod-app-data-us-east-1 \
  --s3-config '{
    "BucketAccessRoleArn": "arn:aws:iam::ACCOUNT_ID:role/DataSyncS3Role"
  }' \
  --region us-east-1

# Create DataSync agent (EC2 instance or on-premises)
# Download and deploy DataSync agent AMI

# Create DataSync location for Azure Blob (via SMB/NFS)
aws datasync create-location-smb \
  --server-hostname azure-blob-endpoint.blob.core.windows.net \
  --subdirectory /container-name \
  --user azure-storage-account \
  --password <AZURE_STORAGE_KEY> \
  --agent-arns arn:aws:datasync:us-east-1:ACCOUNT_ID:agent/agent-xxxxx

# Create DataSync task
aws datasync create-task \
  --source-location-arn arn:aws:datasync:us-east-1:ACCOUNT_ID:location/loc-xxxxx \
  --destination-location-arn arn:aws:datasync:us-east-1:ACCOUNT_ID:location/loc-yyyyy \
  --cloud-watch-log-group-arn arn:aws:logs:us-east-1:ACCOUNT_ID:log-group:/aws/datasync \
  --name s3-to-azure-sync \
  --options '{
    "VerifyMode": "ONLY_FILES_TRANSFERRED",
    "OverwriteMode": "ALWAYS",
    "TransferMode": "CHANGED",
    "TaskQueueing": "ENABLED"
  }' \
  --schedule '{
    "ScheduleExpression": "rate(15 minutes)"
  }'
```

**Rclone for Multi-Cloud Sync (Alternative Approach):**

```bash
# Install Rclone
curl https://rclone.org/install.sh | sudo bash

# Configure Rclone
cat > ~/.config/rclone/rclone.conf <<EOF
[aws-s3]
type = s3
provider = AWS
env_auth = false
access_key_id = YOUR_AWS_ACCESS_KEY
secret_access_key = YOUR_AWS_SECRET_KEY
region = us-east-1

[azure-blob]
type = azureblob
account = yourstorageaccount
key = YOUR_AZURE_STORAGE_KEY

[gcp-gcs]
type = google cloud storage
project_number = YOUR_PROJECT_NUMBER
service_account_file = /path/to/service-account.json
location = us-central1
EOF

# Sync S3 to Azure Blob
rclone sync aws-s3:prod-app-data-us-east-1 azure-blob:prod-container \
  --transfers 32 \
  --checkers 16 \
  --fast-list \
  --update \
  --use-server-modtime \
  --log-file /var/log/rclone-s3-azure.log \
  --log-level INFO

# Sync Azure Blob to GCS
rclone sync azure-blob:prod-container gcp-gcs:prod-bucket \
  --transfers 32 \
  --checkers 16 \
  --fast-list \
  --update \
  --log-file /var/log/rclone-azure-gcp.log

# Create systemd service for continuous sync
cat > /etc/systemd/system/rclone-sync.service <<EOF
[Unit]
Description=Rclone Multi-Cloud Sync
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/rclone sync aws-s3:prod-app-data-us-east-1 azure-blob:prod-container --transfers 32 --checkers 16 --fast-list --update
Restart=on-failure
RestartSec=300

[Install]
WantedBy=multi-user.target
EOF

systemctl enable rclone-sync.service
systemctl start rclone-sync.service
```

#### Step 2.2: Database Replication (RDS ↔ Azure SQL ↔ Cloud SQL)

**AWS RDS PostgreSQL Cross-Region Read Replica:**

```bash
# Create cross-region read replica
aws rds create-db-instance-read-replica \
  --db-instance-identifier prod-db-replica-us-west-2 \
  --source-db-instance-identifier prod-db-us-east-1 \
  --db-instance-class db.r6g.xlarge \
  --availability-zone us-west-2a \
  --publicly-accessible false \
  --multi-az false \
  --storage-encrypted \
  --kms-key-id arn:aws:kms:us-west-2:ACCOUNT_ID:key/xxxxx \
  --region us-west-2

# Enable automated backups
aws rds modify-db-instance \
  --db-instance-identifier prod-db-replica-us-west-2 \
  --backup-retention-period 7 \
  --preferred-backup-window "03:00-04:00" \
  --apply-immediately
```

**PostgreSQL Logical Replication to Azure:**

```sql
-- On AWS RDS (Primary)
-- Enable logical replication
ALTER SYSTEM SET wal_level = 'logical';
ALTER SYSTEM SET max_replication_slots = 10;
ALTER SYSTEM SET max_wal_senders = 10;

-- Restart database (via AWS Console or CLI)

-- Create publication
CREATE PUBLICATION azure_replication FOR ALL TABLES;

-- Create replication user
CREATE USER repl_user WITH REPLICATION PASSWORD 'SecurePassword123';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO repl_user;
GRANT USAGE ON SCHEMA public TO repl_user;

-- On Azure PostgreSQL (Secondary)
-- Create subscription
CREATE SUBSCRIPTION azure_subscription
  CONNECTION 'host=prod-db-us-east-1.xxxxx.rds.amazonaws.com port=5432 dbname=proddb user=repl_user password=SecurePassword123 sslmode=require'
  PUBLICATION azure_replication
  WITH (copy_data = true, create_slot = true, enabled = true);

-- Monitor replication lag
SELECT 
  subscription_name,
  received_lsn,
  latest_end_lsn,
  pg_size_pretty(pg_wal_lsn_diff(latest_end_lsn, received_lsn)) AS replication_lag
FROM pg_stat_subscription;
```

**Database Migration Service (DMS) for Continuous Replication:**

```bash
# Create replication instance
aws dms create-replication-instance \
  --replication-instance-identifier prod-dms-instance \
  --replication-instance-class dms.c5.2xlarge \
  --allocated-storage 100 \
  --vpc-security-group-ids sg-xxxxx \
  --replication-subnet-group-identifier default \
  --multi-az \
  --engine-version 3.4.7 \
  --publicly-accessible false

# Create source endpoint (AWS RDS)
aws dms create-endpoint \
  --endpoint-identifier rds-source \
  --endpoint-type source \
  --engine-name postgres \
  --server-name prod-db-us-east-1.xxxxx.rds.amazonaws.com \
  --port 5432 \
  --database-name proddb \
  --username admin \
  --password SecurePassword123 \
  --ssl-mode require

# Create target endpoint (Azure PostgreSQL)
aws dms create-endpoint \
  --endpoint-identifier azure-target \
  --endpoint-type target \
  --engine-name postgres \
  --server-name prod-db-azure.postgres.database.azure.com \
  --port 5432 \
  --database-name proddb \
  --username admin@prod-db-azure \
  --password SecurePassword456 \
  --ssl-mode require

# Create replication task
aws dms create-replication-task \
  --replication-task-identifier rds-to-azure-replication \
  --source-endpoint-arn arn:aws:dms:us-east-1:ACCOUNT_ID:endpoint:rds-source \
  --target-endpoint-arn arn:aws:dms:us-east-1:ACCOUNT_ID:endpoint:azure-target \
  --replication-instance-arn arn:aws:dms:us-east-1:ACCOUNT_ID:rep:prod-dms-instance \
  --migration-type full-load-and-cdc \
  --table-mappings file://table-mappings.json \
  --replication-task-settings file://task-settings.json

# table-mappings.json
cat > table-mappings.json <<EOF
{
  "rules": [{
    "rule-type": "selection",
    "rule-id": "1",
    "rule-name": "replicate-all-tables",
    "object-locator": {
      "schema-name": "public",
      "table-name": "%"
    },
    "rule-action": "include"
  }]
}
EOF

# Start replication task
aws dms start-replication-task \
  --replication-task-arn arn:aws:dms:us-east-1:ACCOUNT_ID:task:rds-to-azure-replication \
  --start-replication-task-type start-replication
```

