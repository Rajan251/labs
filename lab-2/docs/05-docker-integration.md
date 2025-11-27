# 5. Docker Integration with Jenkins

## Overview

This guide covers installing Docker on Ubuntu and integrating it with Jenkins for building and pushing container images in CI/CD pipelines.

## Prerequisites

- Ubuntu 22.04 LTS or 20.04 LTS
- Sudo privileges
- Jenkins installed (native or containerized)

## Step 1: Install Docker CE

### Remove Old Versions

```bash
# Remove old Docker versions
sudo apt remove docker docker-engine docker.io containerd runc
```

### Install Dependencies

```bash
# Update package index
sudo apt update

# Install prerequisites
sudo apt install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release
```

### Add Docker Repository

```bash
# Create keyrings directory
sudo mkdir -p /etc/apt/keyrings

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

### Install Docker Engine

```bash
# Update package index
sudo apt update

# Install Docker
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Verify installation
docker --version
```

**Expected output**:
```
Docker version 24.0.7, build afdd53b
```

### Test Docker Installation

```bash
# Run hello-world container
sudo docker run hello-world
```

## Step 2: Configure Docker

### Start and Enable Docker

```bash
# Start Docker service
sudo systemctl start docker

# Enable Docker to start on boot
sudo systemctl enable docker

# Check status
sudo systemctl status docker
```

### Add Jenkins User to Docker Group

This allows Jenkins to run Docker commands without sudo.

```bash
# Add jenkins user to docker group
sudo usermod -aG docker jenkins

# Verify
groups jenkins
```

**Expected output**:
```
jenkins : jenkins docker
```

### Restart Jenkins

```bash
# For native Jenkins
sudo systemctl restart jenkins

# For containerized Jenkins
docker restart jenkins
```

### Test Docker Access

```bash
# Test as jenkins user
sudo -u jenkins docker ps

# Should show running containers without permission errors
```

## Step 3: Configure Docker Daemon

### Create daemon.json

```bash
sudo nano /etc/docker/daemon.json
```

Add configuration:

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "insecure-registries": [],
  "registry-mirrors": []
}
```

### Restart Docker

```bash
sudo systemctl restart docker

# Verify configuration
docker info
```

## Step 4: Install Docker Compose

Docker Compose is included with Docker Engine, but verify:

```bash
# Check version
docker compose version

# Or install standalone (if needed)
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

## Step 5: Configure Jenkins for Docker

### Install Docker Pipeline Plugin

1. Go to **Manage Jenkins** → **Manage Plugins**
2. Click **Available** tab
3. Search for **Docker Pipeline**
4. Install and restart Jenkins

### Configure Docker in Jenkins

**Manage Jenkins** → **Global Tool Configuration** → **Docker**

- **Name**: docker
- **Install automatically**: Check
- **Docker version**: latest

Or use system Docker:
- **Name**: docker
- **Installation root**: `/usr/bin`

## Step 6: Test Docker in Jenkins Pipeline

### Create Test Pipeline

1. **New Item** → **Pipeline**
2. Name: `docker-test`
3. Pipeline script:

```groovy
pipeline {
    agent any
    
    stages {
        stage('Test Docker') {
            steps {
                script {
                    sh 'docker --version'
                    sh 'docker ps'
                    sh 'docker images'
                }
            }
        }
        
        stage('Run Container') {
            steps {
                script {
                    sh 'docker run hello-world'
                }
            }
        }
    }
}
```

4. **Save** and **Build Now**

## Dockerfile Basics

### Simple Node.js Application

```dockerfile
# Use official Node.js image
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install --production

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node healthcheck.js || exit 1

# Run application
CMD ["node", "server.js"]
```

### Multi-Stage Build (Optimized)

```dockerfile
# Build stage
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Production stage
FROM node:18-alpine

WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY package*.json ./

EXPOSE 3000

USER node

CMD ["node", "dist/server.js"]
```

### Python Application

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["python", "app.py"]
```

### Java Application

```dockerfile
FROM maven:3.9-eclipse-temurin-17 AS build

WORKDIR /app
COPY pom.xml .
COPY src ./src

RUN mvn clean package -DskipTests

FROM eclipse-temurin:17-jre-alpine

WORKDIR /app
COPY --from=build /app/target/*.jar app.jar

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "app.jar"]
```

