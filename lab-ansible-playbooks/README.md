# Production-Grade Ansible Playbook Templates

A comprehensive collection of battle-tested Ansible playbook templates used in modern organizations for infrastructure automation, configuration management, and deployment orchestration.

## 📚 Table of Contents

1. [Overview](docs/01-overview.md)
2. [Project Structure](docs/02-project-structure.md)
3. [Core Playbook Templates](docs/03-core-templates.md)
4. [Roles Library](roles/)
5. [Dynamic Inventory](docs/04-dynamic-inventory.md)
6. [Best Practices](docs/05-best-practices.md)
7. [Troubleshooting](docs/06-troubleshooting.md)
8. [CI/CD Integration](docs/07-cicd-integration.md)

## 🚀 Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd lab-ansible-playbooks

# Install Ansible
pip install ansible ansible-lint

# Verify installation
ansible --version

# Run a playbook (dry-run)
ansible-playbook -i inventories/dev playbooks/site.yml --check

# Run a playbook (actual execution)
ansible-playbook -i inventories/dev playbooks/site.yml
```

## 📋 What's Included

### Core Templates
- **Server Bootstrap** - Initial server setup and hardening
- **User Management** - User creation and SSH key distribution
- **Nginx** - Web server installation and configuration
- **Docker** - Container runtime setup
- **Application Deployment** - Git-based and artifact deployments
- **Kubernetes Prep** - K8s node preparation
- **OS Patching** - Safe rolling updates
- **Log Management** - Centralized logging setup
- **Security Hardening** - CIS benchmarks and best practices
- **Monitoring** - Prometheus exporters and agents

### Production Features
✅ Idempotent operations  
✅ Error handling with block/rescue/always  
✅ Ansible Vault for secrets  
✅ Dynamic inventory support  
✅ Role-based organization  
✅ Comprehensive tagging  
✅ Handler-based service management  
✅ CI/CD ready  

## 🏗️ Project Structure

```
ansible/
├── inventories/          # Environment-specific inventories
├── group_vars/          # Group variables
├── host_vars/           # Host-specific variables
├── roles/               # Reusable roles
├── playbooks/           # Playbook collection
├── docs/                # Documentation
├── ansible.cfg          # Ansible configuration
└── requirements.yml     # Role dependencies
```

## 🎯 Use Cases

- **Infrastructure Provisioning** - Bootstrap new servers
- **Configuration Management** - Maintain consistent configurations
- **Application Deployment** - Deploy applications reliably
- **Security Compliance** - Enforce security policies
- **Disaster Recovery** - Automated recovery procedures
- **Scaling Operations** - Add/remove nodes dynamically

## 📖 Documentation

Detailed documentation is available in the [docs/](docs/) directory:

- [What are Ansible Playbooks?](docs/01-overview.md)
- [Standard Folder Structure](docs/02-project-structure.md)
- [Template Library](docs/03-core-templates.md)
- [Dynamic Inventory Guide](docs/04-dynamic-inventory.md)
- [Production Best Practices](docs/05-best-practices.md)
- [Common Problems & Solutions](docs/06-troubleshooting.md)
- [CI/CD Integration](docs/07-cicd-integration.md)

## 🔒 Security

- Never commit secrets to version control
- Use Ansible Vault for sensitive data
- Follow principle of least privilege
- Regularly update dependencies
- Enable audit logging

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

## 📄 License

MIT License - See LICENSE file for details

## 🆘 Support

For issues and questions:
- Check [Troubleshooting Guide](docs/06-troubleshooting.md)
- Review [Best Practices](docs/05-best-practices.md)
- Open an issue on GitHub

---

**Note**: These templates are designed for production use but should be tested in development environments first.
