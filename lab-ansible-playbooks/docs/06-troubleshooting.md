# Troubleshooting Guide

This document provides solutions to common Ansible problems encountered in production environments, including root causes, debugging steps, and fixes.

## Table of Contents

1. [SSH Connection Failures](#1-ssh-connection-failures)
2. [Permission Denied Errors](#2-permission-denied-errors)
3. [Handlers Not Running](#3-handlers-not-running)
4. [Playbook Not Idempotent](#4-playbook-not-idempotent)
5. [Variable Scope Issues](#5-variable-scope-issues)
6. [Inventory Mismatch](#6-inventory-mismatch)
7. [Template Rendering Failures](#7-template-rendering-failures)
8. [Module Errors](#8-module-errors)
9. [Performance Issues](#9-performance-issues)
10. [Vault Problems](#10-vault-problems)

---

## 1. SSH Connection Failures

### Problem

```
fatal: [web01]: UNREACHABLE! => {
    "changed": false,
    "msg": "Failed to connect to the host via ssh",
    "unreachable": true
}
```

### Root Causes

1. SSH key not configured
2. Wrong SSH user
3. Host key verification failed
4. Firewall blocking SSH
5. SSH service not running

### Debugging Steps

```bash
# Test SSH connection manually
ssh -i ~/.ssh/ansible_key ansible@web01.example.com

# Verbose SSH output
ssh -vvv -i ~/.ssh/ansible_key ansible@web01.example.com

# Check Ansible connection
ansible web01 -m ping -vvv

# Test with different user
ansible web01 -m ping -u ubuntu
```

### Solutions

#### Solution 1: Configure SSH Key

```bash
# Generate SSH key
ssh-keygen -t rsa -b 4096 -f ~/.ssh/ansible_key

# Copy key to remote host
ssh-copy-id -i ~/.ssh/ansible_key.pub ansible@web01.example.com

# Set correct permissions
chmod 600 ~/.ssh/ansible_key
chmod 644 ~/.ssh/ansible_key.pub
```

#### Solution 2: Update Inventory

```ini
# inventories/production/hosts
[webservers]
web01.example.com ansible_host=192.168.1.10 ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/ansible_key
```

#### Solution 3: Disable Host Key Checking (Dev Only)

```ini
# ansible.cfg
[defaults]
host_key_checking = False

# Or use environment variable
export ANSIBLE_HOST_KEY_CHECKING=False
```

#### Solution 4: Add Host Key

```bash
# Add host key to known_hosts
ssh-keyscan web01.example.com >> ~/.ssh/known_hosts
```

---

## 2. Permission Denied Errors

### Problem

```
fatal: [web01]: FAILED! => {
    "msg": "Failed to set permissions on the temporary files",
    "failed": true
}
```

Or:

```
fatal: [web01]: FAILED! => {
    "msg": "sudo: a password is required"
}
```

### Root Causes

1. User doesn't have sudo privileges
2. Sudo requires password
3. Incorrect file permissions
4. SELinux blocking operations

### Debugging Steps

```bash
# Check sudo access
ansible web01 -m command -a "sudo whoami" -u ansible

# Check user groups
ansible web01 -m command -a "groups ansible"

# Test with become
ansible web01 -m command -a "whoami" --become
```

### Solutions

#### Solution 1: Configure Passwordless Sudo

```bash
# On remote host
sudo visudo

# Add line:
ansible ALL=(ALL) NOPASSWD: ALL
```

#### Solution 2: Use Become in Playbook

```yaml
- name: Install package
  apt:
    name: nginx
  become: yes
  become_user: root
  become_method: sudo
```

#### Solution 3: Provide Sudo Password

```bash
# Prompt for sudo password
ansible-playbook site.yml --ask-become-pass

# Or in ansible.cfg
[privilege_escalation]
become_ask_pass = True
```

#### Solution 4: Fix File Permissions

```yaml
- name: Set correct permissions
  file:
    path: /etc/app/config.conf
    owner: ansible
    group: ansible
    mode: '0644'
  become: yes
```

---

## 3. Handlers Not Running

### Problem

Handlers defined but not executing when notified.

```yaml
tasks:
  - name: Update config
    template:
      src: nginx.conf.j2
      dest: /etc/nginx/nginx.conf
    notify: reload nginx

handlers:
  - name: reload nginx
    service:
      name: nginx
      state: reloaded
```

### Root Causes

1. Handler name mismatch
2. Task didn't change
3. Play failed before handlers run
4. Handler in wrong file

### Debugging Steps

```bash
# Run with verbose output
ansible-playbook site.yml -vv

# Check if task changed
ansible-playbook site.yml --check --diff
```

### Solutions

#### Solution 1: Exact Name Match

```yaml
# ❌ WRONG - Name mismatch
notify: Reload Nginx
handlers:
  - name: reload nginx  # Different case

# ✅ CORRECT - Exact match
notify: reload nginx
handlers:
  - name: reload nginx
```

#### Solution 2: Force Handler Execution

```yaml
- name: Update config
  template:
    src: nginx.conf.j2
    dest: /etc/nginx/nginx.conf
  notify: reload nginx

# Force handlers to run immediately
- name: Flush handlers
  meta: flush_handlers

- name: Verify nginx is running
  uri:
    url: http://localhost
```

#### Solution 3: Use Listen

```yaml
tasks:
  - name: Update config
    template:
      src: nginx.conf.j2
      dest: /etc/nginx/nginx.conf
    notify: restart web services

  - name: Update SSL cert
    copy:
      src: ssl.crt
      dest: /etc/ssl/certs/ssl.crt
    notify: restart web services

handlers:
  - name: reload nginx
    service:
      name: nginx
      state: reloaded
    listen: restart web services
```

---

## 4. Playbook Not Idempotent

### Problem

Running playbook multiple times causes changes every time.

```
TASK [Add line to file] ****
changed: [web01]

# Run again
TASK [Add line to file] ****
changed: [web01]  # Should be "ok" not "changed"
```

### Root Causes

1. Using shell/command without changed_when
2. Not using proper modules
3. Missing state parameter
4. Timestamp in files

### Debugging Steps

```bash
# Run twice and compare
ansible-playbook site.yml
ansible-playbook site.yml  # Should show no changes
```

### Solutions

#### Solution 1: Use Proper Modules

```yaml
# ❌ NOT IDEMPOTENT
- name: Add line to file
  shell: echo "export PATH=$PATH:/opt/bin" >> ~/.bashrc

# ✅ IDEMPOTENT
- name: Add line to file
  lineinfile:
    path: ~/.bashrc
    line: 'export PATH=$PATH:/opt/bin'
    state: present
```

#### Solution 2: Use changed_when

```yaml
# ❌ NOT IDEMPOTENT
- name: Check service
  command: systemctl is-active nginx

# ✅ IDEMPOTENT
- name: Check service
  command: systemctl is-active nginx
  register: nginx_status
  changed_when: false
  failed_when: false
```

#### Solution 3: Use creates/removes

```yaml
# ❌ NOT IDEMPOTENT
- name: Extract archive
  command: tar -xzf /tmp/app.tar.gz -C /opt/app

# ✅ IDEMPOTENT
- name: Extract archive
  command: tar -xzf /tmp/app.tar.gz -C /opt/app
  args:
    creates: /opt/app/bin/app
```

---

## 5. Variable Scope Issues

### Problem

Variables not accessible or wrong values used.

```
fatal: [web01]: FAILED! => {
    "msg": "The task includes an option with an undefined variable. The error was: 'app_port' is undefined"
}
```

### Root Causes

1. Variable defined in wrong scope
2. Variable precedence issue
3. Typo in variable name
4. Variable not imported

### Debugging Steps

```bash
# Show all variables for host
ansible web01 -m debug -a "var=hostvars[inventory_hostname]"

# Show specific variable
ansible web01 -m debug -a "var=app_port"

# List all variables
ansible-inventory -i inventories/production/hosts --list --yaml
```

### Variable Precedence (Highest to Lowest)

1. Extra vars (`-e`)
2. Task vars
3. Block vars
4. Role and include vars
5. Play vars_files
6. Play vars
7. Host facts
8. host_vars
9. group_vars
10. Role defaults

### Solutions

#### Solution 1: Define in Correct Scope

```yaml
# For all hosts
# group_vars/all.yml
app_port: 3000

# For specific group
# group_vars/webservers.yml
app_port: 8080

# For specific host
# host_vars/web01.yml
app_port: 9000
```

#### Solution 2: Use Default Values

```yaml
# Use default if variable not defined
- name: Start application
  service:
    name: myapp
    state: started
  environment:
    PORT: "{{ app_port | default(3000) }}"
```

#### Solution 3: Check Variable Defined

```yaml
- name: Ensure variable is defined
  assert:
    that:
      - app_port is defined
    fail_msg: "app_port must be defined"
```

---

## 6. Inventory Mismatch

### Problem

Hosts not found or wrong hosts targeted.

```
[WARNING]: Could not match supplied host pattern, ignoring: webservers
```

### Root Causes

1. Wrong inventory file
2. Group name typo
3. Host not in inventory
4. Inventory file syntax error

### Debugging Steps

```bash
# List inventory
ansible-inventory -i inventories/production/hosts --list

# Show inventory graph
ansible-inventory -i inventories/production/hosts --graph

# Verify host in group
ansible-inventory -i inventories/production/hosts --host web01
```

### Solutions

#### Solution 1: Verify Inventory Path

```bash
# Specify inventory explicitly
ansible-playbook -i inventories/production/hosts site.yml

# Or set in ansible.cfg
[defaults]
inventory = ./inventories/production/hosts
```

#### Solution 2: Check Group Names

```yaml
# ❌ WRONG
- hosts: webserver  # Missing 's'

# ✅ CORRECT
- hosts: webservers
```

#### Solution 3: Validate Inventory Syntax

```bash
# Check YAML syntax
yamllint inventories/production/hosts.yml

# Verify inventory loads
ansible-inventory -i inventories/production/hosts.yml --list
```

---

## 7. Template Rendering Failures

### Problem

```
fatal: [web01]: FAILED! => {
    "msg": "AnsibleUndefinedVariable: 'nginx_port' is undefined"
}
```

### Root Causes

1. Variable not defined
2. Jinja2 syntax error
3. Wrong variable name
4. Missing filter

### Debugging Steps

```bash
# Test template locally
ansible all -i inventories/production/hosts -m template \
  -a "src=templates/nginx.conf.j2 dest=/tmp/nginx.conf" \
  --check --diff
```

### Solutions

#### Solution 1: Provide Default Values

```jinja2
{# templates/nginx.conf.j2 #}

# ❌ FAILS if nginx_port not defined
listen {{ nginx_port }};

# ✅ WORKS with default
listen {{ nginx_port | default(80) }};
```

#### Solution 2: Check Variable Defined

```jinja2
{% if nginx_ssl_enabled is defined and nginx_ssl_enabled %}
    listen 443 ssl;
    ssl_certificate {{ ssl_cert_path }};
{% endif %}
```

#### Solution 3: Use Filters

```jinja2
# Convert to JSON
{{ app_config | to_json }}

# Convert to YAML
{{ app_config | to_yaml }}

# Join list
{{ dns_servers | join(',') }}

# Default value
{{ app_port | default(3000) }}
```

---

## 8. Module Errors

### Problem

```
fatal: [web01]: FAILED! => {
    "msg": "The module apt was not found in configured module paths"
}
```

### Root Causes

1. Module not installed
2. Wrong module name
3. Python dependencies missing
4. Module deprecated

### Debugging Steps

```bash
# List available modules
ansible-doc -l

# Show module documentation
ansible-doc apt

# Check Python path
ansible web01 -m setup -a "filter=ansible_python*"
```

### Solutions

#### Solution 1: Install Required Collections

```bash
# Install collection
ansible-galaxy collection install community.general

# Install from requirements
ansible-galaxy collection install -r requirements.yml
```

```yaml
# requirements.yml
collections:
  - name: community.general
    version: 7.0.0
  - name: ansible.posix
    version: 1.5.0
```

#### Solution 2: Use Correct Module Name

```yaml
# ❌ WRONG - Old module name
- name: Install package
  yum:
    name: nginx

# ✅ CORRECT - Use package module
- name: Install package
  package:
    name: nginx
```

#### Solution 3: Install Python Dependencies

```bash
# On control node
pip install netaddr dnspython

# On managed nodes
ansible all -m pip -a "name=netaddr state=present"
```

---

## 9. Performance Issues

### Problem

Playbooks running very slowly.

### Root Causes

1. Serial execution (forks=1)
2. Fact gathering on every run
3. No SSH pipelining
4. Slow network
5. Large inventory

### Debugging Steps

```bash
# Time playbook execution
time ansible-playbook site.yml

# Profile tasks
ansible-playbook site.yml --profile

# Verbose output
ansible-playbook site.yml -vvv
```

### Solutions

#### Solution 1: Optimize ansible.cfg

```ini
[defaults]
# Increase parallel execution
forks = 50

# Smart fact gathering
gathering = smart
fact_caching = jsonfile
fact_caching_connection = /tmp/ansible_facts
fact_caching_timeout = 86400

# Disable cowsay
nocows = 1

[ssh_connection]
# Enable pipelining
pipelining = True

# SSH multiplexing
ssh_args = -o ControlMaster=auto -o ControlPersist=60s
control_path = /tmp/ansible-ssh-%%h-%%p-%%r
```

#### Solution 2: Disable Fact Gathering When Not Needed

```yaml
- hosts: all
  gather_facts: no  # Skip fact gathering
  tasks:
    - name: Simple task
      command: echo "Hello"
```

#### Solution 3: Use Async for Long Tasks

```yaml
- name: Long running task
  command: /usr/local/bin/long-task
  async: 3600
  poll: 0
  register: long_task

- name: Check on task later
  async_status:
    jid: "{{ long_task.ansible_job_id }}"
  register: job_result
  until: job_result.finished
  retries: 30
  delay: 60
```

---

## 10. Vault Problems

### Problem

```
ERROR! Attempting to decrypt but no vault secrets found
```

Or:

```
ERROR! Decryption failed (no vault secrets would found that could decrypt)
```

### Root Causes

1. Vault password file not found
2. Wrong vault password
3. Vault file corrupted
4. Multiple vault IDs mixed up

### Debugging Steps

```bash
# View vault file
ansible-vault view group_vars/all/vault.yml

# Verify vault password
ansible-vault decrypt group_vars/all/vault.yml --output=-
```

### Solutions

#### Solution 1: Provide Vault Password

```bash
# Prompt for password
ansible-playbook site.yml --ask-vault-pass

# Use password file
ansible-playbook site.yml --vault-password-file .vault_pass

# Set in ansible.cfg
[defaults]
vault_password_file = ./.vault_pass
```

#### Solution 2: Rekey Vault File

```bash
# Change vault password
ansible-vault rekey group_vars/all/vault.yml
```

#### Solution 3: Use Vault IDs

```bash
# Encrypt with vault ID
ansible-vault encrypt --vault-id prod@prompt group_vars/production/vault.yml

# Decrypt with vault ID
ansible-playbook site.yml --vault-id prod@.vault_pass_prod
```

---

## Quick Troubleshooting Checklist

### Before Running Playbook

- [ ] Syntax check: `ansible-playbook site.yml --syntax-check`
- [ ] Lint check: `ansible-lint playbooks/*.yml`
- [ ] Inventory check: `ansible-inventory --list`
- [ ] Connectivity check: `ansible all -m ping`
- [ ] Dry run: `ansible-playbook site.yml --check`

### When Playbook Fails

1. **Read the error message carefully**
2. **Run with verbose output**: `-vvv`
3. **Check the specific task**: `--start-at-task="Task Name"`
4. **Limit to one host**: `--limit web01`
5. **Check logs**: `/var/log/ansible.log`

### Common Commands

```bash
# Verbose output
ansible-playbook site.yml -vvv

# Dry run
ansible-playbook site.yml --check --diff

# Step through playbook
ansible-playbook site.yml --step

# Start at specific task
ansible-playbook site.yml --start-at-task="Install Nginx"

# Limit to specific hosts
ansible-playbook site.yml --limit web01,web02

# List tasks
ansible-playbook site.yml --list-tasks

# List tags
ansible-playbook site.yml --list-tags
```

---

**Next**: [CI/CD Integration →](07-cicd-integration.md)
