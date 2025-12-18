#!/bin/bash

# ArgoCD Installation Script
# This script installs ArgoCD on a Kubernetes cluster

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl not found. Please install kubectl first."
        exit 1
    fi
    
    # Check cluster connection
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster. Please start your cluster first."
        exit 1
    fi
    
    print_info "✓ Prerequisites check passed"
}

install_argocd() {
    print_info "Installing ArgoCD..."
    
    #Create namespace
    print_info "Creating argocd namespace..."
    kubectl create namespace argocd 2>/dev/null || print_warn "Namespace 'argocd' already exists"
    
    # Install ArgoCD
    print_info "Applying ArgoCD manifests..."
    kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
    
    # Wait for pods
    print_info "Waiting for ArgoCD pods to be ready (this may take 2-3 minutes)..."
    kubectl wait --for=condition=ready pod --all -n argocd --timeout=300s || {
        print_error "ArgoCD pods failed to become ready"
        print_info "Checking pod status:"
        kubectl get pods -n argocd
        exit 1
    }
    
    print_info "✓ ArgoCD installed successfully"
}

get_credentials() {
    print_info "Retrieving ArgoCD credentials..."
    
    # Wait for secret to be created
    sleep 5
    
    local password=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" 2>/dev/null | base64 -d)
    
    if [ -z "$password" ]; then
        print_error "Could not retrieve admin password"
        exit 1
    fi
    
    echo
    print_info "==================================="
    print_info "ArgoCD Credentials"
    print_info "==================================="
    echo "Username: admin"
    echo "Password: $password"
    print_info "==================================="
    echo
    
    # Save to file
    echo "admin:$password" > ~/argocd-credentials.txt
    chmod 600 ~/argocd-credentials.txt
    print_info "Credentials saved to: ~/argocd-credentials.txt"
}

setup_port_forward() {
    print_info "Setting up port-forward..."
    
    # Kill existing port-forward if any
    pkill -f "port-forward.*argocd-server" 2>/dev/null || true
    
    # Start port-forward in background
    kubectl port-forward svc/argocd-server -n argocd 8080:443 > /dev/null 2>&1 &
    
    sleep 2
    
    print_info "✓ Port-forward started on https://localhost:8080"
}

install_cli() {
    print_info "Do you want to install ArgoCD CLI? (y/n)"
    read -r response
    
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_info "Installing ArgoCD CLI..."
        
        # Detect OS
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            if command -v brew &> /dev/null; then
                brew install argocd
            else
                curl -sSL -o /usr/local/bin/argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-darwin-amd64
                chmod +x /usr/local/bin/argocd
            fi
        else
            # Linux
            curl -sSL -o /tmp/argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
            sudo install -m 555 /tmp/argocd /usr/local/bin/argocd
            rm /tmp/argocd
        fi
        
        print_info "✓ ArgoCD CLI installed"
        argocd version --client
    else
        print_info "Skipping CLI installation"
    fi
}

verify_installation() {
    print_info "Verifying installation..."
    
    echo
    print_info "Pods in argocd namespace:"
    kubectl get pods -n argocd
    
    echo
    print_info "Services in argocd namespace:"
    kubectl get svc -n argocd
}

print_next_steps() {
    echo
    print_info "==================================="
    print_info "Installation Complete!"
    print_info "==================================="
    echo
    echo "Next steps:"
    echo "1. Open browser to: https://localhost:8080"
    echo "2. Accept the self-signed certificate warning"
    echo "3. Login with credentials from above"
    echo "4. Change the default password (User Info → Update Password)"
    echo
    echo "To access ArgoCD Server later:"
    echo "  kubectl port-forward svc/argocd-server -n argocd 8080:443"
    echo
    echo "To get password again:"
    echo "  cat ~/argocd-credentials.txt"
    echo "  # OR"
    echo "  kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath=\"{.data.password}\" | base64 -d"
    echo
    echo "To uninstall ArgoCD:"
    echo "  kubectl delete -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml"
    echo "  kubectl delete namespace argocd"
    echo
}

# Main execution
main() {
    echo
    print_info "==================================="
    print_info "ArgoCD Installation Script"
    print_info "==================================="
    echo
    
    check_prerequisites
    install_argocd
    get_credentials
    setup_port_forward
    install_cli
    verify_installation
    print_next_steps
}

main
