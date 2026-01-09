# Quick Start Guide

Get your AWS three-tier architecture up and running in under 30 minutes!

## Prerequisites Checklist

Before you begin, ensure you have:

- [ ] AWS Account with administrative access
- [ ] AWS CLI installed and configured
- [ ] Terraform >= 1.0 installed
- [ ] SSH key pair created in your AWS region
- [ ] (Optional) Domain name for Route 53
- [ ] (Optional) SSL certificate in ACM

## Installation Steps

### Step 1: Install Required Tools

```bash
# Install AWS CLI (if not already installed)
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Install Terraform (if not already installed)
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/

# Verify installations
aws --version
terraform --version
```

### Step 2: Configure AWS Credentials

```bash
# Configure AWS CLI
aws configure

# Enter your credentials when prompted:
# AWS Access Key ID: YOUR_ACCESS_KEY
# AWS Secret Access Key: YOUR_SECRET_KEY
# Default region name: us-east-1
# Default output format: json
```

### Step 3: Create SSH Key Pair

```bash
# Create key pair in AWS
aws ec2 create-key-pair \
  --key-name three-tier-key \
  --query 'KeyMaterial' \
  --output text > ~/.ssh/three-tier-key.pem

# Set permissions
chmod 400 ~/.ssh/three-tier-key.pem
```

### Step 4: Clone and Configure Project

```bash
# Navigate to project directory
cd /home/rk/Documents/labs/ha-design-lab/aws-three-tier-cloudfront

# Navigate to dev environment
cd terraform/environments/dev

# Create terraform.tfvars from example
cat > terraform.tfvars <<EOF
# Project Configuration
project_name = "three-tier-app"
environment  = "dev"
region       = "us-east-1"

# Network Configuration
vpc_cidr           = "10.0.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b"]

# Compute Configuration
key_name          = "three-tier-key"
app_instance_type = "t3.medium"
db_instance_type  = "t3.large"
vpn_instance_type = "t3.small"

# Auto Scaling Configuration
app_min_size = 2
app_max_size = 6
app_desired  = 2
db_min_size  = 2
db_max_size  = 4
db_desired   = 2

# Monitoring Configuration
alert_email = "your-email@example.com"

# Domain Configuration (optional)
# domain_name = "example.com"
# create_route53_zone = true
EOF

# Edit the file with your specific values
nano terraform.tfvars
```

### Step 5: Deploy Infrastructure

```bash
# Initialize Terraform
terraform init

# Validate configuration
terraform validate

# Review the execution plan
terraform plan

# Apply the configuration
terraform apply

# Type 'yes' when prompted
```

**Expected deployment time**: 10-15 minutes

### Step 6: Verify Deployment

```bash
# Get outputs
terraform output

# Example outputs:
# alb_dns_name = "three-tier-alb-123456789.us-east-1.elb.amazonaws.com"
# cloudfront_domain = "d1234567890abc.cloudfront.net"
# vpn_server_ip = "54.123.45.67"
# s3_bucket_name = "three-tier-app-dev-static-content"
```

### Step 7: Test the Infrastructure

```bash
# Test ALB endpoint
curl http://$(terraform output -raw alb_dns_name)

# Test CloudFront endpoint (may take 15-20 minutes for distribution to deploy)
curl https://$(terraform output -raw cloudfront_domain)

# Connect to VPN (OpenVPN example)
# Download VPN configuration from VPN server first
sudo openvpn --config client.ovpn
```

## Quick Deployment Script

For even faster deployment, use the automated script:

```bash
# From project root
./scripts/deploy.sh dev

# This script will:
# 1. Validate prerequisites
# 2. Initialize Terraform
# 3. Deploy infrastructure
# 4. Run health checks
# 5. Display outputs
```

## Post-Deployment Configuration

### 1. Configure Application Servers

```bash
# Connect via VPN first
ssh -i ~/.ssh/three-tier-key.pem ec2-user@<app-server-private-ip>

# Deploy your application
# Example for Node.js app:
git clone https://github.com/your-org/your-app.git
cd your-app
npm install
npm start
```

### 2. Configure Database Servers

```bash
# Connect via VPN
ssh -i ~/.ssh/three-tier-key.pem ec2-user@<db-server-private-ip>

# Initialize MongoDB replica set (example)
mongosh
rs.initiate({
  _id: "rs0",
  members: [
    { _id: 0, host: "10.0.21.10:27017" },
    { _id: 1, host: "10.0.22.10:27017" }
  ]
})
```

### 3. Upload Static Content to S3

```bash
# Sync local files to S3
aws s3 sync ./static-content s3://$(terraform output -raw s3_bucket_name)/

# Verify upload
aws s3 ls s3://$(terraform output -raw s3_bucket_name)/
```

