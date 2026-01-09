#!/bin/bash
# Deployment script for AWS Three-Tier Architecture

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if environment argument is provided
if [ -z "$1" ]; then
    print_error "Usage: $0 <environment>"
    print_info "Example: $0 dev"
    exit 1
fi

ENVIRONMENT=$1
TERRAFORM_DIR="terraform/environments/${ENVIRONMENT}"

# Check if environment directory exists
if [ ! -d "$TERRAFORM_DIR" ]; then
    print_error "Environment directory not found: $TERRAFORM_DIR"
    exit 1
fi

print_info "Starting deployment for environment: $ENVIRONMENT"

# Navigate to terraform directory
cd "$TERRAFORM_DIR"

# Check if terraform.tfvars exists
if [ ! -f "terraform.tfvars" ]; then
    print_warning "terraform.tfvars not found. Creating from example..."
    if [ -f "terraform.tfvars.example" ]; then
        cp terraform.tfvars.example terraform.tfvars
        print_warning "Please edit terraform.tfvars with your configuration before proceeding."
        print_info "Required changes:"
        print_info "  - Set your SSH key_name"
        print_info "  - Set your IP address in vpn_allowed_ips"
        print_info "  - Set your alert_email"
        exit 1
    else
        print_error "terraform.tfvars.example not found"
        exit 1
    fi
fi

# Validate prerequisites
print_info "Validating prerequisites..."

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI not found. Please install it first."
    exit 1
fi

# Check Terraform
if ! command -v terraform &> /dev/null; then
    print_error "Terraform not found. Please install it first."
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS credentials not configured. Run 'aws configure' first."
    exit 1
fi

print_info "Prerequisites validated successfully"

# Initialize Terraform
print_info "Initializing Terraform..."
terraform init

# Validate Terraform configuration
print_info "Validating Terraform configuration..."
terraform validate

if [ $? -ne 0 ]; then
    print_error "Terraform validation failed"
    exit 1
fi

print_info "Terraform configuration is valid"

# Format Terraform files
print_info "Formatting Terraform files..."
terraform fmt -recursive

# Generate and show plan
print_info "Generating Terraform plan..."
terraform plan -out=tfplan

# Ask for confirmation
echo ""
print_warning "Review the plan above carefully."
read -p "Do you want to apply this plan? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    print_info "Deployment cancelled"
    rm -f tfplan
    exit 0
fi

# Apply the plan
print_info "Applying Terraform plan..."
terraform apply tfplan

if [ $? -eq 0 ]; then
    print_info "Deployment completed successfully!"
    echo ""
    print_info "Getting outputs..."
    terraform output
    echo ""
    print_info "Next steps:"
    print_info "  1. Connect to VPN server: ssh -i ~/.ssh/your-key.pem ec2-user@\$(terraform output -raw vpn_server_ip)"
    print_info "  2. Access application: \$(terraform output -raw application_url)"
    print_info "  3. CloudFront URL: \$(terraform output -raw cloudfront_url)"
    print_info "  4. Upload static content: aws s3 sync ./static s3://\$(terraform output -raw s3_bucket_name)/"
else
    print_error "Deployment failed"
    exit 1
fi

# Cleanup
rm -f tfplan

print_info "Deployment script completed"
