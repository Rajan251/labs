# 🚀 Jenkins Pipeline - Quick Reference Guide

## 📋 Overview

This guide provides quick commands and procedures for using the Jenkins pipeline in production.

---

## 🎯 Quick Commands

### Running Tests Locally

```bash
# Run all tests
./jenkins/scripts/run-tests.sh

# Run with specific markers
./jenkins/scripts/run-tests.sh --markers "unit"
./jenkins/scripts/run-tests.sh --markers "not slow"

# Run with load tests
./jenkins/scripts/run-tests.sh --load-tests

# Run in parallel
./jenkins/scripts/run-tests.sh --parallel

# Custom coverage threshold
./jenkins/scripts/run-tests.sh --coverage 90
```

### Triggering Jenkins Build

```bash
# Via Git push (automatic)
git push origin main

# Via Jenkins CLI
java -jar jenkins-cli.jar -s http://jenkins:8080/ \
  -auth username:token \
  build python-app-pipeline

# Via curl
curl -X POST http://jenkins:8080/job/python-app-pipeline/build \
  --user username:token
```

---

## 📁 File Locations

### In Repository
```
jenkins/
├── Jenkinsfile                      # Main pipeline
├── shared-libraries/                # Groovy utilities
│   └── vars/testUtils.groovy
├── scripts/                         # Helper scripts
│   └── run-tests.sh
├── PRODUCTION_SETUP.md             # Setup guide
└── ADVANCED_TESTING.md             # Testing guide
```

### On Jenkins Server
```
/var/lib/jenkins/
├── jobs/python-app-pipeline/       # Job directory
├── workspace/python-app-pipeline/  # Build workspace
└── shared-libraries/               # Shared libraries
```

### On Application Server
```
/opt/app/
├── current/                        # Current release
├── releases/                       # Previous releases
└── shared/                         # Shared files
    ├── logs/
    └── .env
```

---

## 🔄 Pipeline Stages

| Stage | Duration | Can Fail? | Notes |
|-------|----------|-----------|-------|
| Checkout | 10s | Yes | Gets code from Git |
| Setup Environment | 30s | Yes | Creates venv, installs deps |
| Code Quality | 1-2min | No* | Warnings only |
| Security Scan | 1-2min | No* | Warnings only |
| Unit Tests | 2-5min | Yes | Must pass |
| Integration Tests | 5-10min | Yes | Must pass |
| Coverage Report | 30s | Yes | Must be >80% |
| Load Tests | 5-10min | No* | Optional |
| Build Docker | 2-5min | Yes | Creates image |
| Push Docker | 1-2min | Yes | Uploads to registry |
| Deploy Staging | 1-2min | No* | Auto-deploy |
| Deploy Production | 1-2min | No* | Manual approval |

*Can be configured to fail

---

## 🎨 Pipeline Parameters

When building manually, you can set these parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| ENVIRONMENT | Choice | dev | Target environment |
| RUN_LOAD_TESTS | Boolean | false | Run performance tests |
| SKIP_TESTS | Boolean | false | Skip all tests (NOT RECOMMENDED) |
| LOAD_TEST_USERS | String | 100 | Number of concurrent users |
| LOAD_TEST_DURATION | String | 5m | Test duration |

---

## 📊 Accessing Reports

### During Build
```
Build Page → Console Output
```

### After Build
```
Build Page → Left Sidebar:
├── Test Result (JUnit)
├── Coverage Report (Cobertura)
└── HTML Publisher
    ├── Unit Test Report
    ├── Integration Test Report
    └── Load Test Report
```

### Direct URLs
```
http://jenkins:8080/job/python-app-pipeline/42/testReport/
http://jenkins:8080/job/python-app-pipeline/42/cobertura/
http://jenkins:8080/job/python-app-pipeline/42/HTML_20Report/
```

---

## 🆕 Testing New Features

### 1. Create Feature Branch
```bash
git checkout -b feature/new-feature
```

