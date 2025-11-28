# Core Playbook Templates (Part 3)

This document continues with the remaining production-grade Ansible playbook templates: Kubernetes Node Preparation, OS Patching, Log Management, Security Hardening, and Monitoring.

## Table of Contents

6. [Kubernetes Node Preparation](#f-kubernetes-node-preparation-template)
7. [OS Patching (Rolling Update)](#g-os-patching-safe-rolling-update)
8. [Log Management](#h-log-management-template)
9. [Security & Hardening](#i-security--hardening-template)
10. [Monitoring](#j-monitoring-template)

---

## (F) Kubernetes Node Preparation Template

### Purpose
Prepare nodes for Kubernetes cluster by installing container runtime (containerd/CRI-O), kubeadm, kubelet, kubectl, configuring sysctl, and disabling swap.

### Use Case
- Kubernetes cluster setup
- Node addition to existing cluster
- Container orchestration preparation
- Production K8s deployment

### Full Playbook

```yaml
---
# playbooks/k8s-node-prep.yml
# Purpose: Prepare nodes for Kubernetes cluster

- name: Prepare Kubernetes Nodes
  hosts: k8s_nodes
  become: yes
  gather_facts: yes
  
  vars:
    # Kubernetes version
    k8s_version: "1.28"
    k8s_package_version: "1.28.0-00"
    
    # Container runtime: containerd or crio
    container_runtime: "containerd"
    containerd_version: "1.7.8"
    
    # Network configuration
    pod_network_cidr: "10.244.0.0/16"
    service_cidr: "10.96.0.0/12"
    
    # Kernel modules
    k8s_kernel_modules:
      - overlay
      - br_netfilter
    
    # Sysctl parameters
    k8s_sysctl_params:
      net.bridge.bridge-nf-call-iptables: 1
      net.bridge.bridge-nf-call-ip6tables: 1
      net.ipv4.ip_forward: 1
      net.ipv4.conf.all.forwarding: 1
    
    # Firewall ports
    k8s_master_ports:
      - 6443   # Kubernetes API server
      - 2379   # etcd client
      - 2380   # etcd peer
      - 10250  # Kubelet API
      - 10251  # kube-scheduler
      - 10252  # kube-controller-manager
    
    k8s_worker_ports:
      - 10250  # Kubelet API
      - 30000-32767  # NodePort Services
  
  tasks:
    # ========================================
    # PHASE 1: Pre-flight Checks
    # ========================================
    - name: Pre-flight checks
      block:
        - name: Check if swap is enabled
          command: swapon --show
          register: swap_status
          changed_when: false
          failed_when: false
        
        - name: Display swap status
          debug:
            msg: "Swap is {{ 'ENABLED - will be disabled' if swap_status.stdout else 'already disabled' }}"
        
        - name: Check system requirements
          assert:
            that:
              - ansible_memtotal_mb >= 2048
              - ansible_processor_vcpus >= 2
            fail_msg: "System does not meet minimum requirements (2GB RAM, 2 CPUs)"
            success_msg: "System meets minimum requirements"
      
      tags:
        - k8s
        - preflight

    # ========================================
    # PHASE 2: Disable Swap
    # ========================================
    - name: Disable swap
      block:
        - name: Disable swap immediately
          command: swapoff -a
          when: swap_status.stdout
        
        - name: Remove swap from /etc/fstab
          lineinfile:
            path: /etc/fstab
            regexp: '^\s*[^#].*\s+swap\s+'
            state: absent
        
        - name: Verify swap is disabled
          command: swapon --show
          register: swap_verify
          changed_when: false
          failed_when: swap_verify.stdout
      
      tags:
        - k8s
        - swap

    # ========================================
    # PHASE 3: Load Kernel Modules
    # ========================================
    - name: Configure kernel modules
      block:
        - name: Load kernel modules
          modprobe:
            name: "{{ item }}"
            state: present
          loop: "{{ k8s_kernel_modules }}"
        
        - name: Ensure modules load on boot
          copy:
            content: |
              # Kubernetes required modules
              {% for module in k8s_kernel_modules %}
              {{ module }}
              {% endfor %}
            dest: /etc/modules-load.d/k8s.conf
            mode: '0644'
      
      tags:
        - k8s
        - kernel

    # ========================================
    # PHASE 4: Configure Sysctl
    # ========================================
    - name: Configure sysctl parameters
      block:
        - name: Set sysctl parameters
          sysctl:
            name: "{{ item.key }}"
            value: "{{ item.value }}"
            state: present
            reload: yes
            sysctl_file: /etc/sysctl.d/k8s.conf
          loop: "{{ k8s_sysctl_params | dict2items }}"
        
        - name: Verify sysctl settings
          command: sysctl {{ item.key }}
          loop: "{{ k8s_sysctl_params | dict2items }}"
          changed_when: false
          register: sysctl_verify
        
        - name: Display sysctl verification
          debug:
            msg: "{{ sysctl_verify.results | map(attribute='stdout') | list }}"
      
      tags:
        - k8s
        - sysctl

    # ========================================
    # PHASE 5: Install Container Runtime
    # ========================================
    - name: Install containerd
      block:
        - name: Install containerd prerequisites
          apt:
            name:
              - apt-transport-https
              - ca-certificates
              - curl
              - gnupg
              - lsb-release
            state: present
            update_cache: yes
          when: ansible_os_family == "Debian"
        
        - name: Add Docker GPG key (for containerd)
          apt_key:
            url: https://download.docker.com/linux/{{ ansible_distribution | lower }}/gpg
            state: present
          when: ansible_os_family == "Debian"
        
        - name: Add Docker repository (for containerd)
          apt_repository:
            repo: "deb [arch=amd64] https://download.docker.com/linux/{{ ansible_distribution | lower }} {{ ansible_distribution_release }} stable"
            state: present
          when: ansible_os_family == "Debian"
        
        - name: Install containerd
          apt:
            name: containerd.io
            state: present
            update_cache: yes
          when: ansible_os_family == "Debian"
        
        - name: Create containerd config directory
          file:
            path: /etc/containerd
            state: directory
            mode: '0755'
        
        - name: Generate default containerd config
          shell: containerd config default > /etc/containerd/config.toml
          args:
            creates: /etc/containerd/config.toml
        
        - name: Configure containerd to use systemd cgroup driver
          lineinfile:
            path: /etc/containerd/config.toml
            regexp: '^\s*SystemdCgroup\s*='
            line: '            SystemdCgroup = true'
            insertafter: '^\s*\[plugins\."io\.containerd\.grpc\.v1\.cri"\.containerd\.runtimes\.runc\.options\]'
          notify: restart containerd
        
        - name: Start and enable containerd
          service:
            name: containerd
            state: started
            enabled: yes
      
      when: container_runtime == "containerd"
      tags:
        - k8s
        - containerd

    # ========================================
    # PHASE 6: Install Kubernetes Packages
    # ========================================
    - name: Install Kubernetes packages
      block:
        - name: Add Kubernetes GPG key
          apt_key:
            url: https://pkgs.k8s.io/core:/stable:/v{{ k8s_version }}/deb/Release.key
            state: present
          when: ansible_os_family == "Debian"
        
        - name: Add Kubernetes repository
          apt_repository:
            repo: "deb https://pkgs.k8s.io/core:/stable:/v{{ k8s_version }}/deb/ /"
            state: present
            filename: kubernetes
          when: ansible_os_family == "Debian"
        
        - name: Update apt cache
          apt:
            update_cache: yes
          when: ansible_os_family == "Debian"
        
        - name: Install Kubernetes packages
          apt:
            name:
              - "kubelet={{ k8s_package_version }}"
              - "kubeadm={{ k8s_package_version }}"
              - "kubectl={{ k8s_package_version }}"
            state: present
            allow_downgrade: yes
          when: ansible_os_family == "Debian"
        
        - name: Hold Kubernetes packages at current version
          dpkg_selections:
            name: "{{ item }}"
            selection: hold
          loop:
            - kubelet
            - kubeadm
            - kubectl
          when: ansible_os_family == "Debian"
        
        - name: Enable kubelet service
          service:
            name: kubelet
            enabled: yes
      
      tags:
        - k8s
        - packages

    # ========================================
    # PHASE 7: Configure Firewall
    # ========================================
    - name: Configure firewall for Kubernetes
      block:
        - name: Allow Kubernetes master ports
          ufw:
            rule: allow
            port: "{{ item }}"
            proto: tcp
          loop: "{{ k8s_master_ports }}"
          when: 
            - ansible_os_family == "Debian"
            - "'k8s_masters' in group_names"
        
        - name: Allow Kubernetes worker ports
          ufw:
            rule: allow
            port: "{{ item }}"
            proto: tcp
          loop: "{{ k8s_worker_ports }}"
          when: 
            - ansible_os_family == "Debian"
            - "'k8s_workers' in group_names"
      
      tags:
        - k8s
        - firewall

    # ========================================
    # PHASE 8: Verification
    # ========================================
    - name: Verify Kubernetes node preparation
      block:
        - name: Check kubelet version
          command: kubelet --version
          changed_when: false
          register: kubelet_version
        
        - name: Check kubeadm version
          command: kubeadm version -o short
          changed_when: false
          register: kubeadm_version
        
        - name: Check kubectl version
          command: kubectl version --client -o yaml
          changed_when: false
          register: kubectl_version
        
        - name: Check containerd status
          command: systemctl status containerd
          changed_when: false
          register: containerd_status
          when: container_runtime == "containerd"
        
        - name: Display verification results
          debug:
            msg:
              - "Kubelet: {{ kubelet_version.stdout }}"
              - "Kubeadm: {{ kubeadm_version.stdout }}"
              - "Kubectl: {{ kubectl_version.stdout_lines[0] }}"
              - "Containerd: {{ 'Running' if containerd_status.rc == 0 else 'Not Running' }}"
              - "Swap: Disabled"
              - "Node is ready for Kubernetes cluster"
      
      tags:
        - k8s
        - verify

    # ========================================
    # PHASE 9: Create Preparation Marker
    # ========================================
    - name: Create preparation completion marker
      copy:
        content: |
          Kubernetes node preparation completed: {{ ansible_date_time.iso8601 }}
          Hostname: {{ ansible_hostname }}
          Kubernetes version: {{ k8s_version }}
          Container runtime: {{ container_runtime }}
          Kubelet: {{ kubelet_version.stdout }}
          Kubeadm: {{ kubeadm_version.stdout }}
        dest: /var/log/k8s-node-prep-complete
        mode: '0644'
      tags:
        - k8s

  handlers:
    - name: restart containerd
      service:
        name: containerd
        state: restarted
```

### Step-by-Step Implementation

#### Step 1: Prepare Inventory

```ini
# inventories/production/hosts
[k8s_masters]
k8s-master01.example.com ansible_host=192.168.1.10

[k8s_workers]
k8s-worker01.example.com ansible_host=192.168.1.11
k8s-worker02.example.com ansible_host=192.168.1.12
k8s-worker03.example.com ansible_host=192.168.1.13

[k8s_nodes:children]
k8s_masters
k8s_workers
```

#### Step 2: Run Node Preparation

```bash
ansible-playbook playbooks/k8s-node-prep.yml \
  -i inventories/production/hosts \
  --limit k8s_nodes
```

#### Step 3: Verify Preparation

```bash
# Check all nodes
ansible k8s_nodes -i inventories/production/hosts \
  -m command -a "kubeadm version"

# Verify swap is disabled
ansible k8s_nodes -i inventories/production/hosts \
  -m command -a "swapon --show"

# Check containerd
ansible k8s_nodes -i inventories/production/hosts \
  -m command -a "systemctl status containerd"
```

#### Step 4: Initialize Cluster (Master Only)

```bash
# On master node
sudo kubeadm init \
  --pod-network-cidr=10.244.0.0/16 \
  --apiserver-advertise-address=192.168.1.10

# Setup kubectl for user
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

#### Step 5: Join Worker Nodes

```bash
# Get join command from master
kubeadm token create --print-join-command

# Run on worker nodes
sudo kubeadm join 192.168.1.10:6443 --token <token> \
  --discovery-token-ca-cert-hash sha256:<hash>
```

---

## (G) OS Patching (Safe Rolling Update)

### Purpose
Safely patch operating systems with rolling updates, health checks, and rollback capabilities.

### Use Case
- Security updates
- Kernel updates
- Package updates
- Compliance requirements

### Full Playbook

```yaml
---
# playbooks/os-patch.yml
# Purpose: Safe OS patching with rolling updates

- name: OS Patching with Rolling Updates
  hosts: all
  become: yes
  gather_facts: yes
  serial: "{{ patch_serial | default(1) }}"
  max_fail_percentage: 10
  
  vars:
    # Patching configuration
    patch_reboot_required: true
    patch_reboot_timeout: 600
    patch_pre_check: true
    patch_post_check: true
    
    # Notification
    notify_team: true
    notification_webhook: "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
    
    # Backup before patching
    create_snapshot: false
    
    # Package exclusions
    exclude_packages:
      - docker-ce
      - kubelet
      - kubeadm
      - kubectl
    
    # Health check
    health_check_url: "http://localhost/health"
    health_check_enabled: false
  
  tasks:
    # ========================================
    # PHASE 1: Pre-patch Checks
    # ========================================
    - name: Pre-patch validation
      block:
        - name: Check disk space
          assert:
            that:
              - item.size_available > item.size_total|float * 0.1
            fail_msg: "Insufficient disk space on {{ item.mount }}"
          loop: "{{ ansible_mounts }}"
          when: item.mount in ['/','/ var','/tmp']
        
        - name: Check current kernel version
          command: uname -r
          register: current_kernel
          changed_when: false
        
        - name: Get list of available updates
          shell: |
            {% if ansible_os_family == "Debian" %}
            apt list --upgradable 2>/dev/null | grep -v "Listing"
            {% elif ansible_os_family == "RedHat" %}
            yum list updates
            {% endif %}
          register: available_updates
          changed_when: false
          failed_when: false
        
        - name: Display available updates
          debug:
            msg: "{{ available_updates.stdout_lines }}"
        
        - name: Check if reboot is required
          stat:
            path: /var/run/reboot-required
          register: reboot_required_file
          when: ansible_os_family == "Debian"
        
        - name: Notify team - Patching started
          uri:
            url: "{{ notification_webhook }}"
            method: POST
            body_format: json
            body:
              text: "🔧 OS Patching started on {{ ansible_hostname }}"
              attachments:
                - color: "warning"
                  fields:
                    - title: "Hostname"
                      value: "{{ ansible_hostname }}"
                      short: true
                    - title: "Current Kernel"
                      value: "{{ current_kernel.stdout }}"
                      short: true
          when: notify_team
          delegate_to: localhost
      
      when: patch_pre_check
      tags:
        - patch
        - pre-check

    # ========================================
    # PHASE 2: Create Backup/Snapshot
    # ========================================
    - name: Create backup before patching
      block:
        - name: Create package list backup
          shell: |
            {% if ansible_os_family == "Debian" %}
            dpkg --get-selections > /root/package-list-{{ ansible_date_time.epoch }}.txt
            {% elif ansible_os_family == "RedHat" %}
            rpm -qa > /root/package-list-{{ ansible_date_time.epoch }}.txt
            {% endif %}
        
        - name: Backup critical configuration files
          archive:
            path:
              - /etc/
            dest: "/root/etc-backup-{{ ansible_date_time.epoch }}.tar.gz"
            format: gz
      
      tags:
        - patch
        - backup

    # ========================================
    # PHASE 3: Apply Updates
    # ========================================
    - name: Apply OS updates
      block:
        # Debian/Ubuntu
        - name: Update package cache (Debian/Ubuntu)
          apt:
            update_cache: yes
            cache_valid_time: 3600
          when: ansible_os_family == "Debian"
        
        - name: Upgrade packages (Debian/Ubuntu)
          apt:
            upgrade: dist
            autoremove: yes
            autoclean: yes
          when: ansible_os_family == "Debian"
          register: apt_upgrade_result
        
        # RedHat/CentOS
        - name: Upgrade packages (RedHat/CentOS)
          yum:
            name: '*'
            state: latest
            exclude: "{{ exclude_packages | join(',') }}"
          when: ansible_os_family == "RedHat"
          register: yum_upgrade_result
        
        - name: Display upgrade results
          debug:
            msg: "Packages upgraded: {{ apt_upgrade_result.changed if ansible_os_family == 'Debian' else yum_upgrade_result.changed }}"
      
      rescue:
        - name: Log update failure
          debug:
            msg: "Package update failed on {{ ansible_hostname }}"
        
        - name: Notify team - Update failed
          uri:
            url: "{{ notification_webhook }}"
            method: POST
            body_format: json
            body:
              text: "❌ OS Patching FAILED on {{ ansible_hostname }}"
          when: notify_team
          delegate_to: localhost
        
        - name: Fail playbook
          fail:
            msg: "OS update failed"
      
      tags:
        - patch
        - update

    # ========================================
    # PHASE 4: Check if Reboot Required
    # ========================================
    - name: Determine if reboot is needed
      block:
        - name: Check for reboot-required file (Debian/Ubuntu)
          stat:
            path: /var/run/reboot-required
          register: debian_reboot_required
          when: ansible_os_family == "Debian"
        
        - name: Check if kernel was updated (RedHat/CentOS)
          shell: |
            LAST_KERNEL=$(rpm -q --last kernel | head -1 | awk '{print $1}')
            CURRENT_KERNEL=$(uname -r)
            if [ "$LAST_KERNEL" != "kernel-$CURRENT_KERNEL" ]; then
              echo "reboot_needed"
            fi
          register: redhat_reboot_check
          when: ansible_os_family == "RedHat"
          changed_when: false
        
        - name: Set reboot required fact
          set_fact:
            needs_reboot: "{{ (debian_reboot_required.stat.exists | default(false)) or (redhat_reboot_check.stdout | default('') == 'reboot_needed') }}"
      
      tags:
        - patch
        - reboot-check

    # ========================================
    # PHASE 5: Reboot if Required
    # ========================================
    - name: Reboot server if required
      block:
        - name: Notify team - Rebooting
          uri:
            url: "{{ notification_webhook }}"
            method: POST
            body_format: json
            body:
              text: "🔄 Rebooting {{ ansible_hostname }} after patching"
          when: notify_team
          delegate_to: localhost
        
        - name: Reboot the server
          reboot:
            reboot_timeout: "{{ patch_reboot_timeout }}"
            pre_reboot_delay: 10
            post_reboot_delay: 30
            msg: "Reboot initiated by Ansible for OS patching"
          when: needs_reboot
        
        - name: Wait for server to come back online
          wait_for_connection:
            delay: 30
            timeout: 300
          when: needs_reboot
      
      when: 
        - patch_reboot_required
        - needs_reboot
      tags:
        - patch
        - reboot

    # ========================================
    # PHASE 6: Post-patch Verification
    # ========================================
    - name: Post-patch validation
      block:
        - name: Verify new kernel version
          command: uname -r
          register: new_kernel
          changed_when: false
        
        - name: Compare kernel versions
          debug:
            msg: "Kernel: {{ current_kernel.stdout }} → {{ new_kernel.stdout }}"
        
        - name: Check system services
          command: systemctl is-system-running
          register: system_status
          changed_when: false
          failed_when: false
        
        - name: Verify critical services
          service_facts:
        
        - name: Check application health
          uri:
            url: "{{ health_check_url }}"
            status_code: 200
            timeout: 10
          register: health_check
          when: health_check_enabled
          retries: 5
          delay: 10
        
        - name: Display post-patch status
          debug:
            msg:
              - "System status: {{ system_status.stdout }}"
              - "Health check: {{ 'PASSED' if health_check.status == 200 else 'N/A' }}"
      
      when: patch_post_check
      tags:
        - patch
        - post-check

    # ========================================
    # PHASE 7: Cleanup
    # ========================================
    - name: Cleanup after patching
      block:
        - name: Remove old kernels (Debian/Ubuntu)
          apt:
            autoremove: yes
            purge: yes
          when: ansible_os_family == "Debian"
        
        - name: Clean package cache
          shell: |
            {% if ansible_os_family == "Debian" %}
            apt-get clean
            {% elif ansible_os_family == "RedHat" %}
            yum clean all
            {% endif %}
        
        - name: Remove old backups (keep last 5)
          shell: |
            cd /root
            ls -t etc-backup-*.tar.gz | tail -n +6 | xargs -r rm
            ls -t package-list-*.txt | tail -n +6 | xargs -r rm
      
      tags:
        - patch
        - cleanup

    # ========================================
    # PHASE 8: Final Notification
    # ========================================
    - name: Send completion notification
      block:
        - name: Create patch report
          set_fact:
            patch_report:
              hostname: "{{ ansible_hostname }}"
              old_kernel: "{{ current_kernel.stdout }}"
              new_kernel: "{{ new_kernel.stdout }}"
              rebooted: "{{ needs_reboot }}"
              status: "SUCCESS"
        
        - name: Notify team - Patching completed
          uri:
            url: "{{ notification_webhook }}"
            method: POST
            body_format: json
            body:
              text: "✅ OS Patching completed on {{ ansible_hostname }}"
              attachments:
                - color: "good"
                  fields:
                    - title: "Hostname"
                      value: "{{ ansible_hostname }}"
                      short: true
                    - title: "Kernel"
                      value: "{{ new_kernel.stdout }}"
                      short: true
                    - title: "Rebooted"
                      value: "{{ 'Yes' if needs_reboot else 'No' }}"
                      short: true
          when: notify_team
          delegate_to: localhost
      
      always:
        - name: Create patch completion marker
          copy:
            content: |
              Patching completed: {{ ansible_date_time.iso8601 }}
              Old kernel: {{ current_kernel.stdout }}
              New kernel: {{ new_kernel.stdout }}
              Rebooted: {{ needs_reboot }}
            dest: /var/log/ansible-patch-{{ ansible_date_time.date }}
            mode: '0644'
      
      tags:
        - patch
        - notify
```

### Step-by-Step Implementation

#### Step 1: Test on Single Server

```bash
# Dry run on one server
ansible-playbook playbooks/os-patch.yml \
  -i inventories/production/hosts \
  --limit web01.example.com \
  --check

# Actual run on one server
ansible-playbook playbooks/os-patch.yml \
  -i inventories/production/hosts \
  --limit web01.example.com
```

#### Step 2: Rolling Update (One at a Time)

```bash
ansible-playbook playbooks/os-patch.yml \
  -i inventories/production/hosts \
  -e "patch_serial=1"
```

#### Step 3: Batch Update (2 Servers at a Time)

```bash
ansible-playbook playbooks/os-patch.yml \
  -i inventories/production/hosts \
  -e "patch_serial=2"
```

#### Step 4: Update Without Reboot

```bash
ansible-playbook playbooks/os-patch.yml \
  -i inventories/production/hosts \
  -e "patch_reboot_required=false"
```

### Patching Strategies

**1. Conservative (Production)**
```yaml
serial: 1
max_fail_percentage: 0
patch_reboot_required: true
```

**2. Moderate (Staging)**
```yaml
serial: 2
max_fail_percentage: 25
patch_reboot_required: true
```

**3. Aggressive (Development)**
```yaml
serial: "100%"
max_fail_percentage: 50
patch_reboot_required: false
```

---

*Continuing with remaining templates (H, I, J) in next section...*
