#!/bin/bash

# ============================================================================
# Terraform + Ansible Cleanup Script
# ============================================================================
# This script destroys all infrastructure created by Terraform
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TERRAFORM_DIR="$PROJECT_ROOT/terraform"
ANSIBLE_DIR="$PROJECT_ROOT/ansible"

# Functions
print_header() {
    echo -e "${BLUE}============================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================================${NC}"
}

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
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Confirm destruction
confirm_destruction() {
    print_header "⚠️  WARNING: Infrastructure Destruction"
    
    echo ""
    print_warning "This will DESTROY all infrastructure created by Terraform!"
    print_warning "This action CANNOT be undone!"
    echo ""
    
    cd "$TERRAFORM_DIR"
    
    # Show what will be destroyed
    print_info "Resources that will be destroyed:"
    terraform show -no-color | grep -E "^resource|^  id" || true
    echo ""
    
    read -p "Are you sure you want to destroy all infrastructure? (type 'yes' to confirm): " confirmation
    
    if [ "$confirmation" != "yes" ]; then
        print_info "Destruction cancelled"
        exit 0
    fi
}

# Destroy infrastructure
destroy_infrastructure() {
    print_header "Destroying Infrastructure"
    
    cd "$TERRAFORM_DIR"
    
    print_info "Running terraform destroy..."
    terraform destroy -auto-approve
    
    print_success "Infrastructure destroyed successfully"
}

# Cleanup generated files
cleanup_files() {
    print_header "Cleaning Up Generated Files"
    
    # Remove Ansible inventory
    if [ -f "$ANSIBLE_DIR/inventory/hosts.ini" ]; then
        print_info "Removing Ansible inventory..."
        rm -f "$ANSIBLE_DIR/inventory/hosts.ini"
        print_success "Ansible inventory removed"
    fi
    
    # Remove Terraform state backup files
    if [ -f "$TERRAFORM_DIR/terraform.tfstate.backup" ]; then
        print_info "Removing Terraform state backup..."
        rm -f "$TERRAFORM_DIR/terraform.tfstate.backup"
        print_success "Terraform state backup removed"
    fi
    
    # Remove plan files
    if [ -f "$TERRAFORM_DIR/tfplan" ]; then
        rm -f "$TERRAFORM_DIR/tfplan"
    fi
}

# Main function
main() {
    print_header "Terraform + Ansible Cleanup"
    echo ""
    
    confirm_destruction
    echo ""
    
    destroy_infrastructure
    echo ""
    
    cleanup_files
    echo ""
    
    print_header "Cleanup Complete! ✨"
    print_success "All infrastructure has been destroyed"
    print_info "Terraform state file preserved for reference"
}

# Run main function
main "$@"
