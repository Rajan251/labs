# 3. Jenkins Installation on Ubuntu

## Installation Methods

There are two primary ways to install Jenkins:
1. **Native Installation** (Recommended for beginners)
2. **Containerized Installation** (Covered in next section)

This guide covers native installation.

## Prerequisites

- Ubuntu 22.04 LTS or 20.04 LTS
- Java 11 or Java 17 (Jenkins requirement)
- Sudo privileges
- At least 2 GB RAM

## Step 1: Install Java

Jenkins requires Java to run. Install OpenJDK 17:

```bash
# Update package list
sudo apt update

# Install OpenJDK 17
sudo apt install -y openjdk-17-jdk

# Verify installation
java -version
```

**Expected Output**:
```
openjdk version "17.0.8" 2023-07-18
OpenJDK Runtime Environment (build 17.0.8+7-Ubuntu-122.04)
OpenJDK 64-Bit Server VM (build 17.0.8+7-Ubuntu-122.04, mixed mode, sharing)
```

**Alternative**: Install Java 11
```bash
sudo apt install -y openjdk-11-jdk
```

## Step 2: Add Jenkins Repository

```bash
# Add Jenkins GPG key
curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key | sudo tee \
  /usr/share/keyrings/jenkins-keyring.asc > /dev/null

# Add Jenkins repository
echo deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] \
  https://pkg.jenkins.io/debian-stable binary/ | sudo tee \
  /etc/apt/sources.list.d/jenkins.list > /dev/null

# Update package list
sudo apt update
```

## Step 3: Install Jenkins

```bash
# Install Jenkins
sudo apt install -y jenkins

# Verify installation
jenkins --version
```

## Step 4: Start and Enable Jenkins

```bash
# Start Jenkins service
sudo systemctl start jenkins

# Enable Jenkins to start on boot
sudo systemctl enable jenkins

# Check Jenkins status
sudo systemctl status jenkins
```

**Expected Output**:
```
● jenkins.service - Jenkins Continuous Integration Server
     Loaded: loaded (/lib/systemd/system/jenkins.service; enabled; vendor preset: enabled)
     Active: active (running) since Mon 2024-01-15 10:30:45 UTC; 1min ago
```

## Step 5: Configure Firewall

```bash
# Allow Jenkins port
sudo ufw allow 8080/tcp

# Verify
sudo ufw status
```

## Step 6: Access Jenkins Web UI

### Get Initial Admin Password

```bash
# Display initial password
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

**Copy this password** - you'll need it for the web setup.

### Access Jenkins

1. Open browser: `http://<your-server-ip>:8080`
2. Paste the initial admin password
3. Click "Continue"

## Step 7: Install Plugins

You'll see two options:

### Option 1: Install Suggested Plugins (Recommended)

Click **"Install suggested plugins"**

This installs:
- Git
- Pipeline
- Credentials
- SSH Slaves
- Matrix Authorization
- And many more...

### Option 2: Select Plugins to Install

Choose this if you want custom plugin selection.

**Wait for installation to complete** (5-10 minutes)

## Step 8: Create Admin User

Fill in the form:
- **Username**: admin (or your choice)
- **Password**: Strong password
- **Full name**: Your name
- **Email**: your-email@example.com

Click **"Save and Continue"**

## Step 9: Configure Jenkins URL

- **Jenkins URL**: `http://<your-server-ip>:8080/`

Click **"Save and Finish"**

## Step 10: Start Using Jenkins

Click **"Start using Jenkins"**

You're now on the Jenkins Dashboard! 🎉

## Essential Plugin Installation

Install these additional plugins for CI/CD:

1. Go to **Manage Jenkins** → **Manage Plugins**
2. Click **Available** tab
3. Search and install:

### Required Plugins

- **Docker Pipeline** - Docker integration
- **Kubernetes** - Kubernetes deployment
- **Git** - Git integration (usually pre-installed)
- **Pipeline** - Pipeline support (usually pre-installed)
- **Credentials Binding** - Manage credentials
- **Blue Ocean** - Modern UI (optional but recommended)
- **Slack Notification** - Slack integration (optional)
- **Email Extension** - Email notifications

### Installation Steps

1. Check the checkbox next to each plugin
2. Click **"Install without restart"**
3. Wait for installation
4. Check **"Restart Jenkins when installation is complete"**

## Jenkins Configuration

### Configure System Settings

Go to **Manage Jenkins** → **Configure System**

#### Set Number of Executors

- **# of executors**: 2 (or based on CPU cores)

#### Configure Git

- Usually auto-detected
- Verify: **Manage Jenkins** → **Global Tool Configuration** → **Git**

#### Configure JDK

**Manage Jenkins** → **Global Tool Configuration** → **JDK**

- **Name**: JDK-17
- **JAVA_HOME**: `/usr/lib/jvm/java-17-openjdk-amd64`

## Common Installation Errors

### Error 1: Port 8080 Already in Use

**Symptom**:
```
Job for jenkins.service failed because the control process exited with error code
```

