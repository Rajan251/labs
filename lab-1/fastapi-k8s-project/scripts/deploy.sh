#!/bin/bash

# =============================================================================
# KUBERNETES DEPLOYMENT SCRIPT
# =============================================================================
# This script deploys the FastAPI application to Kubernetes
#
# Usage:
#   ./deploy.sh [environment] [image-tag]
#
# Examples:
#   ./deploy.sh dev latest
#   ./deploy.sh staging v1.2.3
#   ./deploy.sh prod v1.2.3
#
# Prerequisites:
# - kubectl installed and configured
# - Access to Kubernetes cluster
# - Docker image already pushed to registry
# =============================================================================

set -e  # Exit on error
set -u  # Exit on undefined variable
set -o pipefail  # Exit on pipe failure

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="${1:-dev}"
IMAGE_TAG="${2:-latest}"
NAMESPACE="fastapi-app"
DEPLOYMENT_NAME="fastapi-deployment"
DOCKER_REGISTRY="your-registry.com"
IMAGE_NAME="fastapi-app"

# Full image path
FULL_IMAGE="${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"

# -----------------------------------------------------------------------------
# Functions
# -----------------------------------------------------------------------------

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command_exists kubectl; then
        log_error "kubectl is not installed"
        exit 1
    fi
    
    if ! kubectl cluster-info >/dev/null 2>&1; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Create namespace if it doesn't exist
create_namespace() {
    log_info "Checking namespace: ${NAMESPACE}"
    
    if kubectl get namespace "${NAMESPACE}" >/dev/null 2>&1; then
        log_info "Namespace ${NAMESPACE} already exists"
    else
        log_info "Creating namespace: ${NAMESPACE}"
        kubectl create namespace "${NAMESPACE}"
        log_success "Namespace created"
    fi
}

# Apply Kubernetes manifests
apply_manifests() {
    log_info "Applying Kubernetes manifests..."
    
    # Apply in order
    kubectl apply -f k8s/base/namespace.yaml
    kubectl apply -f k8s/base/configmap.yaml
    kubectl apply -f k8s/base/secret.yaml
    kubectl apply -f k8s/base/deployment.yaml
    kubectl apply -f k8s/base/service.yaml
    kubectl apply -f k8s/base/ingress.yaml
    kubectl apply -f k8s/base/hpa.yaml
    
    log_success "Manifests applied"
}

# Update deployment image
update_image() {
    log_info "Updating deployment image to: ${FULL_IMAGE}"
    
    kubectl set image deployment/${DEPLOYMENT_NAME} \
        fastapi-app=${FULL_IMAGE} \
        -n ${NAMESPACE}
    
    log_success "Image updated"
}

# Wait for rollout
wait_for_rollout() {
    log_info "Waiting for rollout to complete..."
    
    if kubectl rollout status deployment/${DEPLOYMENT_NAME} \
        -n ${NAMESPACE} \
        --timeout=5m; then
        log_success "Rollout completed successfully"
    else
        log_error "Rollout failed"
        exit 1
    fi
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    # Get pod status
    echo ""
    log_info "Pod Status:"
    kubectl get pods -n ${NAMESPACE} -l app=fastapi-app
    
    # Get service status
    echo ""
    log_info "Service Status:"
    kubectl get svc -n ${NAMESPACE}
    
    # Get ingress status
    echo ""
    log_info "Ingress Status:"
    kubectl get ingress -n ${NAMESPACE}
    
    # Check if pods are ready
    READY_PODS=$(kubectl get pods -n ${NAMESPACE} -l app=fastapi-app \
        -o jsonpath='{.items[*].status.conditions[?(@.type=="Ready")].status}' | grep -o "True" | wc -l)
    
    TOTAL_PODS=$(kubectl get pods -n ${NAMESPACE} -l app=fastapi-app --no-headers | wc -l)
    
    echo ""
    log_info "Ready Pods: ${READY_PODS}/${TOTAL_PODS}"
    
    if [ "${READY_PODS}" -eq "${TOTAL_PODS}" ] && [ "${TOTAL_PODS}" -gt 0 ]; then
        log_success "All pods are ready"
    else
        log_warning "Not all pods are ready"
    fi
}

# Run smoke tests
run_smoke_tests() {
    log_info "Running smoke tests..."
    
    # Get service endpoint
    INGRESS_HOST=$(kubectl get ingress fastapi-ingress \
        -n ${NAMESPACE} \
        -o jsonpath='{.spec.rules[0].host}' 2>/dev/null || echo "")
    
    if [ -z "${INGRESS_HOST}" ]; then
        log_warning "Ingress not configured, skipping smoke tests"
        return
    fi
    
    # Test health endpoint
    if curl -f -s "https://${INGRESS_HOST}/api/v1/health" > /dev/null; then
        log_success "Health check passed"
    else
        log_error "Health check failed"
        exit 1
    fi
}

# Rollback deployment
rollback_deployment() {
    log_warning "Rolling back deployment..."
    
    kubectl rollout undo deployment/${DEPLOYMENT_NAME} -n ${NAMESPACE}
    
    log_info "Waiting for rollback to complete..."
    kubectl rollout status deployment/${DEPLOYMENT_NAME} -n ${NAMESPACE}
    
    log_success "Rollback completed"
}

# -----------------------------------------------------------------------------
# Main Script
# -----------------------------------------------------------------------------

main() {
    echo "============================================="
    echo "FastAPI Kubernetes Deployment Script"
    echo "============================================="
    echo "Environment: ${ENVIRONMENT}"
    echo "Image: ${FULL_IMAGE}"
    echo "Namespace: ${NAMESPACE}"
    echo "============================================="
    echo ""
    
    # Run deployment steps
    check_prerequisites
    create_namespace
    apply_manifests
    update_image
    wait_for_rollout
    verify_deployment
    run_smoke_tests
    
    echo ""
    echo "============================================="
    log_success "Deployment completed successfully!"
    echo "============================================="
}

# Handle script interruption
trap 'log_error "Script interrupted"; exit 1' INT TERM

# Run main function
main "$@"
