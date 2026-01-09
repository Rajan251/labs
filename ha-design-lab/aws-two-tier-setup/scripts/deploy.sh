#!/bin/bash

# ============================================
# Two-Tier Architecture Deployment Script
# ============================================

set -e

echo "🚀 Two-Tier Architecture Deployment Script"
echo "==========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Check prerequisites
print_info "Checking prerequisites..."

if ! command -v terraform &> /dev/null; then
    print_error "Terraform is not installed"
    exit 1
fi

if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed"
    exit 1
fi

print_success "Prerequisites check passed"
echo ""

# Navigate to Terraform directory
cd "$(dirname "$0")/../terraform/environments/dev"

# Check if terraform.tfvars exists
if [ ! -f "terraform.tfvars" ]; then
    print_error "terraform.tfvars not found"
    print_info "Copy terraform.tfvars.example to terraform.tfvars and customize it"
    exit 1
fi

# Check environment variables
if [ -z "$TF_VAR_mongodb_admin_password" ]; then
    print_error "TF_VAR_mongodb_admin_password not set"
    print_info "Set it with: export TF_VAR_mongodb_admin_password='YourPassword'"
    exit 1
fi

if [ -z "$TF_VAR_mongodb_app_password" ]; then
    print_error "TF_VAR_mongodb_app_password not set"
    print_info "Set it with: export TF_VAR_mongodb_app_password='YourPassword'"
    exit 1
fi

print_success "Environment variables set"
echo ""

# Initialize Terraform
print_info "Initializing Terraform..."
terraform init
print_success "Terraform initialized"
echo ""

# Validate configuration
print_info "Validating Terraform configuration..."
terraform validate
print_success "Configuration valid"
echo ""

# Plan deployment
print_info "Creating deployment plan..."
terraform plan -out=tfplan
print_success "Plan created"
echo ""

# Ask for confirmation
read -p "Do you want to apply this plan? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    print_info "Deployment cancelled"
    exit 0
fi

# Apply plan
print_info "Deploying infrastructure..."
terraform apply tfplan
print_success "Infrastructure deployed"
echo ""

# Get outputs
print_info "Deployment complete! Here are your outputs:"
echo ""
terraform output

# Save outputs to file
terraform output -json > ../../../deployment-outputs.json
print_success "Outputs saved to deployment-outputs.json"
echo ""

# Display next steps
echo "=========================================="
echo "🎉 Deployment Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Configure MongoDB replica set (see docs/02-DATABASE-TIER-SETUP.md)"
echo "2. Test the application:"
echo "   curl http://\$(terraform output -raw alb_dns_name)/health"
echo "3. Monitor auto-scaling in CloudWatch"
echo ""
echo "Application URL: http://$(terraform output -raw alb_dns_name)"
echo ""