**Solution**:
```bash
# Check what's using port 8080
sudo lsof -i :8080

# Kill the process or change Jenkins port
sudo nano /etc/default/jenkins
```

Change:
```
HTTP_PORT=8080
```
To:
```
HTTP_PORT=8081
```

Restart:
```bash
sudo systemctl restart jenkins
```

### Error 2: Java Not Found

**Symptom**:
```
Unable to access jarfile /usr/share/jenkins/jenkins.war
```

**Solution**:
```bash
# Install Java
sudo apt install -y openjdk-17-jdk

# Set JAVA_HOME
echo 'export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64' >> ~/.bashrc
source ~/.bashrc

# Restart Jenkins
sudo systemctl restart jenkins
```

### Error 3: Permission Denied

**Symptom**:
```
Permission denied on /var/lib/jenkins
```

**Solution**:
```bash
# Fix ownership
sudo chown -R jenkins:jenkins /var/lib/jenkins
sudo chown -R jenkins:jenkins /var/cache/jenkins
sudo chown -R jenkins:jenkins /var/log/jenkins

# Restart Jenkins
sudo systemctl restart jenkins
```

### Error 4: Jenkins Won't Start

**Check logs**:
```bash
# View Jenkins logs
sudo journalctl -u jenkins -n 50

# Or
sudo tail -f /var/log/jenkins/jenkins.log
```

**Common fixes**:
```bash
# Check disk space
df -h

# Check memory
free -h

# Verify Java
java -version

# Restart Jenkins
sudo systemctl restart jenkins
```

### Error 5: Cannot Access Web UI

**Checklist**:
```bash
# 1. Check Jenkins is running
sudo systemctl status jenkins

# 2. Check firewall
sudo ufw status

# 3. Check port
sudo netstat -tulpn | grep 8080

# 4. Check from server itself
curl http://localhost:8080
```

## Jenkins Directory Structure

```
/var/lib/jenkins/          # Jenkins home directory
├── config.xml             # Main configuration
├── jobs/                  # Job configurations
├── plugins/               # Installed plugins
├── secrets/               # Secrets and credentials
├── users/                 # User configurations
├── workspace/             # Build workspaces
└── logs/                  # Log files

/var/log/jenkins/          # Log directory
└── jenkins.log            # Main log file

/etc/default/jenkins       # Jenkins configuration file
```

## Useful Jenkins Commands

```bash
# Start Jenkins
sudo systemctl start jenkins

# Stop Jenkins
sudo systemctl stop jenkins

# Restart Jenkins
sudo systemctl restart jenkins

# Check status
sudo systemctl status jenkins

# View logs
sudo journalctl -u jenkins -f

# Reload configuration (without restart)
sudo systemctl reload jenkins
```

## Backup Jenkins

### Manual Backup

```bash
# Stop Jenkins
sudo systemctl stop jenkins

# Backup Jenkins home
sudo tar -czf jenkins-backup-$(date +%Y%m%d).tar.gz /var/lib/jenkins/

# Start Jenkins
sudo systemctl start jenkins
```

### Automated Backup Script

Create `/usr/local/bin/backup-jenkins.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backup/jenkins"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup Jenkins home
tar -czf $BACKUP_DIR/jenkins-$DATE.tar.gz \
    --exclude='/var/lib/jenkins/workspace/*' \
    --exclude='/var/lib/jenkins/war/*' \
    /var/lib/jenkins/

# Keep only last 7 backups
find $BACKUP_DIR -name "jenkins-*.tar.gz" -mtime +7 -delete

echo "Backup completed: jenkins-$DATE.tar.gz"
```

Make executable and schedule:
```bash
sudo chmod +x /usr/local/bin/backup-jenkins.sh

# Add to crontab (daily at 2 AM)
sudo crontab -e
```

Add:
```
0 2 * * * /usr/local/bin/backup-jenkins.sh
```

## Security Best Practices

### 1. Enable Security

**Manage Jenkins** → **Configure Global Security**

- ✅ Enable security
- ✅ Jenkins' own user database
- ✅ Allow users to sign up: **Uncheck** (after creating admin)
- ✅ Authorization: **Matrix-based security**

### 2. Configure CSRF Protection

- ✅ Prevent Cross Site Request Forgery exploits: **Check**

### 3. Set Up Agent Security

- ✅ Enable Agent → Master Access Control

### 4. Use HTTPS (Production)

Install Nginx as reverse proxy:

```bash
sudo apt install -y nginx

# Configure Nginx
sudo nano /etc/nginx/sites-available/jenkins
```

Add:
```nginx
server {
    listen 80;
    server_name jenkins.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable and restart:
```bash
sudo ln -s /etc/nginx/sites-available/jenkins /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Next Steps

Jenkins is now installed and configured. Proceed to:
- [Containerized Jenkins](04-containerized-jenkins.md) for Docker-based setup
- [Docker Integration](05-docker-integration.md) to integrate Docker with Jenkins
