# DEPLOY-01: Ubuntu Server Setup

Complete checklist for initial Ubuntu server configuration.

**Estimated Time:** 30 minutes  
**Prerequisites:** Fresh Ubuntu 20.04/22.04 LTS server with root access

---

## ✅ Phase 1: Initial Server Access (5 minutes)

### 1.1 Connect to Server
- [ ] Connect via SSH as root:
  ```bash
  ssh root@your-server-ip
  ```
- [ ] Verify Ubuntu version:
  ```bash
  lsb_release -a
  # Expected: Ubuntu 20.04 or 22.04 LTS
  ```
- [ ] Check available resources:
  ```bash
  # Check RAM
  free -h
  # Expected: 4GB+ total
  
  # Check CPU
  nproc
  # Expected: 2+ cores
  
  # Check disk space
  df -h
  # Expected: 50GB+ available
  ```

### 1.2 Set Hostname
- [ ] Set meaningful hostname:
  ```bash
  hostnamectl set-hostname prod-microservices-01
  ```
- [ ] Verify hostname:
  ```bash
  hostnamectl
  ```
- [ ] Update /etc/hosts:
  ```bash
  nano /etc/hosts
  # Add: 127.0.0.1 prod-microservices-01
  ```

---

## ✅ Phase 2: System Updates (10 minutes)

### 2.1 Update Package Lists
- [ ] Update package index:
  ```bash
  apt update
  ```
- [ ] Check for available updates:
  ```bash
  apt list --upgradable
  ```

### 2.2 Upgrade System
- [ ] Upgrade all packages:
  ```bash
  apt upgrade -y
  ```
- [ ] Perform full upgrade:
  ```bash
  apt full-upgrade -y
  ```
- [ ] Remove unnecessary packages:
  ```bash
  apt autoremove -y
  apt autoclean
  ```

### 2.3 Install Essential Tools
- [ ] Install basic utilities:
  ```bash
  apt install -y \
    curl \
    wget \
    git \
    vim \
    htop \
    net-tools \
    ufw \
    fail2ban \
    unattended-upgrades \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release
  ```
- [ ] Verify installations:
  ```bash
  curl --version
  git --version
  ufw --version
  ```

---

## ✅ Phase 3: User Setup (5 minutes)

### 3.1 Create Deployment User
- [ ] Create non-root user:
  ```bash
  adduser deploy
  # Set strong password when prompted
  ```
- [ ] Add user to sudo group:
  ```bash
  usermod -aG sudo deploy
  ```
- [ ] Verify sudo access:
  ```bash
  su - deploy
  sudo whoami
  # Expected: root
  exit
  ```

### 3.2 Setup SSH for Deploy User
- [ ] Create .ssh directory:
  ```bash
  mkdir -p /home/deploy/.ssh
  chmod 700 /home/deploy/.ssh
  ```
- [ ] Copy authorized keys from root (if exists):
  ```bash
  cp /root/.ssh/authorized_keys /home/deploy/.ssh/
  chown -R deploy:deploy /home/deploy/.ssh
  chmod 600 /home/deploy/.ssh/authorized_keys
  ```
- [ ] **OR** Add your SSH public key:
  ```bash
  nano /home/deploy/.ssh/authorized_keys
  # Paste your public key
  chown -R deploy:deploy /home/deploy/.ssh
  chmod 600 /home/deploy/.ssh/authorized_keys
  ```

### 3.3 Test Deploy User Access
- [ ] From your local machine, test SSH:
  ```bash
  ssh deploy@your-server-ip
  ```
- [ ] Test sudo access:
  ```bash
  sudo ls /root
  ```
- [ ] Exit and continue as deploy user

---

## ✅ Phase 4: SSH Hardening (5 minutes)

### 4.1 Configure SSH
- [ ] Backup SSH config:
  ```bash
  sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup
  ```
- [ ] Edit SSH configuration:
  ```bash
  sudo nano /etc/ssh/sshd_config
  ```
- [ ] Apply these settings:
  ```bash
  # Disable root login
  PermitRootLogin no
  
  # Disable password authentication (only after SSH key is working!)
  PasswordAuthentication no
  PubkeyAuthentication yes
  
  # Disable empty passwords
  PermitEmptyPasswords no
  
  # Change default port (optional but recommended)
  Port 22  # Or change to custom port like 2222
  
  # Limit authentication attempts
  MaxAuthTries 3
  
  # Disconnect idle sessions
  ClientAliveInterval 300
  ClientAliveCountMax 2
  ```
