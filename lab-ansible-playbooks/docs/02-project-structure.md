# Standard Project Folder Structure

This document explains the recommended folder structure for production Ansible projects, following industry best practices.

## Complete Directory Tree

```
ansible/
│
├── inventories/                    # Environment-specific inventories
│   ├── production/
│   │   ├── hosts                  # Production inventory file
│   │   └── group_vars/
│   │       ├── all.yml           # Variables for all hosts
│   │       ├── webservers.yml    # Variables for webserver group
│   │       └── databases.yml     # Variables for database group
│   │
│   ├── staging/
│   │   ├── hosts
│   │   └── group_vars/
│   │       └── all.yml
│   │
│   └── development/
│       ├── hosts
│       └── group_vars/
│           └── all.yml
│
├── group_vars/                     # Global group variables
│   ├── all.yml                    # Variables for all groups
│   ├── all/                       # Split variables into multiple files
│   │   ├── common.yml
│   │   └── vault.yml              # Encrypted secrets
│   ├── webservers.yml
│   └── databases.yml
│
├── host_vars/                      # Host-specific variables
│   ├── web01.example.com.yml
│   ├── db01.example.com.yml
│   └── web01.example.com/
│       ├── vars.yml
│       └── vault.yml              # Encrypted host secrets
│
├── roles/                          # Reusable roles
│   ├── common/                    # Base configuration for all servers
│   │   ├── tasks/
│   │   │   └── main.yml
│   │   ├── handlers/
│   │   │   └── main.yml
│   │   ├── templates/
│   │   ├── files/
│   │   ├── vars/
│   │   │   └── main.yml
│   │   ├── defaults/
│   │   │   └── main.yml
│   │   ├── meta/
│   │   │   └── main.yml
│   │   └── README.md
│   │
│   ├── nginx/                     # Nginx web server role
│   ├── docker/                    # Docker installation role
│   ├── users/                     # User management role
│   ├── hardening/                 # Security hardening role
│   ├── monitoring/                # Monitoring agents role
│   ├── postgresql/                # PostgreSQL database role
│   └── app_deploy/                # Application deployment role
│
├── playbooks/                      # Playbook collection
│   ├── site.yml                   # Master playbook
│   ├── webservers.yml             # Web server setup
│   ├── databases.yml              # Database setup
│   ├── deploy-app.yml             # Application deployment
│   ├── os-patch.yml               # OS patching
│   ├── security.yml               # Security hardening
│   ├── backup.yml                 # Backup operations
│   └── disaster-recovery.yml      # DR procedures
│
├── library/                        # Custom modules (optional)
│   └── custom_module.py
│
├── module_utils/                   # Shared module code (optional)
│   └── helper.py
│
├── filter_plugins/                 # Custom Jinja2 filters (optional)
│   └── custom_filters.py
│
├── callback_plugins/               # Custom callback plugins (optional)
│   └── custom_callback.py
│
├── files/                          # Static files (global)
│   ├── scripts/
│   └── configs/
│
├── templates/                      # Jinja2 templates (global)
│   └── common/
│
├── vars/                           # Additional variable files
│   ├── external_vars.yml
│   └── secrets.yml
│
├── docs/                           # Documentation
│   ├── 01-overview.md
│   ├── 02-project-structure.md
│   ├── runbooks/
│   └── architecture/
│
├── tests/                          # Testing
│   ├── integration/
│   ├── unit/
│   └── inventory
│
├── .github/                        # CI/CD workflows
│   └── workflows/
│       └── ansible-ci.yml
│
├── ansible.cfg                     # Ansible configuration
├── requirements.yml                # Role dependencies
├── requirements.txt                # Python dependencies
├── .ansible-lint                   # Ansible-lint configuration
├── .gitignore                      # Git ignore rules
├── .vault_pass                     # Vault password (DO NOT COMMIT)
├── Makefile                        # Common commands
└── README.md                       # Project documentation
```

## Detailed Component Breakdown

### 1. Inventories Directory

**Purpose**: Define hosts and groups for different environments.

