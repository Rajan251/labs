# GitLab Runner Setup Guide

This guide provides step-by-step instructions for installing, configuring, and managing GitLab Runners.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Registration](#registration)
4. [Configuration](#configuration)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- **Operating System**: Linux (Ubuntu/Debian recommended), macOS, or Windows
- **Docker**: v20.10+ (for Docker executor)
- **Kubernetes**: v1.24+ (for Kubernetes executor)
- **GitLab Access**: Project Maintainer or Owner role
- **Network**: Access to GitLab instance and container registries

---

## Installation

### Ubuntu/Debian

```bash
# Add GitLab's official repository
curl -L "https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.deb.sh" | sudo bash

# Install GitLab Runner
sudo apt-get update
sudo apt-get install gitlab-runner

# Verify installation
gitlab-runner --version
```

### RHEL/CentOS/Fedora

```bash
# Add GitLab's official repository
curl -L "https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.rpm.sh" | sudo bash

# Install GitLab Runner
sudo yum install gitlab-runner

# Verify installation
gitlab-runner --version
```

### macOS

```bash
# Using Homebrew
brew install gitlab-runner

# Start the runner service
brew services start gitlab-runner

# Verify installation
gitlab-runner --version
```

### Docker

```bash
# Run GitLab Runner in a Docker container
docker run -d --name gitlab-runner --restart always \
  -v /srv/gitlab-runner/config:/etc/gitlab-runner \
  -v /var/run/docker.sock:/var/run/docker.sock \
  gitlab/gitlab-runner:latest

# Verify installation
docker exec gitlab-runner gitlab-runner --version
```

---

## Registration

### Get Registration Token

1. Go to your GitLab project
2. Navigate to **Settings > CI/CD > Runners**
3. Expand **Specific runners**
4. Copy the registration token

### Interactive Registration

```bash
sudo gitlab-runner register
```

You'll be prompted for:

```
Enter the GitLab instance URL (for example, https://gitlab.com/):
https://gitlab.com/

Enter the registration token:
YOUR_REGISTRATION_TOKEN

Enter a description for the runner:
my-docker-runner

Enter tags for the runner (comma-separated):
docker,linux,production

Enter optional maintenance note for the runner:
Production Docker runner

Enter an executor: custom, docker, parallels, shell, ssh, virtualbox, docker+machine, kubernetes:
docker

Enter the default Docker image (for example, ruby:2.7):
alpine:latest
```

### Non-Interactive Registration

```bash
sudo gitlab-runner register \
  --non-interactive \
  --url "https://gitlab.com/" \
  --registration-token "YOUR_REGISTRATION_TOKEN" \
  --executor "docker" \
  --docker-image "alpine:latest" \
  --description "docker-runner" \
  --tag-list "docker,linux" \
  --run-untagged="true" \
  --locked="false" \
  --docker-privileged="true" \
  --docker-volumes "/certs/client" \
  --docker-volumes "/cache"
```

### Register with Different Executors

#### Shell Executor

```bash
sudo gitlab-runner register \
  --non-interactive \
  --url "https://gitlab.com/" \
  --registration-token "YOUR_TOKEN" \
  --executor "shell" \
  --description "shell-runner" \
  --tag-list "shell,linux"
```

#### Kubernetes Executor

```bash
sudo gitlab-runner register \
  --non-interactive \
  --url "https://gitlab.com/" \
  --registration-token "YOUR_TOKEN" \
  --executor "kubernetes" \
  --description "k8s-runner" \
  --tag-list "kubernetes,production" \
  --kubernetes-host "https://kubernetes.example.com" \
  --kubernetes-namespace "gitlab-runner"
```

---

## Configuration

### Configuration File Location

- **Linux**: `/etc/gitlab-runner/config.toml`
- **macOS**: `/usr/local/etc/gitlab-runner/config.toml`
- **Docker**: `/srv/gitlab-runner/config/config.toml` (mounted volume)

### Recommended config.toml

See `runner-config.toml` in this directory for a complete example.

### Key Configuration Options

#### Concurrency

```toml
concurrent = 4  # Number of jobs to run simultaneously
check_interval = 0  # How often to check for new jobs (0 = default 3s)
```

#### Docker Executor Settings

```toml
[[runners]]
  [runners.docker]
    image = "alpine:latest"
    privileged = true  # Required for Docker-in-Docker
    volumes = ["/cache", "/certs/client"]
    cpus = "2"
    memory = "4g"
```

#### Cache Configuration

```toml
[[runners]]
  [runners.cache]
    Type = "s3"
    Shared = true
    [runners.cache.s3]
      ServerAddress = "s3.amazonaws.com"
      AccessKey = "YOUR_ACCESS_KEY"
      SecretKey = "YOUR_SECRET_KEY"
      BucketName = "gitlab-runner-cache"
```

---

## Verification

### Check Runner Status

```bash
# Check if runner service is running
sudo gitlab-runner status

# List registered runners
sudo gitlab-runner list

# Verify runner configuration
sudo gitlab-runner verify
```

### View Runner Logs

```bash
# View logs (systemd)
sudo journalctl -u gitlab-runner -f

# View logs (Docker)
docker logs -f gitlab-runner
```

### Test Runner

```bash
# Run a test job locally
sudo gitlab-runner exec docker test --docker-image=alpine:latest
```

### Check in GitLab UI

1. Go to **Settings > CI/CD > Runners**
2. Your runner should appear with a green dot (active)
3. Check "Last contact" timestamp

---

## Troubleshooting

### Runner Not Appearing in GitLab

**Cause**: Registration failed or runner not started

**Solution**:
```bash
# Verify registration
sudo gitlab-runner verify

# Restart runner
sudo gitlab-runner restart

# Check logs
sudo journalctl -u gitlab-runner -f
```

### Runner Not Picking Up Jobs

**Cause**: Tags mismatch or runner paused

**Solution**:
1. Check job tags match runner tags
2. Ensure runner is not paused in GitLab UI
3. Check `run-untagged` setting in config.toml

### Docker Permission Denied

**Cause**: Runner user doesn't have Docker permissions

**Solution**:
```bash
# Add gitlab-runner user to docker group
sudo usermod -aG docker gitlab-runner

# Restart runner
sudo gitlab-runner restart
```

### Out of Disk Space

**Cause**: Docker images and containers filling disk

**Solution**:
```bash
# Clean up Docker
docker system prune -a --volumes

# Set up automatic cleanup
docker system prune -a --volumes --filter "until=24h"
```

---

## Security Best Practices

1. **Use Protected Runners** for production deployments
2. **Limit runner tags** to prevent unauthorized job execution
3. **Enable runner locking** to specific projects
4. **Rotate registration tokens** regularly
5. **Set resource limits** to prevent resource exhaustion
6. **Use separate runners** for different environments
7. **Monitor runner logs** for suspicious activity

---

## Maintenance

### Update Runner

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install gitlab-runner

# Docker
docker pull gitlab/gitlab-runner:latest
docker stop gitlab-runner
docker rm gitlab-runner
# Re-run docker run command with new image
```

### Unregister Runner

```bash
# Unregister specific runner
sudo gitlab-runner unregister --name my-runner

# Unregister all runners
sudo gitlab-runner unregister --all-runners
```

### Backup Configuration

```bash
# Backup config.toml
sudo cp /etc/gitlab-runner/config.toml /etc/gitlab-runner/config.toml.backup
```

---

## Additional Resources

- [GitLab Runner Documentation](https://docs.gitlab.com/runner/)
- [GitLab Runner Executors](https://docs.gitlab.com/runner/executors/)
- [GitLab Runner Advanced Configuration](https://docs.gitlab.com/runner/configuration/advanced-configuration.html)
