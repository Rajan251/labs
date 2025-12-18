#!/usr/bin/env bash

#######################################
# GitOps Lab Cleanup Script
# Removes all lab resources
#######################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

#######################################
# Cleanup Functions
#######################################

cleanup_argocd_apps() {
    log_step "Cleaning up ArgoCD applications..."
    
    if ! kubectl get namespace argocd &> /dev/null; then
        log_warn "ArgoCD namespace not found, skipping application cleanup"
        return 0
    fi
    
    # Delete all applications
    local apps=$(kubectl get applications -n argocd -o name 2>/dev/null || echo "")
    
    if [ -n "$apps" ]; then
        log_info "Deleting ArgoCD applications..."
        kubectl delete applications --all -n argocd --timeout=60s
        
        # Wait for applications to be deleted
        log_info "Waiting for applications to be deleted..."
        timeout 120s bash -c 'while kubectl get applications -n argocd 2>&1 | grep -q "guestbook\|wordpress"; do sleep 2; done' || true
        
        log_info "ArgoCD applications deleted ✓"
    else
        log_info "No ArgoCD applications found"
    fi
}

cleanup_application_namespaces() {
    log_step "Cleaning up application namespaces..."
    
    local namespaces=("guestbook-dev" "guestbook-staging" "guestbook-prod" "wordpress")
    
    for ns in "${namespaces[@]}"; do
        if kubectl get namespace "$ns" &> /dev/null; then
            log_info "Deleting namespace: $ns"
            kubectl delete namespace "$ns" --timeout=60s || log_warn "Failed to delete $ns"
        fi
    done
    
    log_info "Application namespaces cleaned ✓"
}

cleanup_argocd() {
    log_step "Cleaning up ArgoCD..."
    
    if ! kubectl get namespace argocd &> /dev/null; then
        log_warn "ArgoCD namespace not found, skipping ArgoCD cleanup"
        return 0
    fi
    
    read -p "Delete ArgoCD? [y/N]: " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        # Check if installed via Helm
        if helm list -n argocd 2>/dev/null | grep -q argocd; then
            log_info "Uninstalling ArgoCD via Helm..."
            helm uninstall argocd -n argocd
        fi
        
        # Delete namespace
        log_info "Deleting ArgoCD namespace..."
        kubectl delete namespace argocd --timeout=120s
        
        log_info "ArgoCD deleted ✓"
    else
        log_info "Keeping ArgoCD installed"
    fi
}

cleanup_cluster() {
    log_step "Cleaning up Kubernetes cluster..."
    
    read -p "Delete the entire Kubernetes cluster? [y/N]: " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        log_info "Keeping cluster"
        return 0
    fi
    
    # Detect cluster type
    local context=$(kubectl config current-context)
    
    if [[ "$context" == *"minikube"* ]]; then
        log_info "Deleting Minikube cluster..."
        local profile=$(echo "$context" | sed 's/^minikube-//')
        minikube delete --profile "$profile"
        log_info "Minikube cluster deleted ✓"
        
    elif [[ "$context" == *"kind"* ]]; then
        log_info "Deleting Kind cluster..."
        local cluster=$(echo "$context" | sed 's/^kind-//')
        kind delete cluster --name "$cluster"
        log_info "Kind cluster deleted ✓"
        
    elif [[ "$context" == *"k3d"* ]]; then
        log_info "Deleting K3d cluster..."
        local cluster=$(echo "$context" | sed 's/^k3d-//')
        k3d cluster delete "$cluster"
        log_info "K3d cluster deleted ✓"
        
    else
        log_warn "Unknown cluster type: $context"
        log_warn "Please delete cluster manually"
    fi
}

cleanup_temp_files() {
    log_step "Cleaning up temporary files..."
    
    if [ -f /tmp/argocd-credentials.txt ]; then
        rm -f /tmp/argocd-credentials.txt
        log_info "Removed /tmp/argocd-credentials.txt"
    fi
    
    if [ -f /tmp/kind-config.yaml ]; then
        rm -f /tmp/kind-config.yaml
        log_info "Removed /tmp/kind-config.yaml"
    fi
    
    log_info "Temporary files cleaned ✓"
}

verify_cleanup() {
    log_step "Verifying cleanup..."
    
    local issues=0
    
    # Check if ArgoCD applications exist
    if kubectl get applications -n argocd &> /dev/null; then
        local app_count=$(kubectl get applications -n argocd --no-headers 2>/dev/null | wc -l)
        if [ "$app_count" -gt 0 ]; then
            log_warn "Found $app_count ArgoCD applications still present"
            ((issues++))
        fi
    fi
    
    # Check if application namespaces exist
    local namespaces=("guestbook-dev" "guestbook-staging" "guestbook-prod" "wordpress")
    for ns in "${namespaces[@]}"; do
        if kubectl get namespace "$ns" &> /dev/null; then
            log_warn "Namespace $ns still exists"
            ((issues++))
        fi
    done
    
    if [ $issues -eq 0 ]; then
        log_info "Cleanup verification passed ✓"
    else
        log_warn "Found $issues issues during verification"
    fi
}

show_summary() {
    echo
    log_info "================================================"
    log_info "Cleanup Summary"
    log_info "================================================"
    log_info "✓ ArgoCD applications deleted"
    log_info "✓ Application namespaces removed"
    log_info "✓ Temporary files cleaned"
    
    if kubectl get namespace argocd &> /dev/null; then
        log_info "⚠ ArgoCD is still installed"
    else
        log_info "✓ ArgoCD removed"
    fi
    
    if kubectl cluster-info &> /dev/null; then
        log_info "⚠ Kubernetes cluster is still running"
        log_info "  Current context: $(kubectl config current-context)"
    else
        log_info "✓ Kubernetes cluster deleted"
    fi
    
    log_info "================================================"
}

#######################################
# Main Script
#######################################

main() {
    echo "================================================"
    echo "       GitOps Lab Cleanup Script"
    echo "================================================"
    echo
    
    log_warn "This script will clean up all GitOps lab resources"
    log_warn "This action cannot be undone!"
    echo
    
    read -p "Continue with cleanup? [y/N]: " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        log_info "Cleanup cancelled"
        exit 0
    fi
    
    echo
    
    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl not found"
        exit 1
    fi
    
    # Check if cluster is accessible
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        log_error "Is your cluster running?"
        exit 1
    fi
    
    log_info "Current cluster: $(kubectl config current-context)"
    echo
    
    # Execute cleanup steps
    cleanup_argocd_apps
    cleanup_application_namespaces
    cleanup_argocd
    cleanup_cluster
    cleanup_temp_files
    
    # Verify cleanup
    if kubectl cluster-info &> /dev/null; then
        verify_cleanup
    fi
    
    # Show summary
    show_summary
    
    echo
    log_info "Cleanup complete!"
    echo
}

# Run main function
main "$@"
