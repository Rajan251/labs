# Ansible Playbooks - Complete Overview

## What are Ansible Playbooks?

**Ansible playbooks** are YAML-formatted files that define a series of tasks to be executed on remote hosts. They are the core of Ansible's configuration management and orchestration capabilities.

### Key Characteristics

- **Declarative**: You describe the desired state, not the steps to achieve it
- **Idempotent**: Running the same playbook multiple times produces the same result
- **Agentless**: No software installation required on managed nodes
- **Human-readable**: YAML syntax is easy to read and write
- **Version-controllable**: Playbooks are text files perfect for Git

### Anatomy of a Playbook

```yaml
---
- name: Playbook description
  hosts: target_hosts
  become: yes
  vars:
    variable_name: value
  
  tasks:
    - name: Task description
      module_name:
        parameter: value
      notify: handler_name
  
  handlers:
    - name: handler_name
      service:
        name: service_name
        state: restarted
```

## Why Templates are Needed

### 1. **Consistency Across Environments**
Templates ensure that development, staging, and production environments are configured identically, reducing "works on my machine" issues.

### 2. **Faster Onboarding**
New team members can understand and use proven patterns instead of learning from scratch.

### 3. **Reduced Errors**
Pre-tested templates minimize configuration mistakes and security vulnerabilities.

### 4. **Best Practices Enforcement**
Templates embed organizational standards and industry best practices.

### 5. **Time Savings**
Reusable templates eliminate repetitive work and accelerate delivery.

### 6. **Compliance & Auditing**
Standardized templates make it easier to prove compliance with regulations.

## Role-Based vs Flat Playbooks

### Flat Playbooks

**Structure:**
```yaml
# playbook.yml
---
- name: Install and configure Nginx
  hosts: webservers
  become: yes
  
  tasks:
    - name: Install Nginx
      apt:
        name: nginx
        state: present
    
    - name: Copy config
      template:
        src: nginx.conf.j2
        dest: /etc/nginx/nginx.conf
    
    - name: Start Nginx
      service:
        name: nginx
        state: started
```

**Pros:**
- Simple and straightforward
- Good for one-off tasks
- Easy to understand for beginners
- Quick to write

**Cons:**
- Not reusable
- Difficult to maintain at scale
- Code duplication
- Hard to test independently

**Use Cases:**
- Ad-hoc automation
- Simple one-time tasks
- Learning Ansible
- Quick fixes

### Role-Based Playbooks

**Structure:**
```
roles/nginx/
├── tasks/
│   └── main.yml
├── handlers/
│   └── main.yml
├── templates/
│   └── nginx.conf.j2
├── files/
├── vars/
│   └── main.yml
├── defaults/
│   └── main.yml
└── meta/
    └── main.yml
```

**Playbook:**
```yaml
---
- name: Configure web servers
  hosts: webservers
  become: yes
  
  roles:
    - common
    - nginx
    - monitoring
```

**Pros:**
- Highly reusable
- Modular and maintainable
- Easy to test
- Shareable via Ansible Galaxy
- Clear separation of concerns

**Cons:**
- More complex structure
- Steeper learning curve
- Overkill for simple tasks

**Use Cases:**
- Production environments
- Large-scale infrastructure
- Team collaboration
- Complex configurations

### Comparison Table

| Aspect | Flat Playbooks | Role-Based Playbooks |
|--------|---------------|---------------------|
| **Complexity** | Low | Medium-High |
| **Reusability** | Low | High |
| **Maintainability** | Poor at scale | Excellent |
| **Testing** | Difficult | Easy |
| **Organization** | Single file | Multiple files |
| **Best For** | Quick tasks | Production systems |
| **Learning Curve** | Gentle | Steeper |
| **Scalability** | Limited | Excellent |

## Production Concerns

### 1. **Idempotency**

**Definition**: Running a playbook multiple times should produce the same result without unwanted side effects.

**Why It Matters:**
- Safe to re-run after failures
- Prevents configuration drift
- Enables continuous enforcement

**Example - Non-Idempotent:**
```yaml
- name: Add line to file (BAD)
  shell: echo "export PATH=$PATH:/opt/bin" >> ~/.bashrc
```
Running this twice adds the line twice.

**Example - Idempotent:**
```yaml
- name: Add line to file (GOOD)
  lineinfile:
    path: ~/.bashrc
    line: 'export PATH=$PATH:/opt/bin'
    state: present
```
Running this multiple times adds the line only once.

**Best Practices:**
- Use Ansible modules instead of shell/command when possible
- Use `creates` or `removes` parameters with shell/command
- Test playbooks multiple times
- Use `--check` mode for dry runs

### 2. **Security**

**Critical Concerns:**

**a) Secrets Management**
```yaml
# ❌ NEVER DO THIS
vars:
  db_password: "SuperSecret123"

# ✅ USE ANSIBLE VAULT
vars:
  db_password: "{{ vault_db_password }}"
```

**b) Privilege Escalation**
```yaml
# Use become only when necessary
- name: Install package
  apt:
    name: nginx
  become: yes  # Required for system changes

- name: Create user file
  copy:
    src: file.txt
    dest: /home/user/file.txt
  become: no  # Not required for user files
```

