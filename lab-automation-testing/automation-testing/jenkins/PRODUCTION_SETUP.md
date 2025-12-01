# 🏢 Production Environment Setup Guide

## 📁 Complete File Structure for Production

```
production-deployment/
├── app/                              # Application code
│   ├── api/                          # API endpoints
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── users.py
│   │   │   ├── items.py
│   │   │   └── auth.py
│   │   └── dependencies.py
│   ├── core/                         # Core functionality
│   │   ├── __init__.py
│   │   ├── config.py                # Configuration
│   │   ├── security.py              # Security utilities
│   │   └── database.py              # Database connection
│   ├── models/                       # Data models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── item.py
│   ├── services/                     # Business logic
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   └── item_service.py
│   ├── schemas/                      # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── item.py
│   └── main.py                       # Application entry point
│
├── tests/                            # Test suite
│   ├── unit/                         # Unit tests
│   │   ├── test_models.py
│   │   ├── test_services.py
│   │   └── test_utils.py
│   ├── integration/                  # Integration tests
│   │   ├── test_api.py
│   │   ├── test_database.py
│   │   └── test_auth.py
│   ├── e2e/                         # End-to-end tests
│   │   └── test_user_flows.py
│   ├── performance/                  # Performance tests
│   │   └── load_tests.py
│   ├── fixtures/                     # Test fixtures
│   │   ├── conftest.py
│   │   └── factories.py
│   └── utils/                        # Test utilities
│       └── helpers.py
│
├── jenkins/                          # Jenkins CI/CD
│   ├── Jenkinsfile                  # Main pipeline
│   ├── Jenkinsfile.feature          # Feature branch pipeline
│   ├── Jenkinsfile.release          # Release pipeline
│   ├── shared-libraries/            # Shared Groovy libraries
│   │   └── vars/
│   │       ├── testUtils.groovy
│   │       ├── deployUtils.groovy
│   │       └── notificationUtils.groovy
│   ├── scripts/                     # Helper scripts
│   │   ├── setup-env.sh
│   │   ├── run-tests.sh
│   │   └── deploy.sh
│   └── configs/                     # Jenkins configurations
│       ├── credentials.xml
│       └── plugins.txt
│
├── docker/                           # Docker configuration
│   ├── Dockerfile                   # Production Dockerfile
│   ├── Dockerfile.dev               # Development Dockerfile
│   ├── docker-compose.yml           # Local development
│   ├── docker-compose.test.yml      # Testing environment
│   ├── docker-compose.prod.yml      # Production environment
│   └── .dockerignore
│
├── kubernetes/                       # Kubernetes manifests
│   ├── base/                        # Base configurations
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── configmap.yaml
│   │   └── secret.yaml
│   ├── overlays/                    # Environment-specific
│   │   ├── dev/
│   │   │   └── kustomization.yaml
│   │   ├── staging/
│   │   │   └── kustomization.yaml
│   │   └── production/
│   │       └── kustomization.yaml
│   └── helm/                        # Helm charts
│       └── app/
│           ├── Chart.yaml
│           ├── values.yaml
│           ├── values-dev.yaml
│           ├── values-staging.yaml
│           ├── values-prod.yaml
│           └── templates/
│
├── scripts/                          # Utility scripts
│   ├── setup/
│   │   ├── install-dependencies.sh
│   │   └── setup-database.sh
│   ├── deployment/
│   │   ├── deploy-staging.sh
│   │   ├── deploy-production.sh
│   │   └── rollback.sh
│   ├── testing/
│   │   ├── run-all-tests.sh
│   │   ├── run-unit-tests.sh
│   │   ├── run-integration-tests.sh
│   │   └── run-load-tests.sh
│   └── maintenance/
│       ├── backup-database.sh
│       └── cleanup.sh
│
├── config/                           # Configuration files
│   ├── environments/
│   │   ├── .env.dev
│   │   ├── .env.staging
│   │   └── .env.production
│   ├── nginx/
│   │   ├── nginx.conf
│   │   └── ssl/
│   └── monitoring/
│       ├── prometheus.yml
│       └── grafana-dashboards/
│
├── docs/                             # Documentation
│   ├── api/
│   │   └── openapi.yaml
│   ├── architecture/
│   │   ├── system-design.md
│   │   └── diagrams/
│   ├── deployment/
│   │   ├── deployment-guide.md
│   │   └── rollback-procedure.md
│   └── testing/
│       ├── testing-strategy.md
│       └── test-coverage-report.md
│
├── .github/                          # GitHub Actions (alternative)
│   └── workflows/
│       ├── ci.yml
│       ├── cd.yml
│       └── release.yml
│
├── .gitlab-ci.yml                    # GitLab CI (alternative)
├── pytest.ini                        # Pytest configuration
├── requirements.txt                  # Production dependencies
├── requirements-dev.txt              # Development dependencies
├── requirements-test.txt             # Testing dependencies
├── setup.py                          # Package setup
├── pyproject.toml                    # Project configuration
├── .env.example                      # Environment variables template
├── .gitignore
└── README.md
```

