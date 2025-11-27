#!/bin/bash
# Terraform initialization script

set -e

ENVIRONMENT="${1:-dev}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_DIR="${PROJECT_ROOT}/envs/${ENVIRONMENT}"

if [ ! -d "$ENV_DIR" ]; then
    echo "Error: Environment directory not found: $ENV_DIR"
    exit 1
fi

echo "Initializing Terraform for environment: ${ENVIRONMENT}"
cd "$ENV_DIR"

# Check if terraform.tfvars exists
if [ ! -f "terraform.tfvars" ]; then
    if [ -f "terraform.tfvars.example" ]; then
        echo "Warning: terraform.tfvars not found. Copy from example:"
        echo "  cp terraform.tfvars.example terraform.tfvars"
        exit 1
    fi
fi

# Initialize
terraform init -upgrade

echo "✓ Terraform initialized successfully"
