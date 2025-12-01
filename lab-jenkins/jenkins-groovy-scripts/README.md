# Production-Ready Jenkins Groovy Scripts

This repository contains **production-grade** Jenkins CI/CD pipeline scripts organized by approach. All scripts are heavily commented and ready to use in modern production environments.

## 📁 Directory Structure

```
jenkins-groovy-scripts/
├── shared-library/              # ⭐ MOST POPULAR (80% of teams)
│   ├── vars/
│   │   ├── standardPipeline.groovy      # Main reusable pipeline
│   │   ├── deployApp.groovy             # Deployment helper
│   │   ├── notifySlack.groovy           # Notification helper
│   │   └── rollbackApp.groovy           # Rollback helper
│   └── src/org/company/
│       ├── Docker.groovy                # Docker utility class
│       └── K8s.groovy                   # Kubernetes utility class
│
├── declarative-pipelines/       # 70% of modern teams
│   ├── nodejs-declarative.groovy        # Node.js app pipeline
│   └── python-fastapi-declarative.groovy # FastAPI app pipeline
│
├── scripted-pipelines/          # 20% of teams (complex logic)
│   └── advanced-scripted.groovy         # Advanced scripted pipeline
│
├── multibranch-pipelines/       # Auto-discovery pipelines
│   └── multibranch-config.groovy        # Multibranch configuration
│
├── parameterized-pipelines/     # Manual/flexible deployments
│   └── parameterized-deploy.groovy      # Parameterized pipeline
│
├── deployment-strategies/       # Deployment patterns
│   ├── blue-green-deployment.groovy     # Blue-Green strategy
│   └── canary-deployment.groovy         # Canary strategy
│
└── utility-scripts/             # Helper scripts
    └── (additional utilities)
```

## 🚀 Quick Start

### 1. Shared Library Approach (Recommended)

**Step 1**: Upload `shared-library/` to a Git repository (e.g., `https://github.com/your-org/jenkins-shared-library`)

**Step 2**: Register in Jenkins:
- Go to: **Manage Jenkins** → **Configure System** → **Global Pipeline Libraries**
- Add:
  - Name: `jenkins-shared-library`
  - Default version: `main`
  - Retrieval method: Modern SCM → Git
  - Project Repository: `https://github.com/your-org/jenkins-shared-library`

**Step 3**: Use in your app's `Jenkinsfile`:

```groovy
@Library('jenkins-shared-library@main') _

standardPipeline(
    appName: 'my-app',
    buildTool: 'npm',
    dockerRegistry: 'registry.company.com',
    deployEnvs: ['dev', 'qa', 'prod']
)
```

**That's it!** The shared library handles everything.

### 2. Declarative Pipeline Approach

Copy `declarative-pipelines/nodejs-declarative.groovy` to your repo as `Jenkinsfile`.

### 3. Scripted Pipeline Approach

Copy `scripted-pipelines/advanced-scripted.groovy` to your repo as `Jenkinsfile`.

## 📋 Script Descriptions

### Shared Library Scripts

| File | Purpose | Use Case |
|------|---------|----------|
| `standardPipeline.groovy` | Main reusable pipeline template | All microservices |
| `deployApp.groovy` | Deployment with multiple strategies | Rolling, Blue-Green, Canary |
| `notifySlack.groovy` | Send Slack notifications | Build status alerts |
| `rollbackApp.groovy` | Automated rollback | Production failures |
| `Docker.groovy` | Docker operations utility | Build, push, scan images |
| `K8s.groovy` | Kubernetes operations utility | Deploy, rollback, scale |

### Declarative Pipelines

| File | Framework | Features |
|------|-----------|----------|
| `nodejs-declarative.groovy` | Node.js | npm, Docker, K8s deployment |
| `python-fastapi-declarative.groovy` | FastAPI | pytest, coverage, async tests |

### Scripted Pipelines

| File | Purpose | Features |
|------|---------|----------|
| `advanced-scripted.groovy` | Complex logic | Dynamic stages, auto-detection |