---

## 📍 Where to Place Files in Production

### 1. **Application Server**
```
/opt/app/                            # Main application directory
├── current/                         # Current release (symlink)
├── releases/                        # Previous releases
│   ├── 2024-12-01-123456/
│   ├── 2024-12-01-234567/
│   └── 2024-12-02-012345/
├── shared/                          # Shared files across releases
│   ├── logs/
│   ├── uploads/
│   └── .env
└── repo/                            # Git repository
```

### 2. **Jenkins Server**
```
/var/lib/jenkins/
├── jobs/
│   └── python-app/
│       ├── builds/
│       └── workspace/
├── workspace/
│   └── python-app/                  # Build workspace
└── shared-libraries/                # Shared Groovy libraries
    └── testUtils/
```

### 3. **Test Environment**
```
/opt/test/
├── app/                             # Test application
├── data/                            # Test data
└── reports/                         # Test reports
    ├── coverage/
    ├── junit/
    └── load-tests/
```

---

## 🚀 Step-by-Step CI/CD Pipeline Setup

### Step 1: Jenkins Installation and Configuration

#### 1.1 Install Jenkins
```bash
# On Ubuntu/Debian
wget -q -O - https://pkg.jenkins.io/debian-stable/jenkins.io.key | sudo apt-key add -
sudo sh -c 'echo deb https://pkg.jenkins.io/debian-stable binary/ > /etc/apt/sources.list.d/jenkins.list'
sudo apt update
sudo apt install jenkins

# Start Jenkins
sudo systemctl start jenkins
sudo systemctl enable jenkins
```

#### 1.2 Install Required Plugins
```bash
# Access Jenkins at http://your-server:8080
# Install these plugins:
- Pipeline
- Docker Pipeline
- Git
- GitHub Integration
- Slack Notification
- HTML Publisher
- Cobertura Plugin
- JUnit Plugin
- Blue Ocean (optional, for better UI)
```

#### 1.3 Configure Jenkins Credentials
```
Jenkins Dashboard → Manage Jenkins → Manage Credentials

Add the following credentials:
1. GitHub/GitLab credentials (SSH key or token)
2. Docker Hub credentials
3. Database credentials
4. Slack webhook URL
5. SSH keys for deployment servers
```

### Step 2: Create Jenkins Pipeline Job

#### 2.1 Create New Pipeline Job
```
1. Jenkins Dashboard → New Item
2. Enter name: "python-app-pipeline"
3. Select "Pipeline"
4. Click OK
```

#### 2.2 Configure Pipeline
```groovy
Pipeline Definition:
- Select "Pipeline script from SCM"
- SCM: Git
- Repository URL: https://github.com/your-org/your-repo.git
- Credentials: Select your GitHub credentials
- Branch: */main
- Script Path: jenkins/Jenkinsfile
```

#### 2.3 Configure Build Triggers
```
✅ GitHub hook trigger for GITScm polling
✅ Poll SCM: H/5 * * * * (every 5 minutes)
```

### Step 3: Setup Shared Libraries

#### 3.1 Create Shared Library Repository
```bash
# Create a new repository for shared libraries
mkdir jenkins-shared-libraries
cd jenkins-shared-libraries

# Create structure
mkdir -p vars src resources

# Add testUtils.groovy to vars/
cp /path/to/testUtils.groovy vars/

# Commit and push
git init
git add .
git commit -m "Add shared libraries"
git push origin main
```

#### 3.2 Configure Shared Library in Jenkins
```
Jenkins Dashboard → Manage Jenkins → Configure System
→ Global Pipeline Libraries

Add:
- Name: testUtils
- Default version: main
- Retrieval method: Modern SCM
- Source Code Management: Git
- Project Repository: https://github.com/your-org/jenkins-shared-libraries.git
```

### Step 4: Configure Webhooks

#### 4.1 GitHub Webhook
```
GitHub Repository → Settings → Webhooks → Add webhook

Payload URL: http://your-jenkins-server:8080/github-webhook/
Content type: application/json
Events: Just the push event
Active: ✅
```

#### 4.2 GitLab Webhook
```
GitLab Project → Settings → Webhooks

URL: http://your-jenkins-server:8080/project/python-app-pipeline
Trigger: Push events, Merge request events
SSL verification: Enable
```

### Step 5: Setup Test Environment

