#!/bin/bash

# ==============================================================================
# RHEL/CentOS 8+ Security Hardening Script
# Role: Senior Linux Administrator
# Objective: Harden system based on CIS Benchmarks and Best Practices.
# Features: Dry-Run, Rollback, Modular Auditing
# ==============================================================================

# Configuration
BACKUP_DIR="/var/backup/hardening_$(date +%F_%H%M%S)"
LOG_FILE="/var/log/security_hardening.log"
DRY_RUN=true

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Helper Functions
log() {
    echo -e "$(date +'%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${CYAN}[INFO] $1${NC}"
    log "[INFO] $1"
}

warn() {
    echo -e "${YELLOW}[WARN] $1${NC}"
    log "[WARN] $1"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    log "[ERROR] $1"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        error "This script must be run as root."
        exit 1
    fi
}

prepare_backup() {
    info "Creating backup directory: $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
}

backup_file() {
    local file="$1"
    if [ -f "$file" ]; then
        cp -p "$file" "$BACKUP_DIR/$(basename "$file").bak"
    fi
}

# ==============================================================================
# 1. CIS Benchmark Checking
# ==============================================================================
audit_cis() {
    info "Starting CIS Benchmark Audit..."
    
    # Filesystem Checks (CIS 1.1.1)
    local unused_fs=("cramfs" "freevxfs" "jffs2" "hfs" "hfsplus" "squashfs" "udf")
    for fs in "${unused_fs[@]}"; do
        if lsmod | grep -q "$fs"; then
            warn "Unused filesystem module loaded: $fs"
        else
            info "Filesystem module disabled: $fs (OK)"
        fi
    done

    # /tmp Mount Options (CIS 1.1.2)
    if mount | grep " /tmp " | grep -qE "nodev|nosuid|noexec"; then
        info "/tmp mount options secure (OK)"
    else
        warn "/tmp should be mounted with nodev, nosuid, noexec"
    fi
}

# ==============================================================================
# 2. FirewallD Configuration
# ==============================================================================
configure_firewall() {
    info "Configuring FirewallD..."
    
    if [ "$DRY_RUN" = true ]; then
        info "[DRY-RUN] Would enable firewalld and configure zones."
        return
    fi
    
    systemctl enable --now firewalld
    
    # Create web zone
    firewall-cmd --new-zone=secure_web --permanent || true
    firewall-cmd --zone=secure_web --add-service=http --permanent
    firewall-cmd --zone=secure_web --add-service=https --permanent
    firewall-cmd --zone=secure_web --add-port=3306/tcp --permanent # Internal DB access
    
    firewall-cmd --reload
    info "FirewallD configured."
}

# ==============================================================================
# 3. Auditd Rules
# ==============================================================================
configure_auditd() {
    info "Configuring Auditd Rules..."
    backup_file "/etc/audit/rules.d/audit.rules"

    if [ "$DRY_RUN" = true ]; then
        info "[DRY-RUN] Would add audit rules for /etc/passwd and system calls."
        return
    fi

    cat <<EOF > /etc/audit/rules.d/hardening.rules
-w /etc/passwd -p wa -k identity
-w /etc/group -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/sudoers -p wa -k scope
-a always,exit -F arch=b64 -S mount -S umount2 -k mounts
EOF
    
    service auditd reload
    info "Auditd rules updated."
}

# ==============================================================================
# 4. SSH Hardening
# ==============================================================================
harden_ssh() {
    info "Hardening SSH Configuration..."
    backup_file "/etc/ssh/sshd_config"

    if [ "$DRY_RUN" = true ]; then
        info "[DRY-RUN] Would disable Root Login and Password Auth."
        return
    fi

    sed -i 's/^#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
    sed -i 's/^PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
    
    sed -i 's/^#PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
    sed -i 's/^PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
    
    systemctl restart sshd
    info "SSH Hardened. Root login disabled. Key-based auth enforced."
}

# ==============================================================================
# 5. Filesystem Integrity (AIDE)
# ==============================================================================
configure_aide() {
    info "Configuring AIDE..."
    if ! command -v aide &> /dev/null; then
        if [ "$DRY_RUN" = true ]; then
            info "[DRY-RUN] Would install AIDE."
            return
        fi
        dnf install -y aide
    fi

    if [ "$DRY_RUN" = true ]; then
        info "[DRY-RUN] Would initialize AIDE database."
    else
        aide --init
        mv /var/lib/aide/aide.db.new.gz /var/lib/aide/aide.db.gz
        info "AIDE initialized."
    fi
}

# ==============================================================================
# 6. Unnecessary Services
# ==============================================================================
disable_services() {
    info "Disabling unnecessary services..."
    local services=("avahi-daemon" "cups" "postfix")
    
    for svc in "${services[@]}"; do
        if [ "$DRY_RUN" = true ]; then
            info "[DRY-RUN] Would disable $svc."
        else
            systemctl disable --now "$svc" || true
            info "Disabled $svc."
        fi
    done
}

# ==============================================================================
# 7. Fail2Ban Setup
# ==============================================================================
configure_fail2ban() {
    info "Setting up Fail2Ban..."
    if ! command -v fail2ban-client &> /dev/null; then
        if [ "$DRY_RUN" = true ]; then
            info "[DRY-RUN] Would install Fail2Ban."
            return
        fi
        dnf install -y epel-release
        dnf install -y fail2ban
    fi

    if [ "$DRY_RUN" = true ]; then
        info "[DRY-RUN] Would configure Fail2Ban jails."
        return
    fi

    backup_file "/etc/fail2ban/jail.local"

    cat <<EOF > /etc/fail2ban/jail.local
[sshd]
enabled = true
bantime = 1h
maxretry = 3

[nginx-http-auth]
enabled = true
EOF
    
    systemctl enable --now fail2ban
    info "Fail2Ban configured."
}

# ==============================================================================
# Rollback
# ==============================================================================
rollback() {
    error "Initiating Rollback..."
    if [ ! -d "$BACKUP_DIR" ]; then
        error "No backup directory found!"
        return 1
    fi

    [ -f "$BACKUP_DIR/sshd_config.bak" ] && cp "$BACKUP_DIR/sshd_config.bak" /etc/ssh/sshd_config && systemctl restart sshd
    [ -f "$BACKUP_DIR/audit.rules.bak" ] && cp "$BACKUP_DIR/audit.rules.bak" /etc/audit/rules.d/audit.rules && service auditd reload
    [ -f "$BACKUP_DIR/jail.local.bak" ] && cp "$BACKUP_DIR/jail.local.bak" /etc/fail2ban/jail.local
    
    info "Rollback complete. Verify services manually."
}

# ==============================================================================
# Main Execution
# ==============================================================================
check_root

if [ "$1" == "--apply" ]; then
    DRY_RUN=false
    warn "Running in APPLY mode. Changes will be made."
else
    info "Running in DRY-RUN mode. Use --apply to make changes."
fi

prepare_backup
audit_cis
configure_firewall
configure_auditd
harden_ssh
configure_aide
disable_services
configure_fail2ban

info "Hardening process completed."