## Common Docker Commands for CI/CD

### Build Image

```bash
# Basic build
docker build -t myapp:latest .

# Build with tag
docker build -t myapp:v1.0.0 .

# Build with build args
docker build --build-arg VERSION=1.0.0 -t myapp:latest .

# Build from specific Dockerfile
docker build -f Dockerfile.prod -t myapp:prod .
```

### Tag Image

```bash
# Tag for Docker Hub
docker tag myapp:latest username/myapp:latest
docker tag myapp:latest username/myapp:v1.0.0

# Tag for private registry
docker tag myapp:latest registry.example.com/myapp:latest
```

### Push Image

```bash
# Login to Docker Hub
docker login

# Push image
docker push username/myapp:latest
docker push username/myapp:v1.0.0

# Login to private registry
docker login registry.example.com

# Push to private registry
docker push registry.example.com/myapp:latest
```

### Pull Image

```bash
# Pull from Docker Hub
docker pull username/myapp:latest

# Pull specific version
docker pull username/myapp:v1.0.0
```

## Fixing Permission Errors

### Error: Permission Denied

**Symptom**:
```
Got permission denied while trying to connect to the Docker daemon socket
```

**Solution 1**: Add user to docker group
```bash
sudo usermod -aG docker jenkins
sudo systemctl restart jenkins
```

**Solution 2**: Temporary fix (not recommended for production)
```bash
sudo chmod 666 /var/run/docker.sock
```

**Solution 3**: Restart Docker daemon
```bash
sudo systemctl restart docker
```

### Error: Cannot Connect to Docker Daemon

**Symptom**:
```
Cannot connect to the Docker daemon at unix:///var/run/docker.sock
```

**Solution**:
```bash
# Check if Docker is running
sudo systemctl status docker

# Start Docker
sudo systemctl start docker

# Check socket permissions
ls -l /var/run/docker.sock
```

## Docker Registry Configuration

### Docker Hub

```bash
# Login
docker login

# Or with credentials
docker login -u username -p password
```

### AWS ECR

```bash
# Install AWS CLI
sudo apt install -y awscli

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
```

### Google Container Registry (GCR)

```bash
# Install gcloud
curl https://sdk.cloud.google.com | bash

# Login
gcloud auth configure-docker
```

### Private Registry

```bash
# Login to private registry
docker login registry.example.com

# With credentials
docker login registry.example.com -u username -p password
```

## Best Practices

### Dockerfile Best Practices

1. ✅ **Use official base images**
2. ✅ **Use specific tags** (not `latest`)
3. ✅ **Minimize layers** - combine RUN commands
4. ✅ **Use multi-stage builds** for smaller images
5. ✅ **Run as non-root user**
6. ✅ **Use .dockerignore** file
7. ✅ **Add health checks**
8. ✅ **Scan for vulnerabilities**

### .dockerignore Example

```
node_modules
npm-debug.log
.git
.gitignore
README.md
.env
.DS_Store
*.md
.vscode
.idea
```

### Security Best Practices

1. ✅ **Scan images** with Trivy or Clair
2. ✅ **Use minimal base images** (alpine, distroless)
3. ✅ **Don't store secrets** in images
4. ✅ **Keep images updated**
5. ✅ **Use Docker Content Trust**
6. ✅ **Limit container resources**

## Troubleshooting

### Issue 1: Build Fails with "No Space Left"

**Solution**:
```bash
# Clean up Docker
docker system prune -a

# Remove unused volumes
docker volume prune

# Check disk space
df -h
```

### Issue 2: Slow Build Times

**Solution**:
```bash
# Use BuildKit
export DOCKER_BUILDKIT=1
docker build -t myapp .

# Or enable in daemon.json
{
  "features": {
    "buildkit": true
  }
}
```

### Issue 3: Image Too Large

**Solution**:
- Use multi-stage builds
- Use alpine base images
- Remove unnecessary files
- Combine RUN commands

```dockerfile
# Bad - multiple layers
RUN apt-get update
RUN apt-get install -y package1
RUN apt-get install -y package2

# Good - single layer
RUN apt-get update && apt-get install -y \
    package1 \
    package2 \
    && rm -rf /var/lib/apt/lists/*
```

## Next Steps

Proceed to [Kubernetes Access](06-kubernetes-access.md) to configure kubectl and Helm for deployments.
