#!/usr/bin/env bash

#######################################
# ArgoCD Installation Script
# Installs ArgoCD using Helm
#######################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ARGOCD_NAMESPACE="argocd"
ARGOCD_VERSION="5.51.0"
HELM_RELEASE_NAME="argocd"

#######################################
# Helper Functions
#######################################

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "$1 is not installed. Please install it and try again."
        exit 1
    fi
    log_info "$1 is installed ✓"
}

#######################################
# Prerequisite Checks
#######################################

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    check_command kubectl
    check_command helm
    
    # Check if kubectl can connect to cluster
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        log_error "Please ensure your cluster is running and kubectl is configured"
        exit 1
    fi
    
    log_info "Connected to cluster: $(kubectl config current-context)"
    log_info "All prerequisites satisfied ✓"
}

#######################################
# ArgoCD Installation
#######################################

install_argocd() {
    log_step "Installing ArgoCD..."
    
    # Create namespace
    if kubectl get namespace "$ARGOCD_NAMESPACE" &> /dev/null; then
        log_warn "Namespace '$ARGOCD_NAMESPACE' already exists"
    else
        log_info "Creating namespace '$ARGOCD_NAMESPACE'..."
        kubectl create namespace "$ARGOCD_NAMESPACE"
    fi
    
    # Add Helm repository
    log_info "Adding ArgoCD Helm repository..."
    helm repo add argo https://argoproj.github.io/argo-helm
    helm repo update
    
    # Check if ArgoCD is already installed
    if helm list -n "$ARGOCD_NAMESPACE" | grep -q "$HELM_RELEASE_NAME"; then
        log_warn "ArgoCD is already installed"
        read -p "Upgrade ArgoCD? [y/N]: " confirm
        if [[ "$confirm" =~ ^[Yy]$ ]]; then
            log_info "Upgrading ArgoCD..."
            helm upgrade "$HELM_RELEASE_NAME" argo/argo-cd \
                --namespace "$ARGOCD_NAMESPACE" \
                --version "$ARGOCD_VERSION"
        else
            log_info "Skipping installation"
            return 0
        fi
    else
        # Install ArgoCD
        log_info "Installing ArgoCD (version: $ARGOCD_VERSION)..."
        helm install "$HELM_RELEASE_NAME" argo/argo-cd \
            --namespace "$ARGOCD_NAMESPACE" \
            --version "$ARGOCD_VERSION" \
            --set server.service.type=ClusterIP \
            --set configs.params."server\.insecure"=true
    fi
    
    log_info "ArgoCD installation initiated ✓"
}

#######################################
# Wait for ArgoCD to be Ready
#######################################

wait_for_argocd() {
    log_step "Waiting for ArgoCD to be ready..."
    
    log_info "This may take a few minutes..."
    
    # Wait for all pods to be ready
    kubectl wait --for=condition=ready pod \
        --all \
        -n "$ARGOCD_NAMESPACE" \
        --timeout=600s
    
    log_info "All ArgoCD pods are ready ✓"
}

#######################################
# Get Admin Password
#######################################

get_admin_password() {
    log_step "Retrieving ArgoCD admin password..."
    
    # Wait for secret to be created
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if kubectl get secret argocd-initial-admin-secret -n "$ARGOCD_NAMESPACE" &> /dev/null; then
            break
        fi
        log_info "Waiting for admin secret... (attempt $attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        log_error "Admin secret not found after ${max_attempts} attempts"
        return 1
    fi
    
    local password
    password=$(kubectl -n "$ARGOCD_NAMESPACE" get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)
    
    echo
    log_info "================================================"
    log_info "ArgoCD Admin Credentials:"
    log_info "================================================"
    log_info "Username: admin"
    log_info "Password: $password"
    log_info "================================================"
    echo
    
    # Save to file (optional)
    echo "Username: admin" > /tmp/argocd-credentials.txt
    echo "Password: $password" >> /tmp/argocd-credentials.txt
    log_info "Credentials saved to: /tmp/argocd-credentials.txt"
}

#######################################
# Setup Port Forwarding
#######################################

setup_port_forward() {
    log_step "Setting up port forwarding..."
    
    read -p "Do you want to start port-forwarding to access ArgoCD UI? [Y/n]: " confirm
    if [[ ! "$confirm" =~ ^[Nn]$ ]]; then
        log_info "Starting port-forward on localhost:8080..."
        log_info "ArgoCD UI will be available at: https://localhost:8080"
        log_info ""
        log_warn "Keep this terminal open to maintain port-forward"
        log_warn "Press Ctrl+C to stop port-forwarding"
        echo
        
        kubectl port-forward svc/argocd-server -n "$ARGOCD_NAMESPACE" 8080:443
    else
        log_info "Skipping port-forward setup"
        log_info "To access ArgoCD UI later, run:"
        log_info "  kubectl port-forward svc/argocd-server -n $ARGOCD_NAMESPACE 8080:443"
    fi
}

#######################################
# Display Summary
#######################################

display_summary() {
    echo
    log_info "================================================"
    log_info "✅ ArgoCD Installation Complete!"
    log_info "================================================"
    log_info "Namespace: $ARGOCD_NAMESPACE"
    log_info "Version: $ARGOCD_VERSION"
    echo
    log_info "Access ArgoCD UI:"
    log_info "  1. Start port-forward (if not already running):"
    log_info "     kubectl port-forward svc/argocd-server -n argocd 8080:443"
    log_info ""
    log_info "  2. Open browser: https://localhost:8080"
    log_info ""
    log_info "  3. Login with credentials from above"
    echo
    log_info "Useful Commands:"
    log_info "  - Get password again:"
    log_info "    kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath=\"{.data.password}\" | base64 -d"
    log_info ""
    log_info "  - View ArgoCD pods:"
    log_info "    kubectl get pods -n argocd"
    log_info ""
    log_info "  - View ArgoCD logs:"
    log_info "    kubectl logs -n argocd -l app.kubernetes.io/name=argocd-server"
    echo
    log_info "Next Steps:"
    log_info "  1. Read the documentation: ../documentation/02-argocd-installation.md"
    log_info "  2. Deploy sample apps: kubectl apply -f ../examples/argocd-apps/"
    log_info "  3. Try Lab 01: ../labs/lab-01-first-deployment.md"
    log_info "================================================"
}

#######################################
# Main Script
#######################################

main() {
    echo "================================================"
    echo "       ArgoCD Installation Script"
    echo "================================================"
    echo
    
    check_prerequisites
    install_argocd
    wait_for_argocd
    get_admin_password
    display_summary
    setup_port_forward
}

# Run main function
main "$@"
