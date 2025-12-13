# K8s Master Lab 🚀

> A comprehensive Kubernetes educational and production-ready platform demonstrating all core concepts, components, and best practices through complete examples, detailed documentation, and hands-on labs.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-1.28+-blue.svg)](https://kubernetes.io/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Learning Paths](#learning-paths)
- [Prerequisites](#prerequisites)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Overview

**K8s-Master-Lab** is a complete learning platform serving as both an educational resource and production-reference implementation. It demonstrates real-world Kubernetes usage patterns across different application types, infrastructure setups, and operational scenarios.

### Key Objectives

✅ **Educational Excellence**: Cover 100% of Kubernetes certification objectives (CKA, CKAD, CKS)  
✅ **Production Ready**: Follow all security and best practices for real-world deployments  
✅ **Hands-On Learning**: 75+ interactive labs from beginner to advanced levels  
✅ **Comprehensive Coverage**: 300+ YAML examples, 50+ Helm charts, 100+ utility scripts  
✅ **Deep Documentation**: 50+ ADRs, deep-dive guides, troubleshooting runbooks

## ✨ Features

### 📚 Comprehensive Examples
- **300+ YAML configurations** covering all Kubernetes resources
- **50+ production-ready Helm charts** for common applications
- **100+ utility scripts** for automation and operations
- **Real-world application patterns** (microservices, ML, batch processing)

### 🎓 Interactive Learning
- **75 hands-on labs** with step-by-step instructions
- **Beginner to advanced** progression path
- **Solutions and explanations** for all exercises
- **Quiz questions** for knowledge validation

### 📖 Deep Documentation
- **50+ Architecture Decision Records** (ADRs)
- **Deep-dive guides** on networking, storage, security, scheduling
- **Best practices** for production deployments
- **Troubleshooting runbooks** for common issues
- **Cheatsheets** for quick reference

### 🔧 Production Tools
- **30+ Grafana dashboards** for monitoring
- **Prometheus alert rules** for proactive monitoring
- **Security scanning** and compliance tools
- **Backup/restore** procedures
- **Performance benchmarking** tools

## 📁 Project Structure

```
k8s-master-lab/
│
├── 01-fundamentals/          # Core Kubernetes concepts
│   ├── 01-pods/              # Pod patterns and lifecycle
│   ├── 02-controllers/       # Deployments, StatefulSets, DaemonSets, Jobs
│   ├── 03-services/          # Services and networking
│   ├── 04-storage/           # Volumes and persistent storage
│   └── 05-configuration/     # ConfigMaps and Secrets
│
├── 02-advanced/              # Advanced Kubernetes features
│   ├── 01-crd-operators/     # Custom Resources and Operators
│   ├── 02-resource-management/ # HPA, VPA, Resource Quotas
│   ├── 03-security/          # RBAC, Security Contexts, Policies
│   ├── 04-networking/        # Network Policies, Service Mesh
│   └── 05-scheduling/        # Advanced scheduling patterns
│
├── 03-patterns/              # Real-world application patterns
│   ├── 01-microservices/     # Complete microservices application
│   ├── 02-ml-platform/       # Machine Learning platform
│   ├── 03-batch-processing/  # Batch processing systems
│   ├── 04-serverless/        # Serverless patterns
│   └── 05-edge-computing/    # Edge computing examples
│
├── 04-tools-ecosystem/       # Kubernetes ecosystem tools
│   ├── 01-monitoring/        # Prometheus, Grafana
│   ├── 02-logging/           # Loki, ELK stack
│   ├── 03-ci-cd/             # Jenkins, Tekton, GitHub Actions
│   ├── 04-gitops/            # ArgoCD, Flux
│   └── 05-service-mesh/      # Istio, Linkerd
│
├── 05-production-ready/      # Production deployment guides
│   ├── 01-cluster-setup/     # Multi-platform cluster setup
│   ├── 02-disaster-recovery/ # Backup and restore
│   ├── 03-security-hardening/ # CIS benchmarks
│   ├── 04-cost-optimization/ # Cost management
│   └── 05-scaling-strategies/ # Scaling patterns
│
├── 06-labs/                  # Interactive hands-on labs
│   ├── beginner/             # 20 beginner labs
│   ├── intermediate/         # 25 intermediate labs
│   └── advanced/             # 30 advanced labs
│
├── documentation/            # Comprehensive documentation
│   ├── architecture-decisions/ # ADRs
│   ├── concepts/             # Deep-dive guides
│   ├── best-practices/       # Production guidelines
│   ├── troubleshooting/      # Common issues and solutions
│   └── cheatsheets/          # Quick references
│
├── helm/                     # Helm chart library
│   ├── common/               # Common library charts
│   ├── databases/            # Database charts
│   ├── monitoring/           # Monitoring stack charts
│   ├── ci-cd/                # CI/CD tool charts
│   └── applications/         # Application templates
│
├── scripts/                  # Utility scripts
│   ├── setup/                # Environment setup
│   ├── monitoring/           # Monitoring helpers
│   ├── security/             # Security scanners
│   ├── backup/               # Backup/restore
│   └── troubleshooting/      # Debug tools
│
├── tests/                    # Testing framework
│   ├── unit/                 # YAML validation
│   ├── integration/          # End-to-end tests
│   ├── performance/          # Load tests
│   └── security/             # Security scans
│
└── monitoring/               # Monitoring configurations
    ├── dashboards/           # Grafana dashboards
    └── alerts/               # Prometheus alerts
```

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/Rajan251/labs
cd lab-k8s
```

### 2. Set Up Your Environment

Choose your preferred Kubernetes environment:

```bash
# Option 1: Minikube (Recommended for beginners)
./scripts/setup/setup-minikube.sh

# Option 2: K3d (Lightweight, fast)
./scripts/setup/setup-k3d.sh

# Option 3: Kind (Kubernetes in Docker)
./scripts/setup/setup-kind.sh
```

See [SETUP.md](SETUP.md) for detailed setup instructions.

### 3. Deploy Your First Example

```bash
# Deploy a simple pod
kubectl apply -f 01-fundamentals/01-pods/examples/basic-pod.yaml

# Verify it's running
kubectl get pods

# View logs
kubectl logs my-first-pod
```

### 4. Start Learning

Begin with the beginner labs:

```bash
cd 06-labs/beginner
cat lab-01-your-first-pod.md
```

## 🎓 Learning Paths

### Path 1: Kubernetes Beginner (CKA Prep)
1. **Fundamentals** → Start with `01-fundamentals/`
2. **Beginner Labs** → Complete `06-labs/beginner/`
3. **Basic Patterns** → Explore simple deployments in `03-patterns/`
4. **Practice** → Deploy examples and modify them

**Estimated Time**: 2-3 weeks

### Path 2: Application Developer (CKAD Prep)
1. **Pods & Controllers** → `01-fundamentals/01-pods/` and `01-fundamentals/02-controllers/`
2. **Configuration** → `01-fundamentals/05-configuration/`
3. **Intermediate Labs** → `06-labs/intermediate/`
4. **Microservices Pattern** → `03-patterns/01-microservices/`

**Estimated Time**: 3-4 weeks

### Path 3: Security Specialist (CKS Prep)
1. **Security Fundamentals** → `02-advanced/03-security/`
2. **Network Policies** → `02-advanced/04-networking/`
3. **Security Hardening** → `05-production-ready/03-security-hardening/`
4. **Advanced Labs** → Security-focused labs in `06-labs/advanced/`

**Estimated Time**: 4-5 weeks

### Path 4: Platform Engineer (Production Focus)
1. **All Fundamentals** → Complete `01-fundamentals/`
2. **Advanced Features** → Complete `02-advanced/`
3. **Production Ready** → Complete `05-production-ready/`
4. **Tools Ecosystem** → `04-tools-ecosystem/`
5. **All Labs** → Complete all 75 labs

**Estimated Time**: 8-10 weeks

## 📋 Prerequisites

### Required Knowledge
- Basic Linux command line
- Understanding of containers (Docker)
- Basic networking concepts
- YAML syntax

### Required Tools
- `kubectl` (v1.28+)
- Docker or Podman
- Git
- Text editor (VS Code recommended)

### Optional Tools
- `helm` (v3.0+)
- `k9s` (Kubernetes CLI UI)
- `kubectx` and `kubens` (context switching)
- `stern` (multi-pod log tailing)

See [SETUP.md](SETUP.md) for installation instructions.

## 📚 Documentation

### Core Concepts
- [Kubernetes Networking Deep Dive](documentation/concepts/networking-deep-dive.md)
- [Storage Complete Guide](documentation/concepts/storage-complete-guide.md)
- [Security Master Guide](documentation/concepts/security-master-guide.md)
- [Scheduling and Resource Management](documentation/concepts/scheduling-resource-management.md)

### Best Practices
- [Application Design](documentation/best-practices/application-design.md)
- [Resource Management](documentation/best-practices/resource-management.md)
- [Security](documentation/best-practices/security.md)
- [Monitoring](documentation/best-practices/monitoring.md)

### Troubleshooting
- [Pod Failures](documentation/troubleshooting/pod-failures.md)
- [Network Issues](documentation/troubleshooting/network-issues.md)
- [Storage Problems](documentation/troubleshooting/storage-problems.md)
- [Performance Degradation](documentation/troubleshooting/performance-degradation.md)

### Cheatsheets
- [kubectl Commands](documentation/cheatsheets/kubectl-commands.md)
- [YAML Syntax](documentation/cheatsheets/yaml-syntax.md)
- [Common Patterns](documentation/cheatsheets/common-patterns.md)
- [Debugging Commands](documentation/cheatsheets/debugging-commands.md)

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on:
- Code of Conduct
- Development process
- How to submit pull requests
- Coding standards


## 🙏 Acknowledgments

- Kubernetes community for excellent documentation
- CNCF projects for ecosystem tools
- Contributors and reviewers

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Rajan251/labs/tree/Dev/lab-k8s)
- **Discussions**: [GitHub Discussions](https://github.com/Rajan251/labs/tree/Dev/lab-k8s/discussions)
- **Documentation**: [Full Documentation](documentation/)

## 🗺️ Roadmap

See [ROADMAP.md](ROADMAP.md) for planned features and improvements.

---

**Happy Learning! 🎉**

*Star ⭐ this repository if you find it helpful!*
