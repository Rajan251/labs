# DEPLOY-02: Docker Installation

Complete checklist for installing Docker and Docker Compose on Ubuntu.

**Estimated Time:** 15 minutes  
**Prerequisites:** Completed DEPLOY-01-SERVER-SETUP.md

---

## ✅ Phase 1: Remove Old Docker Versions (2 minutes)

### 1.1 Uninstall Conflicting Packages
- [ ] Remove old Docker versions:
  ```bash
  sudo apt remove -y docker docker-engine docker.io containerd runc
  ```
- [ ] Verify removal:
  ```bash
  docker --version
  # Expected: command not found
  ```

---

## ✅ Phase 2: Install Docker Engine (5 minutes)

### 2.1 Setup Docker Repository
- [ ] Update package index:
  ```bash
  sudo apt update
  ```
- [ ] Install prerequisites:
  ```bash
  sudo apt install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release
  ```
- [ ] Add Docker's official GPG key:
  ```bash
  sudo mkdir -p /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  ```
- [ ] Set up Docker repository:
  ```bash
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/ubuntu \
    $(lsb_release -cs) stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
  ```

### 2.2 Install Docker
- [ ] Update package index:
  ```bash
  sudo apt update
  ```
- [ ] Install Docker Engine:
  ```bash
  sudo apt install -y \
    docker-ce \
    docker-ce-cli \
    containerd.io \
    docker-buildx-plugin \
    docker-compose-plugin
  ```
- [ ] Verify Docker installation:
  ```bash
  docker --version
  # Expected: Docker version 24.0+ or higher
  ```
- [ ] Check Docker Compose:
  ```bash
  docker compose version
  # Expected: Docker Compose version 2.0+ or higher
  ```

### 2.3 Start Docker Service
- [ ] Start Docker:
  ```bash
  sudo systemctl start docker
  ```
- [ ] Enable Docker to start on boot:
  ```bash
  sudo systemctl enable docker
  ```
- [ ] Verify Docker is running:
  ```bash
  sudo systemctl status docker
  # Expected: active (running)
  ```

---

## ✅ Phase 3: Configure Docker (5 minutes)

### 3.1 Add User to Docker Group
- [ ] Add deploy user to docker group:
  ```bash
  sudo usermod -aG docker deploy
  ```
- [ ] Verify group membership:
  ```bash
  groups deploy
  # Expected: deploy sudo docker
  ```
- [ ] **IMPORTANT:** Logout and login again for group changes to take effect:
  ```bash
  exit
  # Then SSH back in
  ssh deploy@your-server-ip
  ```
- [ ] Test Docker without sudo:
  ```bash
  docker run hello-world
  # Expected: Hello from Docker! message
  ```

### 3.2 Configure Docker Daemon
- [ ] Create Docker daemon config directory:
  ```bash
  sudo mkdir -p /etc/docker
  ```
- [ ] Create daemon.json:
  ```bash
  sudo nano /etc/docker/daemon.json
  ```
- [ ] Add this configuration:
  ```json
  {
    "log-driver": "json-file",
    "log-opts": {
      "max-size": "10m",
      "max-file": "3"
    },
    "storage-driver": "overlay2",
    "default-address-pools": [
      {
        "base": "172.17.0.0/16",
        "size": 24
      }
    ],
    "live-restore": true,
    "userland-proxy": false
  }
  ```
- [ ] Restart Docker to apply changes:
  ```bash
  sudo systemctl restart docker
  ```
- [ ] Verify configuration:
  ```bash
  docker info | grep -A 5 "Log"
  docker info | grep "Storage Driver"
  ```

### 3.3 Configure Docker Resource Limits
- [ ] Create systemd override directory:
  ```bash
  sudo mkdir -p /etc/systemd/system/docker.service.d
  ```
- [ ] Create override file:
  ```bash
  sudo nano /etc/systemd/system/docker.service.d/override.conf
  ```
- [ ] Add resource limits:
  ```ini
  [Service]
  LimitNOFILE=1048576
  LimitNPROC=infinity
  LimitCORE=infinity
  TasksMax=infinity
  ```
