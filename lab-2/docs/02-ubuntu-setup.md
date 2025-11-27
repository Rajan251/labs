# 2. Ubuntu Server Setup

## Prerequisites

### Hardware Requirements

| Component | Minimum | Recommended | Production |
|-----------|---------|-------------|------------|
| **CPU** | 2 cores | 4 cores | 8+ cores |
| **RAM** | 4 GB | 8 GB | 16+ GB |
| **Disk** | 30 GB | 50 GB | 100+ GB SSD |
| **Network** | 100 Mbps | 1 Gbps | 1+ Gbps |

### Software Requirements

- **OS**: Ubuntu 22.04 LTS or Ubuntu 20.04 LTS
- **Architecture**: x86_64 (amd64)
- **Access**: Root or sudo privileges
- **Network**: Static IP recommended for production

## Initial Server Configuration

### 1. Update System

```bash
# Update package lists
sudo apt update

# Upgrade installed packages
sudo apt upgrade -y

# Remove unnecessary packages
sudo apt autoremove -y

# Verify Ubuntu version
lsb_release -a
```

**Expected Output**:
```
Distributor ID: Ubuntu
Description:    Ubuntu 22.04.3 LTS
Release:        22.04
Codename:       jammy
```

### 2. Install Essential Packages

```bash
# Install common utilities
sudo apt install -y \
    curl \
    wget \
    git \
    vim \
    nano \
    net-tools \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    build-essential \
    unzip \
    tree

# Verify installations
curl --version
git --version
```

### 3. Configure Hostname

```bash
# Set hostname
sudo hostnamectl set-hostname jenkins-server

# Verify
hostnamectl

# Update /etc/hosts
sudo nano /etc/hosts
```

Add this line:
```
127.0.0.1   jenkins-server
```

### 4. Configure Firewall (UFW)

```bash
# Check firewall status
sudo ufw status

# Allow SSH (IMPORTANT: Do this first!)
sudo ufw allow 22/tcp
sudo ufw allow OpenSSH

# Allow Jenkins
sudo ufw allow 8080/tcp comment 'Jenkins Web UI'

# Allow Jenkins agent communication
sudo ufw allow 50000/tcp comment 'Jenkins Agent'

# Allow HTTP/HTTPS (if using reverse proxy)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Verify rules
sudo ufw status numbered
```

**Expected Output**:
```
Status: active

     To                         Action      From
     --                         ------      ----
[ 1] 22/tcp                     ALLOW IN    Anywhere
[ 2] 8080/tcp                   ALLOW IN    Anywhere    # Jenkins Web UI
[ 3] 50000/tcp                  ALLOW IN    Anywhere    # Jenkins Agent
```

### 5. Create System Users

```bash
# Jenkins user (created automatically during installation)
# But you can create it manually if needed:

# Create jenkins user
sudo useradd -m -s /bin/bash jenkins

# Set password (optional)
sudo passwd jenkins

# Add to sudo group (if needed)
sudo usermod -aG sudo jenkins

# Verify user
id jenkins
```

### 6. Configure SSH (Optional but Recommended)

```bash
# Backup SSH config
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup

# Edit SSH config
sudo nano /etc/ssh/sshd_config
```

**Recommended settings**:
```
# Disable root login
PermitRootLogin no

# Use SSH keys only (disable password authentication)
PasswordAuthentication no

# Allow specific users
AllowUsers your_username jenkins
```

Restart SSH:
```bash
sudo systemctl restart sshd
```

### 7. Configure Time Synchronization

```bash
# Install NTP
sudo apt install -y ntp

# Enable and start NTP
sudo systemctl enable ntp
sudo systemctl start ntp

# Verify time sync
timedatectl status
```

### 8. Increase File Limits (for Jenkins)

```bash
# Edit limits.conf
sudo nano /etc/security/limits.conf
```

Add these lines:
```
jenkins soft nofile 65536
jenkins hard nofile 65536
jenkins soft nproc 32768
jenkins hard nproc 32768
```

