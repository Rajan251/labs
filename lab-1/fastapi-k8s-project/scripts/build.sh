#!/bin/bash

# =============================================================================
# DOCKER BUILD AND PUSH SCRIPT
# =============================================================================
# This script builds the Docker image and pushes it to the registry
#
# Usage:
#   ./build.sh [tag]
#
# Examples:
#   ./build.sh latest
#   ./build.sh v1.2.3
#   ./build.sh $(git rev-parse --short HEAD)
#
# Prerequisites:
# - Docker installed
# - Logged in to Docker registry
# =============================================================================

set -e

# Configuration
DOCKER_REGISTRY="${DOCKER_REGISTRY:-your-registry.com}"
IMAGE_NAME="${IMAGE_NAME:-fastapi-app}"
TAG="${1:-latest}"
FULL_IMAGE="${DOCKER_REGISTRY}/${IMAGE_NAME}:${TAG}"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=============================================${NC}"
echo -e "${BLUE}Building Docker Image${NC}"
echo -e "${BLUE}=============================================${NC}"
echo "Image: ${FULL_IMAGE}"
echo ""

# Build image
echo -e "${BLUE}[1/3] Building image...${NC}"
docker build \
    --tag ${FULL_IMAGE} \
    --tag ${DOCKER_REGISTRY}/${IMAGE_NAME}:latest \
    --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
    --build-arg VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown") \
    --build-arg VERSION=${TAG} \
    .

echo -e "${GREEN}✓ Build completed${NC}"
echo ""

# Push image
echo -e "${BLUE}[2/3] Pushing image...${NC}"
docker push ${FULL_IMAGE}

if [ "${TAG}" != "latest" ]; then
    docker push ${DOCKER_REGISTRY}/${IMAGE_NAME}:latest
fi

echo -e "${GREEN}✓ Push completed${NC}"
echo ""

# Display image info
echo -e "${BLUE}[3/3] Image information:${NC}"
docker images | grep ${IMAGE_NAME}

echo ""
echo -e "${GREEN}=============================================${NC}"
echo -e "${GREEN}Build and push completed successfully!${NC}"
echo -e "${GREEN}=============================================${NC}"
