# Automation Practices for Linux Administration

**Level:** Expert / DevOps Engineer
**Focus:** Infrastructure as Code, configuration management, and automation best practices.

---

## 1. Infrastructure as Code Principles

### 1.1 Idempotency
*   **Definition**: Running the same automation multiple times produces the same result.
*   **Example**: `ansible-playbook site.yml` run 10 times = same final state.
*   **Benefit**: Safe to re-run without fear of breaking things.

### 1.2 Declarative vs Imperative
*   **Declarative**: Describe desired state. "User `alice` should exist."
*   **Imperative**: Describe steps. "Run `useradd alice`."
*   **Recommendation**: Prefer declarative (Ansible, Puppet).

### 1.3 Version Control
*   All infrastructure code in Git.
*   Branching strategy (main, dev, feature branches).
*   Pull requests for peer review.

---

## 2. Configuration Management Comparison

| Feature | **Ansible** | **Puppet** | **Chef** | **SaltStack** |
| :--- | :--- | :--- | :--- | :--- |
| **Agent** | Agentless (SSH) | Agent-based | Agent-based | Agent-based |
| **Language** | YAML | Puppet DSL | Ruby | YAML/Python |
| **Model** | Push | Pull | Pull | Push/Pull |
| **Learning Curve** | Easy | Medium | Hard | Medium |
| **Best For** | Orchestration, simple setups | Large enterprises | Complex logic | Event-driven, fast |

---

## 3. Ansible Best Practices

### 3.1 Playbook Organization
```
site.yml              # Master playbook
roles/
  webserver/
    tasks/main.yml
    handlers/main.yml
    templates/
    files/
  database/
inventories/
  production/
    hosts
    group_vars/all.yml
  staging/
```

### 3.2 Variable Precedence
1.  Extra vars (`-e "var=value"`) - Highest
2.  Task vars
3.  Role defaults - Lowest

### 3.3 Error Handling
```yaml
- name: Attempt risky operation
  command: /usr/bin/risky_command
  register: result
  failed_when: result.rc != 0 and result.rc != 2
  ignore_errors: yes
```

### 3.4 Performance Optimization
*   **Pipelining**: `ansible.cfg`: `pipelining = True` (reduces SSH overhead).
*   **Strategy**: `strategy: free` (don't wait for all hosts to finish each task).

---

## 4. Template Management

### 4.1 Jinja2 Templating
```jinja2
# /etc/nginx/nginx.conf.j2
worker_processes {{ ansible_processor_vcpus }};

{% if environment == "production" %}
worker_connections 4096;
{% else %}
worker_connections 1024;
{% endif %}
```

### 4.2 Variable Substitution
```yaml
- name: Deploy config
  template:
    src: nginx.conf.j2
    dest: /etc/nginx/nginx.conf
  vars:
    environment: production
```

---

## 5. Secret Management

### 5.1 Ansible Vault
```bash
# Encrypt file
ansible-vault encrypt secrets.yml

# Use in playbook
ansible-playbook site.yml --ask-vault-pass
```

### 5.2 HashiCorp Vault Integration
```yaml
- name: Fetch DB password from Vault
  set_fact:
    db_password: "{{ lookup('hashi_vault', 'secret=secret/data/db:password') }}"
```

### 5.3 Certificate Rotation
```yaml
- name: Generate new cert
  openssl_certificate:
    path: /etc/ssl/certs/server.crt
    privatekey_path: /etc/ssl/private/server.key
    provider: selfsigned
    force: yes
  when: cert_expiry_days < 30
```

---

## 6. Change Management Integration

### 6.1 Approval Workflows
*   Use CI/CD pipelines (GitLab CI, Jenkins).
*   Require approval for production deploys.
*   Automated testing in staging before production.

### 6.2 Rollback Procedures
```yaml
- name: Deploy new version
  copy:
    src: app-v2.jar
    dest: /opt/app/app.jar
    backup: yes  # Creates backup before overwriting
```

---

## 7. Monitoring Automation

### 7.1 Self-Healing
```yaml
- name: Restart crashed service
  systemd:
    name: myapp
    state: started
  when: "'myapp' not in ansible_facts.services or ansible_facts.services['myapp'].state != 'running'"
```

### 7.2 Automated Scaling
*   Trigger Ansible playbook from monitoring alert (Prometheus Alertmanager webhook).

---

## 8. Practical Examples

### 8.1 User Management Automation
```yaml
- name: Ensure users exist
  user:
    name: "{{ item.name }}"
    groups: "{{ item.groups }}"
    state: present
  loop:
    - { name: alice, groups: wheel }
    - { name: bob, groups: developers }
```

### 8.2 Security Patch Deployment
```yaml
- name: Update all packages
  yum:
    name: '*'
    state: latest
    security: yes
  when: ansible_os_family == "RedHat"
```

### 8.3 Application Deployment Pipeline
```yaml
- name: Stop service
  systemd:
    name: myapp
    state: stopped

- name: Deploy new version
  copy:
    src: myapp-{{ version }}.jar
    dest: /opt/myapp/myapp.jar

- name: Start service
  systemd:
    name: myapp
    state: started

- name: Wait for health check
  uri:
    url: http://localhost:8080/health
    status_code: 200
  retries: 5
  delay: 10
```