### 4. Configure Route 53 (if using custom domain)

```bash
# Get CloudFront domain
CLOUDFRONT_DOMAIN=$(terraform output -raw cloudfront_domain)

# Create CNAME record (or use AWS Console)
aws route53 change-resource-record-sets \
  --hosted-zone-id YOUR_ZONE_ID \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "www.example.com",
        "Type": "CNAME",
        "TTL": 300,
        "ResourceRecords": [{"Value": "'$CLOUDFRONT_DOMAIN'"}]
      }
    }]
  }'
```

## Verification Checklist

After deployment, verify:

- [ ] ALB is healthy and responding
- [ ] Application servers are registered with ALB
- [ ] Database servers are running and accessible
- [ ] CloudFront distribution is deployed
- [ ] S3 bucket is accessible via CloudFront
- [ ] VPN connection works
- [ ] CloudWatch dashboards show metrics
- [ ] SNS notifications are configured
- [ ] Auto Scaling groups are active

## Common Issues & Quick Fixes

### Issue: Terraform apply fails with "InvalidKeyPair.NotFound"

**Solution**:
```bash
# Verify key pair exists
aws ec2 describe-key-pairs --key-names three-tier-key

# If not, create it
aws ec2 create-key-pair --key-name three-tier-key \
  --query 'KeyMaterial' --output text > ~/.ssh/three-tier-key.pem
chmod 400 ~/.ssh/three-tier-key.pem
```

### Issue: ALB health checks failing

**Solution**:
```bash
# Check security group rules
aws ec2 describe-security-groups --group-ids <app-sg-id>

# Verify application is running on correct port
ssh -i ~/.ssh/three-tier-key.pem ec2-user@<app-server-ip>
sudo netstat -tlnp | grep <app-port>
```

### Issue: CloudFront returns 403 errors

**Solution**:
```bash
# Verify S3 bucket policy allows CloudFront OAI
aws s3api get-bucket-policy --bucket <bucket-name>

# Check CloudFront origin settings in AWS Console
```

### Issue: Cannot connect to VPN

**Solution**:
```bash
# Verify VPN server security group allows your IP
aws ec2 describe-security-groups --group-ids <vpn-sg-id>

# Check VPN server is running
aws ec2 describe-instances --instance-ids <vpn-instance-id>

# Verify VPN service is running
ssh -i ~/.ssh/three-tier-key.pem ec2-user@<vpn-public-ip>
sudo systemctl status openvpn
```

## Scaling Your Infrastructure

### Increase Application Capacity

```bash
# Edit terraform.tfvars
app_max_size = 10
app_desired  = 4

# Apply changes
terraform apply
```

### Add More Availability Zones

```bash
# Edit terraform.tfvars
availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]

# Apply changes
terraform apply
```

## Monitoring & Alerts

### View CloudWatch Dashboard

```bash
# Get dashboard URL from outputs
terraform output cloudwatch_dashboard_url

# Or open in AWS Console
aws cloudwatch list-dashboards
```

### Test SNS Notifications

```bash
# Trigger a test alarm
aws cloudwatch set-alarm-state \
  --alarm-name "three-tier-app-dev-high-cpu" \
  --state-value ALARM \
  --state-reason "Testing notification"
```

## Cleanup

When you're done testing:

```bash
# Destroy all resources
terraform destroy

# Type 'yes' when prompted

# Or use the cleanup script
./scripts/destroy.sh dev
```

**Warning**: This will delete all resources including data. Make sure to backup any important data first!

## Next Steps

1. **Security Hardening**: Review [Security Groups](docs/04-SECURITY-GROUPS.md) and [NACLs](docs/05-NACLS.md)
2. **Monitoring Setup**: Configure [CloudWatch](docs/13-CLOUDWATCH.md) dashboards and alarms
3. **Application Deployment**: Deploy your application to the servers
4. **Database Configuration**: Set up replication and backups
5. **Performance Testing**: Load test your infrastructure
6. **Documentation**: Document your specific configuration

## Getting Help

- **Troubleshooting**: See [Troubleshooting Guide](docs/99-TROUBLESHOOTING.md)
- **Architecture Details**: Read [Architecture Documentation](ARCHITECTURE.md)
- **Component Guides**: Check individual guides in `docs/` directory

## Estimated Costs

For development environment:
- **Minimal usage**: ~$390/month
- **Moderate usage**: ~$600/month
- **High usage**: ~$925/month

> **Tip**: Use AWS Cost Explorer to monitor actual costs and set up billing alerts.

---

**Ready to deploy?** Start with Step 1 above! 🚀
