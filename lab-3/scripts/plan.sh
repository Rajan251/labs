#!/bin/bash
# Terraform plan script

set -e

ENVIRONMENT="${1:-dev}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_DIR="${PROJECT_ROOT}/envs/${ENVIRONMENT}"

if [ ! -d "$ENV_DIR" ]; then
    echo "Error: Environment directory not found: $ENV_DIR"
    exit 1
fi

echo "Planning Terraform changes for environment: ${ENVIRONMENT}"
cd "$ENV_DIR"

# Run plan
terraform plan -out=tfplan

echo ""
echo "✓ Plan saved to tfplan"
echo ""
echo "To apply these changes, run:"
echo "  ./scripts/apply.sh ${ENVIRONMENT}"
