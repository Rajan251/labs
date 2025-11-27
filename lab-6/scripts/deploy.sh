#!/bin/bash

# ============================================================================
# Terraform + Ansible Deployment Script
# ============================================================================
# This script automates the complete deployment process:
# 1. Provisions infrastructure with Terraform
# 2. Waits for instances to be ready
# 3. Configures servers with Ansible
# ============================================================================

set -e  # Exit on error
set -u  # Exit on undefined variable

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

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    local missing_tools=()
    
    if ! command -v terraform &> /dev/null; then
        missing_tools+=("terraform")
    fi
    
    if ! command -v ansible &> /dev/null; then
        missing_tools+=("ansible")
    fi
    
    if ! command -v aws &> /dev/null; then
        print_warning "AWS CLI not found (optional but recommended)"
    fi
    
    if [ ${#missing_tools[@]} -gt 0 ]; then
        print_error "Missing required tools: ${missing_tools[*]}"
        echo "Please install the missing tools and try again."
        exit 1
    fi
    
    print_success "All prerequisites met"
}

# Terraform deployment
deploy_terraform() {
    print_header "Provisioning Infrastructure with Terraform"
    
    cd "$TERRAFORM_DIR"
    
    # Initialize Terraform
    print_info "Initializing Terraform..."
    terraform init
    
    # Validate configuration
    print_info "Validating Terraform configuration..."
    terraform validate
    
    # Plan infrastructure
    print_info "Planning infrastructure changes..."
    terraform plan -out=tfplan
    
    # Apply infrastructure
    print_info "Applying infrastructure changes..."
    terraform apply tfplan
    
    # Remove plan file
    rm -f tfplan
    
    print_success "Infrastructure provisioned successfully"
    
    # Display outputs
    print_info "Infrastructure details:"
    terraform output
}

# Wait for instances
wait_for_instances() {
    print_header "Waiting for Instances to be Ready"
    
    cd "$TERRAFORM_DIR"
    
    # Get instance IPs
    local web_ips=$(terraform output -json web_instance_public_ips | jq -r '.[]')
    local app_ips=$(terraform output -json app_instance_public_ips | jq -r '.[]' 2>/dev/null || echo "")
    
    # Combine all IPs
    local all_ips="$web_ips $app_ips"
    
    # SSH key path
    local ssh_key=$(terraform output -json | jq -r '.deployment_summary.value' | grep -oP '(?<=-i )[^ ]+' | head -1)
    
    print_info "Waiting for SSH to be available on all instances..."
    
    for ip in $all_ips; do
        if [ -z "$ip" ]; then
            continue
        fi
        
        print_info "Checking $ip..."
        
        local max_attempts=30
        local attempt=1
        
        while [ $attempt -le $max_attempts ]; do
            if ssh -i "$ssh_key" -o StrictHostKeyChecking=no -o ConnectTimeout=5 ubuntu@"$ip" "echo 'SSH ready'" &> /dev/null; then
                print_success "$ip is ready"
                break
            fi
            
            if [ $attempt -eq $max_attempts ]; then
                print_error "Timeout waiting for $ip"
                exit 1
            fi
            
            echo -n "."
            sleep 10
            ((attempt++))
        done
    done
    
    print_success "All instances are ready"
}

# Ansible configuration
configure_ansible() {
    print_header "Configuring Servers with Ansible"
    
    cd "$ANSIBLE_DIR"
    
    # Check inventory file exists
    if [ ! -f "inventory/hosts.ini" ]; then
        print_error "Inventory file not found: inventory/hosts.ini"
        print_info "Make sure Terraform generated the inventory file"
        exit 1
    fi
    
    # Display inventory
    print_info "Inventory:"
    cat inventory/hosts.ini
    echo ""
    
    # Test connectivity
    print_info "Testing connectivity to all hosts..."
    if ansible all -i inventory/hosts.ini -m ping; then
        print_success "All hosts are reachable"
    else
        print_error "Some hosts are not reachable"
        exit 1
    fi
    
    # Run playbook
    print_info "Running Ansible playbook..."
    ansible-playbook -i inventory/hosts.ini setup.yml
    
    print_success "Server configuration completed"
}

# Verification
verify_deployment() {
    print_header "Verifying Deployment"
    
    cd "$TERRAFORM_DIR"
    
    # Get web server IPs
    local web_ips=$(terraform output -json web_instance_public_ips | jq -r '.[]')
    
    print_info "Testing web servers..."
    
    for ip in $web_ips; do
        if curl -s -o /dev/null -w "%{http_code}" "http://$ip" | grep -q "200"; then
            print_success "Web server at $ip is responding"
        else
            print_warning "Web server at $ip is not responding"
        fi
    done
}

# Main deployment flow
main() {
    print_header "Terraform + Ansible Deployment"
    echo ""
    
    check_prerequisites
    echo ""
    
    deploy_terraform
    echo ""
    
    wait_for_instances
    echo ""
    
    configure_ansible
    echo ""
    
    verify_deployment
    echo ""
    
    print_header "Deployment Complete! 🎉"
    
    cd "$TERRAFORM_DIR"
    
    echo ""
    print_success "Infrastructure provisioned and configured successfully!"
    echo ""
    print_info "Next steps:"
    terraform output -raw next_steps
}

# Run main function
main "$@"