- [ ] Reload systemd:
  ```bash
  sudo systemctl daemon-reload
  ```
- [ ] Restart Docker:
  ```bash
  sudo systemctl restart docker
  ```

---

## ✅ Phase 4: Install Docker Compose Standalone (Optional) (2 minutes)

**Note:** Docker Compose Plugin is already installed. This step is optional for standalone binary.

### 4.1 Download Docker Compose Binary
- [ ] Download latest version:
  ```bash
  sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
    -o /usr/local/bin/docker-compose
  ```
- [ ] Make executable:
  ```bash
  sudo chmod +x /usr/local/bin/docker-compose
  ```
- [ ] Verify installation:
  ```bash
  docker-compose --version
  # Expected: Docker Compose version 2.x.x
  ```

---

## ✅ Phase 5: Configure Firewall for Docker (2 minutes)

### 5.1 Allow Docker Network
- [ ] Docker creates its own iptables rules, verify:
  ```bash
  sudo iptables -L -n | grep DOCKER
  ```
- [ ] If using UFW, allow Docker subnet:
  ```bash
  sudo ufw allow from 172.17.0.0/16
  ```
- [ ] Reload UFW:
  ```bash
  sudo ufw reload
  ```

---

## ✅ Phase 6: Setup Docker Directories (2 minutes)

### 6.1 Create Docker Data Directories
- [ ] Create volumes directory:
  ```bash
  sudo mkdir -p /var/lib/docker/volumes
  ```
- [ ] Create backup directory:
  ```bash
  sudo mkdir -p /opt/docker-backups
  sudo chown deploy:deploy /opt/docker-backups
  ```
- [ ] Create compose files directory:
  ```bash
  mkdir -p /opt/microservices/docker
  ```

### 6.2 Configure Log Rotation
- [ ] Create Docker logrotate config:
  ```bash
  sudo nano /etc/logrotate.d/docker-container
  ```
- [ ] Add configuration:
  ```
  /var/lib/docker/containers/*/*.log {
    rotate 7
    daily
    compress
    size=10M
    missingok
    delaycompress
    copytruncate
  }
  ```
- [ ] Test logrotate:
  ```bash
  sudo logrotate -f /etc/logrotate.d/docker-container
  ```

---

## ✅ Phase 7: Test Docker Installation (3 minutes)

### 7.1 Run Test Containers
- [ ] Test basic container:
  ```bash
  docker run hello-world
  # Expected: Success message
  ```
- [ ] Test interactive container:
  ```bash
  docker run -it ubuntu:22.04 bash
  # Inside container:
  cat /etc/os-release
  exit
  ```
- [ ] Test Docker Compose:
  ```bash
  cd /opt/microservices
  cat > docker-compose-test.yml << 'EOF'
  version: '3.8'
  services:
    test:
      image: nginx:alpine
      ports:
        - "8080:80"
  EOF
  ```
- [ ] Start test service:
  ```bash
  docker compose -f docker-compose-test.yml up -d
  ```
- [ ] Test service:
  ```bash
  curl http://localhost:8080
  # Expected: Nginx welcome page
  ```
- [ ] Stop and remove test:
  ```bash
  docker compose -f docker-compose-test.yml down
  rm docker-compose-test.yml
  ```

### 7.2 Verify Docker Info
- [ ] Check Docker system info:
  ```bash
  docker info
  ```
- [ ] Verify these settings:
  ```
  Storage Driver: overlay2
  Logging Driver: json-file
  Cgroup Driver: systemd
  ```
- [ ] Check Docker version:
  ```bash
  docker version
  ```
- [ ] List Docker networks:
  ```bash
  docker network ls
  # Expected: bridge, host, none
  ```

---

## ✅ Phase 8: Install Docker Monitoring Tools (2 minutes)

### 8.1 Install ctop (Container Top)
- [ ] Download ctop:
  ```bash
  sudo wget https://github.com/bcicen/ctop/releases/download/v0.7.7/ctop-0.7.7-linux-amd64 \
    -O /usr/local/bin/ctop
  ```
- [ ] Make executable:
  ```bash
  sudo chmod +x /usr/local/bin/ctop
  ```