#### 5.1 Install Dependencies on Jenkins Agent
```bash
# Install Python
sudo apt install python3.11 python3.11-venv python3-pip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker jenkins

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### 5.2 Setup Test Database
```bash
# Create PostgreSQL container for testing
docker run -d --name postgres-test \
  --restart always \
  -e POSTGRES_USER=testuser \
  -e POSTGRES_PASSWORD=testpass \
  -e POSTGRES_DB=testdb \
  -p 5432:5432 \
  postgres:15
```

### Step 6: Configure Deployment Servers

#### 6.1 Staging Server Setup
```bash
# On staging server
sudo mkdir -p /opt/app/{current,releases,shared}
sudo chown -R deploy:deploy /opt/app

# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Setup SSH access from Jenkins
# Add Jenkins public key to ~/.ssh/authorized_keys
```

#### 6.2 Production Server Setup
```bash
# Same as staging, but with additional security
# Setup firewall rules
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Install monitoring tools
# Setup log aggregation
```

---

## 🔄 Running the Pipeline

### Method 1: Automatic (Webhook Trigger)
```bash
# Simply push code to repository
git add .
git commit -m "Add new feature"
git push origin main

# Pipeline will automatically trigger
```

### Method 2: Manual Trigger
```
1. Go to Jenkins Dashboard
2. Click on "python-app-pipeline"
3. Click "Build with Parameters"
4. Select options:
   - ENVIRONMENT: staging/production
   - RUN_LOAD_TESTS: true/false
5. Click "Build"
```

### Method 3: CLI Trigger
```bash
# Using Jenkins CLI
java -jar jenkins-cli.jar -s http://jenkins-server:8080/ \
  -auth username:token \
  build python-app-pipeline \
  -p ENVIRONMENT=staging \
  -p RUN_LOAD_TESTS=true
```

---

## 📊 Monitoring Pipeline Execution

### View Build Progress
```
1. Jenkins Dashboard → python-app-pipeline
2. Click on build number (e.g., #42)
3. View:
   - Console Output (real-time logs)
   - Test Results
   - Coverage Report
   - Load Test Report
```

### Access Reports
```
Build Page → Left Sidebar:
- Test Result
- Coverage Report
- HTML Publisher Reports
  - Unit Test Report
  - Integration Test Report
  - Load Test Report
```

---

## 🎯 Pipeline Stages Explained

| Stage | Duration | Purpose | Failure Impact |
|-------|----------|---------|----------------|
| Checkout | 10s | Get latest code | Pipeline stops |
| Setup Environment | 30s | Install dependencies | Pipeline stops |
| Code Quality | 1-2min | Linting, formatting | Warning only |
| Security Scan | 1-2min | Vulnerability check | Warning only |
| Unit Tests | 2-5min | Fast isolated tests | Pipeline stops |
| Integration Tests | 5-10min | Database, API tests | Pipeline stops |
| Coverage Report | 30s | Check coverage | Stops if <80% |
| Load Tests | 5-10min | Performance testing | Warning only |
| Build Docker | 2-5min | Create container | Pipeline stops |
| Push Docker | 1-2min | Upload to registry | Pipeline stops |
| Deploy Staging | 1-2min | Deploy to staging | Warning only |
| Deploy Production | 1-2min | Deploy to prod | Requires approval |

**Total Duration**: ~20-40 minutes (without load tests: ~15-25 minutes)

---

## 📝 Environment Variables

Create `.env` files for each environment:

### `.env.dev`
```bash
ENVIRONMENT=development
DEBUG=True
DATABASE_URL=postgresql://user:pass@localhost:5432/devdb
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=dev-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1
```

### `.env.staging`
```bash
ENVIRONMENT=staging
DEBUG=False
DATABASE_URL=postgresql://user:pass@staging-db:5432/stagingdb
REDIS_URL=redis://staging-redis:6379/0
SECRET_KEY=${STAGING_SECRET_KEY}
ALLOWED_HOSTS=staging.example.com
```

### `.env.production`
```bash
ENVIRONMENT=production
DEBUG=False
DATABASE_URL=postgresql://user:pass@prod-db:5432/proddb
REDIS_URL=redis://prod-redis:6379/0
SECRET_KEY=${PRODUCTION_SECRET_KEY}
ALLOWED_HOSTS=example.com,www.example.com
```

---

## 🔐 Security Best Practices

1. **Never commit secrets** - Use Jenkins credentials
2. **Use environment variables** - For configuration
3. **Scan dependencies** - Use Safety, Bandit
4. **Scan Docker images** - Use Trivy
5. **Use HTTPS** - For all communications
6. **Rotate credentials** - Regularly update passwords
7. **Limit access** - Use role-based access control
8. **Audit logs** - Monitor all activities

---

## 📚 Next Steps

1. Review the Jenkinsfile
2. Setup Jenkins server
3. Configure credentials
4. Create pipeline job
5. Test with a simple commit
6. Monitor execution
7. Review reports
8. Deploy to staging
9. Test staging environment
10. Deploy to production (with approval)
