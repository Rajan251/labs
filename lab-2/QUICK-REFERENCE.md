# Jenkins CI/CD Pipeline - Quick Reference

## 📁 Project Structure

```
lab-2/
├── README.md                          # Main documentation hub
├── docs/                              # Detailed guides (10 files)
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
├── jenkins/                           # Pipeline examples (3 files)
│   ├── Jenkinsfile
│   ├── Jenkinsfile.helm
│   └── Jenkinsfile.advanced
├── kubernetes/                        # K8s manifests (8 files)
│   ├── namespace.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── hpa.yaml
│   └── rbac.yaml
├── docker/                            # Docker files (3 files)
│   ├── Dockerfile
│   ├── Dockerfile.jenkins
│   └── docker-compose.yml
└── scripts/                           # Installation scripts (4 files)
    ├── install-jenkins.sh
    ├── install-docker.sh
    ├── install-kubectl-helm.sh
    └── setup-k8s-access.sh
```

## 🚀 Quick Start

### 1. Install Components

```bash
cd scripts

# Install Jenkins
sudo ./install-jenkins.sh

# Install Docker
sudo ./install-docker.sh

# Install kubectl and Helm
sudo ./install-kubectl-helm.sh

# Setup Kubernetes access
sudo ./setup-k8s-access.sh
```

### 2. Deploy Application

```bash
# Apply Kubernetes manifests
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/rbac.yaml
kubectl apply -f kubernetes/configmap.yaml
kubectl apply -f kubernetes/secret.yaml
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml
kubectl apply -f kubernetes/ingress.yaml
kubectl apply -f kubernetes/hpa.yaml
```

### 3. Create Jenkins Pipeline

1. Create new Pipeline job in Jenkins
2. Point to your Git repository
3. Use one of the Jenkinsfiles:
   - `jenkins/Jenkinsfile` - Basic pipeline
   - `jenkins/Jenkinsfile.helm` - Helm deployment
   - `jenkins/Jenkinsfile.advanced` - Advanced features

## 📚 Documentation Overview

### Core Guides

| File | Description |
|------|-------------|
| **01-project-overview.md** | Architecture and workflow explanation |
| **02-ubuntu-setup.md** | Server prerequisites and configuration |
| **03-jenkins-installation.md** | Native Jenkins installation |
| **04-containerized-jenkins.md** | Docker-based Jenkins setup |
| **05-docker-integration.md** | Docker installation and configuration |
| **06-kubernetes-access.md** | kubectl, Helm, and cluster access |
| **07-cicd-pipeline.md** | Complete pipeline setup |
| **08-monitoring-logs.md** | Logging and monitoring strategies |
| **09-troubleshooting.md** | Common problems and solutions |
| **10-best-practices.md** | Security and optimization tips |

## 🔧 Configuration Files

### Jenkinsfiles

- **Jenkinsfile**: Standard CI/CD pipeline with build, test, Docker build/push, and K8s deployment
- **Jenkinsfile.helm**: Helm-based deployment with automatic rollback
- **Jenkinsfile.advanced**: Parallel stages, security scanning, smoke tests, parameters

### Kubernetes Manifests

- **namespace.yaml**: Production namespace
- **deployment.yaml**: Application deployment with health checks
- **service.yaml**: LoadBalancer service
- **ingress.yaml**: Ingress with TLS
- **configmap.yaml**: Application configuration
- **secret.yaml**: Sensitive data (base64 encoded)
- **hpa.yaml**: Horizontal Pod Autoscaler
- **rbac.yaml**: Jenkins service account and permissions

### Docker Files

- **Dockerfile**: Multi-stage Node.js application
- **Dockerfile.jenkins**: Custom Jenkins with Docker, kubectl, Helm
- **docker-compose.yml**: Complete Jenkins setup with DinD

## 📋 Common Commands

### Jenkins

```bash
# Start/stop Jenkins
sudo systemctl start jenkins
sudo systemctl stop jenkins
sudo systemctl restart jenkins

# View logs
sudo journalctl -u jenkins -f

# Get initial password
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

### Docker

```bash
# Build image
docker build -t myapp:latest .

# Push image
docker push username/myapp:latest

# Clean up
docker system prune -a
```

### Kubernetes

```bash
# Deploy
kubectl apply -f kubernetes/

# Check status
kubectl get pods -n production
kubectl get svc -n production

# View logs
kubectl logs -f <pod-name> -n production

# Rollback
kubectl rollout undo deployment/myapp -n production
```

## 🔍 Troubleshooting Quick Reference

### Jenkins Won't Start
```bash
sudo journalctl -u jenkins -n 50
sudo systemctl restart jenkins
```

### Docker Permission Denied
```bash
sudo usermod -aG docker jenkins
sudo systemctl restart jenkins
```

### Pod ImagePullBackOff
```bash
kubectl describe pod <pod-name> -n production
# Check image name, registry credentials
```

### Pod CrashLoopBackOff
```bash
kubectl logs <pod-name> -n production
kubectl logs <pod-name> --previous -n production
```

## 🎯 Learning Path

1. **Start**: Read `docs/01-project-overview.md`
2. **Setup**: Follow `docs/02-ubuntu-setup.md`
3. **Install**: Use scripts in `scripts/` directory
4. **Configure**: Follow guides 03-06
5. **Deploy**: Use `docs/07-cicd-pipeline.md`
6. **Monitor**: Reference `docs/08-monitoring-logs.md`
7. **Troubleshoot**: Use `docs/09-troubleshooting.md`
8. **Optimize**: Apply `docs/10-best-practices.md`

## 📞 Support

- Check `docs/09-troubleshooting.md` for common issues
- Review logs: Jenkins, Docker, Kubernetes
- Verify configurations in `kubernetes/` and `jenkins/`

## ✅ Checklist

- [ ] Ubuntu server configured
- [ ] Jenkins installed and accessible
- [ ] Docker installed and configured
- [ ] kubectl and Helm installed
- [ ] Kubernetes access configured
- [ ] Credentials added to Jenkins
- [ ] Pipeline created and tested
- [ ] Application deployed to Kubernetes
- [ ] Monitoring configured
- [ ] Backups scheduled

---

**Created**: 2024
**Purpose**: Complete guide for Jenkins CI/CD pipeline with Docker and Kubernetes
**Total Files**: 29 files across 6 directories
