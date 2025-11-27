#!/bin/bash
# Terraform destroy script

set -e

ENVIRONMENT="${1:-dev}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_DIR="${PROJECT_ROOT}/envs/${ENVIRONMENT}"

if [ ! -d "$ENV_DIR" ]; then
    echo "Error: Environment directory not found: $ENV_DIR"
    exit 1
fi

echo "⚠️  WARNING: This will destroy all resources in environment: ${ENVIRONMENT}"
echo ""
read -p "Are you sure? Type 'yes' to confirm: " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted"
    exit 0
fi

cd "$ENV_DIR"

# Destroy
terraform destroy

echo ""
echo "✓ Resources destroyed"
