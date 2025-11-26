#!/bin/bash
# GitLab Runner Registration Script
# This script automates runner registration with different executors

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
GITLAB_URL="${GITLAB_URL:-https://gitlab.com/}"
REGISTRATION_TOKEN="${REGISTRATION_TOKEN:-}"
RUNNER_NAME="${RUNNER_NAME:-gitlab-runner}"
RUNNER_TAGS="${RUNNER_TAGS:-docker,linux}"
EXECUTOR="${EXECUTOR:-docker}"
DOCKER_IMAGE="${DOCKER_IMAGE:-alpine:latest}"

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
    
    if ! command -v gitlab-runner &> /dev/null; then
        print_error "gitlab-runner not found. Please install it first."
        exit 1
    fi
    
    if [ -z "$REGISTRATION_TOKEN" ]; then
        print_error "REGISTRATION_TOKEN not set. Please set it as environment variable."
        exit 1
    fi
    
    print_info "Prerequisites check passed"
}

register_docker_runner() {
    print_info "Registering Docker runner..."
    
    sudo gitlab-runner register \
        --non-interactive \
        --url "$GITLAB_URL" \
        --registration-token "$REGISTRATION_TOKEN" \
        --executor "docker" \
        --docker-image "$DOCKER_IMAGE" \
        --description "$RUNNER_NAME-docker" \
        --tag-list "$RUNNER_TAGS" \
        --run-untagged="false" \
        --locked="false" \
        --docker-privileged="true" \
        --docker-volumes "/certs/client" \
        --docker-volumes "/cache"
    
    print_info "Docker runner registered successfully"
}

register_kubernetes_runner() {
    print_info "Registering Kubernetes runner..."
    
    sudo gitlab-runner register \
        --non-interactive \
        --url "$GITLAB_URL" \
        --registration-token "$REGISTRATION_TOKEN" \
        --executor "kubernetes" \
        --description "$RUNNER_NAME-kubernetes" \
        --tag-list "kubernetes,k8s" \
        --run-untagged="false" \
        --locked="false" \
        --kubernetes-namespace "gitlab-runner" \
        --kubernetes-privileged="true"
    
    print_info "Kubernetes runner registered successfully"
}

register_shell_runner() {
    print_warn "Shell executor runs commands directly on host. Use with caution!"
    
    sudo gitlab-runner register \
        --non-interactive \
        --url "$GITLAB_URL" \
        --registration-token "$REGISTRATION_TOKEN" \
        --executor "shell" \
        --description "$RUNNER_NAME-shell" \
        --tag-list "shell,linux" \
        --run-untagged="false" \
        --locked="false"
    
    print_info "Shell runner registered successfully"
}

verify_registration() {
    print_info "Verifying runner registration..."
    
    sudo gitlab-runner verify
    sudo gitlab-runner list
    
    print_info "Runner verification completed"
}

# Main script
main() {
    echo "======================================"
    echo "  GitLab Runner Registration Script  "
    echo "======================================"
    echo ""
    
    check_prerequisites
    
    case "$EXECUTOR" in
        docker)
            register_docker_runner
            ;;
        kubernetes|k8s)
            register_kubernetes_runner
            ;;
        shell)
            register_shell_runner
            ;;
        *)
            print_error "Unknown executor: $EXECUTOR"
            echo "Supported executors: docker, kubernetes, shell"
            exit 1
            ;;
    esac
    
    verify_registration
    
    echo ""
    print_info "Runner registration completed successfully!"
    print_info "Check GitLab UI: Settings > CI/CD > Runners"
}

# Run main function
main
