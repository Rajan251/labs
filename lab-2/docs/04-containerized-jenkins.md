# 4. Containerized Jenkins

## Overview

Running Jenkins in a Docker container offers several advantages:
- ✅ Easy to upgrade/rollback
- ✅ Isolated environment
- ✅ Portable configuration
- ✅ Quick setup and teardown

## Prerequisites

- Docker installed (see [Docker Integration](05-docker-integration.md))
- Basic Docker knowledge
- At least 4 GB RAM

## Advantages vs Disadvantages

### Advantages

| Benefit | Description |
|---------|-------------|
| **Portability** | Move Jenkins between servers easily |
| **Isolation** | Doesn't affect host system |
| **Version Control** | Easy to test different Jenkins versions |
| **Quick Setup** | Up and running in minutes |
| **Easy Backup** | Just backup volumes |

### Disadvantages

| Challenge | Description |
|-----------|-------------|
| **Docker-in-Docker** | Complex setup for building Docker images |
| **Performance** | Slight overhead compared to native |
| **Networking** | Additional network configuration |
| **Volume Management** | Need to manage persistent data |

## Method 1: Basic Jenkins Container

### Create Volume for Persistence

```bash
# Create Docker volume for Jenkins data
docker volume create jenkins_home

# Verify
docker volume ls
```

### Run Jenkins Container

```bash
docker run -d \
  --name jenkins \
  --restart=unless-stopped \
  -p 8080:8080 \
  -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  jenkins/jenkins:lts-jdk17
```

**Parameters explained**:
- `-d`: Run in detached mode
- `--name jenkins`: Container name
- `--restart=unless-stopped`: Auto-restart on failure
- `-p 8080:8080`: Web UI port
- `-p 50000:50000`: Agent communication port
- `-v jenkins_home:/var/jenkins_home`: Persistent storage
- `jenkins/jenkins:lts-jdk17`: Official Jenkins image with Java 17

### Get Initial Password

```bash
# View initial admin password
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

### Access Jenkins

Open browser: `http://<server-ip>:8080`

## Method 2: Jenkins with Docker Socket Access

This allows Jenkins to build Docker images using the host's Docker daemon.

```bash
docker run -d \
  --name jenkins \
  --restart=unless-stopped \
  -p 8080:8080 \
  -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(which docker):/usr/bin/docker \
  jenkins/jenkins:lts-jdk17
```

**Additional parameters**:
- `-v /var/run/docker.sock:/var/run/docker.sock`: Mount Docker socket
- `-v $(which docker):/usr/bin/docker`: Mount Docker CLI

### Fix Permissions

```bash
# Get docker group ID
DOCKER_GID=$(getent group docker | cut -d: -f3)

# Run with docker group
docker run -d \
  --name jenkins \
  --restart=unless-stopped \
  -p 8080:8080 \
  -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  --group-add $DOCKER_GID \
  jenkins/jenkins:lts-jdk17
```

## Method 3: Custom Jenkins Image with Docker CLI

### Create Dockerfile

Create `Dockerfile.jenkins`:

```dockerfile
FROM jenkins/jenkins:lts-jdk17

USER root

# Install Docker CLI
RUN apt-get update && apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker's official GPG key
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Set up Docker repository
RUN echo \
  "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker CLI
RUN apt-get update && apt-get install -y docker-ce-cli

# Install kubectl
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
    install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl && \
    rm kubectl

# Install Helm
RUN curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Clean up
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

USER jenkins

# Pre-install plugins (optional)
RUN jenkins-plugin-cli --plugins \
    docker-workflow \
    kubernetes \
    git \
    pipeline-stage-view \
    blueocean
```

### Build Custom Image

```bash
# Build image
docker build -t jenkins-docker:latest -f Dockerfile.jenkins .

# Verify
docker images | grep jenkins-docker
```

### Run Custom Jenkins

```bash
docker run -d \
  --name jenkins \
  --restart=unless-stopped \
  -p 8080:8080 \
  -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  --group-add $(getent group docker | cut -d: -f3) \
  jenkins-docker:latest
```

## Method 4: Docker Compose Setup

### Create docker-compose.yml

```yaml
version: '3.8'

services:
  jenkins:
    image: jenkins/jenkins:lts-jdk17
    container_name: jenkins
    restart: unless-stopped
    privileged: true
    user: root
    ports:
      - "8080:8080"
      - "50000:50000"
    volumes:
      - jenkins_home:/var/jenkins_home
      - /var/run/docker.sock:/var/run/docker.sock
      - /usr/bin/docker:/usr/bin/docker
    environment:
      - JAVA_OPTS=-Djenkins.install.runSetupWizard=false
      - JENKINS_OPTS=--prefix=/jenkins

volumes:
  jenkins_home:
    driver: local
```

### Start Jenkins with Docker Compose

```bash
# Start Jenkins
docker-compose up -d

# View logs
docker-compose logs -f jenkins

# Stop Jenkins
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Docker-in-Docker (DinD) Setup

For complete isolation, use Docker-in-Docker:

### Create docker-compose-dind.yml

```yaml
version: '3.8'

