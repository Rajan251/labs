#!/bin/bash

# Docker Installation Script for Ubuntu
# This script installs Docker CE on Ubuntu 22.04/20.04

set -e

echo "========================================="
echo "Docker Installation Script"
echo "========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root or with sudo"
    exit 1
fi

# Remove old versions
echo "Removing old Docker versions..."
apt remove -y docker docker-engine docker.io containerd runc || true

# Update system
echo "Updating system packages..."
apt update

# Install prerequisites
echo "Installing prerequisites..."
apt install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker's official GPG key
echo "Adding Docker GPG key..."
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up Docker repository
echo "Setting up Docker repository..."
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update package list
apt update

# Install Docker Engine
echo "Installing Docker Engine..."
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start and enable Docker
echo "Starting Docker service..."
systemctl start docker
systemctl enable docker

# Add current user to docker group
if [ -n "$SUDO_USER" ]; then
    echo "Adding $SUDO_USER to docker group..."
    usermod -aG docker $SUDO_USER
fi

# Add jenkins user to docker group (if exists)
if id "jenkins" &>/dev/null; then
    echo "Adding jenkins user to docker group..."
    usermod -aG docker jenkins
fi

# Test Docker installation
echo "Testing Docker installation..."
docker run hello-world

echo "========================================="
echo "Docker Installation Complete!"
echo "========================================="
echo ""
echo "Docker version:"
docker --version
echo ""
echo "Docker Compose version:"
docker compose version
echo ""
echo "Note: You may need to log out and back in for group changes to take effect."
echo "========================================="
