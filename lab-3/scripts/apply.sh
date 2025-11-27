#!/bin/bash
# Terraform apply script

set -e

ENVIRONMENT="${1:-dev}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_DIR="${PROJECT_ROOT}/envs/${ENVIRONMENT}"

if [ ! -d "$ENV_DIR" ]; then
    echo "Error: Environment directory not found: $ENV_DIR"
    exit 1
fi

cd "$ENV_DIR"

if [ ! -f "tfplan" ]; then
    echo "Error: No plan file found. Run plan.sh first:"
    echo "  ./scripts/plan.sh ${ENVIRONMENT}"
    exit 1
fi

echo "Applying Terraform changes for environment: ${ENVIRONMENT}"
echo ""

# Apply
terraform apply tfplan

# Clean up plan file
rm -f tfplan

echo ""
echo "✓ Changes applied successfully"
echo ""
echo "View outputs:"
echo "  terraform output"
