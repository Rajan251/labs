#!/bin/bash

# ============================================
# Infrastructure Cleanup Script
# ============================================

set -e

echo "🗑️  Two-Tier Architecture Cleanup"
echo "================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Warning
print_warning "This will destroy ALL infrastructure created by Terraform"
print_warning "This action CANNOT be undone!"
echo ""

# Confirmation
read -p "Are you sure you want to destroy everything? Type 'destroy' to confirm: " confirm
if [ "$confirm" != "destroy" ]; then
    print_info "Cleanup cancelled"
    exit 0
fi

# Navigate to Terraform directory
cd "$(dirname "$0")/../terraform/environments/dev"

# Destroy infrastructure
print_info "Destroying infrastructure..."
terraform destroy

print_success "Infrastructure destroyed"
echo ""

# Clean up local files
print_info "Cleaning up local files..."
rm -f tfplan
rm -f ../../../deployment-outputs.json
rm -f /tmp/init-replica-set.js

print_success "Cleanup complete"