- [ ] Test ctop:
  ```bash
  ctop
  # Press q to quit
  ```

### 8.2 Install lazydocker (Optional)
- [ ] Download lazydocker:
  ```bash
  curl https://raw.githubusercontent.com/jesseduffield/lazydocker/master/scripts/install_update_linux.sh | bash
  ```
- [ ] Test lazydocker:
  ```bash
  lazydocker
  # Press q to quit
  ```

---

## ✅ Phase 9: Configure Docker Security (2 minutes)

### 9.1 Enable Docker Content Trust
- [ ] Add to deploy user's .bashrc:
  ```bash
  echo 'export DOCKER_CONTENT_TRUST=1' >> ~/.bashrc
  source ~/.bashrc
  ```
- [ ] Verify:
  ```bash
  echo $DOCKER_CONTENT_TRUST
  # Expected: 1
  ```

### 9.2 Configure Docker Socket Permissions
- [ ] Check Docker socket permissions:
  ```bash
  ls -l /var/run/docker.sock
  # Expected: srw-rw---- 1 root docker
  ```
- [ ] Verify deploy user can access:
  ```bash
  docker ps
  # Should work without sudo
  ```

---

## ✅ Phase 10: Cleanup and Verification (2 minutes)

### 10.1 Clean Up Test Containers
- [ ] Remove test containers:
  ```bash
  docker container prune -f
  ```
- [ ] Remove test images:
  ```bash
  docker image prune -a -f
  ```
- [ ] Check disk usage:
  ```bash
  docker system df
  ```

### 10.2 Final Verification
- [ ] Verify Docker service:
  ```bash
  sudo systemctl status docker
  # Expected: active (running)
  ```
- [ ] Verify Docker Compose:
  ```bash
  docker compose version
  # Expected: version 2.x.x
  ```
- [ ] Verify user permissions:
  ```bash
  docker ps
  # Should work without sudo
  ```
- [ ] Check Docker networks:
  ```bash
  docker network ls
  ```
- [ ] Check Docker volumes:
  ```bash
  docker volume ls
  ```

---

## ✅ Final Checklist

- [ ] Docker Engine installed (version 24.0+)
- [ ] Docker Compose Plugin installed (version 2.0+)
- [ ] Docker service running and enabled
- [ ] Deploy user in docker group
- [ ] Can run docker commands without sudo
- [ ] Docker daemon configured with logging limits
- [ ] Resource limits configured
- [ ] Test containers run successfully
- [ ] Monitoring tools installed (ctop)
- [ ] Log rotation configured
- [ ] Docker security enabled

---

## 🎯 Success Criteria

Docker installation is complete when:
- ✅ `docker --version` shows 24.0+
- ✅ `docker compose version` shows 2.0+
- ✅ `docker ps` works without sudo
- ✅ `docker run hello-world` succeeds
- ✅ Docker service is active and enabled
- ✅ Log rotation configured

---

## 🚨 Troubleshooting

**Docker commands require sudo:**
```bash
# Verify user is in docker group
groups deploy

# If not, add and re-login
sudo usermod -aG docker deploy
exit
# SSH back in
```

**Docker service won't start:**
```bash
# Check logs
sudo journalctl -u docker.service -n 50

# Check daemon config
sudo dockerd --validate

# Restart service
sudo systemctl restart docker
```

**Permission denied on docker.sock:**
```bash
# Check socket permissions
ls -l /var/run/docker.sock

# Fix permissions
sudo chmod 666 /var/run/docker.sock
sudo systemctl restart docker
```

**Docker Compose not found:**
```bash
# Install plugin
sudo apt install docker-compose-plugin

# Or install standalone
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

---

## 📝 Important Commands Reference

```bash
# Check Docker status
sudo systemctl status docker

# View Docker logs
sudo journalctl -u docker.service -f

# Check Docker info
docker info

# List all containers
docker ps -a

# List all images
docker images

# Check disk usage
docker system df

# Clean up everything
docker system prune -a --volumes

# Monitor containers
ctop
# or
docker stats
```

---

**Next Step:** Proceed to [DEPLOY-03-MONGODB-SETUP.md](DEPLOY-03-MONGODB-SETUP.md)