services:
  docker-dind:
    image: docker:dind
    container_name: jenkins-docker
    restart: unless-stopped
    privileged: true
    environment:
      - DOCKER_TLS_CERTDIR=/certs
    volumes:
      - jenkins-docker-certs:/certs/client
      - jenkins-data:/var/jenkins_home
    networks:
      jenkins:
        aliases:
          - docker
    command: --storage-driver=overlay2

  jenkins:
    image: jenkins/jenkins:lts-jdk17
    container_name: jenkins
    restart: unless-stopped
    user: root
    ports:
      - "8080:8080"
      - "50000:50000"
    volumes:
      - jenkins-data:/var/jenkins_home
      - jenkins-docker-certs:/certs/client:ro
    environment:
      - DOCKER_HOST=tcp://docker:2376
      - DOCKER_CERT_PATH=/certs/client
      - DOCKER_TLS_VERIFY=1
    networks:
      - jenkins
    depends_on:
      - docker-dind

networks:
  jenkins:
    driver: bridge

volumes:
  jenkins-data:
  jenkins-docker-certs:
```

### Start DinD Setup

```bash
docker-compose -f docker-compose-dind.yml up -d
```

## Container Management

### View Jenkins Logs

```bash
# Follow logs
docker logs -f jenkins

# Last 100 lines
docker logs --tail 100 jenkins

# Logs since 1 hour ago
docker logs --since 1h jenkins
```

### Execute Commands in Container

```bash
# Open bash shell
docker exec -it jenkins bash

# Run command as root
docker exec -u root -it jenkins bash

# Run single command
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

### Stop/Start/Restart Container

```bash
# Stop Jenkins
docker stop jenkins

# Start Jenkins
docker start jenkins

# Restart Jenkins
docker restart jenkins

# Remove container (keeps volume)
docker rm -f jenkins
```

### Update Jenkins

```bash
# Pull latest image
docker pull jenkins/jenkins:lts-jdk17

# Stop and remove old container
docker stop jenkins
docker rm jenkins

# Start new container with same volume
docker run -d \
  --name jenkins \
  --restart=unless-stopped \
  -p 8080:8080 \
  -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  jenkins/jenkins:lts-jdk17
```

## Backup and Restore

### Backup Jenkins Data

```bash
# Create backup directory
mkdir -p ~/jenkins-backups

# Backup volume
docker run --rm \
  -v jenkins_home:/var/jenkins_home \
  -v ~/jenkins-backups:/backup \
  ubuntu \
  tar czf /backup/jenkins-backup-$(date +%Y%m%d).tar.gz /var/jenkins_home
```

### Restore Jenkins Data

```bash
# Create new volume
docker volume create jenkins_home_restored

# Restore backup
docker run --rm \
  -v jenkins_home_restored:/var/jenkins_home \
  -v ~/jenkins-backups:/backup \
  ubuntu \
  tar xzf /backup/jenkins-backup-20240115.tar.gz -C /
```

## Troubleshooting

### Issue 1: Permission Denied on Docker Socket

**Error**:
```
permission denied while trying to connect to the Docker daemon socket
```

**Solution**:
```bash
# Get docker group ID
DOCKER_GID=$(getent group docker | cut -d: -f3)

# Add group to container
docker run -d \
  --name jenkins \
  -p 8080:8080 \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  --group-add $DOCKER_GID \
  jenkins/jenkins:lts-jdk17
```

### Issue 2: Container Keeps Restarting

**Check logs**:
```bash
docker logs jenkins
```

**Common causes**:
- Insufficient memory
- Port conflict
- Volume permission issues

**Solution**:
```bash
# Check resources
docker stats jenkins

# Check port
sudo lsof -i :8080

# Fix volume permissions
docker exec -u root jenkins chown -R jenkins:jenkins /var/jenkins_home
```

### Issue 3: Cannot Build Docker Images

**Error**:
```
docker: command not found
```

**Solution**: Use custom image with Docker CLI or mount Docker binary:
```bash
docker run -d \
  --name jenkins \
  -p 8080:8080 \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(which docker):/usr/bin/docker \
  jenkins/jenkins:lts-jdk17
```

### Issue 4: Volume Data Lost

**Prevention**: Always use named volumes, not bind mounts for critical data

```bash
# Create named volume
docker volume create jenkins_home

# Use in container
-v jenkins_home:/var/jenkins_home
```

## Best Practices

1. ✅ **Use named volumes** for data persistence
2. ✅ **Set restart policy** to `unless-stopped`
3. ✅ **Regular backups** of Jenkins volume
4. ✅ **Use specific image tags** (not `latest`)
5. ✅ **Limit container resources** with `--memory` and `--cpus`
6. ✅ **Monitor container logs** regularly
7. ✅ **Use Docker Compose** for complex setups
8. ✅ **Implement health checks** in Dockerfile

## Next Steps

Proceed to [Docker Integration](05-docker-integration.md) to configure Docker for CI/CD pipelines.
