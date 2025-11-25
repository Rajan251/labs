# Complete Containerized Jenkins CI/CD Pipeline

A comprehensive guide and implementation for building a production-ready CI/CD pipeline using Jenkins, Docker, and Kubernetes on Ubuntu Server.

## 📚 Documentation Structure

This repository contains detailed documentation, configuration files, and scripts for setting up a complete CI/CD pipeline.

### Documentation Files

Navigate to the `docs/` directory for detailed guides:

1. **[Project Overview](docs/01-project-overview.md)** - Understanding the architecture and workflow
2. **[Ubuntu Server Setup](docs/02-ubuntu-setup.md)** - Server prerequisites and initial configuration
3. **[Jenkins Installation](docs/03-jenkins-installation.md)** - Native Jenkins installation on Ubuntu
4. **[Containerized Jenkins](docs/04-containerized-jenkins.md)** - Running Jenkins in Docker
5. **[Docker Integration](docs/05-docker-integration.md)** - Integrating Docker with Jenkins
6. **[Kubernetes Access](docs/06-kubernetes-access.md)** - Setting up kubectl, Helm, and cluster access
7. **[CI/CD Pipeline](docs/07-cicd-pipeline.md)** - Building the complete pipeline
8. **[Monitoring & Logs](docs/08-monitoring-logs.md)** - Logging and monitoring strategies
9. **[Troubleshooting](docs/09-troubleshooting.md)** - Common problems and solutions
10. **[Best Practices](docs/10-best-practices.md)** - Security and optimization guidelines

## 🗂️ Repository Structure

```
.
├── README.md                          # This file
├── docs/                              # Documentation files
│   ├── 01-project-overview.md
│   ├── 02-ubuntu-setup.md
│   ├── 03-jenkins-installation.md
│   ├── 04-containerized-jenkins.md
│   ├── 05-docker-integration.md
│   ├── 06-kubernetes-access.md
│   ├── 07-cicd-pipeline.md
│   ├── 08-monitoring-logs.md
│   ├── 09-troubleshooting.md
│   └── 10-best-practices.md
├── jenkins/                           # Jenkins configuration files
│   ├── Jenkinsfile                    # Basic pipeline
│   ├── Jenkinsfile.helm               # Helm-based deployment
│   └── Jenkinsfile.advanced           # Advanced with parallel stages
├── kubernetes/                        # Kubernetes manifests
│   ├── namespace.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── hpa.yaml
│   └── rbac.yaml
├── docker/                            # Docker files
│   ├── Dockerfile                     # Application Dockerfile
│   ├── Dockerfile.jenkins             # Custom Jenkins image
│   └── docker-compose.yml             # Jenkins Docker Compose
└── scripts/                           # Installation scripts
    ├── install-jenkins.sh
    ├── install-docker.sh
    ├── install-kubectl-helm.sh
    └── setup-k8s-access.sh
```

## 🚀 Quick Start

### Prerequisites

- Ubuntu 22.04 LTS or 20.04 LTS
- 4 CPU cores, 8 GB RAM minimum
- 50 GB disk space
- Root or sudo access

### Installation Steps

1. **Setup Ubuntu Server**
   ```bash
   cd scripts
   chmod +x *.sh
   ```

2. **Install Jenkins**
   ```bash
   ./install-jenkins.sh
   ```

3. **Install Docker**
   ```bash
   ./install-docker.sh
   ```

4. **Install kubectl and Helm**
   ```bash
   ./install-kubectl-helm.sh
   ```

5. **Configure Kubernetes Access**
   ```bash
   ./setup-k8s-access.sh
   ```

## 📋 Pipeline Workflow

```
Developer → Git Push → Webhook → Jenkins Pipeline
    ↓
Build Application
    ↓
Run Tests
    ↓
Build Docker Image
    ↓
Push to Registry
    ↓
Deploy to Kubernetes
    ↓
Monitor & Validate
```

## 🔧 Configuration Files

### Jenkins Pipelines

- **[Jenkinsfile](jenkins/Jenkinsfile)** - Basic CI/CD pipeline
- **[Jenkinsfile.helm](jenkins/Jenkinsfile.helm)** - Helm-based deployment
- **[Jenkinsfile.advanced](jenkins/Jenkinsfile.advanced)** - Advanced with parallel stages

### Kubernetes Manifests

All Kubernetes YAML files are in the `kubernetes/` directory:
- Namespace, Deployment, Service
- Ingress, ConfigMap, Secret
- HPA (Horizontal Pod Autoscaler)
- RBAC (Service Account and Roles)

### Docker Files

- **[Dockerfile](docker/Dockerfile)** - Sample application Dockerfile
- **[Dockerfile.jenkins](docker/Dockerfile.jenkins)** - Custom Jenkins with Docker CLI
- **[docker-compose.yml](docker/docker-compose.yml)** - Jenkins Docker Compose setup

## 🛠️ Key Features

- ✅ Complete CI/CD pipeline from code to deployment
- ✅ Docker-based containerization
- ✅ Kubernetes orchestration
- ✅ Automated testing and building
- ✅ Rolling updates and rollbacks
- ✅ Health checks and auto-scaling
- ✅ Comprehensive monitoring and logging
- ✅ Security best practices

## 📖 Learning Path

1. Start with **[Project Overview](docs/01-project-overview.md)** to understand the architecture
2. Follow **[Ubuntu Setup](docs/02-ubuntu-setup.md)** to prepare your server
3. Install components in order: Jenkins → Docker → Kubernetes tools
4. Study the **[CI/CD Pipeline](docs/07-cicd-pipeline.md)** guide
5. Review **[Troubleshooting](docs/09-troubleshooting.md)** for common issues

## 🔍 Common Use Cases

### Deploy a Node.js Application

1. Use the sample [Jenkinsfile](jenkins/Jenkinsfile)
2. Modify the build commands for your app
3. Update [Dockerfile](docker/Dockerfile) for Node.js
4. Apply [Kubernetes manifests](kubernetes/)

### Deploy with Helm

1. Use [Jenkinsfile.helm](jenkins/Jenkinsfile.helm)
2. Create Helm chart for your application
3. Configure values for different environments

### Containerized Jenkins

1. Use [docker-compose.yml](docker/docker-compose.yml)
2. Or build custom image with [Dockerfile.jenkins](docker/Dockerfile.jenkins)
3. Mount volumes for persistence

## 🐛 Troubleshooting

Refer to the **[Troubleshooting Guide](docs/09-troubleshooting.md)** for:
- Jenkins installation issues
- Docker permission errors
- Kubernetes deployment failures
- Image pull problems
- RBAC and authentication issues

## 🔒 Security Considerations

- Use secrets management (Kubernetes Secrets, HashiCorp Vault)
- Implement RBAC for Jenkins and Kubernetes
- Scan Docker images for vulnerabilities
- Use TLS/SSL for all communications
- Regular security updates

## 📚 Additional Resources

- [Jenkins Documentation](https://www.jenkins.io/doc/)
- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Helm Documentation](https://helm.sh/docs/)

## 🤝 Contributing

This is an educational resource. Feel free to:
- Report issues or errors
- Suggest improvements
- Add examples for other languages/frameworks

## 📝 License

This documentation is provided as-is for educational purposes.

---

**Built with ❤️ for DevOps Engineers**
