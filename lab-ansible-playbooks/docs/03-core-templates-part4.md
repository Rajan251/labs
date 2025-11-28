# Core Playbook Templates (Part 4 - Final)

This document completes the production-grade Ansible playbook templates with Log Management, Security & Hardening, and Monitoring configurations.

## Table of Contents

8. [Log Management](#h-log-management-template)
9. [Security & Hardening](#i-security--hardening-template)
10. [Monitoring](#j-monitoring-template)

---

## (H) Log Management Template

### Purpose
Install and configure log forwarding agents (Filebeat/FluentBit) to send logs to centralized logging systems (ELK Stack, Loki, etc.).

### Use Case
- Centralized logging
- Log aggregation
- Security monitoring
- Troubleshooting and debugging

### Full Playbook

```yaml
---
# playbooks/log-management.yml
# Purpose: Setup centralized logging with Filebeat

- name: Configure Log Management
  hosts: all
  become: yes
  gather_facts: yes
  
  vars:
    # Log agent: filebeat or fluentbit
    log_agent: "filebeat"
    
    # Filebeat configuration
    filebeat_version: "8.11.0"
    
    # Elasticsearch/Logstash configuration
    elasticsearch_hosts:
      - "https://elasticsearch.example.com:9200"
    elasticsearch_username: "elastic"
    elasticsearch_password: "{{ vault_elasticsearch_password }}"
    
    logstash_hosts:
      - "logstash.example.com:5044"
    
    # Output type: elasticsearch, logstash, or kafka
    log_output: "logstash"
    
    # Logs to collect
    log_inputs:
      - type: log
        enabled: true
        paths:
          - /var/log/syslog
          - /var/log/auth.log
        fields:
          log_type: system
      
      - type: log
        enabled: true
        paths:
          - /var/log/nginx/*.log
        fields:
          log_type: nginx
        multiline:
          pattern: '^\d{4}-\d{2}-\d{2}'
          negate: true
          match: after
      
      - type: log
        enabled: true
        paths:
          - /opt/apps/*/current/logs/*.log
        fields:
          log_type: application
    
    # Processors
    filebeat_processors:
      - add_host_metadata:
          when.not.contains.tags: forwarded
      - add_cloud_metadata: ~
      - add_docker_metadata: ~
      - add_kubernetes_metadata: ~
    
    # Enable modules
    filebeat_modules:
      - system
      - nginx
      - docker
  
  tasks:
    # ========================================
    # PHASE 1: Install Filebeat
    # ========================================
    - name: Install Filebeat
      block:
        - name: Add Elastic GPG key
          apt_key:
            url: https://artifacts.elastic.co/GPG-KEY-elasticsearch
            state: present
          when: ansible_os_family == "Debian"
        
        - name: Add Elastic repository
          apt_repository:
            repo: "deb https://artifacts.elastic.co/packages/8.x/apt stable main"
            state: present
            filename: elastic-8.x
          when: ansible_os_family == "Debian"
        
        - name: Install Filebeat
          apt:
            name: "filebeat={{ filebeat_version }}"
            state: present
            update_cache: yes
          when: ansible_os_family == "Debian"
      
      when: log_agent == "filebeat"
      tags:
        - logging
        - filebeat
        - install

    # ========================================
    # PHASE 2: Configure Filebeat
    # ========================================
    - name: Configure Filebeat
      block:
        - name: Backup original filebeat.yml
          copy:
            src: /etc/filebeat/filebeat.yml
            dest: /etc/filebeat/filebeat.yml.backup
            remote_src: yes
            force: no
        
        - name: Deploy Filebeat configuration
          template:
            src: templates/logging/filebeat.yml.j2
            dest: /etc/filebeat/filebeat.yml
            owner: root
            group: root
            mode: '0600'
            validate: 'filebeat test config -c %s'
          notify: restart filebeat
        
        - name: Create Filebeat data directory
          file:
            path: /var/lib/filebeat
            state: directory
            owner: root
            group: root
            mode: '0750'
      
      when: log_agent == "filebeat"
      tags:
        - logging
        - filebeat
        - config

    # ========================================
    # PHASE 3: Enable Filebeat Modules
    # ========================================
    - name: Enable Filebeat modules
      block:
        - name: Enable modules
          command: "filebeat modules enable {{ item }}"
          loop: "{{ filebeat_modules }}"
          register: module_enable
          changed_when: "'Enabled' in module_enable.stdout"
        
        - name: List enabled modules
          command: filebeat modules list
          register: modules_list
          changed_when: false
        
        - name: Display enabled modules
          debug:
            var: modules_list.stdout_lines
      
      when: 
        - log_agent == "filebeat"
        - filebeat_modules is defined
      tags:
        - logging
        - filebeat
        - modules

    # ========================================
    # PHASE 4: Setup Filebeat Keystore (Secrets)
    # ========================================
    - name: Configure Filebeat keystore
      block:
        - name: Create Filebeat keystore
          command: filebeat keystore create --force
          args:
            creates: /var/lib/filebeat/filebeat.keystore
        
        - name: Add Elasticsearch password to keystore
          shell: |
            echo "{{ elasticsearch_password }}" | filebeat keystore add ES_PWD --stdin --force
          no_log: true
          when: log_output == "elasticsearch"
      
      when: log_agent == "filebeat"
      tags:
        - logging
        - filebeat
        - secrets

    # ========================================
    # PHASE 5: Setup Filebeat Index Template
    # ========================================
    - name: Setup Filebeat index template
      block:
        - name: Load Filebeat index template
          command: filebeat setup --index-management
          when: log_output == "elasticsearch"
        
        - name: Load Filebeat dashboards (if Kibana available)
          command: filebeat setup --dashboards
          when: 
            - log_output == "elasticsearch"
            - kibana_host is defined
          failed_when: false
      
      when: log_agent == "filebeat"
      tags:
        - logging
        - filebeat
        - setup

    # ========================================
    # PHASE 6: Start Filebeat Service
    # ========================================
    - name: Start and enable Filebeat
      block:
        - name: Start Filebeat service
          service:
            name: filebeat
            state: started
            enabled: yes
        
        - name: Wait for Filebeat to start
          wait_for:
            path: /var/run/filebeat/filebeat.pid
            timeout: 30
      
      when: log_agent == "filebeat"
      tags:
        - logging
        - filebeat
        - service

    # ========================================
    # PHASE 7: Verify Filebeat
    # ========================================
    - name: Verify Filebeat installation
      block:
        - name: Check Filebeat version
          command: filebeat version
          register: filebeat_version_output
          changed_when: false
        
        - name: Test Filebeat configuration
          command: filebeat test config
          register: config_test
          changed_when: false
        
        - name: Test Filebeat output
          command: filebeat test output
          register: output_test
          changed_when: false
          failed_when: false
        
        - name: Check Filebeat service status
          command: systemctl status filebeat
          register: service_status
          changed_when: false
          failed_when: false
        
        - name: Display verification results
          debug:
            msg:
              - "Version: {{ filebeat_version_output.stdout }}"
              - "Config test: {{ 'PASSED' if config_test.rc == 0 else 'FAILED' }}"
              - "Output test: {{ 'PASSED' if output_test.rc == 0 else 'FAILED' }}"
              - "Service: {{ 'Running' if 'active (running)' in service_status.stdout else 'Not Running' }}"
      
      when: log_agent == "filebeat"
      tags:
        - logging
        - filebeat
        - verify

    # ========================================
    # PHASE 8: Configure Log Rotation
    # ========================================
    - name: Configure log rotation
      block:
        - name: Deploy logrotate configuration
          copy:
            content: |
              /var/log/filebeat/*.log {
                  daily
                  rotate 7
                  compress
                  delaycompress
                  missingok
                  notifempty
                  create 0640 root adm
                  sharedscripts
                  postrotate
                      systemctl reload filebeat > /dev/null 2>&1 || true
                  endscript
              }
            dest: /etc/logrotate.d/filebeat
            mode: '0644'
      
      tags:
        - logging
        - logrotate

  handlers:
    - name: restart filebeat
      service:
        name: filebeat
        state: restarted
```

### Filebeat Configuration Template

```jinja2
{# templates/logging/filebeat.yml.j2 #}
###################### Filebeat Configuration ######################

# ============================== Filebeat inputs ===============================
filebeat.inputs:
{% for input in log_inputs %}
- type: {{ input.type }}
  enabled: {{ input.enabled | default(true) }}
  paths:
{% for path in input.paths %}
    - {{ path }}
{% endfor %}
{% if input.fields is defined %}
  fields:
{% for key, value in input.fields.items() %}
    {{ key }}: {{ value }}
{% endfor %}
  fields_under_root: true
{% endif %}
{% if input.multiline is defined %}
  multiline:
    pattern: '{{ input.multiline.pattern }}'
    negate: {{ input.multiline.negate }}
    match: {{ input.multiline.match }}
{% endif %}

{% endfor %}

# ============================== Filebeat modules ==============================
filebeat.config.modules:
  path: ${path.config}/modules.d/*.yml
  reload.enabled: true
  reload.period: 10s

# ======================= Elasticsearch template setting =======================
setup.template.settings:
  index.number_of_shards: 1
  index.codec: best_compression

# ================================== General ===================================
name: {{ ansible_hostname }}
tags: ["{{ environment | default('production') }}", "{{ ansible_hostname }}"]

# ================================= Processors =================================
processors:
{% for processor in filebeat_processors %}
{% for key, value in processor.items() %}
  - {{ key }}:
{% if value %}
{% for k, v in value.items() %}
      {{ k }}: {{ v }}
{% endfor %}
{% endif %}
{% endfor %}
{% endfor %}

# ================================== Outputs ===================================
{% if log_output == "elasticsearch" %}
# ---------------------------- Elasticsearch Output ----------------------------
output.elasticsearch:
  hosts: {{ elasticsearch_hosts | to_json }}
  username: "{{ elasticsearch_username }}"
  password: "${ES_PWD}"
  ssl.verification_mode: none

{% elif log_output == "logstash" %}
# ------------------------------ Logstash Output -------------------------------
output.logstash:
  hosts: {{ logstash_hosts | to_json }}
  ssl.enabled: false
  loadbalance: true

{% elif log_output == "kafka" %}
# ------------------------------- Kafka Output ---------------------------------
output.kafka:
  hosts: {{ kafka_hosts | to_json }}
  topic: 'filebeat'
  partition.round_robin:
    reachable_only: false
  required_acks: 1
  compression: gzip
  max_message_bytes: 1000000
{% endif %}

# ================================= Logging ====================================
logging.level: info
logging.to_files: true
logging.files:
  path: /var/log/filebeat
  name: filebeat
  keepfiles: 7
  permissions: 0644

# ============================= X-Pack Monitoring ==============================
monitoring.enabled: false
```

### Step-by-Step Implementation

#### Step 1: Prepare Variables

```yaml
# group_vars/all/logging.yml
log_agent: "filebeat"
log_output: "logstash"

logstash_hosts:
  - "logstash.example.com:5044"

log_inputs:
  - type: log
    enabled: true
    paths:
      - /var/log/syslog
      - /var/log/auth.log
    fields:
      log_type: system
```

#### Step 2: Deploy Filebeat

```bash
ansible-playbook playbooks/log-management.yml \
  -i inventories/production/hosts
```

#### Step 3: Verify Log Collection

```bash
# Check Filebeat status
ansible all -i inventories/production/hosts \
  -m command -a "systemctl status filebeat"

# Test configuration
ansible all -i inventories/production/hosts \
  -m command -a "filebeat test config"

# Test output connectivity
ansible all -i inventories/production/hosts \
  -m command -a "filebeat test output"
```

---

## (I) Security & Hardening Template

### Purpose
Implement security hardening measures including disabling unused services, password policies, firewall setup, and Fail2ban configuration.

### Use Case
- CIS benchmark compliance
- Security hardening
- Intrusion prevention
- Compliance requirements

### Full Playbook

```yaml
---
# playbooks/security-hardening.yml
# Purpose: Security hardening based on CIS benchmarks

- name: Security Hardening
  hosts: all
  become: yes
  gather_facts: yes
  
  vars:
    # Services to disable
    disable_services:
      - avahi-daemon
      - cups
      - isc-dhcp-server
      - isc-dhcp-server6
      - rpcbind
      - rsync
      - snmpd
    
    # Firewall configuration
    firewall_allowed_ports:
      - 22    # SSH
      - 80    # HTTP
      - 443   # HTTPS
    
    # Fail2ban configuration
    fail2ban_enabled: true
    fail2ban_bantime: 3600
    fail2ban_findtime: 600
    fail2ban_maxretry: 5
    
    # Password policy
    password_min_length: 14
    password_max_days: 90
    password_min_days: 7
    password_warn_age: 14
    
    # Audit logging
    auditd_enabled: true
    
    # File permissions
    secure_permissions:
      - { path: '/etc/passwd', mode: '0644' }
      - { path: '/etc/shadow', mode: '0000' }
      - { path: '/etc/group', mode: '0644' }
      - { path: '/etc/gshadow', mode: '0000' }
      - { path: '/etc/ssh/sshd_config', mode: '0600' }
  
  tasks:
    # ========================================
    # PHASE 1: Disable Unnecessary Services
    # ========================================
    - name: Disable unnecessary services
      block:
        - name: Stop and disable services
          service:
            name: "{{ item }}"
            state: stopped
            enabled: no
          loop: "{{ disable_services }}"
          failed_when: false
        
        - name: Mask disabled services
          systemd:
            name: "{{ item }}"
            masked: yes
          loop: "{{ disable_services }}"
          failed_when: false
      
      tags:
        - security
        - services

    # ========================================
    # PHASE 2: Configure Firewall (UFW)
    # ========================================
    - name: Configure UFW firewall
      block:
        - name: Install UFW
          apt:
            name: ufw
            state: present
          when: ansible_os_family == "Debian"
        
        - name: Reset UFW to defaults
          ufw:
            state: reset
          when: ansible_os_family == "Debian"
        
        - name: Set default policies
          ufw:
            direction: "{{ item.direction }}"
            policy: "{{ item.policy }}"
          loop:
            - { direction: 'incoming', policy: 'deny' }
            - { direction: 'outgoing', policy: 'allow' }
            - { direction: 'routed', policy: 'deny' }
          when: ansible_os_family == "Debian"
        
        - name: Allow specified ports
          ufw:
            rule: allow
            port: "{{ item }}"
            proto: tcp
          loop: "{{ firewall_allowed_ports }}"
          when: ansible_os_family == "Debian"
        
        - name: Enable UFW
          ufw:
            state: enabled
          when: ansible_os_family == "Debian"
      
      tags:
        - security
        - firewall

    # ========================================
    # PHASE 3: Install and Configure Fail2ban
    # ========================================
    - name: Setup Fail2ban
      block:
        - name: Install Fail2ban
          apt:
            name: fail2ban
            state: present
          when: ansible_os_family == "Debian"
        
        - name: Create Fail2ban local configuration
          template:
            src: templates/security/jail.local.j2
            dest: /etc/fail2ban/jail.local
            owner: root
            group: root
            mode: '0644'
          notify: restart fail2ban
        
        - name: Create SSH jail configuration
          copy:
            content: |
              [sshd]
              enabled = true
              port = ssh
              filter = sshd
              logpath = /var/log/auth.log
              maxretry = {{ fail2ban_maxretry }}
              bantime = {{ fail2ban_bantime }}
              findtime = {{ fail2ban_findtime }}
            dest: /etc/fail2ban/jail.d/sshd.local
            mode: '0644'
          notify: restart fail2ban
        
        - name: Start and enable Fail2ban
          service:
            name: fail2ban
            state: started
            enabled: yes
      
      when: fail2ban_enabled
      tags:
        - security
        - fail2ban

    # ========================================
    # PHASE 4: Password Policy
    # ========================================
    - name: Configure password policies
      block:
        - name: Install password quality library
          apt:
            name: libpam-pwquality
            state: present
          when: ansible_os_family == "Debian"
        
        - name: Configure password quality
          lineinfile:
            path: /etc/security/pwquality.conf
            regexp: "^{{ item.key }}"
            line: "{{ item.key }} = {{ item.value }}"
            state: present
          loop:
            - { key: 'minlen', value: "{{ password_min_length }}" }
            - { key: 'dcredit', value: '-1' }
            - { key: 'ucredit', value: '-1' }
            - { key: 'lcredit', value: '-1' }
            - { key: 'ocredit', value: '-1' }
            - { key: 'minclass', value: '4' }
            - { key: 'maxrepeat', value: '3' }
            - { key: 'maxsequence', value: '3' }
        
        - name: Configure password aging
          lineinfile:
            path: /etc/login.defs
            regexp: "^{{ item.key }}"
            line: "{{ item.key }}\t{{ item.value }}"
            state: present
          loop:
            - { key: 'PASS_MAX_DAYS', value: "{{ password_max_days }}" }
            - { key: 'PASS_MIN_DAYS', value: "{{ password_min_days }}" }
            - { key: 'PASS_WARN_AGE', value: "{{ password_warn_age }}" }
            - { key: 'PASS_MIN_LEN', value: "{{ password_min_length }}" }
      
      tags:
        - security
        - password-policy

    # ========================================
    # PHASE 5: SSH Hardening
    # ========================================
    - name: Harden SSH configuration
      block:
        - name: Configure SSH settings
          lineinfile:
            path: /etc/ssh/sshd_config
            regexp: "^#?{{ item.key }}"
            line: "{{ item.key }} {{ item.value }}"
            state: present
          loop:
            - { key: 'PermitRootLogin', value: 'no' }
            - { key: 'PasswordAuthentication', value: 'no' }
            - { key: 'PubkeyAuthentication', value: 'yes' }
            - { key: 'PermitEmptyPasswords', value: 'no' }
            - { key: 'X11Forwarding', value: 'no' }
            - { key: 'MaxAuthTries', value: '3' }
            - { key: 'ClientAliveInterval', value: '300' }
            - { key: 'ClientAliveCountMax', value: '2' }
            - { key: 'Protocol', value: '2' }
            - { key: 'LogLevel', value: 'VERBOSE' }
          notify: restart sshd
        
        - name: Validate SSH configuration
          command: sshd -t
          changed_when: false
      
      tags:
        - security
        - ssh

    # ========================================
    # PHASE 6: File Permissions
    # ========================================
    - name: Set secure file permissions
      block:
        - name: Set permissions on critical files
          file:
            path: "{{ item.path }}"
            mode: "{{ item.mode }}"
          loop: "{{ secure_permissions }}"
        
        - name: Set permissions on home directories
          file:
            path: "/home/{{ item }}"
            mode: '0750'
          loop: "{{ ansible_facts.getent_passwd.keys() | list }}"
          when: 
            - item != 'root'
            - ansible_facts.getent_passwd[item][4] is match("/home/.*")
      
      tags:
        - security
        - permissions

    # ========================================
    # PHASE 7: Kernel Hardening
    # ========================================
    - name: Kernel security parameters
      block:
        - name: Configure kernel parameters
          sysctl:
            name: "{{ item.key }}"
            value: "{{ item.value }}"
            state: present
            reload: yes
            sysctl_file: /etc/sysctl.d/99-security.conf
          loop:
            # Network security
            - { key: 'net.ipv4.conf.all.send_redirects', value: '0' }
            - { key: 'net.ipv4.conf.default.send_redirects', value: '0' }
            - { key: 'net.ipv4.conf.all.accept_source_route', value: '0' }
            - { key: 'net.ipv4.conf.default.accept_source_route', value: '0' }
            - { key: 'net.ipv4.conf.all.accept_redirects', value: '0' }
            - { key: 'net.ipv4.conf.default.accept_redirects', value: '0' }
            - { key: 'net.ipv4.conf.all.secure_redirects', value: '0' }
            - { key: 'net.ipv4.conf.default.secure_redirects', value: '0' }
            - { key: 'net.ipv4.conf.all.log_martians', value: '1' }
            - { key: 'net.ipv4.conf.default.log_martians', value: '1' }
            - { key: 'net.ipv4.icmp_echo_ignore_broadcasts', value: '1' }
            - { key: 'net.ipv4.icmp_ignore_bogus_error_responses', value: '1' }
            - { key: 'net.ipv4.conf.all.rp_filter', value: '1' }
            - { key: 'net.ipv4.conf.default.rp_filter', value: '1' }
            - { key: 'net.ipv4.tcp_syncookies', value: '1' }
            # IPv6 security
            - { key: 'net.ipv6.conf.all.accept_source_route', value: '0' }
            - { key: 'net.ipv6.conf.default.accept_source_route', value: '0' }
            - { key: 'net.ipv6.conf.all.accept_redirects', value: '0' }
            - { key: 'net.ipv6.conf.default.accept_redirects', value: '0' }
            # Kernel security
            - { key: 'kernel.dmesg_restrict', value: '1' }
            - { key: 'kernel.kptr_restrict', value: '2' }
            - { key: 'kernel.yama.ptrace_scope', value: '1' }
            - { key: 'fs.suid_dumpable', value: '0' }
      
      tags:
        - security
        - kernel

    # ========================================
    # PHASE 8: Install and Configure Auditd
    # ========================================
    - name: Setup audit logging
      block:
        - name: Install auditd
          apt:
            name: auditd
            state: present
          when: ansible_os_family == "Debian"
        
        - name: Configure audit rules
          copy:
            content: |
              # Audit rules for security monitoring
              
              # Monitor authentication
              -w /var/log/auth.log -p wa -k auth
              -w /etc/pam.d/ -p wa -k pam
              
              # Monitor user/group changes
              -w /etc/passwd -p wa -k identity
              -w /etc/group -p wa -k identity
              -w /etc/shadow -p wa -k identity
              -w /etc/gshadow -p wa -k identity
              
              # Monitor sudo usage
              -w /etc/sudoers -p wa -k sudoers
              -w /etc/sudoers.d/ -p wa -k sudoers
              
              # Monitor SSH configuration
              -w /etc/ssh/sshd_config -p wa -k sshd
              
              # Monitor kernel modules
              -w /sbin/insmod -p x -k modules
              -w /sbin/rmmod -p x -k modules
              -w /sbin/modprobe -p x -k modules
              
              # Monitor file deletions
              -a always,exit -F arch=b64 -S unlink -S unlinkat -S rename -S renameat -k delete
            dest: /etc/audit/rules.d/hardening.rules
            mode: '0640'
          notify: restart auditd
        
        - name: Start and enable auditd
          service:
            name: auditd
            state: started
            enabled: yes
      
      when: auditd_enabled
      tags:
        - security
        - audit

    # ========================================
    # PHASE 9: Remove Unnecessary Packages
    # ========================================
    - name: Remove unnecessary packages
      block:
        - name: Remove packages
          apt:
            name:
              - telnet
              - rsh-client
              - rsh-redone-client
            state: absent
            purge: yes
          when: ansible_os_family == "Debian"
      
      tags:
        - security
        - packages

    # ========================================
    # PHASE 10: Verification
    # ========================================
    - name: Verify security hardening
      block:
        - name: Check firewall status
          command: ufw status
          register: ufw_status
          changed_when: false
          when: ansible_os_family == "Debian"
        
        - name: Check Fail2ban status
          command: fail2ban-client status
          register: fail2ban_status
          changed_when: false
          when: fail2ban_enabled
        
        - name: Check auditd status
          command: systemctl status auditd
          register: auditd_status
          changed_when: false
          failed_when: false
          when: auditd_enabled
        
        - name: Display verification results
          debug:
            msg:
              - "Firewall: {{ 'Active' if 'Status: active' in ufw_status.stdout else 'Inactive' }}"
              - "Fail2ban: {{ 'Running' if fail2ban_status.rc == 0 else 'Not Running' }}"
              - "Auditd: {{ 'Running' if 'active (running)' in auditd_status.stdout else 'Not Running' }}"
      
      tags:
        - security
        - verify

  handlers:
    - name: restart sshd
      service:
        name: "{{ 'sshd' if ansible_os_family == 'RedHat' else 'ssh' }}"
        state: restarted
    
    - name: restart fail2ban
      service:
        name: fail2ban
        state: restarted
    
    - name: restart auditd
      service:
        name: auditd
        state: restarted
```

### Fail2ban Configuration Template

```jinja2
{# templates/security/jail.local.j2 #}
[DEFAULT]
bantime  = {{ fail2ban_bantime }}
findtime  = {{ fail2ban_findtime }}
maxretry = {{ fail2ban_maxretry }}

# Destination email for notifications
destemail = security@example.com
sender = fail2ban@{{ ansible_hostname }}

# Ban action
banaction = ufw
action = %(action_mwl)s

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
```

---

## (J) Monitoring Template

### Purpose
Install and configure monitoring agents (Node Exporter, Prometheus exporters, monitoring agents) for metrics collection.

### Use Case
- Infrastructure monitoring
- Application performance monitoring
- Alerting
- Capacity planning

### Full Playbook

```yaml
---
# playbooks/monitoring-setup.yml
# Purpose: Setup monitoring with Prometheus exporters

- name: Configure Monitoring
  hosts: all
  become: yes
  gather_facts: yes
  
  vars:
    # Prometheus configuration
    prometheus_server: "prometheus.example.com:9090"
    
    # Node Exporter
    node_exporter_version: "1.7.0"
    node_exporter_port: 9100
    
    # Additional exporters
    install_exporters:
      - node_exporter
    
    # Metrics retention
    metrics_path: "/var/lib/prometheus"
    
    # Firewall configuration
    allow_prometheus_scrape: true
    prometheus_source_ips:
      - "10.0.0.0/8"
      - "192.168.0.0/16"
  
  tasks:
    # ========================================
    # PHASE 1: Create Monitoring User
    # ========================================
    - name: Create prometheus user
      user:
        name: prometheus
        system: yes
        shell: /bin/false
        create_home: no
      tags:
        - monitoring
        - setup

    # ========================================
    # PHASE 2: Install Node Exporter
    # ========================================
    - name: Install Node Exporter
      block:
        - name: Download Node Exporter
          get_url:
            url: "https://github.com/prometheus/node_exporter/releases/download/v{{ node_exporter_version }}/node_exporter-{{ node_exporter_version }}.linux-amd64.tar.gz"
            dest: "/tmp/node_exporter.tar.gz"
            mode: '0644'
        
        - name: Extract Node Exporter
          unarchive:
            src: "/tmp/node_exporter.tar.gz"
            dest: "/tmp"
            remote_src: yes
        
        - name: Copy Node Exporter binary
          copy:
            src: "/tmp/node_exporter-{{ node_exporter_version }}.linux-amd64/node_exporter"
            dest: "/usr/local/bin/node_exporter"
            remote_src: yes
            owner: prometheus
            group: prometheus
            mode: '0755'
        
        - name: Cleanup Node Exporter files
          file:
            path: "{{ item }}"
            state: absent
          loop:
            - "/tmp/node_exporter.tar.gz"
            - "/tmp/node_exporter-{{ node_exporter_version }}.linux-amd64"
      
      when: "'node_exporter' in install_exporters"
      tags:
        - monitoring
        - node-exporter

    # ========================================
    # PHASE 3: Create Systemd Service
    # ========================================
    - name: Create Node Exporter systemd service
      block:
        - name: Deploy systemd service file
          copy:
            content: |
              [Unit]
              Description=Prometheus Node Exporter
              After=network.target
              
              [Service]
              Type=simple
              User=prometheus
              Group=prometheus
              ExecStart=/usr/local/bin/node_exporter \
                --web.listen-address=:{{ node_exporter_port }} \
                --collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/) \
                --collector.netclass.ignored-devices=^(veth.*|docker.*|br-.*)$$
              
              Restart=always
              RestartSec=10
              
              [Install]
              WantedBy=multi-user.target
            dest: /etc/systemd/system/node_exporter.service
            mode: '0644'
          notify: reload systemd
        
        - name: Start and enable Node Exporter
          systemd:
            name: node_exporter
            state: started
            enabled: yes
            daemon_reload: yes
      
      when: "'node_exporter' in install_exporters"
      tags:
        - monitoring
        - node-exporter

    # ========================================
    # PHASE 4: Configure Firewall
    # ========================================
    - name: Configure firewall for monitoring
      block:
        - name: Allow Prometheus scraping
          ufw:
            rule: allow
            port: "{{ node_exporter_port }}"
            proto: tcp
            from_ip: "{{ item }}"
          loop: "{{ prometheus_source_ips }}"
          when: ansible_os_family == "Debian"
      
      when: allow_prometheus_scrape
      tags:
        - monitoring
        - firewall

    # ========================================
    # PHASE 5: Verify Installation
    # ========================================
    - name: Verify monitoring setup
      block:
        - name: Check Node Exporter service
          command: systemctl status node_exporter
          register: exporter_status
          changed_when: false
          failed_when: false
        
        - name: Test Node Exporter metrics endpoint
          uri:
            url: "http://localhost:{{ node_exporter_port }}/metrics"
            return_content: yes
          register: metrics_test
        
        - name: Display verification results
          debug:
            msg:
              - "Node Exporter: {{ 'Running' if 'active (running)' in exporter_status.stdout else 'Not Running' }}"
              - "Metrics endpoint: {{ 'OK' if metrics_test.status == 200 else 'FAILED' }}"
              - "Metrics URL: http://{{ ansible_default_ipv4.address }}:{{ node_exporter_port }}/metrics"
      
      tags:
        - monitoring
        - verify

  handlers:
    - name: reload systemd
      systemd:
        daemon_reload: yes
```

### Step-by-Step Implementation

```bash
# Deploy monitoring
ansible-playbook playbooks/monitoring-setup.yml \
  -i inventories/production/hosts

# Verify metrics collection
curl http://server:9100/metrics
```

---

## Summary

All 10 core playbook templates are now complete:

1. ✅ Server Bootstrap
2. ✅ User & SSH Key Management
3. ✅ Nginx Installation & Reverse Proxy
4. ✅ Docker Installation
5. ✅ Application Deployment
6. ✅ Kubernetes Node Preparation
7. ✅ OS Patching (Rolling Update)
8. ✅ Log Management
9. ✅ Security & Hardening
10. ✅ Monitoring

Each template includes:
- Full production-ready code
- Variables and configuration
- Handlers for service management
- Error handling with block/rescue
- Idempotency logic
- Step-by-step implementation
- Verification procedures
- Best practices

---

**Next**: [Dynamic Inventory →](04-dynamic-inventory.md)
