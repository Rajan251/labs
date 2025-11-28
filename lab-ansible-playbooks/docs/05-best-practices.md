# Best Practices for Production Ansible

This document outlines production best practices for Ansible automation, covering idempotency, roles, secrets management, handlers, tags, testing, linting, and CI/CD integration.

## Table of Contents

1. [Idempotency Guidelines](#idempotency-guidelines)
2. [Using Roles Effectively](#using-roles-effectively)
3. [Secrets Management with Vault](#secrets-management-with-vault)
4. [Handler Best Practices](#handler-best-practices)
5. [Effective Use of Tags](#effective-use-of-tags)
6. [Dry-Run and Testing](#dry-run-and-testing)
7. [Linting with ansible-lint](#linting-with-ansible-lint)
8. [CI/CD Integration](#cicd-integration)
9. [Performance Optimization](#performance-optimization)
10. [Documentation Standards](#documentation-standards)

---

## Idempotency Guidelines

### What is Idempotency?

**Idempotency** means running the same playbook multiple times produces the same result without unwanted side effects.

### Why It Matters

✅ Safe to re-run after failures  
✅ Prevents configuration drift  
✅ Enables continuous enforcement  
✅ Predictable outcomes  

### Idempotent vs Non-Idempotent Examples

#### ❌ Non-Idempotent (BAD)

```yaml
# This adds the line every time it runs
- name: Add PATH to bashrc
  shell: echo 'export PATH=$PATH:/opt/bin' >> ~/.bashrc

# This creates duplicate entries
- name: Add user to group
  command: usermod -aG docker john

# This downloads every time
- name: Download file
  command: wget https://example.com/file.tar.gz
```

#### ✅ Idempotent (GOOD)

```yaml
# This adds the line only once
- name: Add PATH to bashrc
  lineinfile:
    path: ~/.bashrc
    line: 'export PATH=$PATH:/opt/bin'
    state: present

# This adds user only if not in group
- name: Add user to group
  user:
    name: john
    groups: docker
    append: yes

# This downloads only if file doesn't exist
- name: Download file
  get_url:
    url: https://example.com/file.tar.gz
    dest: /tmp/file.tar.gz
    checksum: sha256:abc123...
```

### Best Practices for Idempotency

#### 1. Prefer Modules Over Commands

```yaml
# ❌ BAD - Not idempotent
- name: Install package
  command: apt-get install nginx

# ✅ GOOD - Idempotent
- name: Install package
  apt:
    name: nginx
    state: present
```

#### 2. Use `creates` or `removes` with Shell/Command

```yaml
# When you must use shell/command
- name: Extract archive
  command: tar -xzf /tmp/app.tar.gz -C /opt/app
  args:
    creates: /opt/app/bin/app  # Only run if this doesn't exist

- name: Compile source
  command: make install
  args:
    chdir: /opt/source
    creates: /usr/local/bin/myapp
```

#### 3. Use `changed_when` to Control Change Detection

```yaml
- name: Check service status
  command: systemctl is-active nginx
  register: nginx_status
  changed_when: false  # Never report as changed
  failed_when: false

- name: Get file checksum
  stat:
    path: /etc/config.conf
  register: config_stat
  changed_when: false
```

#### 4. Use `state` Parameter

```yaml
# File management
- name: Ensure file exists
  file:
    path: /etc/app/config.conf
    state: file  # or: absent, directory, link

# Package management
- name: Ensure package state
  apt:
    name: nginx
    state: present  # or: absent, latest

# Service management
- name: Ensure service state
  service:
    name: nginx
    state: started  # or: stopped, restarted, reloaded
    enabled: yes
```

---

## Using Roles Effectively

### Role Structure

```
roles/nginx/
├── tasks/
│   ├── main.yml          # Main entry point
│   ├── install.yml       # Installation tasks
│   ├── configure.yml     # Configuration tasks
│   └── ssl.yml           # SSL setup
├── handlers/
│   └── main.yml          # Service handlers
├── templates/
│   ├── nginx.conf.j2
│   └── site.conf.j2
├── files/
│   └── custom_page.html
├── vars/
│   └── main.yml          # Role variables (high priority)
├── defaults/
│   └── main.yml          # Default variables (low priority)
├── meta/
│   └── main.yml          # Role metadata and dependencies
└── README.md             # Role documentation
```

### Role Best Practices

#### 1. Keep Roles Focused

```yaml
# ✅ GOOD - Single responsibility
roles/
├── nginx/              # Only Nginx
├── docker/             # Only Docker
├── users/              # Only user management

# ❌ BAD - Too broad
roles/
└── webserver/          # Nginx + app + SSL + monitoring
```

#### 2. Use Role Dependencies

```yaml
# roles/nginx/meta/main.yml
---
dependencies:
  - role: common
  - role: firewall
    vars:
      firewall_ports:
        - 80
        - 443
```

#### 3. Parameterize Roles

```yaml
# roles/nginx/defaults/main.yml
---
nginx_port: 80
nginx_worker_processes: auto
nginx_sites: []

# Use in playbook
- hosts: webservers
  roles:
    - role: nginx
      vars:
        nginx_port: 8080
        nginx_sites:
          - name: myapp.com
            root: /var/www/myapp
```

#### 4. Include vs Import

```yaml
# include_tasks - Dynamic (runtime)
- name: Include OS-specific tasks
  include_tasks: "{{ ansible_os_family }}.yml"

# import_tasks - Static (parse time)
- name: Import common tasks
  import_tasks: common.yml
```

---

## Secrets Management with Vault

### Creating Encrypted Files

```bash
# Create new encrypted file
ansible-vault create group_vars/all/vault.yml

# Edit encrypted file
ansible-vault edit group_vars/all/vault.yml

# Encrypt existing file
ansible-vault encrypt group_vars/all/secrets.yml

# Decrypt file
ansible-vault decrypt group_vars/all/vault.yml

# View encrypted file
ansible-vault view group_vars/all/vault.yml

# Rekey (change password)
ansible-vault rekey group_vars/all/vault.yml
```

### Vault Password File

```bash
# Create password file
echo "MyVaultPassword123" > .vault_pass
chmod 600 .vault_pass

# Add to .gitignore
echo ".vault_pass" >> .gitignore

# Configure in ansible.cfg
[defaults]
vault_password_file = ./.vault_pass
```

### Best Practices for Vault

#### 1. Separate Vault Variables

```yaml
# group_vars/all/vars.yml (not encrypted)
db_host: "db.example.com"
db_port: 5432
db_name: "myapp"
db_user: "appuser"
db_password: "{{ vault_db_password }}"  # Reference vault variable

# group_vars/all/vault.yml (encrypted)
vault_db_password: "SuperSecretPassword123"
vault_api_key: "sk-1234567890abcdef"
vault_ssl_key: |
  -----BEGIN PRIVATE KEY-----
  MIIEvQIBADANBgkqhkiG9w0BAQEFAASC...
  -----END PRIVATE KEY-----
```

#### 2. Use Vault IDs for Multiple Passwords

```bash
# Create vault with ID
ansible-vault create --vault-id prod@prompt group_vars/production/vault.yml
ansible-vault create --vault-id dev@prompt group_vars/development/vault.yml

# Run playbook with multiple vault passwords
ansible-playbook site.yml \
  --vault-id prod@.vault_pass_prod \
  --vault-id dev@.vault_pass_dev
```

#### 3. Encrypt Specific Variables

```yaml
# Encrypt single variable
db_password: !vault |
  $ANSIBLE_VAULT;1.1;AES256
  66386439653966636339613934373366...
```

```bash
# Create encrypted string
ansible-vault encrypt_string 'MyPassword123' --name 'db_password'
```

---

## Handler Best Practices

### What are Handlers?

Handlers are tasks that run only when notified and only once at the end of a play.

### Handler Examples

```yaml
# tasks/main.yml
- name: Update nginx configuration
  template:
    src: nginx.conf.j2
    dest: /etc/nginx/nginx.conf
  notify: reload nginx

- name: Update SSL certificate
  copy:
    src: ssl.crt
    dest: /etc/ssl/certs/ssl.crt
  notify: reload nginx

# handlers/main.yml
- name: reload nginx
  service:
    name: nginx
    state: reloaded

- name: restart nginx
  service:
    name: nginx
    state: restarted
```

### Handler Best Practices

#### 1. Use Reload Instead of Restart

```yaml
# ✅ GOOD - Minimal disruption
- name: reload nginx
  service:
    name: nginx
    state: reloaded

# ❌ BAD - Full service restart
- name: restart nginx
  service:
    name: nginx
    state: restarted
```

#### 2. Listen to Multiple Notifications

```yaml
# tasks
- name: Update config
  template:
    src: app.conf.j2
    dest: /etc/app/app.conf
  notify: restart application

- name: Update binary
  copy:
    src: app
    dest: /usr/local/bin/app
  notify: restart application

# handlers
- name: restart application
  service:
    name: myapp
    state: restarted
  listen: restart application
```

#### 3. Force Handler Execution

```yaml
# Force handlers to run immediately
- name: Update critical config
  template:
    src: config.j2
    dest: /etc/app/config.conf
  notify: restart app

- name: Flush handlers
  meta: flush_handlers

- name: Verify app is running
  uri:
    url: http://localhost:8080/health
```

---

## Effective Use of Tags

### Tagging Tasks

```yaml
- name: Install packages
  apt:
    name: nginx
  tags:
    - packages
    - nginx
    - install

- name: Configure nginx
  template:
    src: nginx.conf.j2
    dest: /etc/nginx/nginx.conf
  tags:
    - config
    - nginx

- name: Start nginx
  service:
    name: nginx
    state: started
  tags:
    - service
    - nginx
```

### Running with Tags

```bash
# Run only nginx tasks
ansible-playbook site.yml --tags "nginx"

# Run install and config, skip service
ansible-playbook site.yml --tags "install,config"

# Skip specific tags
ansible-playbook site.yml --skip-tags "service"

# List all tags
ansible-playbook site.yml --list-tags
```

### Tag Best Practices

#### 1. Use Consistent Tag Naming

```yaml
# ✅ GOOD - Consistent naming
tags:
  - install
  - config
  - service

# ❌ BAD - Inconsistent
tags:
  - installation
  - configure
  - start_service
```

#### 2. Use Special Tags

```yaml
# Always run (even with --tags)
- name: Critical security check
  command: /usr/local/bin/security-check
  tags:
    - always

# Never run (unless explicitly specified)
- name: Dangerous operation
  command: rm -rf /tmp/*
  tags:
    - never
    - cleanup
```

---

## Dry-Run and Testing

### Check Mode (Dry Run)

```bash
# Run in check mode (no changes)
ansible-playbook site.yml --check

# Show differences
ansible-playbook site.yml --check --diff

# Limit to specific hosts
ansible-playbook site.yml --check --limit web01
```

### Syntax Check

```bash
# Check playbook syntax
ansible-playbook site.yml --syntax-check

# Check all playbooks
find playbooks/ -name "*.yml" -exec ansible-playbook {} --syntax-check \;
```

### Testing Strategies

#### 1. Molecule for Role Testing

```bash
# Install Molecule
pip install molecule molecule-docker

# Initialize role with Molecule
molecule init role my_role --driver-name docker

# Test role
cd roles/my_role
molecule test
```

#### 2. Test in Development First

```bash
# Test in dev environment
ansible-playbook site.yml -i inventories/development/hosts

# Then staging
ansible-playbook site.yml -i inventories/staging/hosts

# Finally production
ansible-playbook site.yml -i inventories/production/hosts
```

---

## Linting with ansible-lint

### Install ansible-lint

```bash
pip install ansible-lint
```

### Run Linting

```bash
# Lint all playbooks
ansible-lint playbooks/*.yml

# Lint specific playbook
ansible-lint playbooks/site.yml

# Lint with specific rules
ansible-lint -r rules/ playbooks/site.yml

# Auto-fix issues
ansible-lint --fix playbooks/site.yml
```

### Configuration

```yaml
# .ansible-lint
---
profile: production

exclude_paths:
  - .cache/
  - .github/
  - test/

skip_list:
  - yaml[line-length]  # Allow long lines
  - name[casing]       # Allow flexible naming

warn_list:
  - experimental
  - role-name

# Enable specific rules
enable_list:
  - no-changed-when
  - no-handler
  - syntax-check
```

### Common Lint Rules

```yaml
# ❌ FAILS: Missing name
- apt:
    name: nginx

# ✅ PASSES: Has descriptive name
- name: Install Nginx web server
  apt:
    name: nginx

# ❌ FAILS: Using command without changed_when
- command: echo "Hello"

# ✅ PASSES: Has changed_when
- name: Echo message
  command: echo "Hello"
  changed_when: false

# ❌ FAILS: Using shell when module exists
- shell: systemctl restart nginx

# ✅ PASSES: Using service module
- name: Restart Nginx
  service:
    name: nginx
    state: restarted
```

---

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/ansible-ci.yml
name: Ansible CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install ansible ansible-lint
      
      - name: Run ansible-lint
        run: |
          ansible-lint playbooks/*.yml

  syntax-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install Ansible
        run: pip install ansible
      
      - name: Syntax check
        run: |
          find playbooks/ -name "*.yml" -exec ansible-playbook {} --syntax-check \;

  deploy-dev:
    needs: [lint, syntax-check]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    steps:
      - uses: actions/checkout@v3
      
      - name: Install Ansible
        run: pip install ansible
      
      - name: Deploy to development
        env:
          ANSIBLE_VAULT_PASSWORD: ${{ secrets.ANSIBLE_VAULT_PASSWORD }}
        run: |
          echo "$ANSIBLE_VAULT_PASSWORD" > .vault_pass
          ansible-playbook playbooks/site.yml -i inventories/development/hosts

  deploy-prod:
    needs: [lint, syntax-check]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: production
    steps:
      - uses: actions/checkout@v3
      
      - name: Install Ansible
        run: pip install ansible
      
      - name: Deploy to production
        env:
          ANSIBLE_VAULT_PASSWORD: ${{ secrets.ANSIBLE_VAULT_PASSWORD }}
        run: |
          echo "$ANSIBLE_VAULT_PASSWORD" > .vault_pass
          ansible-playbook playbooks/site.yml -i inventories/production/hosts
```

### GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - lint
  - test
  - deploy

variables:
  ANSIBLE_FORCE_COLOR: "true"

lint:
  stage: lint
  image: python:3.10
  before_script:
    - pip install ansible ansible-lint
  script:
    - ansible-lint playbooks/*.yml

syntax-check:
  stage: test
  image: python:3.10
  before_script:
    - pip install ansible
  script:
    - find playbooks/ -name "*.yml" -exec ansible-playbook {} --syntax-check \;

deploy-dev:
  stage: deploy
  image: python:3.10
  before_script:
    - pip install ansible
    - echo "$ANSIBLE_VAULT_PASSWORD" > .vault_pass
  script:
    - ansible-playbook playbooks/site.yml -i inventories/development/hosts
  only:
    - develop
  environment:
    name: development

deploy-prod:
  stage: deploy
  image: python:3.10
  before_script:
    - pip install ansible
    - echo "$ANSIBLE_VAULT_PASSWORD" > .vault_pass
  script:
    - ansible-playbook playbooks/site.yml -i inventories/production/hosts
  only:
    - main
  when: manual
  environment:
    name: production
```

---

## Performance Optimization

### ansible.cfg Optimizations

```ini
[defaults]
# Increase parallel execution
forks = 50

# Smart fact gathering
gathering = smart
fact_caching = jsonfile
fact_caching_connection = /tmp/ansible_facts
fact_caching_timeout = 86400

# SSH optimizations
[ssh_connection]
pipelining = True
ssh_args = -o ControlMaster=auto -o ControlPersist=60s
control_path = /tmp/ansible-ssh-%%h-%%p-%%r
```

### Playbook Optimizations

```yaml
# Disable fact gathering when not needed
- hosts: all
  gather_facts: no
  tasks:
    - name: Simple task
      command: echo "Hello"

# Use async for long-running tasks
- name: Long running task
  command: /usr/local/bin/long-task
  async: 3600
  poll: 0
  register: long_task

- name: Check on long task
  async_status:
    jid: "{{ long_task.ansible_job_id }}"
  register: job_result
  until: job_result.finished
  retries: 30
  delay: 60
```

---

## Documentation Standards

### Playbook Documentation

```yaml
---
# playbooks/deploy-app.yml
# Purpose: Deploy application with zero-downtime
# Author: DevOps Team
# Last Updated: 2024-01-15
# Dependencies: Docker, Nginx
# Tags: deploy, application

- name: Deploy Application
  hosts: appservers
  become: yes
  
  # Document variables
  vars:
    # Application version to deploy
    app_version: "1.2.3"
    
    # Deployment strategy: rolling, blue-green, canary
    deployment_strategy: "rolling"
```

### Role README

```markdown
# Nginx Role

## Description
Installs and configures Nginx web server with SSL support.

## Requirements
- Ubuntu 20.04+ or Debian 11+
- Python 3.8+

## Role Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `nginx_port` | 80 | HTTP port |
| `nginx_ssl_port` | 443 | HTTPS port |
| `nginx_worker_processes` | auto | Worker processes |

## Dependencies
- common
- firewall

## Example Playbook

\`\`\`yaml
- hosts: webservers
  roles:
    - role: nginx
      vars:
        nginx_port: 8080
\`\`\`

## License
MIT

## Author
DevOps Team
```

---

**Next**: [Troubleshooting →](06-troubleshooting.md)
