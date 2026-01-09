#!/bin/bash
# Destroy script for AWS Three-Tier Architecture

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

print_warning "This will DESTROY all resources in environment: $ENVIRONMENT"
print_warning "This action CANNOT be undone!"
echo ""

# Navigate to terraform directory
cd "$TERRAFORM_DIR"

# Show current resources
print_info "Current resources:"
terraform show

echo ""
print_warning "All the above resources will be DESTROYED"
echo ""

# Ask for confirmation
read -p "Type 'destroy' to confirm: " CONFIRM

if [ "$CONFIRM" != "destroy" ]; then
    print_info "Destruction cancelled"
    exit 0
fi

# Additional confirmation
read -p "Are you absolutely sure? Type 'yes' to proceed: " FINAL_CONFIRM

if [ "$FINAL_CONFIRM" != "yes" ]; then
    print_info "Destruction cancelled"
    exit 0
fi

# Destroy resources
print_info "Destroying infrastructure..."
terraform destroy -auto-approve

if [ $? -eq 0 ]; then
    print_info "All resources destroyed successfully"
else
    print_error "Destruction failed. Some resources may still exist."
    print_info "Check AWS Console and run 'terraform destroy' manually if needed"
    exit 1
fi

print_info "Cleanup completed"
