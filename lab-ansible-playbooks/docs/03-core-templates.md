# Core Playbook Templates

This document provides production-grade Ansible playbook templates commonly used in modern organizations. Each template includes complete code, explanations, variables, handlers, error handling, and step-by-step implementation instructions.

## Table of Contents

1. [Server Bootstrap Template](#a-server-bootstrap-template)
2. [User & SSH Key Management](#b-user--ssh-key-management-template)
3. [Nginx Installation & Reverse Proxy](#c-nginx-installation--reverse-proxy-template)
4. [Docker Installation](#d-docker-installation-template)
5. [Application Deployment](#e-application-deployment-playbook)
6. [Kubernetes Node Preparation](#f-kubernetes-node-preparation-template)
7. [OS Patching (Rolling Update)](#g-os-patching-safe-rolling-update)
8. [Log Management](#h-log-management-template)
9. [Security & Hardening](#i-security--hardening-template)
10. [Monitoring](#j-monitoring-template)

---

## (A) Server Bootstrap Template

### Purpose
Initial server setup including package updates, dependency installation, timezone configuration, SSH hardening, and basic OS hardening.

### Use Case
- New server provisioning
- Base configuration for all servers
- Standardizing server setup across fleet

### Full Playbook

```yaml
---
# playbooks/server-bootstrap.yml
# Purpose: Bootstrap new servers with base configuration

- name: Bootstrap New Servers
  hosts: all
  become: yes
  gather_facts: yes
  
  vars:
    # Timezone configuration
    server_timezone: "UTC"
    
    # Base packages to install
    base_packages:
      - vim
      - git
      - curl
      - wget
      - htop
      - net-tools
      - unzip
      - ca-certificates
      - gnupg
      - lsb-release
    
    # SSH configuration
    ssh_port: 22
    ssh_permit_root_login: "no"
    ssh_password_authentication: "no"
    ssh_max_auth_tries: 3
    ssh_client_alive_interval: 300
    ssh_client_alive_count_max: 2
    
    # Security settings
    disable_ipv6: false
    enable_firewall: true
    
  tasks:
    # ========================================
    # PHASE 1: System Updates
    # ========================================
    - name: Update and Upgrade System
      block:
        - name: Update apt cache (Debian/Ubuntu)
          apt:
            update_cache: yes
            cache_valid_time: 3600
          when: ansible_os_family == "Debian"
          changed_when: false
        
        - name: Upgrade all packages (Debian/Ubuntu)
          apt:
            upgrade: dist
            autoremove: yes
            autoclean: yes
          when: ansible_os_family == "Debian"
          register: apt_upgrade
        
        - name: Update yum cache (RedHat/CentOS)
          yum:
            update_cache: yes
          when: ansible_os_family == "RedHat"
          changed_when: false
        
        - name: Upgrade all packages (RedHat/CentOS)
          yum:
            name: '*'
            state: latest
          when: ansible_os_family == "RedHat"
          register: yum_upgrade
      
      rescue:
        - name: Log update failure
          debug:
            msg: "Package update failed. Continuing with bootstrap..."
        
        - name: Create failure marker
          file:
            path: /var/log/ansible-bootstrap-update-failed
            state: touch
            mode: '0644'
      
      tags:
        - bootstrap
        - updates

    # ========================================
    # PHASE 2: Install Base Dependencies
    # ========================================
    - name: Install base packages
      block:
        - name: Install base packages (Debian/Ubuntu)
          apt:
            name: "{{ base_packages }}"
            state: present
            update_cache: yes
          when: ansible_os_family == "Debian"
        
        - name: Install base packages (RedHat/CentOS)
          yum:
            name: "{{ base_packages }}"
            state: present
          when: ansible_os_family == "RedHat"
      
      rescue:
        - name: Log package installation failure
          debug:
            msg: "Failed to install some packages. Check logs."
      
      tags:
        - bootstrap
        - packages

    # ========================================
    # PHASE 3: Configure Timezone
    # ========================================
    - name: Set timezone
      timezone:
        name: "{{ server_timezone }}"
      notify: restart cron
      tags:
        - bootstrap
        - timezone

    # ========================================
    # PHASE 4: SSH Hardening
    # ========================================
    - name: Harden SSH Configuration
      block:
        - name: Backup original SSH config
          copy:
            src: /etc/ssh/sshd_config
            dest: /etc/ssh/sshd_config.backup
            remote_src: yes
            force: no
        
        - name: Configure SSH - Disable root login
          lineinfile:
            path: /etc/ssh/sshd_config
            regexp: '^#?PermitRootLogin'
            line: "PermitRootLogin {{ ssh_permit_root_login }}"
            state: present
          notify: restart sshd
        
        - name: Configure SSH - Disable password authentication
          lineinfile:
            path: /etc/ssh/sshd_config
            regexp: '^#?PasswordAuthentication'
            line: "PasswordAuthentication {{ ssh_password_authentication }}"
            state: present
          notify: restart sshd
        
        - name: Configure SSH - Set max auth tries
          lineinfile:
            path: /etc/ssh/sshd_config
            regexp: '^#?MaxAuthTries'
            line: "MaxAuthTries {{ ssh_max_auth_tries }}"
            state: present
          notify: restart sshd
        
        - name: Configure SSH - Set client alive interval
          lineinfile:
            path: /etc/ssh/sshd_config
            regexp: '^#?ClientAliveInterval'
            line: "ClientAliveInterval {{ ssh_client_alive_interval }}"
            state: present
          notify: restart sshd
        
        - name: Configure SSH - Set client alive count max
          lineinfile:
            path: /etc/ssh/sshd_config
            regexp: '^#?ClientAliveCountMax'
            line: "ClientAliveCountMax {{ ssh_client_alive_count_max }}"
            state: present
          notify: restart sshd
        
        - name: Validate SSH configuration
          command: sshd -t
          changed_when: false
      
      rescue:
        - name: Restore SSH config on failure
          copy:
            src: /etc/ssh/sshd_config.backup
            dest: /etc/ssh/sshd_config
            remote_src: yes
        
        - name: Restart SSH with original config
          service:
            name: sshd
            state: restarted
        
        - name: Fail the playbook
          fail:
            msg: "SSH configuration failed. Original config restored."
      
      tags:
        - bootstrap
        - ssh
        - security

    # ========================================
    # PHASE 5: Basic OS Hardening
    # ========================================
    - name: OS Hardening
      block:
        - name: Disable IPv6 (if configured)
          sysctl:
            name: "{{ item }}"
            value: '1'
            state: present
            reload: yes
          loop:
            - net.ipv6.conf.all.disable_ipv6
            - net.ipv6.conf.default.disable_ipv6
            - net.ipv6.conf.lo.disable_ipv6
          when: disable_ipv6
        
        - name: Enable IP forwarding protection
          sysctl:
            name: net.ipv4.conf.all.forwarding
            value: '0'
            state: present
            reload: yes
        
        - name: Enable SYN cookies
          sysctl:
            name: net.ipv4.tcp_syncookies
            value: '1'
            state: present
            reload: yes
        
        - name: Disable source packet routing
          sysctl:
            name: "{{ item }}"
            value: '0'
            state: present
            reload: yes
          loop:
            - net.ipv4.conf.all.accept_source_route
            - net.ipv4.conf.default.accept_source_route
        
        - name: Enable reverse path filtering
          sysctl:
            name: "{{ item }}"
            value: '1'
            state: present
            reload: yes
          loop:
            - net.ipv4.conf.all.rp_filter
            - net.ipv4.conf.default.rp_filter
        
        - name: Disable ICMP redirect acceptance
          sysctl:
            name: "{{ item }}"
            value: '0'
            state: present
            reload: yes
          loop:
            - net.ipv4.conf.all.accept_redirects
            - net.ipv4.conf.default.accept_redirects
        
        - name: Set file limits
          pam_limits:
            domain: '*'
            limit_type: "{{ item.type }}"
            limit_item: "{{ item.item }}"
            value: "{{ item.value }}"
          loop:
            - { type: 'soft', item: 'nofile', value: '65536' }
            - { type: 'hard', item: 'nofile', value: '65536' }
            - { type: 'soft', item: 'nproc', value: '32768' }
            - { type: 'hard', item: 'nproc', value: '32768' }
      
      tags:
        - bootstrap
        - hardening
        - security

    # ========================================
    # PHASE 6: Setup Firewall (UFW)
    # ========================================
    - name: Configure Firewall
      block:
        - name: Install UFW (Debian/Ubuntu)
          apt:
            name: ufw
            state: present
          when: 
            - ansible_os_family == "Debian"
            - enable_firewall
        
        - name: Allow SSH through firewall
          ufw:
            rule: allow
            port: "{{ ssh_port }}"
            proto: tcp
          when: enable_firewall
        
        - name: Set default firewall policies
          ufw:
            direction: "{{ item.direction }}"
            policy: "{{ item.policy }}"
          loop:
            - { direction: 'incoming', policy: 'deny' }
            - { direction: 'outgoing', policy: 'allow' }
          when: enable_firewall
        
        - name: Enable UFW
          ufw:
            state: enabled
          when: enable_firewall
      
      when: ansible_os_family == "Debian"
      tags:
        - bootstrap
        - firewall
        - security

    # ========================================
    # PHASE 7: Final Steps
    # ========================================
    - name: Create bootstrap completion marker
      copy:
        content: |
          Bootstrap completed: {{ ansible_date_time.iso8601 }}
          Hostname: {{ ansible_hostname }}
          OS: {{ ansible_distribution }} {{ ansible_distribution_version }}
          Kernel: {{ ansible_kernel }}
        dest: /var/log/ansible-bootstrap-complete
        mode: '0644'
      tags:
        - bootstrap

    - name: Display bootstrap summary
      debug:
        msg:
          - "Bootstrap completed successfully!"
          - "Hostname: {{ ansible_hostname }}"
          - "OS: {{ ansible_distribution }} {{ ansible_distribution_version }}"
          - "Timezone: {{ server_timezone }}"
          - "SSH Port: {{ ssh_port }}"
          - "Root Login: {{ ssh_permit_root_login }}"
      tags:
        - bootstrap

  handlers:
    - name: restart sshd
      service:
        name: "{{ 'sshd' if ansible_os_family == 'RedHat' else 'ssh' }}"
        state: restarted
    
    - name: restart cron
      service:
        name: cron
        state: restarted
      when: ansible_os_family == "Debian"
```

### Variables Explanation

| Variable | Default | Description |
|----------|---------|-------------|
| `server_timezone` | UTC | Server timezone |
| `base_packages` | List | Essential packages to install |
| `ssh_port` | 22 | SSH port number |
| `ssh_permit_root_login` | no | Allow root SSH login |
| `ssh_password_authentication` | no | Allow password auth |
| `disable_ipv6` | false | Disable IPv6 |
| `enable_firewall` | true | Enable UFW firewall |

### Step-by-Step Implementation

#### Step 1: Prepare Inventory

```ini
# inventories/production/hosts
[new_servers]
server01.example.com ansible_host=192.168.1.10
server02.example.com ansible_host=192.168.1.11

[new_servers:vars]
ansible_user=root
ansible_ssh_private_key_file=~/.ssh/id_rsa
```

#### Step 2: Create Variable File

```yaml
# group_vars/new_servers.yml
---
server_timezone: "America/New_York"
ssh_port: 22
ssh_permit_root_login: "no"
ssh_password_authentication: "no"
enable_firewall: true
disable_ipv6: false

base_packages:
  - vim
  - git
  - curl
  - wget
  - htop
  - net-tools
  - python3
  - python3-pip
```

#### Step 3: Test Connectivity

```bash
# Test SSH connection
ansible new_servers -i inventories/production/hosts -m ping

# Expected output:
# server01.example.com | SUCCESS => {
#     "changed": false,
#     "ping": "pong"
# }
```

#### Step 4: Run in Check Mode (Dry Run)

```bash
ansible-playbook playbooks/server-bootstrap.yml \
  -i inventories/production/hosts \
  --check \
  --diff
```

#### Step 5: Execute Playbook

```bash
ansible-playbook playbooks/server-bootstrap.yml \
  -i inventories/production/hosts \
  -v
```

#### Step 6: Verify Bootstrap

```bash
# Check bootstrap completion
ansible new_servers -i inventories/production/hosts \
  -m command -a "cat /var/log/ansible-bootstrap-complete"

# Verify SSH configuration
ansible new_servers -i inventories/production/hosts \
  -m command -a "sshd -T | grep -E 'permitrootlogin|passwordauthentication'"

# Check installed packages
ansible new_servers -i inventories/production/hosts \
  -m command -a "dpkg -l | grep -E 'vim|git|curl'"
```

### Idempotency Features

✅ **Package Installation**: Uses `state: present` - installs only if missing  
✅ **Configuration Files**: Uses `lineinfile` - adds lines only once  
✅ **System Settings**: Uses `sysctl` - sets values idempotently  
✅ **File Creation**: Uses `force: no` for backups - doesn't overwrite  

### Error Handling

- **Block/Rescue**: Automatic rollback on SSH config failure
- **Backup**: Creates backup before modifying SSH config
- **Validation**: Tests SSH config before applying
- **Markers**: Creates failure markers for troubleshooting

### Tags Usage

```bash
# Run only SSH hardening
ansible-playbook playbooks/server-bootstrap.yml --tags "ssh"

# Run only package updates
ansible-playbook playbooks/server-bootstrap.yml --tags "updates"

# Skip security hardening
ansible-playbook playbooks/server-bootstrap.yml --skip-tags "security"
```

### Best Practices

1. **Always test in dev first**: Never run directly on production
2. **Use check mode**: Verify changes before applying
3. **Keep SSH access**: Ensure you don't lock yourself out
4. **Document changes**: Use markers and logs
5. **Version control**: Track all configuration changes

---

## (B) User & SSH Key Management Template

### Purpose
Create users, manage groups, distribute SSH keys, and enforce password policies.

### Use Case
- Onboarding new team members
- Managing access across servers
- Enforcing security policies
- Rotating SSH keys

### Full Playbook

```yaml
---
# playbooks/user-management.yml
# Purpose: Manage users and SSH keys across servers

- name: User and SSH Key Management
  hosts: all
  become: yes
  gather_facts: yes
  
  vars:
    # User definitions
    users:
      - name: john
        comment: "John Doe"
        groups: ['sudo', 'docker']
        shell: /bin/bash
        ssh_keys:
          - "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC... john@laptop"
        state: present
      
      - name: jane
        comment: "Jane Smith"
        groups: ['sudo']
        shell: /bin/bash
        ssh_keys:
          - "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQD... jane@laptop"
        state: present
      
      - name: bob
        comment: "Bob Johnson"
        groups: ['developers']
        shell: /bin/bash
        ssh_keys:
          - "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQE... bob@laptop"
        state: present
      
      - name: olduser
        state: absent  # Remove this user
    
    # Groups to create
    custom_groups:
      - developers
      - operators
      - readonly
    
    # Password policy
    password_max_days: 90
    password_min_days: 1
    password_warn_age: 7
    password_min_length: 12
    
    # SSH configuration
    ssh_authorized_keys_dir: "/home/{{ item.name }}/.ssh"
    
  tasks:
    # ========================================
    # PHASE 1: Create Custom Groups
    # ========================================
    - name: Create custom groups
      group:
        name: "{{ item }}"
        state: present
      loop: "{{ custom_groups }}"
      tags:
        - users
        - groups

    # ========================================
    # PHASE 2: Manage Users
    # ========================================
    - name: Manage user accounts
      block:
        - name: Create or update users
          user:
            name: "{{ item.name }}"
            comment: "{{ item.comment | default(omit) }}"
            groups: "{{ item.groups | default([]) }}"
            append: yes
            shell: "{{ item.shell | default('/bin/bash') }}"
            create_home: yes
            state: "{{ item.state | default('present') }}"
          loop: "{{ users }}"
          when: item.state | default('present') == 'present'
          register: user_creation
        
        - name: Remove users
          user:
            name: "{{ item.name }}"
            state: absent
            remove: yes
          loop: "{{ users }}"
          when: item.state | default('present') == 'absent'
      
      rescue:
        - name: Log user management failure
          debug:
            msg: "Failed to manage user: {{ item.name }}"
      
      tags:
        - users

    # ========================================
    # PHASE 3: SSH Key Management
    # ========================================
    - name: Manage SSH authorized keys
      block:
        - name: Ensure .ssh directory exists
          file:
            path: "/home/{{ item.name }}/.ssh"
            state: directory
            owner: "{{ item.name }}"
            group: "{{ item.name }}"
            mode: '0700'
          loop: "{{ users }}"
          when: 
            - item.state | default('present') == 'present'
            - item.ssh_keys is defined
        
        - name: Add SSH authorized keys
          authorized_key:
            user: "{{ item.0.name }}"
            key: "{{ item.1 }}"
            state: present
            exclusive: no
          loop: "{{ users | subelements('ssh_keys', skip_missing=True) }}"
          when: item.0.state | default('present') == 'present'
        
        - name: Set authorized_keys file permissions
          file:
            path: "/home/{{ item.name }}/.ssh/authorized_keys"
            owner: "{{ item.name }}"
            group: "{{ item.name }}"
            mode: '0600'
          loop: "{{ users }}"
          when: 
            - item.state | default('present') == 'present'
            - item.ssh_keys is defined
      
      tags:
        - users
        - ssh

    # ========================================
    # PHASE 4: Password Policy Enforcement
    # ========================================
    - name: Enforce password policies
      block:
        - name: Install libpam-pwquality (Debian/Ubuntu)
          apt:
            name: libpam-pwquality
            state: present
          when: ansible_os_family == "Debian"
        
        - name: Configure password quality requirements
          lineinfile:
            path: /etc/security/pwquality.conf
            regexp: "^{{ item.key }}"
            line: "{{ item.key }} = {{ item.value }}"
            state: present
          loop:
            - { key: 'minlen', value: "{{ password_min_length }}" }
            - { key: 'dcredit', value: '-1' }  # At least 1 digit
            - { key: 'ucredit', value: '-1' }  # At least 1 uppercase
            - { key: 'lcredit', value: '-1' }  # At least 1 lowercase
            - { key: 'ocredit', value: '-1' }  # At least 1 special char
        
        - name: Set password aging for existing users
          command: "chage -M {{ password_max_days }} -m {{ password_min_days }} -W {{ password_warn_age }} {{ item.name }}"
          loop: "{{ users }}"
          when: 
            - item.state | default('present') == 'present'
            - user_creation.changed
          changed_when: false
        
        - name: Set default password aging in login.defs
          lineinfile:
            path: /etc/login.defs
            regexp: "^{{ item.key }}"
            line: "{{ item.key }}\t{{ item.value }}"
            state: present
          loop:
            - { key: 'PASS_MAX_DAYS', value: "{{ password_max_days }}" }
            - { key: 'PASS_MIN_DAYS', value: "{{ password_min_days }}" }
            - { key: 'PASS_WARN_AGE', value: "{{ password_warn_age }}" }
      
      tags:
        - users
        - security
        - password-policy

    # ========================================
    # PHASE 5: Sudo Configuration
    # ========================================
    - name: Configure sudo access
      block:
        - name: Ensure sudo group exists
          group:
            name: sudo
            state: present
        
        - name: Configure sudo group in sudoers
          lineinfile:
            path: /etc/sudoers
            regexp: '^%sudo'
            line: '%sudo   ALL=(ALL:ALL) ALL'
            validate: '/usr/sbin/visudo -cf %s'
            state: present
        
        - name: Create sudoers.d directory
          file:
            path: /etc/sudoers.d
            state: directory
            mode: '0750'
        
        - name: Configure passwordless sudo for operators (optional)
          copy:
            content: |
              # Ansible managed
              %operators ALL=(ALL) NOPASSWD: ALL
            dest: /etc/sudoers.d/operators
            mode: '0440'
            validate: '/usr/sbin/visudo -cf %s'
          when: "'operators' in custom_groups"
      
      tags:
        - users
        - sudo

    # ========================================
    # PHASE 6: Verification
    # ========================================
    - name: Verify user configuration
      block:
        - name: Check user accounts
          command: "id {{ item.name }}"
          loop: "{{ users }}"
          when: item.state | default('present') == 'present'
          changed_when: false
          register: user_check
        
        - name: Display user information
          debug:
            msg: "{{ user_check.results | map(attribute='stdout') | list }}"
      
      tags:
        - users
        - verify

  handlers:
    - name: restart sshd
      service:
        name: "{{ 'sshd' if ansible_os_family == 'RedHat' else 'ssh' }}"
        state: restarted
```

### Variables File

```yaml
# group_vars/all/users.yml
---
users:
  - name: devops
    comment: "DevOps Team"
    groups: ['sudo', 'docker', 'operators']
    shell: /bin/bash
    ssh_keys:
      - "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDm... devops@workstation"
    state: present
  
  - name: readonly
    comment: "Read Only User"
    groups: ['readonly']
    shell: /bin/bash
    ssh_keys:
      - "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCx... readonly@monitor"
    state: present

custom_groups:
  - developers
  - operators
  - readonly

password_max_days: 90
password_min_days: 7
password_warn_age: 14
password_min_length: 14
```

### Step-by-Step Implementation

#### Step 1: Prepare User Data

Create a variable file with user definitions:

```yaml
# group_vars/all/users.yml
users:
  - name: alice
    comment: "Alice Admin"
    groups: ['sudo']
    shell: /bin/bash
    ssh_keys:
      - "ssh-rsa AAAAB3... alice@laptop"
    state: present
```

#### Step 2: Test User Creation (Dry Run)

```bash
ansible-playbook playbooks/user-management.yml \
  -i inventories/production/hosts \
  --check \
  --diff \
  --tags "users"
```

#### Step 3: Create Users

```bash
ansible-playbook playbooks/user-management.yml \
  -i inventories/production/hosts \
  --tags "users"
```

#### Step 4: Verify User Creation

```bash
# Check if user exists
ansible all -i inventories/production/hosts \
  -m command -a "id alice"

# Check SSH key
ansible all -i inventories/production/hosts \
  -m command -a "cat /home/alice/.ssh/authorized_keys"

# Check groups
ansible all -i inventories/production/hosts \
  -m command -a "groups alice"
```

#### Step 5: Test SSH Access

```bash
# Test SSH login with the new user
ssh alice@server01.example.com

# Test sudo access
sudo whoami
```

### Idempotency Features

✅ **User Creation**: Creates only if doesn't exist  
✅ **Group Assignment**: Uses `append: yes` to add groups  
✅ **SSH Keys**: Adds keys only if not present  
✅ **File Permissions**: Sets permissions idempotently  

### Security Best Practices

1. **SSH Keys Only**: Disable password authentication
2. **Strong Passwords**: Enforce complexity requirements
3. **Password Rotation**: Set maximum password age
4. **Least Privilege**: Assign minimal necessary permissions
5. **Audit**: Log all user changes

### Common Use Cases

**Add New User:**
```yaml
users:
  - name: newuser
    comment: "New Team Member"
    groups: ['developers']
    ssh_keys:
      - "ssh-rsa AAAAB3... newuser@laptop"
    state: present
```

**Remove User:**
```yaml
users:
  - name: olduser
    state: absent
```

**Update User Groups:**
```yaml
users:
  - name: existinguser
    groups: ['sudo', 'docker', 'developers']
    state: present
```

---

## (C) Nginx Installation & Reverse Proxy Template

### Purpose
Install Nginx web server, configure virtual hosts, setup SSL, and configure reverse proxy.

### Use Case
- Web server deployment
- Reverse proxy for applications
- Load balancing
- SSL termination

### Full Playbook

```yaml
---
# playbooks/nginx-setup.yml
# Purpose: Install and configure Nginx web server

- name: Install and Configure Nginx
  hosts: webservers
  become: yes
  gather_facts: yes
  
  vars:
    # Nginx configuration
    nginx_user: www-data
    nginx_worker_processes: auto
    nginx_worker_connections: 2048
    nginx_keepalive_timeout: 65
    nginx_client_max_body_size: "100M"
    
    # SSL configuration
    ssl_protocols: "TLSv1.2 TLSv1.3"
    ssl_ciphers: "ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512"
    ssl_prefer_server_ciphers: "on"
    
    # Virtual hosts
    nginx_sites:
      - name: example.com
        server_name: example.com www.example.com
        root: /var/www/example.com
        index: index.html index.htm
        ssl_enabled: true
        ssl_certificate: /etc/ssl/certs/example.com.crt
        ssl_certificate_key: /etc/ssl/private/example.com.key
        proxy_pass: http://localhost:8080
        locations:
          - path: /
            proxy: true
          - path: /static
            proxy: false
            root: /var/www/example.com/static
      
      - name: api.example.com
        server_name: api.example.com
        proxy_pass: http://localhost:3000
        ssl_enabled: true
        ssl_certificate: /etc/ssl/certs/api.example.com.crt
        ssl_certificate_key: /etc/ssl/private/api.example.com.key
    
    # Firewall ports
    nginx_firewall_ports:
      - 80
      - 443
  
  tasks:
    # ========================================
    # PHASE 1: Install Nginx
    # ========================================
    - name: Install Nginx
      block:
        - name: Add Nginx official repository (Debian/Ubuntu)
          block:
            - name: Install prerequisites
              apt:
                name:
                  - curl
                  - gnupg2
                  - ca-certificates
                  - lsb-release
                state: present
            
            - name: Add Nginx signing key
              apt_key:
                url: https://nginx.org/keys/nginx_signing.key
                state: present
            
            - name: Add Nginx repository
              apt_repository:
                repo: "deb http://nginx.org/packages/{{ ansible_distribution | lower }}/ {{ ansible_distribution_release }} nginx"
                state: present
                filename: nginx
            
            - name: Update apt cache
              apt:
                update_cache: yes
          when: ansible_os_family == "Debian"
        
        - name: Install Nginx package
          package:
            name: nginx
            state: present
        
        - name: Ensure Nginx is started and enabled
          service:
            name: nginx
            state: started
            enabled: yes
      
      rescue:
        - name: Install Nginx from default repository
          package:
            name: nginx
            state: present
        
        - name: Start Nginx
          service:
            name: nginx
            state: started
            enabled: yes
      
      tags:
        - nginx
        - install

    # ========================================
    # PHASE 2: Configure Nginx Main Config
    # ========================================
    - name: Configure Nginx main configuration
      block:
        - name: Backup original nginx.conf
          copy:
            src: /etc/nginx/nginx.conf
            dest: /etc/nginx/nginx.conf.backup
            remote_src: yes
            force: no
        
        - name: Deploy nginx.conf template
          template:
            src: templates/nginx/nginx.conf.j2
            dest: /etc/nginx/nginx.conf
            owner: root
            group: root
            mode: '0644'
            validate: 'nginx -t -c %s'
          notify: reload nginx
      
      tags:
        - nginx
        - config

    # ========================================
    # PHASE 3: Create Virtual Host Directories
    # ========================================
    - name: Create virtual host directories
      block:
        - name: Create sites-available directory
          file:
            path: /etc/nginx/sites-available
            state: directory
            mode: '0755'
        
        - name: Create sites-enabled directory
          file:
            path: /etc/nginx/sites-enabled
            state: directory
            mode: '0755'
        
        - name: Create web root directories
          file:
            path: "{{ item.root }}"
            state: directory
            owner: "{{ nginx_user }}"
            group: "{{ nginx_user }}"
            mode: '0755'
          loop: "{{ nginx_sites }}"
          when: item.root is defined
      
      tags:
        - nginx
        - vhosts

    # ========================================
    # PHASE 4: Configure Virtual Hosts
    # ========================================
    - name: Configure virtual hosts
      block:
        - name: Deploy virtual host configurations
          template:
            src: templates/nginx/vhost.conf.j2
            dest: "/etc/nginx/sites-available/{{ item.name }}.conf"
            owner: root
            group: root
            mode: '0644'
          loop: "{{ nginx_sites }}"
          notify: reload nginx
        
        - name: Enable virtual hosts
          file:
            src: "/etc/nginx/sites-available/{{ item.name }}.conf"
            dest: "/etc/nginx/sites-enabled/{{ item.name }}.conf"
            state: link
          loop: "{{ nginx_sites }}"
          notify: reload nginx
        
        - name: Remove default site
          file:
            path: "{{ item }}"
            state: absent
          loop:
            - /etc/nginx/sites-enabled/default
            - /etc/nginx/conf.d/default.conf
          notify: reload nginx
      
      tags:
        - nginx
        - vhosts

    # ========================================
    # PHASE 5: SSL Configuration
    # ========================================
    - name: Configure SSL
      block:
        - name: Create SSL directories
          file:
            path: "{{ item }}"
            state: directory
            mode: '0755'
          loop:
            - /etc/ssl/certs
            - /etc/ssl/private
        
        - name: Set SSL private key directory permissions
          file:
            path: /etc/ssl/private
            mode: '0700'
        
        - name: Generate DH parameters (this may take a while)
          openssl_dhparam:
            path: /etc/ssl/certs/dhparam.pem
            size: 2048
          when: nginx_sites | selectattr('ssl_enabled', 'defined') | selectattr('ssl_enabled') | list | length > 0
      
      tags:
        - nginx
        - ssl

    # ========================================
    # PHASE 6: Firewall Configuration
    # ========================================
    - name: Configure firewall for Nginx
      block:
        - name: Allow Nginx through firewall
          ufw:
            rule: allow
            port: "{{ item }}"
            proto: tcp
          loop: "{{ nginx_firewall_ports }}"
          when: ansible_os_family == "Debian"
      
      tags:
        - nginx
        - firewall

    # ========================================
    # PHASE 7: Validation and Testing
    # ========================================
    - name: Validate Nginx configuration
      block:
        - name: Test Nginx configuration
          command: nginx -t
          changed_when: false
          register: nginx_test
        
        - name: Display test results
          debug:
            var: nginx_test.stderr_lines
        
        - name: Ensure Nginx is running
          service:
            name: nginx
            state: started
        
        - name: Wait for Nginx to be ready
          wait_for:
            port: 80
            delay: 2
            timeout: 30
      
      always:
        - name: Get Nginx status
          command: systemctl status nginx
          changed_when: false
          failed_when: false
          register: nginx_status
        
        - name: Display Nginx status
          debug:
            var: nginx_status.stdout_lines
      
      tags:
        - nginx
        - verify

  handlers:
    - name: reload nginx
      service:
        name: nginx
        state: reloaded
    
    - name: restart nginx
      service:
        name: nginx
        state: restarted
```

### Nginx Configuration Template

```jinja2
{# templates/nginx/nginx.conf.j2 #}
user {{ nginx_user }};
worker_processes {{ nginx_worker_processes }};
pid /run/nginx.pid;
error_log /var/log/nginx/error.log warn;

events {
    worker_connections {{ nginx_worker_connections }};
    use epoll;
    multi_accept on;
}

http {
    ##
    # Basic Settings
    ##
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout {{ nginx_keepalive_timeout }};
    types_hash_max_size 2048;
    server_tokens off;
    client_max_body_size {{ nginx_client_max_body_size }};

    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    ##
    # SSL Settings
    ##
    ssl_protocols {{ ssl_protocols }};
    ssl_ciphers {{ ssl_ciphers }};
    ssl_prefer_server_ciphers {{ ssl_prefer_server_ciphers }};
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    ##
    # Logging Settings
    ##
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    ##
    # Gzip Settings
    ##
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript 
               application/json application/javascript application/xml+rss 
               application/rss+xml font/truetype font/opentype 
               application/vnd.ms-fontobject image/svg+xml;
    gzip_disable "msie6";

    ##
    # Virtual Host Configs
    ##
    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}
```

### Virtual Host Template

```jinja2
{# templates/nginx/vhost.conf.j2 #}
{% if item.ssl_enabled | default(false) %}
# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name {{ item.server_name }};
    return 301 https://$server_name$request_uri;
}

# HTTPS Server
server {
    listen 443 ssl http2;
    server_name {{ item.server_name }};

    # SSL Configuration
    ssl_certificate {{ item.ssl_certificate }};
    ssl_certificate_key {{ item.ssl_certificate_key }};
    ssl_dhparam /etc/ssl/certs/dhparam.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

{% else %}
# HTTP Server
server {
    listen 80;
    server_name {{ item.server_name }};
{% endif %}

    # Logging
    access_log /var/log/nginx/{{ item.name }}-access.log;
    error_log /var/log/nginx/{{ item.name }}-error.log;

{% if item.root is defined %}
    root {{ item.root }};
    index {{ item.index | default('index.html index.htm') }};
{% endif %}

{% if item.locations is defined %}
{% for location in item.locations %}
    location {{ location.path }} {
{% if location.proxy | default(false) %}
        proxy_pass {{ item.proxy_pass }};
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
{% else %}
        try_files $uri $uri/ =404;
{% endif %}
    }
{% endfor %}
{% else %}
    location / {
{% if item.proxy_pass is defined %}
        proxy_pass {{ item.proxy_pass }};
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
{% else %}
        try_files $uri $uri/ =404;
{% endif %}
    }
{% endif %}
}
```

### Step-by-Step Implementation

#### Step 1: Prepare Variables

```yaml
# group_vars/webservers.yml
nginx_sites:
  - name: myapp.com
    server_name: myapp.com www.myapp.com
    root: /var/www/myapp
    proxy_pass: http://localhost:3000
    ssl_enabled: false  # Start without SSL
```

#### Step 2: Run Playbook

```bash
ansible-playbook playbooks/nginx-setup.yml \
  -i inventories/production/hosts \
  --tags "nginx"
```

#### Step 3: Verify Installation

```bash
# Check Nginx status
ansible webservers -i inventories/production/hosts \
  -m command -a "systemctl status nginx"

# Test configuration
ansible webservers -i inventories/production/hosts \
  -m command -a "nginx -t"

# Check listening ports
ansible webservers -i inventories/production/hosts \
  -m command -a "netstat -tlnp | grep nginx"
```

#### Step 4: Test Web Access

```bash
# Test HTTP access
curl -I http://myapp.com

# Expected output:
# HTTP/1.1 200 OK
# Server: nginx
```

### Tags Usage

```bash
# Install only
ansible-playbook playbooks/nginx-setup.yml --tags "install"

# Configure only
ansible-playbook playbooks/nginx-setup.yml --tags "config"

# SSL setup only
ansible-playbook playbooks/nginx-setup.yml --tags "ssl"
```

---

*Due to length constraints, I'll continue with the remaining templates (D through J) in the next section. Would you like me to continue with the Docker, Application Deployment, Kubernetes, OS Patching, Log Management, Security, and Monitoring templates?*
