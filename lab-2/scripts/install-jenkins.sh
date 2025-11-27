#!/bin/bash

# Jenkins Installation Script for Ubuntu
# This script installs Jenkins on Ubuntu 22.04/20.04

set -e

echo "========================================="
echo "Jenkins Installation Script"
echo "========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root or with sudo"
    exit 1
fi

# Update system
echo "Updating system packages..."
apt update && apt upgrade -y

# Install Java
echo "Installing OpenJDK 17..."
apt install -y openjdk-17-jdk

# Verify Java installation
java -version

# Add Jenkins repository
echo "Adding Jenkins repository..."
curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key | tee \
  /usr/share/keyrings/jenkins-keyring.asc > /dev/null

echo deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] \
  https://pkg.jenkins.io/debian-stable binary/ | tee \
  /etc/apt/sources.list.d/jenkins.list > /dev/null

# Update package list
apt update

# Install Jenkins
echo "Installing Jenkins..."
apt install -y jenkins

# Start and enable Jenkins
echo "Starting Jenkins service..."
systemctl start jenkins
systemctl enable jenkins

# Configure firewall
echo "Configuring firewall..."
ufw allow 8080/tcp
ufw allow 50000/tcp

# Wait for Jenkins to start
echo "Waiting for Jenkins to start..."
sleep 30

# Display initial admin password
echo "========================================="
echo "Jenkins Installation Complete!"
echo "========================================="
echo ""
echo "Access Jenkins at: http://$(hostname -I | awk '{print $1}'):8080"
echo ""
echo "Initial Admin Password:"
cat /var/lib/jenkins/secrets/initialAdminPassword
echo ""
echo "========================================="