### 2. Write Tests First (TDD)
```python
# tests/unit/test_new_feature.py
def test_new_feature():
    result = new_feature()
    assert result == expected
```

### 3. Implement Feature
```python
# app/services/new_feature.py
def new_feature():
    return "implemented"
```

### 4. Run Tests Locally
```bash
./jenkins/scripts/run-tests.sh
```

### 5. Commit and Push
```bash
git add .
git commit -m "feat: Add new feature"
git push origin feature/new-feature
```

### 6. Create Pull Request
- Pipeline runs automatically
- Review test results
- Merge after approval

### 7. Deploy
- Merge triggers production pipeline
- Auto-deploy to staging
- Manual approval for production

---

## 🔧 Troubleshooting

### Build Fails at Unit Tests
```bash
# Check test output
Jenkins → Build #42 → Test Result

# Run locally
./jenkins/scripts/run-tests.sh --markers "unit"

# Fix tests and push
git add .
git commit -m "fix: Fix failing tests"
git push
```

### Coverage Below Threshold
```bash
# Check coverage report
Jenkins → Build #42 → Coverage Report

# Identify uncovered code
coverage report --show-missing

# Add tests for uncovered code
```

### Docker Build Fails
```bash
# Check Dockerfile
cat Dockerfile

# Test locally
docker build -t test-image .

# Fix and push
```

### Deployment Fails
```bash
# Check deployment logs
ssh staging-server "docker-compose logs"

# Rollback if needed
ssh staging-server "cd /opt/app && ./rollback.sh"
```

---

## 🔐 Credentials Management

### Adding New Credentials
```
Jenkins → Manage Jenkins → Manage Credentials
→ (global) → Add Credentials

Types:
- Username with password
- SSH Username with private key
- Secret text
- Secret file
```

### Using in Pipeline
```groovy
environment {
    DB_PASSWORD = credentials('db-password')
    DOCKER_CREDS = credentials('docker-hub-credentials')
}
```

---

## 📧 Notifications

### Slack
```groovy
slackSend(
    channel: '#ci-cd',
    color: 'good',
    message: 'Build succeeded!'
)
```

### Email
```groovy
emailext(
    subject: "Build ${env.BUILD_NUMBER}",
    body: "Build completed",
    to: 'team@example.com'
)
```

---

## 🎯 Best Practices

### ✅ DO's
- ✅ Run tests locally before pushing
- ✅ Write tests for new features
- ✅ Keep builds fast (<30 min)
- ✅ Fix failing builds immediately
- ✅ Monitor coverage trends
- ✅ Use meaningful commit messages
- ✅ Review test reports
- ✅ Keep dependencies updated

### ❌ DON'Ts
- ❌ Skip tests (SKIP_TESTS=true)
- ❌ Ignore failing tests
- ❌ Commit untested code
- ❌ Deploy without approval
- ❌ Ignore security warnings
- ❌ Leave flaky tests
- ❌ Commit secrets to repo
- ❌ Bypass code review

---

## 📚 Additional Resources

- [Jenkinsfile](./Jenkinsfile) - Main pipeline definition
- [PRODUCTION_SETUP.md](./PRODUCTION_SETUP.md) - Complete setup guide
- [ADVANCED_TESTING.md](./ADVANCED_TESTING.md) - Advanced testing patterns
- [testUtils.groovy](./shared-libraries/vars/testUtils.groovy) - Shared utilities

---

## 🆘 Getting Help

1. **Check Console Output** - Most errors are visible here
2. **Review Test Reports** - Detailed failure information
3. **Check Documentation** - PRODUCTION_SETUP.md
4. **Ask Team** - Slack #ci-cd channel
5. **Jenkins Logs** - `/var/log/jenkins/jenkins.log`

---

## 📞 Support Contacts

- **CI/CD Team**: cicd-team@example.com
- **DevOps**: devops@example.com
- **Slack**: #ci-cd-support