- [ ] Test SSH config:
  ```bash
  sudo sshd -t
  # Expected: No errors
  ```
- [ ] Restart SSH service:
  ```bash
  sudo systemctl restart sshd
  ```
- [ ] **IMPORTANT:** Keep current session open and test new connection in another terminal before closing!

---

## ✅ Phase 5: Firewall Configuration (5 minutes)

### 5.1 Configure UFW
- [ ] Check UFW status:
  ```bash
  sudo ufw status
  ```
- [ ] Set default policies:
  ```bash
  sudo ufw default deny incoming
  sudo ufw default allow outgoing
  ```
- [ ] Allow SSH (CRITICAL - do this first!):
  ```bash
  sudo ufw allow 22/tcp
  # Or if you changed SSH port:
  # sudo ufw allow 2222/tcp
  ```
- [ ] Allow HTTP and HTTPS:
  ```bash
  sudo ufw allow 80/tcp
  sudo ufw allow 443/tcp
  ```
- [ ] Review rules before enabling:
  ```bash
  sudo ufw show added
  ```
- [ ] Enable firewall:
  ```bash
  sudo ufw enable
  ```
- [ ] Verify status:
  ```bash
  sudo ufw status verbose
  ```

### 5.2 Configure Fail2Ban
- [ ] Check fail2ban status:
  ```bash
  sudo systemctl status fail2ban
  ```
- [ ] Create local config:
  ```bash
  sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
  ```
- [ ] Edit fail2ban config:
  ```bash
  sudo nano /etc/fail2ban/jail.local
  ```
- [ ] Configure SSH protection:
  ```ini
  [sshd]
  enabled = true
  port = 22
  filter = sshd
  logpath = /var/log/auth.log
  maxretry = 3
  bantime = 3600
  findtime = 600
  ```
- [ ] Restart fail2ban:
  ```bash
  sudo systemctl restart fail2ban
  ```
- [ ] Verify fail2ban is active:
  ```bash
  sudo fail2ban-client status
  sudo fail2ban-client status sshd
  ```

---

## ✅ Phase 6: System Optimization (5 minutes)

### 6.1 Increase File Descriptors
- [ ] Edit limits.conf:
  ```bash
  sudo nano /etc/security/limits.conf
  ```
- [ ] Add these lines:
  ```
  * soft nofile 65535
  * hard nofile 65535
  * soft nproc 65535
  * hard nproc 65535
  ```
- [ ] Edit sysctl.conf:
  ```bash
  sudo nano /etc/sysctl.conf
  ```
- [ ] Add these lines:
  ```
  # Network optimization
  net.core.somaxconn = 65535
  net.ipv4.ip_local_port_range = 1024 65535
  net.ipv4.tcp_tw_reuse = 1
  net.ipv4.tcp_fin_timeout = 15
  
  # File system optimization
  fs.file-max = 2097152
  fs.inotify.max_user_watches = 524288
  
  # Memory optimization
  vm.swappiness = 10
  vm.dirty_ratio = 60
  vm.dirty_background_ratio = 2
  ```
- [ ] Apply sysctl changes:
  ```bash
  sudo sysctl -p
  ```
- [ ] Verify changes:
  ```bash
  ulimit -n
  # Expected: 65535
  ```

### 6.2 Configure Automatic Updates
- [ ] Configure unattended-upgrades:
  ```bash
  sudo dpkg-reconfigure -plow unattended-upgrades
  # Select "Yes"
  ```
- [ ] Edit auto-upgrade config:
  ```bash
  sudo nano /etc/apt/apt.conf.d/50unattended-upgrades
  ```
- [ ] Enable automatic security updates:
  ```
  Unattended-Upgrade::Allowed-Origins {
      "${distro_id}:${distro_codename}-security";
  };
  Unattended-Upgrade::Automatic-Reboot "false";
  Unattended-Upgrade::Mail "your-email@example.com";
  ```

### 6.3 Setup Swap (if needed)
- [ ] Check current swap:
  ```bash
  free -h
  swapon --show
  ```
- [ ] Create swap file (if no swap exists):
  ```bash
  sudo fallocate -l 4G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  ```
- [ ] Make swap permanent:
  ```bash
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
  ```
- [ ] Verify swap:
  ```bash
  free -h
  ```

---

## ✅ Phase 7: Time Synchronization (2 minutes)

### 7.1 Configure NTP
- [ ] Check time sync status:
  ```bash
  timedatectl status
  ```
