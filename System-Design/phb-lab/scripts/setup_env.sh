#!/bin/bash
set -e

echo "Setting up local environment..."

# Check dependencies
command -v docker >/dev/null 2>&1 || { echo >&2 "Docker is required but not installed. Aborting."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo >&2 "Docker Compose is required but not installed. Aborting."; exit 1; }
command -v node >/dev/null 2>&1 || { echo >&2 "Node.js is required but not installed. Aborting."; exit 1; }

# Install API dependencies
echo "Installing API dependencies..."
if [ -d "api" ]; then
    cd api && npm install && cd ..
fi

# Install Web dependencies
echo "Installing Web dependencies..."
if [ -d "web" ]; then
    cd web && npm install && cd ..
fi

# Create .env if not exists
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env 2>/dev/null || echo "No .env.example found, skipping."
fi

echo "Setup complete! Run 'make up' to start the system."
