# Ansible Quick Reference Card

## Essential Commands

### Playbook Execution
```bash
# Run playbook
ansible-playbook playbooks/site.yml

# Dry run (check mode)
ansible-playbook playbooks/site.yml --check --diff

# Verbose output
ansible-playbook playbooks/site.yml -v    # -vv, -vvv for more detail

# Limit to specific hosts
ansible-playbook playbooks/site.yml --limit web01,web02

# Use specific inventory
ansible-playbook playbooks/site.yml -i inventories/production/hosts

# Run specific tags
ansible-playbook playbooks/site.yml --tags "nginx,docker"

# Skip tags
ansible-playbook playbooks/site.yml --skip-tags "monitoring"

# Start at specific task
ansible-playbook playbooks/site.yml --start-at-task="Install Nginx"

# Step through playbook
ansible-playbook playbooks/site.yml --step
```

### Ad-Hoc Commands
```bash
# Ping all hosts
ansible all -m ping

# Run command
ansible all -m command -a "uptime"

# Copy file
ansible all -m copy -a "src=/tmp/file dest=/tmp/file"

# Install package
ansible all -m apt -a "name=nginx state=present" --become

# Restart service
ansible all -m service -a "name=nginx state=restarted" --become

# Gather facts
ansible all -m setup
```

### Inventory
```bash
# List inventory
ansible-inventory --list

# Show inventory graph
ansible-inventory --graph

# Show host variables
ansible-inventory --host web01
```

### Vault
```bash
# Create encrypted file
ansible-vault create secrets.yml

# Edit encrypted file
ansible-vault edit secrets.yml

# Encrypt existing file
ansible-vault encrypt file.yml

# Decrypt file
ansible-vault decrypt file.yml

# View encrypted file
ansible-vault view secrets.yml

# Change password
ansible-vault rekey secrets.yml

# Encrypt string
ansible-vault encrypt_string 'secret' --name 'db_password'
```

### Testing & Validation
```bash
# Syntax check
ansible-playbook playbooks/site.yml --syntax-check

# Lint playbooks
ansible-lint playbooks/*.yml

# YAML lint
yamllint .

# List tasks
ansible-playbook playbooks/site.yml --list-tasks

# List tags
ansible-playbook playbooks/site.yml --list-tags

# List hosts
ansible-playbook playbooks/site.yml --list-hosts
```

## Common Patterns

### Playbook Structure
```yaml
---
- name: Playbook description
  hosts: target_hosts
  become: yes
  gather_facts: yes
  
  vars:
    variable: value
  
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

### Error Handling
```yaml
- name: Task with error handling
  block:
    - name: Risky operation
      command: /path/to/command
  
  rescue:
    - name: Handle error
      debug:
        msg: "Task failed, handling error"
  
  always:
    - name: Cleanup
      file:
        path: /tmp/file
        state: absent
```

### Conditionals
```yaml
# When condition
- name: Install on Ubuntu
  apt:
    name: nginx
  when: ansible_distribution == "Ubuntu"

# Multiple conditions (AND)
when:
  - ansible_distribution == "Ubuntu"
  - ansible_distribution_version == "20.04"

# Multiple conditions (OR)
when: ansible_distribution == "Ubuntu" or ansible_distribution == "Debian"

# Check if variable is defined
when: my_variable is defined

# Check if variable is not defined
when: my_variable is not defined
```

### Loops
```yaml
# Simple loop
- name: Install packages
  apt:
    name: "{{ item }}"
  loop:
    - nginx
    - docker
    - git

# Loop with dictionary
- name: Create users
  user:
    name: "{{ item.name }}"
    groups: "{{ item.groups }}"
  loop:
    - { name: 'john', groups: 'sudo' }
    - { name: 'jane', groups: 'docker' }

# Loop with_items (legacy)
- name: Install packages
  apt:
    name: "{{ item }}"
  with_items:
    - nginx
    - docker
```

### Variables
```yaml
# Define variables
vars:
  app_port: 8080
  app_name: myapp

# Use variables
"{{ app_name }}"

# Default value
"{{ app_port | default(3000) }}"

# Register output
- name: Get hostname
  command: hostname
  register: hostname_output

- name: Display hostname
  debug:
    msg: "{{ hostname_output.stdout }}"
```

## File Locations

### Configuration
```
ansible.cfg              # Ansible configuration
requirements.yml         # Role/collection dependencies
.vault_pass             # Vault password (DO NOT COMMIT)
.gitignore              # Git ignore rules
```

### Inventory
```
inventories/
├── production/
│   ├── hosts           # Inventory file
│   ├── group_vars/     # Group variables
│   └── host_vars/      # Host variables
```

### Playbooks & Roles
```
playbooks/              # Playbook collection
roles/                  # Reusable roles
  └── rolename/
      ├── tasks/
      ├── handlers/
      ├── templates/
      ├── files/
      ├── vars/
      ├── defaults/
      └── meta/
```

## Variable Precedence (Highest to Lowest)

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

## Common Modules

| Module | Purpose | Example |
|--------|---------|---------|
| `apt` | Manage packages (Debian) | `apt: name=nginx state=present` |
| `yum` | Manage packages (RedHat) | `yum: name=nginx state=present` |
| `service` | Manage services | `service: name=nginx state=started` |
| `copy` | Copy files | `copy: src=file dest=/tmp/file` |
| `template` | Deploy Jinja2 templates | `template: src=app.j2 dest=/etc/app.conf` |
| `file` | Manage files/directories | `file: path=/tmp/dir state=directory` |
| `user` | Manage users | `user: name=john groups=sudo` |
| `command` | Run commands | `command: /usr/bin/make install` |
| `shell` | Run shell commands | `shell: echo "test" >> file` |
| `git` | Manage git repos | `git: repo=url dest=/opt/app` |
| `docker_container` | Manage containers | `docker_container: name=app image=nginx` |

## Tags

```bash
# Run specific tags
ansible-playbook site.yml --tags "install,config"

# Skip tags
ansible-playbook site.yml --skip-tags "monitoring"

# Special tags
tags: always        # Always run
tags: never         # Never run unless specified
```

## Troubleshooting

### Debug
```yaml
- name: Show variable
  debug:
    var: my_variable

- name: Show message
  debug:
    msg: "Value is {{ my_variable }}"
```

### Common Issues

| Issue | Solution |
|-------|----------|
| SSH connection failed | Check SSH keys, verify `ansible_user` |
| Permission denied | Use `become: yes`, check sudo access |
| Handler not running | Check handler name matches notify |
| Variable undefined | Check variable scope and precedence |
| Module not found | Install required collection |

### Verbose Modes
```bash
-v      # Verbose
-vv     # More verbose
-vvv    # Very verbose (connection debugging)
-vvvv   # Extremely verbose (SSH debugging)
```

## Best Practices

✅ Use roles for reusability  
✅ Always use check mode first  
✅ Use Ansible Vault for secrets  
✅ Tag your tasks  
✅ Use handlers for service restarts  
✅ Make playbooks idempotent  
✅ Use version control  
✅ Test in development first  
✅ Document your playbooks  
✅ Use ansible-lint  

## Resources

- **Docs**: https://docs.ansible.com/
- **Galaxy**: https://galaxy.ansible.com/
- **Lint**: https://ansible-lint.readthedocs.io/
- **Molecule**: https://molecule.readthedocs.io/

---

**Quick Reference v1.0** | Keep this handy! 📋