**c) SSH Security**
```yaml
# ansible.cfg
[defaults]
host_key_checking = True
private_key_file = ~/.ssh/ansible_key

[privilege_escalation]
become_ask_pass = True
```

**Security Checklist:**
- ✅ Use Ansible Vault for all secrets
- ✅ Enable SSH key-based authentication
- ✅ Disable password authentication
- ✅ Use least privilege principle
- ✅ Audit playbook runs
- ✅ Encrypt sensitive files
- ✅ Use secure connection methods
- ✅ Regularly rotate credentials

### 3. **Version Control**

**Git Best Practices:**

```bash
# .gitignore
*.retry
*.pyc
.vault_pass
group_vars/*/vault.yml
host_vars/*/vault.yml
```

**Branching Strategy:**
```
main/master     → Production-ready code
develop         → Integration branch
feature/*       → New features
hotfix/*        → Emergency fixes
```

**Commit Messages:**
```bash
# Good commit messages
git commit -m "feat: add nginx role with SSL support"
git commit -m "fix: correct handler name in docker role"
git commit -m "docs: update README with inventory examples"
```

### 4. **DRY Principle (Don't Repeat Yourself)**

**Problem - Repetition:**
```yaml
- name: Install package on Ubuntu
  apt:
    name: nginx
  when: ansible_distribution == "Ubuntu"

- name: Install package on CentOS
  yum:
    name: nginx
  when: ansible_distribution == "CentOS"
```

**Solution - Use Variables:**
```yaml
- name: Install package
  package:
    name: nginx
    state: present
```

**Solution - Use Roles:**
```yaml
# Instead of duplicating tasks across playbooks
- include_role:
    name: common
```

**Solution - Use Includes:**
```yaml
- name: Include OS-specific variables
  include_vars: "{{ ansible_distribution }}.yml"
```

### 5. **CI/CD Integration**

**Why Integrate with CI/CD:**
- Automated testing before deployment
- Consistent deployment process
- Rollback capabilities
- Audit trail
- Faster feedback

**Pipeline Stages:**

```yaml
# .gitlab-ci.yml example
stages:
  - lint
  - test
  - deploy

lint:
  stage: lint
  script:
    - ansible-lint playbooks/*.yml

test:
  stage: test
  script:
    - ansible-playbook playbooks/site.yml --syntax-check
    - ansible-playbook playbooks/site.yml --check -i inventories/dev

deploy_dev:
  stage: deploy
  script:
    - ansible-playbook playbooks/site.yml -i inventories/dev
  only:
    - develop

deploy_prod:
  stage: deploy
  script:
    - ansible-playbook playbooks/site.yml -i inventories/prod
  only:
    - main
  when: manual
```

**GitHub Actions Example:**
```yaml
# .github/workflows/ansible.yml
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
      - uses: actions/checkout@v2
      - name: Run ansible-lint
        uses: ansible/ansible-lint-action@main

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Syntax check
        run: |
          ansible-playbook playbooks/site.yml --syntax-check
          ansible-playbook playbooks/site.yml --check
```

### 6. **Error Handling**

**Block/Rescue/Always Pattern:**
```yaml
- name: Handle errors gracefully
  block:
    - name: Attempt risky operation
      command: /opt/app/deploy.sh
      register: result
    
    - name: Verify deployment
      uri:
        url: http://localhost:8080/health
        status_code: 200
  
  rescue:
    - name: Rollback on failure
      command: /opt/app/rollback.sh
    
    - name: Notify team
      mail:
        to: ops@company.com
        subject: "Deployment failed"
        body: "{{ result.stderr }}"
  
  always:
    - name: Cleanup temp files
      file:
        path: /tmp/deploy
        state: absent
```

### 7. **Performance & Scalability**

**Optimization Techniques:**

```yaml
# ansible.cfg
[defaults]
forks = 20              # Parallel execution
gathering = smart       # Smart fact gathering
fact_caching = jsonfile # Cache facts
fact_caching_timeout = 3600

[ssh_connection]
pipelining = True       # Reduce SSH operations
ssh_args = -o ControlMaster=auto -o ControlPersist=60s
```

**Selective Execution:**
```yaml
# Use tags for selective runs
- name: Install packages
  apt:
    name: nginx
  tags:
    - packages
    - nginx

# Run only specific tags
# ansible-playbook site.yml --tags "nginx"
```

**Serial Execution for Rolling Updates:**
```yaml
- name: Rolling update
  hosts: webservers
  serial: 2  # Update 2 servers at a time
  max_fail_percentage: 25
  
  tasks:
    - name: Update application
      # tasks here
```

## Summary

| Concern | Solution | Priority |
|---------|----------|----------|
| **Idempotency** | Use proper modules, test thoroughly | 🔴 Critical |
| **Security** | Vault, SSH keys, least privilege | 🔴 Critical |
| **Version Control** | Git, branching strategy, .gitignore | 🟡 High |
| **DRY** | Roles, variables, includes | 🟡 High |
| **CI/CD** | Automated testing and deployment | 🟢 Medium |
| **Error Handling** | Block/rescue/always, validation | 🟡 High |
| **Performance** | Forks, caching, tags, serial | 🟢 Medium |

---

**Next**: [Project Structure →](02-project-structure.md)