### 9. Configure Swap (if needed)

```bash
# Check current swap
free -h

# Create 4GB swap file
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Verify
free -h
```

### 10. Set Up Log Rotation

```bash
# Create logrotate config for Jenkins
sudo nano /etc/logrotate.d/jenkins
```

Add:
```
/var/log/jenkins/jenkins.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 jenkins jenkins
}
```

## Network Configuration

### Static IP Configuration (Ubuntu 22.04 with Netplan)

```bash
# Backup current config
sudo cp /etc/netplan/00-installer-config.yaml /etc/netplan/00-installer-config.yaml.backup

# Edit netplan config
sudo nano /etc/netplan/00-installer-config.yaml
```

**Example configuration**:
```yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    ens33:  # Your interface name (use 'ip a' to find it)
      dhcp4: no
      addresses:
        - 192.168.1.100/24
      gateway4: 192.168.1.1
      nameservers:
        addresses:
          - 8.8.8.8
          - 8.8.4.4
```

Apply configuration:
```bash
# Test configuration
sudo netplan try

# Apply permanently
sudo netplan apply

# Verify
ip addr show
```

## Security Hardening

### 1. Install Fail2Ban

```bash
# Install fail2ban
sudo apt install -y fail2ban

# Create local config
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local

# Edit config
sudo nano /etc/fail2ban/jail.local
```

Enable SSH protection:
```ini
[sshd]
enabled = true
port = 22
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
```

Start fail2ban:
```bash
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
sudo fail2ban-client status
```

### 2. Install and Configure Unattended Upgrades

```bash
# Install
sudo apt install -y unattended-upgrades

# Configure
sudo dpkg-reconfigure -plow unattended-upgrades

# Edit config
sudo nano /etc/apt/apt.conf.d/50unattended-upgrades
```

Enable automatic security updates:
```
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
};
```

## Verification Checklist

Run these commands to verify your setup:

```bash
# System info
echo "=== System Information ==="
uname -a
lsb_release -a

# Resources
echo "=== Resources ==="
free -h
df -h

# Network
echo "=== Network ==="
ip addr show
ip route show

# Firewall
echo "=== Firewall ==="
sudo ufw status

# Services
echo "=== Services ==="
systemctl status ssh
systemctl status ntp

# Time
echo "=== Time ==="
timedatectl

# Disk I/O
echo "=== Disk Performance ==="
sudo hdparm -Tt /dev/sda
```

## Common Issues and Solutions

### Issue 1: Cannot Connect via SSH

**Problem**: Connection refused or timeout

**Solutions**:
```bash
# Check SSH service
sudo systemctl status sshd

# Check firewall
sudo ufw status

# Check SSH config
sudo nano /etc/ssh/sshd_config

# Restart SSH
sudo systemctl restart sshd
```

### Issue 2: Disk Space Full

**Problem**: `/var` or `/` partition full

**Solutions**:
```bash
# Check disk usage
df -h

# Find large files
sudo du -sh /* | sort -h

# Clean apt cache
sudo apt clean
sudo apt autoremove

# Clean journal logs
sudo journalctl --vacuum-time=7d

# Clean Docker (if installed)
docker system prune -a
```

### Issue 3: Slow Network Performance

**Problem**: Network is slow or unstable

**Solutions**:
```bash
# Test network speed
sudo apt install speedtest-cli
speedtest-cli

# Check network errors
ip -s link

# Test DNS
nslookup google.com

# Change DNS if needed
sudo nano /etc/netplan/00-installer-config.yaml
```

### Issue 4: Time Sync Issues

**Problem**: System time is incorrect

**Solutions**:
```bash
# Check time
timedatectl

# Sync time manually
sudo timedatectl set-ntp true

# Restart NTP
sudo systemctl restart ntp

# Force sync
sudo ntpdate -s time.nist.gov
```

## Next Steps

Your Ubuntu server is now ready for Jenkins installation. Proceed to [Jenkins Installation](03-jenkins-installation.md).