**Structure:**
```
inventories/
├── production/
│   ├── hosts
│   └── group_vars/
├── staging/
│   ├── hosts
│   └── group_vars/
└── development/
    ├── hosts
    └── group_vars/
```

**Example - inventories/production/hosts:**
```ini
# Web Servers
[webservers]
web01.example.com ansible_host=192.168.1.10
web02.example.com ansible_host=192.168.1.11
web03.example.com ansible_host=192.168.1.12

# Database Servers
[databases]
db01.example.com ansible_host=192.168.1.20
db02.example.com ansible_host=192.168.1.21

# Load Balancers
[loadbalancers]
lb01.example.com ansible_host=192.168.1.30

# Application Servers
[appservers]
app01.example.com ansible_host=192.168.1.40
app02.example.com ansible_host=192.168.1.41

# Group of groups
[production:children]
webservers
databases
loadbalancers
appservers

# Variables for all production hosts
[production:vars]
ansible_user=ansible
ansible_ssh_private_key_file=~/.ssh/prod_key
environment=production
```

**YAML Format Alternative:**
```yaml
# inventories/production/hosts.yml
all:
  children:
    webservers:
      hosts:
        web01.example.com:
          ansible_host: 192.168.1.10
        web02.example.com:
          ansible_host: 192.168.1.11
    
    databases:
      hosts:
        db01.example.com:
          ansible_host: 192.168.1.20
    
    production:
      children:
        webservers:
        databases:
      vars:
        ansible_user: ansible
        environment: production
```

### 2. Group Variables (group_vars/)

**Purpose**: Define variables that apply to groups of hosts.

**Example - group_vars/all.yml:**
```yaml
---
# Variables applied to ALL hosts

# NTP Configuration
ntp_servers:
  - 0.pool.ntp.org
  - 1.pool.ntp.org

# DNS Servers
dns_servers:
  - 8.8.8.8
  - 8.8.4.4

# Timezone
timezone: "America/New_York"

# Common packages
common_packages:
  - vim
  - git
  - curl
  - wget
  - htop

# SSH Configuration
ssh_port: 22
ssh_permit_root_login: "no"
ssh_password_authentication: "no"

# Monitoring
enable_monitoring: true
monitoring_server: "monitor.example.com"
```

**Example - group_vars/webservers.yml:**
```yaml
---
# Variables for webserver group

nginx_version: "1.24"
nginx_worker_processes: "auto"
nginx_worker_connections: 1024

# SSL Configuration
ssl_certificate_path: "/etc/ssl/certs"
ssl_protocols: "TLSv1.2 TLSv1.3"

# Application
app_port: 8080
app_user: "www-data"
app_directory: "/var/www/app"

# Firewall rules
firewall_allowed_ports:
  - 80
  - 443
  - 22
```

**Example - group_vars/all/vault.yml (encrypted):**
```yaml
---
# Encrypted with ansible-vault

vault_db_password: "SuperSecretPassword123!"
vault_api_key: "sk-1234567890abcdef"
vault_ssl_key_content: |
  -----BEGIN PRIVATE KEY-----
  MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...
  -----END PRIVATE KEY-----
```

### 3. Host Variables (host_vars/)

**Purpose**: Define variables specific to individual hosts.

**Example - host_vars/web01.example.com.yml:**
```yaml
---
# Specific configuration for web01

server_id: 1
nginx_worker_processes: 4
max_connections: 2048

# Host-specific application config
app_memory_limit: "4G"
app_threads: 8

# Backup configuration
backup_enabled: true
backup_schedule: "0 2 * * *"
```

### 4. Roles Directory

**Purpose**: Organize reusable, modular components.