- [ ] Enable NTP:
  ```bash
  sudo timedatectl set-ntp true
  ```
- [ ] Verify timezone:
  ```bash
  timedatectl
  ```
- [ ] Set timezone (if needed):
  ```bash
  sudo timedatectl set-timezone Asia/Kolkata
  # Or your timezone
  ```

---

## ✅ Phase 8: Create Project Directory (2 minutes)

### 8.1 Setup Application Directory
- [ ] Create project directory:
  ```bash
  sudo mkdir -p /opt/microservices
  ```
- [ ] Set ownership:
  ```bash
  sudo chown -R deploy:deploy /opt/microservices
  ```
- [ ] Set permissions:
  ```bash
  sudo chmod 755 /opt/microservices
  ```
- [ ] Navigate to directory:
  ```bash
  cd /opt/microservices
  ```

### 8.2 Setup Log Directory
- [ ] Create log directory:
  ```bash
  sudo mkdir -p /var/log/microservices
  sudo chown -R deploy:deploy /var/log/microservices
  ```

---

## ✅ Phase 9: Verification (3 minutes)

### 9.1 System Check
- [ ] Verify all services running:
  ```bash
  sudo systemctl status ssh
  sudo systemctl status ufw
  sudo systemctl status fail2ban
  ```
- [ ] Check system resources:
  ```bash
  htop
  # Press q to quit
  ```
- [ ] Check disk usage:
  ```bash
  df -h
  ```
- [ ] Check memory:
  ```bash
  free -h
  ```

### 9.2 Security Check
- [ ] Verify firewall rules:
  ```bash
  sudo ufw status numbered
  ```
- [ ] Check fail2ban:
  ```bash
  sudo fail2ban-client status
  ```
- [ ] Review auth logs:
  ```bash
  sudo tail -50 /var/log/auth.log
  ```

### 9.3 Network Check
- [ ] Test internet connectivity:
  ```bash
  ping -c 4 8.8.8.8
  curl -I https://google.com
  ```
- [ ] Check open ports:
  ```bash
  sudo netstat -tulpn
  ```

---

## ✅ Phase 10: Documentation (2 minutes)

### 10.1 Record Server Information
- [ ] Create server info file:
  ```bash
  nano ~/server-info.txt
  ```
- [ ] Document the following:
  ```
  Server IP: _______________
  Hostname: prod-microservices-01
  Ubuntu Version: _______________
  SSH Port: 22
  Deploy User: deploy
  Project Directory: /opt/microservices
  Log Directory: /var/log/microservices
  Firewall: UFW enabled
  Fail2Ban: Enabled
  Swap: 4GB
  Deployment Date: _______________
  ```

### 10.2 Save Configuration Files
- [ ] Backup important configs:
  ```bash
  mkdir -p ~/config-backup
  sudo cp /etc/ssh/sshd_config ~/config-backup/
  sudo cp /etc/ufw/ufw.conf ~/config-backup/
  sudo cp /etc/fail2ban/jail.local ~/config-backup/
  sudo cp /etc/sysctl.conf ~/config-backup/
  ```

---

## ✅ Final Checklist

- [ ] Server accessible via SSH as deploy user
- [ ] Root login disabled
- [ ] Password authentication disabled
- [ ] Firewall (UFW) enabled with correct rules
- [ ] Fail2Ban protecting SSH
- [ ] System fully updated
- [ ] File descriptors increased
- [ ] Swap configured
- [ ] Time synchronized
- [ ] Project directory created
- [ ] All services running
- [ ] Server information documented

---

## 🎯 Success Criteria

Server setup is complete when:
- ✅ Can SSH as deploy user with key
- ✅ Cannot SSH as root
- ✅ Firewall shows only ports 22, 80, 443 open
- ✅ System fully updated
- ✅ All security measures in place
- ✅ Project directory ready

---

## 🚨 Troubleshooting

**Cannot SSH after changes:**
- Check if you have another terminal still connected
- Verify SSH key is in authorized_keys
- Check firewall allows SSH port
- Revert sshd_config from backup if needed

**Firewall locked you out:**
- Access via console (cloud provider dashboard)
- Disable UFW: `sudo ufw disable`
- Fix rules and re-enable

**System slow after updates:**
- Reboot server: `sudo reboot`
- Check running processes: `htop`

---

**Next Step:** Proceed to [DEPLOY-02-DOCKER-INSTALL.md](DEPLOY-02-DOCKER-INSTALL.md)
