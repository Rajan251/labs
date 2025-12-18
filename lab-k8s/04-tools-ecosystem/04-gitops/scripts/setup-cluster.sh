#!/usr/bin/env bash

#######################################
# Kubernetes Cluster Setup Script
# Supports: Minikube, Kind, K3d
#######################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default configuration
CLUSTER_NAME="gitops-lab"
K8S_VERSION="1.28.3"
CPUS="4"
MEMORY="8192"  # MB
CLUSTER_TYPE=""  # Will be detected or selected

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

check_command() {
    if command -v "$1" &> /dev/null; then
        log_info "$1 is installed ✓"
        return 0
    else
        log_warn "$1 is not installed"
        return 1
    fi
}

#######################################
# Prerequisite Checks
#######################################

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    local missing_tools=()
    
    if ! check_command docker; then
        missing_tools+=("docker")
    fi
    
    if ! check_command kubectl; then
        missing_tools+=("kubectl")
    fi
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_error "Please install missing tools and try again."
        exit 1
    fi
    
    # Check Docker is running
    if ! docker info &> /dev/null; then
        log_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    
    log_info "All prerequisites satisfied ✓"
}

#######################################
# Detect or Select Cluster Type
#######################################

detect_cluster_tools() {
    log_info "Detecting available cluster tools..."
    
    local tools=()
    
    if command -v minikube &> /dev/null; then
        tools+=("minikube")
    fi
    
    if command -v kind &> /dev/null; then
        tools+=("kind")
    fi
    
    if command -v k3d &> /dev/null; then
        tools+=("k3d")
    fi
    
    if [ ${#tools[@]} -eq 0 ]; then
        log_error "No Kubernetes cluster tool found (minikube, kind, or k3d)"
        log_error "Please install one and try again."
        exit 1
    fi
    
    echo "${tools[@]}"
}

select_cluster_type() {
    read -p "Select cluster type [minikube/kind/k3d]: " choice
    case "$choice" in
        minikube|kind|k3d)
            CLUSTER_TYPE="$choice"
            ;;
        *)
            log_error "Invalid choice. Please select: minikube, kind, or k3d"
            exit 1
            ;;
    esac
}

#######################################
# Cluster Setup Functions
#######################################

setup_minikube() {
    log_info "Setting up Minikube cluster..."
    
    # Check if cluster already exists
    if minikube status --profile "$CLUSTER_NAME" &> /dev/null; then
        log_warn "Minikube cluster '$CLUSTER_NAME' already exists"
        read -p "Delete and recreate? [y/N]: " confirm
        if [[ "$confirm" =~ ^[Yy]$ ]]; then
            minikube delete --profile "$CLUSTER_NAME"
        else
            log_info "Using existing cluster"
            return 0
        fi
    fi
    
    log_info "Creating Minikube cluster with $CPUS CPUs and ${MEMORY}MB RAM..."
    minikube start \
        --profile "$CLUSTER_NAME" \
        --cpus "$CPUS" \
        --memory "$MEMORY" \
        --kubernetes-version "v$K8S_VERSION" \
        --driver=docker
    
    # Set context
    kubectl config use-context "$CLUSTER_NAME"
    
    log_info "Minikube cluster created successfully ✓"
}

setup_kind() {
    log_info "Setting up Kind cluster..."
    
    # Check if cluster already exists
    if kind get clusters 2>/dev/null | grep -q "^${CLUSTER_NAME}$"; then
        log_warn "Kind cluster '$CLUSTER_NAME' already exists"
        read -p "Delete and recreate? [y/N]: " confirm
        if [[ "$confirm" =~ ^[Yy]$ ]]; then
            kind delete cluster --name "$CLUSTER_NAME"
        else
            log_info "Using existing cluster"
            return 0
        fi
    fi
    
    # Create Kind config
    cat > /tmp/kind-config.yaml <<EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: ${CLUSTER_NAME}
nodes:
  - role: control-plane
    image: kindest/node:v${K8S_VERSION}
  - role: worker
    image: kindest/node:v${K8S_VERSION}
EOF
    
    log_info "Creating Kind cluster..."
    kind create cluster --config /tmp/kind-config.yaml
    
    # Set context
    kubectl config use-context "kind-${CLUSTER_NAME}"
    
    log_info "Kind cluster created successfully ✓"
    rm /tmp/kind-config.yaml
}

setup_k3d() {
    log_info "Setting up K3d cluster..."
    
    # Check if cluster already exists
    if k3d cluster list | grep -q "^${CLUSTER_NAME}"; then
        log_warn "K3d cluster '$CLUSTER_NAME' already exists"
        read -p "Delete and recreate? [y/N]: " confirm
        if [[ "$confirm" =~ ^[Yy]$ ]]; then
            k3d cluster delete "$CLUSTER_NAME"
        else
            log_info "Using existing cluster"
            return 0
        fi
    fi
    
    log_info "Creating K3d cluster..."
    k3d cluster create "$CLUSTER_NAME" \
        --servers 1 \
        --agents 2 \
        --image "rancher/k3s:v${K8S_VERSION}-k3s1"
    
    # Set context
    kubectl config use-context "k3d-${CLUSTER_NAME}"
    
    log_info "K3d cluster created successfully ✓"
}

#######################################
# Verification
#######################################

verify_cluster() {
    log_info "Verifying cluster..."
    
    # Wait for nodes to be ready
    log_info "Waiting for nodes to be ready..."
    kubectl wait --for=condition=ready nodes --all --timeout=300s
    
    log_info "Cluster nodes:"
    kubectl get nodes
    
    log_info "Cluster info:"
    kubectl cluster-info
    
    log_info "Cluster verification complete ✓"
}

#######################################
# Main Script
#######################################

main() {
    echo "================================================"
    echo "   Kubernetes Cluster Setup for GitOps Lab"
    echo "================================================"
    echo
    
    # Check prerequisites
    check_prerequisites
    
    # Detect available tools
    available_tools=($(detect_cluster_tools))
    
    if [ ${#available_tools[@]} -eq 1 ]; then
        CLUSTER_TYPE="${available_tools[0]}"
        log_info "Using ${CLUSTER_TYPE} (only available tool)"
    else
        log_info "Available tools: ${available_tools[*]}"
        select_cluster_type
    fi
    
    # Setup cluster based on type
    case "$CLUSTER_TYPE" in
        minikube)
            setup_minikube
            ;;
        kind)
            setup_kind
            ;;
        k3d)
            setup_k3d
            ;;
    esac
    
    # Verify cluster
    verify_cluster
    
    echo
    log_info "================================================"
    log_info "✅ Cluster setup complete!"
    log_info "================================================"
    log_info "Cluster name: $CLUSTER_NAME"
    log_info "Cluster type: $CLUSTER_TYPE"
    log_info ""
    log_info "Next steps:"
    log_info "  1. Install ArgoCD: ./scripts/install-argocd.sh"
    log_info "  2. Deploy sample apps: kubectl apply -f examples/argocd-apps/"
    log_info ""
    log_info "Useful commands:"
    log_info "  - View nodes: kubectl get nodes"
    log_info "  - View all resources: kubectl get all --all-namespaces"
    
    if [ "$CLUSTER_TYPE" = "minikube" ]; then
        log_info "  - Minikube dashboard: minikube dashboard --profile $CLUSTER_NAME"
    fi
}

# Run main function
main "$@"