**Standard Role Structure:**
```
roles/nginx/
├── tasks/              # Main task list
│   ├── main.yml       # Entry point
│   ├── install.yml    # Installation tasks
│   ├── configure.yml  # Configuration tasks
│   └── ssl.yml        # SSL setup tasks
│
├── handlers/           # Service handlers
│   └── main.yml
│
├── templates/          # Jinja2 templates
│   ├── nginx.conf.j2
│   └── site.conf.j2
│
├── files/              # Static files
│   └── custom_error.html
│
├── vars/               # Role variables (high priority)
│   └── main.yml
│
├── defaults/           # Default variables (low priority)
│   └── main.yml
│
├── meta/               # Role metadata and dependencies
│   └── main.yml
│
├── tests/              # Test playbooks
│   ├── inventory
│   └── test.yml
│
└── README.md           # Role documentation
```

**Example - roles/nginx/tasks/main.yml:**
```yaml
---
# Main task file for nginx role

- name: Include OS-specific variables
  include_vars: "{{ ansible_os_family }}.yml"

- name: Install Nginx
  include_tasks: install.yml

- name: Configure Nginx
  include_tasks: configure.yml

- name: Setup SSL
  include_tasks: ssl.yml
  when: nginx_ssl_enabled | default(false)

- name: Ensure Nginx is started and enabled
  service:
    name: nginx
    state: started
    enabled: yes
```

**Example - roles/nginx/defaults/main.yml:**
```yaml
---
# Default variables for nginx role

nginx_user: www-data
nginx_worker_processes: auto
nginx_worker_connections: 1024
nginx_keepalive_timeout: 65
nginx_ssl_enabled: false
nginx_port: 80
nginx_ssl_port: 443

nginx_sites:
  - name: default
    server_name: localhost
    root: /var/www/html
```

**Example - roles/nginx/meta/main.yml:**
```yaml
---
# Role metadata

galaxy_info:
  author: Your Name
  description: Nginx web server installation and configuration
  company: Your Company
  license: MIT
  min_ansible_version: 2.9
  
  platforms:
    - name: Ubuntu
      versions:
        - focal
        - jammy
    - name: Debian
      versions:
        - bullseye
        - bookworm

dependencies:
  - role: common
  - role: firewall
```

### 5. Playbooks Directory

**Purpose**: Orchestrate roles and tasks.

**Example - playbooks/site.yml (Master Playbook):**
```yaml
---
# Master playbook - orchestrates all infrastructure

- name: Apply common configuration to all hosts
  hosts: all
  become: yes
  roles:
    - common
    - monitoring
  tags:
    - common

- name: Configure web servers
  hosts: webservers
  become: yes
  roles:
    - nginx
    - app_deploy
  tags:
    - webservers

- name: Configure database servers
  hosts: databases
  become: yes
  roles:
    - postgresql
    - backup
  tags:
    - databases

- name: Configure load balancers
  hosts: loadbalancers
  become: yes
  roles:
    - haproxy
  tags:
    - loadbalancers
```

### 6. Configuration Files

**ansible.cfg:**
```ini
[defaults]
# Inventory
inventory = ./inventories/production/hosts
host_key_checking = False

# Roles
roles_path = ./roles

# Output
stdout_callback = yaml
bin_ansible_callbacks = True

# Performance
forks = 20
gathering = smart
fact_caching = jsonfile
fact_caching_connection = /tmp/ansible_facts
fact_caching_timeout = 3600

# SSH
remote_user = ansible
private_key_file = ~/.ssh/ansible_key
timeout = 30

# Logging
log_path = ./ansible.log

# Vault
vault_password_file = ./.vault_pass

# Retry files
retry_files_enabled = False

[privilege_escalation]
become = True
become_method = sudo
become_user = root
become_ask_pass = False

[ssh_connection]
pipelining = True
ssh_args = -o ControlMaster=auto -o ControlPersist=60s -o StrictHostKeyChecking=no
control_path = /tmp/ansible-ssh-%%h-%%p-%%r

[colors]
highlight = white
verbose = blue
warn = bright purple
error = red
debug = dark gray
deprecate = purple
skip = cyan
unreachable = red
ok = green
changed = yellow
```

