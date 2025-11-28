# Core Playbook Templates (Part 2)

This document continues the production-grade Ansible playbook templates, covering Docker, Application Deployment, Kubernetes, OS Patching, Log Management, Security, and Monitoring.

## Table of Contents

4. [Docker Installation](#d-docker-installation-template)
5. [Application Deployment](#e-application-deployment-playbook)
6. [Kubernetes Node Preparation](#f-kubernetes-node-preparation-template)
7. [OS Patching (Rolling Update)](#g-os-patching-safe-rolling-update)
8. [Log Management](#h-log-management-template)
9. [Security & Hardening](#i-security--hardening-template)
10. [Monitoring](#j-monitoring-template)

---

## (D) Docker Installation Template

### Purpose
Install Docker CE, configure daemon settings, add users to docker group, and ensure service is running.

### Use Case
- Container runtime setup
- Development environment preparation
- CI/CD agent configuration
- Microservices infrastructure

### Full Playbook

```yaml
---
# playbooks/docker-install.yml
# Purpose: Install and configure Docker CE

- name: Install and Configure Docker
  hosts: docker_hosts
  become: yes
  gather_facts: yes
  
  vars:
    # Docker version (leave empty for latest)
    docker_version: ""
    
    # Users to add to docker group
    docker_users:
      - devops
      - jenkins
      - gitlab-runner
    
    # Docker daemon configuration
    docker_daemon_config:
      log-driver: "json-file"
      log-opts:
        max-size: "100m"
        max-file: "3"
      storage-driver: "overlay2"
      live-restore: true
      userland-proxy: false
      default-address-pools:
        - base: "172.17.0.0/12"
          size: 24
    
    # Docker Compose version
    docker_compose_version: "2.23.0"
    
    # Enable Docker metrics
    enable_metrics: true
    metrics_address: "0.0.0.0:9323"
  
  tasks:
    # ========================================
    # PHASE 1: Pre-installation Cleanup
    # ========================================
    - name: Remove old Docker versions
      block:
        - name: Remove old Docker packages (Debian/Ubuntu)
          apt:
            name:
              - docker
              - docker-engine
              - docker.io
              - containerd
              - runc
            state: absent
          when: ansible_os_family == "Debian"
        
        - name: Remove old Docker packages (RedHat/CentOS)
          yum:
            name:
              - docker
              - docker-client
              - docker-client-latest
              - docker-common
              - docker-latest
              - docker-latest-logrotate
              - docker-logrotate
              - docker-engine
            state: absent
          when: ansible_os_family == "RedHat"
      
      tags:
        - docker
        - cleanup

    # ========================================
    # PHASE 2: Install Prerequisites
    # ========================================
    - name: Install prerequisites
      block:
        - name: Install required packages (Debian/Ubuntu)
          apt:
            name:
              - apt-transport-https
              - ca-certificates
              - curl
              - gnupg
              - lsb-release
              - software-properties-common
            state: present
            update_cache: yes
          when: ansible_os_family == "Debian"
        
        - name: Install required packages (RedHat/CentOS)
          yum:
            name:
              - yum-utils
              - device-mapper-persistent-data
              - lvm2
            state: present
          when: ansible_os_family == "RedHat"
      
      tags:
        - docker
        - prerequisites

    # ========================================
    # PHASE 3: Add Docker Repository
    # ========================================
    - name: Add Docker repository
      block:
        # Debian/Ubuntu
        - name: Add Docker GPG key (Debian/Ubuntu)
          apt_key:
            url: https://download.docker.com/linux/{{ ansible_distribution | lower }}/gpg
            state: present
          when: ansible_os_family == "Debian"
        
        - name: Add Docker repository (Debian/Ubuntu)
          apt_repository:
            repo: "deb [arch={{ 'amd64' if ansible_architecture == 'x86_64' else ansible_architecture }}] https://download.docker.com/linux/{{ ansible_distribution | lower }} {{ ansible_distribution_release }} stable"
            state: present
            filename: docker
          when: ansible_os_family == "Debian"
        
        # RedHat/CentOS
        - name: Add Docker repository (RedHat/CentOS)
          yum_repository:
            name: docker-ce
            description: Docker CE Repository
            baseurl: "https://download.docker.com/linux/centos/{{ ansible_distribution_major_version }}/$basearch/stable"
            gpgcheck: yes
            gpgkey: https://download.docker.com/linux/centos/gpg
            enabled: yes
          when: ansible_os_family == "RedHat"
      
      tags:
        - docker
        - repository

    # ========================================
    # PHASE 4: Install Docker
    # ========================================
    - name: Install Docker Engine
      block:
        - name: Install Docker CE (Debian/Ubuntu)
          apt:
            name:
              - "docker-ce{{ '=' + docker_version if docker_version else '' }}"
              - "docker-ce-cli{{ '=' + docker_version if docker_version else '' }}"
              - containerd.io
              - docker-buildx-plugin
              - docker-compose-plugin
            state: present
            update_cache: yes
          when: ansible_os_family == "Debian"
        
        - name: Install Docker CE (RedHat/CentOS)
          yum:
            name:
              - "docker-ce{{ '-' + docker_version if docker_version else '' }}"
              - "docker-ce-cli{{ '-' + docker_version if docker_version else '' }}"
              - containerd.io
              - docker-buildx-plugin
              - docker-compose-plugin
            state: present
          when: ansible_os_family == "RedHat"
      
      rescue:
        - name: Log Docker installation failure
          debug:
            msg: "Docker installation failed. Check repository configuration."
        
        - name: Fail playbook
          fail:
            msg: "Cannot proceed without Docker installation"
      
      tags:
        - docker
        - install

    # ========================================
    # PHASE 5: Configure Docker Daemon
    # ========================================
    - name: Configure Docker daemon
      block:
        - name: Create Docker configuration directory
          file:
            path: /etc/docker
            state: directory
            mode: '0755'
        
        - name: Deploy daemon.json configuration
          copy:
            content: "{{ docker_daemon_config | to_nice_json }}"
            dest: /etc/docker/daemon.json
            owner: root
            group: root
            mode: '0644'
          notify: restart docker
        
        - name: Enable Docker metrics (if configured)
          lineinfile:
            path: /etc/docker/daemon.json
            insertafter: EOF
            line: '  "metrics-addr": "{{ metrics_address }}",'
            state: present
          when: enable_metrics
          notify: restart docker
      
      tags:
        - docker
        - config

    # ========================================
    # PHASE 6: Manage Docker Group
    # ========================================
    - name: Manage Docker group and users
      block:
        - name: Ensure docker group exists
          group:
            name: docker
            state: present
        
        - name: Add users to docker group
          user:
            name: "{{ item }}"
            groups: docker
            append: yes
          loop: "{{ docker_users }}"
          when: docker_users is defined
      
      tags:
        - docker
        - users

    # ========================================
    # PHASE 7: Start and Enable Docker
    # ========================================
    - name: Start and enable Docker service
      block:
        - name: Start Docker service
          service:
            name: docker
            state: started
            enabled: yes
        
        - name: Wait for Docker socket
          wait_for:
            path: /var/run/docker.sock
            state: present
            timeout: 30
      
      tags:
        - docker
        - service

    # ========================================
    # PHASE 8: Install Docker Compose (standalone)
    # ========================================
    - name: Install Docker Compose standalone
      block:
        - name: Download Docker Compose
          get_url:
            url: "https://github.com/docker/compose/releases/download/v{{ docker_compose_version }}/docker-compose-{{ ansible_system }}-{{ ansible_architecture }}"
            dest: /usr/local/bin/docker-compose
            mode: '0755'
        
        - name: Create docker-compose symlink
          file:
            src: /usr/local/bin/docker-compose
            dest: /usr/bin/docker-compose
            state: link
      
      when: docker_compose_version is defined
      tags:
        - docker
        - docker-compose

    # ========================================
    # PHASE 9: Verification
    # ========================================
    - name: Verify Docker installation
      block:
        - name: Get Docker version
          command: docker --version
          changed_when: false
          register: docker_version_output
        
        - name: Get Docker Compose version
          command: docker-compose --version
          changed_when: false
          register: docker_compose_version_output
          failed_when: false
        
        - name: Run Docker hello-world
          command: docker run --rm hello-world
          changed_when: false
          register: docker_hello_world
        
        - name: Display verification results
          debug:
            msg:
              - "Docker Version: {{ docker_version_output.stdout }}"
              - "Docker Compose Version: {{ docker_compose_version_output.stdout | default('Not installed') }}"
              - "Hello World Test: {{ 'PASSED' if docker_hello_world.rc == 0 else 'FAILED' }}"
      
      always:
        - name: Clean up test container
          command: docker system prune -f
          changed_when: false
      
      tags:
        - docker
        - verify

    # ========================================
    # PHASE 10: Configure Firewall
    # ========================================
    - name: Configure firewall for Docker
      block:
        - name: Allow Docker API (if needed)
          ufw:
            rule: allow
            port: 2375
            proto: tcp
            comment: "Docker API"
          when: 
            - ansible_os_family == "Debian"
            - docker_api_exposed | default(false)
        
        - name: Allow Docker Swarm ports (if needed)
          ufw:
            rule: allow
            port: "{{ item }}"
            proto: tcp
          loop:
            - 2377  # Cluster management
            - 7946  # Node communication
          when: 
            - ansible_os_family == "Debian"
            - docker_swarm_enabled | default(false)
      
      tags:
        - docker
        - firewall

  handlers:
    - name: restart docker
      service:
        name: docker
        state: restarted
```

### Variables File

```yaml
# group_vars/docker_hosts.yml
---
docker_version: ""  # Latest version

docker_users:
  - devops
  - jenkins

docker_daemon_config:
  log-driver: "json-file"
  log-opts:
    max-size: "100m"
    max-file: "3"
  storage-driver: "overlay2"
  live-restore: true
  default-address-pools:
    - base: "172.17.0.0/12"
      size: 24

docker_compose_version: "2.23.0"
enable_metrics: true
metrics_address: "0.0.0.0:9323"
```

### Step-by-Step Implementation

#### Step 1: Prepare Inventory

```ini
# inventories/production/hosts
[docker_hosts]
app01.example.com
app02.example.com
ci-server.example.com
```

#### Step 2: Test Installation (Dry Run)

```bash
ansible-playbook playbooks/docker-install.yml \
  -i inventories/production/hosts \
  --check \
  --diff
```

#### Step 3: Install Docker

```bash
ansible-playbook playbooks/docker-install.yml \
  -i inventories/production/hosts
```

#### Step 4: Verify Installation

```bash
# Check Docker version
ansible docker_hosts -i inventories/production/hosts \
  -m command -a "docker --version"

# Check Docker service status
ansible docker_hosts -i inventories/production/hosts \
  -m command -a "systemctl status docker"

# Test Docker functionality
ansible docker_hosts -i inventories/production/hosts \
  -m command -a "docker run --rm hello-world"

# Check user in docker group
ansible docker_hosts -i inventories/production/hosts \
  -m command -a "groups devops"
```

#### Step 5: Test Docker Compose

```bash
ansible docker_hosts -i inventories/production/hosts \
  -m command -a "docker-compose --version"
```

### Idempotency Features

✅ **Package Installation**: Installs only if not present  
✅ **Configuration**: Updates only if changed  
✅ **User Groups**: Adds users only if not in group  
✅ **Service**: Starts only if not running  

### Common Issues & Solutions

**Issue 1: Permission Denied**
```bash
# Solution: User needs to log out and back in after being added to docker group
# Or run: newgrp docker
```

**Issue 2: Storage Driver Issues**
```bash
# Check current driver
docker info | grep "Storage Driver"

# Change in daemon.json if needed
```

---

## (E) Application Deployment Playbook

### Purpose
Deploy applications from Git repositories or artifact stores, configure environment variables, and manage services with systemd.

### Use Case
- Application deployments
- CI/CD pipelines
- Blue-green deployments
- Rollback procedures

### Full Playbook

```yaml
---
# playbooks/app-deploy.yml
# Purpose: Deploy applications with zero-downtime

- name: Application Deployment
  hosts: appservers
  become: yes
  gather_facts: yes
  serial: "{{ deployment_serial | default('100%') }}"
  max_fail_percentage: 25
  
  vars:
    # Application configuration
    app_name: "myapp"
    app_user: "appuser"
    app_group: "appgroup"
    app_base_dir: "/opt/apps"
    app_dir: "{{ app_base_dir }}/{{ app_name }}"
    app_releases_dir: "{{ app_dir }}/releases"
    app_shared_dir: "{{ app_dir }}/shared"
    app_current_link: "{{ app_dir }}/current"
    
    # Deployment method: git or artifact
    deployment_method: "git"
    
    # Git configuration
    git_repo: "https://github.com/company/myapp.git"
    git_branch: "main"
    git_version: "HEAD"
    
    # Artifact configuration
    artifact_url: "https://artifacts.company.com/myapp/myapp-1.0.0.tar.gz"
    artifact_checksum: "sha256:abc123..."
    
    # Environment variables
    app_env_vars:
      NODE_ENV: "production"
      PORT: "3000"
      DB_HOST: "db.example.com"
      DB_PORT: "5432"
      DB_NAME: "myapp"
      DB_USER: "appuser"
      DB_PASSWORD: "{{ vault_db_password }}"
      REDIS_HOST: "redis.example.com"
      REDIS_PORT: "6379"
      LOG_LEVEL: "info"
    
    # Keep last N releases
    keep_releases: 5
    
    # Health check
    health_check_url: "http://localhost:3000/health"
    health_check_retries: 30
    health_check_delay: 2
    
    # Rollback on failure
    rollback_on_failure: true
  
  tasks:
    # ========================================
    # PHASE 1: Pre-deployment Checks
    # ========================================
    - name: Pre-deployment validation
      block:
        - name: Check if previous deployment exists
          stat:
            path: "{{ app_current_link }}"
          register: previous_deployment
        
        - name: Get current deployment version
          command: "readlink {{ app_current_link }}"
          register: current_version
          when: previous_deployment.stat.exists
          changed_when: false
        
        - name: Display current version
          debug:
            msg: "Current version: {{ current_version.stdout | default('None') }}"
      
      tags:
        - deploy
        - pre-check

    # ========================================
    # PHASE 2: Setup Application Structure
    # ========================================
    - name: Setup application directory structure
      block:
        - name: Create application user
          user:
            name: "{{ app_user }}"
            group: "{{ app_group }}"
            system: yes
            create_home: no
            shell: /bin/bash
        
        - name: Create application directories
          file:
            path: "{{ item }}"
            state: directory
            owner: "{{ app_user }}"
            group: "{{ app_group }}"
            mode: '0755'
          loop:
            - "{{ app_base_dir }}"
            - "{{ app_dir }}"
            - "{{ app_releases_dir }}"
            - "{{ app_shared_dir }}"
            - "{{ app_shared_dir }}/logs"
            - "{{ app_shared_dir }}/config"
            - "{{ app_shared_dir }}/tmp"
      
      tags:
        - deploy
        - setup

    # ========================================
    # PHASE 3: Deploy Application
    # ========================================
    - name: Deploy application code
      block:
        # Git deployment
        - name: Deploy from Git
          block:
            - name: Set release directory name
              set_fact:
                release_dir: "{{ app_releases_dir }}/{{ ansible_date_time.epoch }}"
            
            - name: Clone repository
              git:
                repo: "{{ git_repo }}"
                dest: "{{ release_dir }}"
                version: "{{ git_version }}"
                force: yes
              become_user: "{{ app_user }}"
          when: deployment_method == "git"
        
        # Artifact deployment
        - name: Deploy from artifact
          block:
            - name: Set release directory name
              set_fact:
                release_dir: "{{ app_releases_dir }}/{{ ansible_date_time.epoch }}"
            
            - name: Create release directory
              file:
                path: "{{ release_dir }}"
                state: directory
                owner: "{{ app_user }}"
                group: "{{ app_group }}"
            
            - name: Download artifact
              get_url:
                url: "{{ artifact_url }}"
                dest: "/tmp/{{ app_name }}.tar.gz"
                checksum: "{{ artifact_checksum }}"
            
            - name: Extract artifact
              unarchive:
                src: "/tmp/{{ app_name }}.tar.gz"
                dest: "{{ release_dir }}"
                remote_src: yes
                owner: "{{ app_user }}"
                group: "{{ app_group }}"
            
            - name: Clean up artifact
              file:
                path: "/tmp/{{ app_name }}.tar.gz"
                state: absent
          when: deployment_method == "artifact"
      
      rescue:
        - name: Log deployment failure
          debug:
            msg: "Deployment failed. Starting rollback..."
        
        - name: Remove failed release
          file:
            path: "{{ release_dir }}"
            state: absent
        
        - name: Fail deployment
          fail:
            msg: "Application deployment failed"
      
      tags:
        - deploy
        - code

    # ========================================
    # PHASE 4: Configure Application
    # ========================================
    - name: Configure application
      block:
        - name: Create symlinks to shared directories
          file:
            src: "{{ app_shared_dir }}/{{ item.src }}"
            dest: "{{ release_dir }}/{{ item.dest }}"
            state: link
            owner: "{{ app_user }}"
            group: "{{ app_group }}"
          loop:
            - { src: 'logs', dest: 'logs' }
            - { src: 'tmp', dest: 'tmp' }
        
        - name: Deploy environment file
          template:
            src: templates/app/env.j2
            dest: "{{ release_dir }}/.env"
            owner: "{{ app_user }}"
            group: "{{ app_group }}"
            mode: '0600'
        
        - name: Install dependencies (Node.js example)
          command: npm ci --production
          args:
            chdir: "{{ release_dir }}"
          become_user: "{{ app_user }}"
          when: deployment_method == "git"
          environment:
            NODE_ENV: production
      
      tags:
        - deploy
        - config

    # ========================================
    # PHASE 5: Create Systemd Service
    # ========================================
    - name: Setup systemd service
      block:
        - name: Deploy systemd service file
          template:
            src: templates/app/systemd.service.j2
            dest: "/etc/systemd/system/{{ app_name }}.service"
            owner: root
            group: root
            mode: '0644'
          notify: reload systemd
        
        - name: Reload systemd
          systemd:
            daemon_reload: yes
      
      tags:
        - deploy
        - service

    # ========================================
    # PHASE 6: Switch to New Release
    # ========================================
    - name: Activate new release
      block:
        - name: Update current symlink
          file:
            src: "{{ release_dir }}"
            dest: "{{ app_current_link }}"
            state: link
            owner: "{{ app_user }}"
            group: "{{ app_group }}"
        
        - name: Restart application service
          systemd:
            name: "{{ app_name }}"
            state: restarted
            enabled: yes
      
      tags:
        - deploy
        - activate

    # ========================================
    # PHASE 7: Health Check
    # ========================================
    - name: Verify deployment
      block:
        - name: Wait for application to start
          wait_for:
            port: "{{ app_env_vars.PORT }}"
            delay: "{{ health_check_delay }}"
            timeout: 60
        
        - name: Check application health
          uri:
            url: "{{ health_check_url }}"
            status_code: 200
            timeout: 5
          register: health_check
          retries: "{{ health_check_retries }}"
          delay: "{{ health_check_delay }}"
          until: health_check.status == 200
      
      rescue:
        - name: Health check failed
          debug:
            msg: "Health check failed. Initiating rollback..."
        
        - name: Rollback to previous version
          include_tasks: tasks/rollback.yml
          when: 
            - rollback_on_failure
            - previous_deployment.stat.exists
        
        - name: Fail deployment
          fail:
            msg: "Deployment failed health check"
      
      tags:
        - deploy
        - verify

    # ========================================
    # PHASE 8: Cleanup Old Releases
    # ========================================
    - name: Cleanup old releases
      block:
        - name: Find all releases
          find:
            paths: "{{ app_releases_dir }}"
            file_type: directory
          register: all_releases
        
        - name: Sort releases by modification time
          set_fact:
            sorted_releases: "{{ all_releases.files | sort(attribute='mtime', reverse=True) }}"
        
        - name: Remove old releases
          file:
            path: "{{ item.path }}"
            state: absent
          loop: "{{ sorted_releases[keep_releases:] }}"
          when: sorted_releases | length > keep_releases
      
      tags:
        - deploy
        - cleanup

    # ========================================
    # PHASE 9: Post-deployment Tasks
    # ========================================
    - name: Post-deployment tasks
      block:
        - name: Create deployment marker
          copy:
            content: |
              Deployment completed: {{ ansible_date_time.iso8601 }}
              Version: {{ release_dir | basename }}
              Deployed by: {{ ansible_user_id }}
              Host: {{ ansible_hostname }}
            dest: "{{ release_dir }}/DEPLOYMENT_INFO"
            owner: "{{ app_user }}"
            group: "{{ app_group }}"
        
        - name: Display deployment summary
          debug:
            msg:
              - "Deployment successful!"
              - "Application: {{ app_name }}"
              - "Version: {{ release_dir | basename }}"
              - "Health check: PASSED"
      
      tags:
        - deploy
        - post-deploy

  handlers:
    - name: reload systemd
      systemd:
        daemon_reload: yes
```

### Environment Template

```jinja2
{# templates/app/env.j2 #}
# Application Environment Variables
# Generated by Ansible on {{ ansible_date_time.iso8601 }}

{% for key, value in app_env_vars.items() %}
{{ key }}={{ value }}
{% endfor %}
```

### Systemd Service Template

```jinja2
{# templates/app/systemd.service.j2 #}
[Unit]
Description={{ app_name }} Application
After=network.target

[Service]
Type=simple
User={{ app_user }}
Group={{ app_group }}
WorkingDirectory={{ app_current_link }}
EnvironmentFile={{ app_current_link }}/.env
ExecStart=/usr/bin/node {{ app_current_link }}/server.js
Restart=always
RestartSec=10
StandardOutput=append:{{ app_shared_dir }}/logs/app.log
StandardError=append:{{ app_shared_dir }}/logs/error.log

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths={{ app_shared_dir }}

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
```

### Rollback Tasks

```yaml
# tasks/rollback.yml
---
- name: Rollback to previous version
  block:
    - name: Get previous release
      command: "readlink {{ app_current_link }}"
      register: failed_release
      changed_when: false
    
    - name: Find previous successful release
      find:
        paths: "{{ app_releases_dir }}"
        file_type: directory
        excludes: "{{ failed_release.stdout | basename }}"
      register: available_releases
    
    - name: Sort releases
      set_fact:
        previous_release: "{{ (available_releases.files | sort(attribute='mtime', reverse=True) | first).path }}"
      when: available_releases.files | length > 0
    
    - name: Switch to previous release
      file:
        src: "{{ previous_release }}"
        dest: "{{ app_current_link }}"
        state: link
      when: previous_release is defined
    
    - name: Restart service with previous version
      systemd:
        name: "{{ app_name }}"
        state: restarted
    
    - name: Remove failed release
      file:
        path: "{{ failed_release.stdout }}"
        state: absent
    
    - name: Log rollback
      debug:
        msg: "Rolled back to {{ previous_release | basename }}"
```

### Step-by-Step Implementation

#### Step 1: Prepare Variables

```yaml
# group_vars/appservers.yml
app_name: "myapp"
deployment_method: "git"
git_repo: "https://github.com/company/myapp.git"
git_branch: "main"

app_env_vars:
  NODE_ENV: "production"
  PORT: "3000"
  DB_HOST: "{{ vault_db_host }}"
  DB_PASSWORD: "{{ vault_db_password }}"
```

#### Step 2: Deploy Application

```bash
# Deploy to all servers
ansible-playbook playbooks/app-deploy.yml \
  -i inventories/production/hosts

# Deploy with rolling update (2 servers at a time)
ansible-playbook playbooks/app-deploy.yml \
  -i inventories/production/hosts \
  -e "deployment_serial=2"

# Deploy specific version
ansible-playbook playbooks/app-deploy.yml \
  -i inventories/production/hosts \
  -e "git_version=v1.2.3"
```

#### Step 3: Verify Deployment

```bash
# Check service status
ansible appservers -i inventories/production/hosts \
  -m command -a "systemctl status myapp"

# Check application health
ansible appservers -i inventories/production/hosts \
  -m uri -a "url=http://localhost:3000/health"

# Check current version
ansible appservers -i inventories/production/hosts \
  -m command -a "readlink /opt/apps/myapp/current"
```

#### Step 4: Manual Rollback (if needed)

```bash
ansible-playbook playbooks/app-deploy.yml \
  -i inventories/production/hosts \
  --tags "rollback"
```

### Deployment Strategies

**1. All-at-Once (Default)**
```yaml
serial: "100%"
```

**2. Rolling Update**
```yaml
serial: 2  # 2 servers at a time
max_fail_percentage: 25
```

**3. Canary Deployment**
```yaml
# First deploy to 1 server
serial: 1

# Then deploy to rest
serial: "100%"
```

---

*Continuing with remaining templates (F through J)...*