### Deployment Strategies

| File | Strategy | Description |
|------|----------|-------------|
| `blue-green-deployment.groovy` | Blue-Green | Zero downtime, instant rollback |
| `canary-deployment.groovy` | Canary | Gradual rollout with monitoring |

## 🎯 Which Approach to Use?

### Use Shared Library When:
✅ You have multiple microservices  
✅ You want standardized pipelines  
✅ You need easy updates across all projects  
✅ **Recommended for 80% of teams**

### Use Declarative Pipeline When:
✅ Simple, straightforward CI/CD  
✅ No shared library setup  
✅ Single project or small team

### Use Scripted Pipeline When:
✅ Complex conditional logic  
✅ Dynamic stage generation  
✅ Advanced Groovy scripting needed

### Use Multibranch Pipeline When:
✅ Feature branch workflows  
✅ Auto-discovery of branches  
✅ PR-based development

### Use Parameterized Pipeline When:
✅ Manual deployments  
✅ Hotfix releases  
✅ Custom build configurations

## 🔧 Configuration Requirements

### Jenkins Plugins Required:
- Pipeline
- Docker Pipeline
- Kubernetes
- Slack Notification
- Git
- Credentials Binding

### Credentials to Add:
1. **Docker Registry**: `docker-creds` (Username/Password)
2. **Kubernetes**: `kubeconfig` (Secret File)
3. **Slack**: `slack-token` (Secret Text)

### Environment Setup:
- Docker installed on Jenkins agents
- kubectl configured with cluster access
- SonarQube server (optional)
- Slack workspace webhook

## 📊 Production Best Practices

### ✅ DO:
- Use shared libraries for consistency
- Always run tests before deployment
- Implement approval gates for production
- Use Blue-Green for critical services
- Monitor deployments with health checks
- Set up automated rollback on failure

### ❌ DON'T:
- Hardcode secrets in pipelines
- Skip tests in production deployments
- Deploy without approval gates
- Ignore security scans
- Deploy without rollback plan

## 🔄 Deployment Strategy Comparison

| Strategy | Downtime | Rollback Speed | Complexity | Best For |
|----------|----------|----------------|------------|----------|
| **Rolling** | None | Medium | Low | Stateless apps |
| **Blue-Green** | None | Instant | Medium | Critical services |
| **Canary** | None | Fast | High | High-risk changes |

## 📝 Example Usage

### Node.js App with Shared Library

```groovy
// Jenkinsfile
@Library('jenkins-shared-library@main') _

standardPipeline(
    appName: 'my-nodejs-app',
    buildTool: 'npm',
    dockerRegistry: 'registry.company.com',
    deployEnvs: ['dev', 'qa', 'prod']
)
```

### FastAPI App with Custom Pipeline

```groovy
// Jenkinsfile
@Library('jenkins-shared-library@main') _

pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                sh 'pip install -r requirements.txt'
            }
        }
        stage('Deploy') {
            steps {
                deployApp(
                    appName: 'my-fastapi-app',
                    environment: 'prod',
                    version: env.BUILD_NUMBER,
                    strategy: 'blue-green'
                )
            }
        }
    }
}
```

## 🛠️ Customization

All scripts are designed to be customizable. Key parameters:

- `appName`: Your application name
- `buildTool`: `npm`, `maven`, `gradle`, `python`
- `dockerRegistry`: Your Docker registry URL
- `deployEnvs`: List of environments (`dev`, `qa`, `prod`)
- `strategy`: `rolling`, `blue-green`, `canary`

## 📚 Additional Resources

- [Jenkins Pipeline Documentation](https://www.jenkins.io/doc/book/pipeline/)
- [Kubernetes Deployment Strategies](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

## 🤝 Contributing

Feel free to customize these scripts for your organization's needs.

## 📄 License

These scripts are provided as production-ready examples for educational and commercial use.

---

**Created for modern DevOps teams** 🚀