**requirements.yml:**
```yaml
---
# Ansible Galaxy role dependencies

roles:
  # From Ansible Galaxy
  - name: geerlingguy.docker
    version: 6.1.0
  
  - name: geerlingguy.postgresql
    version: 3.4.0
  
  - name: geerlingguy.nginx
    version: 3.1.4

  # From Git repository
  - src: https://github.com/company/custom-role.git
    scm: git
    version: main
    name: custom_role

collections:
  # Ansible collections
  - name: community.general
    version: 7.0.0
  
  - name: ansible.posix
    version: 1.5.0
  
  - name: community.docker
    version: 3.4.0
```

**requirements.txt:**
```txt
# Python dependencies

ansible>=2.15.0,<3.0.0
ansible-lint>=6.17.0
jmespath>=1.0.1
netaddr>=0.8.0
dnspython>=2.3.0
```

**.gitignore:**
```
# Ansible
*.retry
*.log
.vault_pass
vault_pass.txt

# Python
*.pyc
__pycache__/
*.py[cod]
*$py.class
.Python
venv/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Secrets
**/vault.yml
secrets/
*.pem
*.key

# Cache
.cache/
/tmp/
fact_cache/
```

**Makefile:**
```makefile
.PHONY: help install lint syntax-check test deploy-dev deploy-prod

help:
	@echo "Available targets:"
	@echo "  install      - Install dependencies"
	@echo "  lint         - Run ansible-lint"
	@echo "  syntax-check - Check playbook syntax"
	@echo "  test         - Run test playbook"
	@echo "  deploy-dev   - Deploy to development"
	@echo "  deploy-prod  - Deploy to production"

install:
	pip install -r requirements.txt
	ansible-galaxy install -r requirements.yml

lint:
	ansible-lint playbooks/*.yml

syntax-check:
	ansible-playbook playbooks/site.yml --syntax-check

test:
	ansible-playbook playbooks/site.yml -i inventories/development/hosts --check

deploy-dev:
	ansible-playbook playbooks/site.yml -i inventories/development/hosts

deploy-prod:
	@echo "Deploying to PRODUCTION. Are you sure? [y/N] " && read ans && [ $${ans:-N} = y ]
	ansible-playbook playbooks/site.yml -i inventories/production/hosts
```

## Directory Organization Best Practices

### 1. **Separation of Concerns**
- Keep inventory separate from code
- Separate environments (dev/staging/prod)
- Use roles for reusable components
- Keep playbooks focused and specific

### 2. **Variable Precedence**
Understanding variable precedence (highest to lowest):
1. Extra vars (`-e` on command line)
2. Task vars
3. Block vars
4. Role and include vars
5. Set_facts
6. Registered vars
7. Play vars_files
8. Play vars_prompt
9. Play vars
10. Host facts
11. Playbook host_vars
12. Playbook group_vars
13. Inventory host_vars
14. Inventory group_vars
15. Inventory vars
16. Role defaults

### 3. **Naming Conventions**

```yaml
# Use descriptive names
# ✅ Good
nginx_worker_processes: 4
app_deployment_directory: /opt/app

# ❌ Bad
workers: 4
dir: /opt/app

# Use prefixes for role variables
# ✅ Good (nginx role)
nginx_port: 80
nginx_ssl_enabled: true

# Use consistent naming
# snake_case for variables
# kebab-case for file names
# PascalCase for class names (if using)
```

### 4. **File Organization**

```yaml
# Split large files
group_vars/all/
├── common.yml          # Common variables
├── packages.yml        # Package lists
├── users.yml           # User definitions
└── vault.yml           # Encrypted secrets

# Instead of one large file
group_vars/all.yml      # ❌ Becomes unwieldy
```

## Quick Reference

| Directory | Purpose | Example |
|-----------|---------|---------|
| `inventories/` | Host definitions | `inventories/prod/hosts` |
| `group_vars/` | Group variables | `group_vars/webservers.yml` |
| `host_vars/` | Host variables | `host_vars/web01.yml` |
| `roles/` | Reusable components | `roles/nginx/` |
| `playbooks/` | Orchestration | `playbooks/site.yml` |
| `files/` | Static files | `files/config.txt` |
| `templates/` | Jinja2 templates | `templates/app.conf.j2` |

---

**Next**: [Core Playbook Templates →](03-core-templates.md)
