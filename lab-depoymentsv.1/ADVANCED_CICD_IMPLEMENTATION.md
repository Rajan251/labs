# Advanced CI/CD Implementation Guide

This guide provides step-by-step instructions, file structures, and implementation details for the Advanced CI/CD patterns included in this repository.

---

## 1. Advanced GitHub Actions

### File Structure
```
03-cicd-deployment/github-actions-advanced/
├── .github/
│   └── workflows/
│       ├── main-workflow.yml    # Primary pipeline (Matrix, Caching, Security)
│       └── reusable-build.yml   # Reusable workflow template
```

### Implementation Steps

#### Step 1: Configure Secrets
In your GitHub Repository, go to **Settings > Secrets and variables > Actions** and add:
- `DOCKER_REGISTRY`: Your registry URL (e.g., `ghcr.io`).
- `DOCKER_USERNAME`: Your registry username.
- `DOCKER_PASSWORD`: Your registry token/password.
- `GITOPS_TOKEN`: A Personal Access Token (PAT) with repo permissions (for the GitOps trigger step).

#### Step 2: Understand the Workflow (`main-workflow.yml`)
1.  **Concurrency**: The `concurrency` block ensures that if you push a new commit to a PR, the previous running build is cancelled to save resources.
2.  **Caching**: `cache: 'pip'` in the setup-python step automatically caches your Python dependencies.
3.  **Matrix Strategy**: The `test` job runs 3 times in parallel for Python 3.8, 3.9, and 3.10.
4.  **Security Scanning**: The `security-scan` job builds the image and runs **Trivy**. If "Critical" vulnerabilities are found, the build fails.
5.  **GitOps Trigger**: The final step updates a separate "Config Repo" (GitOps) with the new image tag.

#### Step 3: Run the Pipeline
- Push code to `main` or open a Pull Request.
- Go to the **Actions** tab in GitHub to visualize the Matrix build and Security Scan results.

---

## 2. Advanced GitLab CI

### File Structure
```
03-cicd-deployment/gitlab-ci-advanced/
└── .gitlab-ci.yml    # Complete pipeline definition
```

### Implementation Steps

#### Step 1: Configure Variables
In GitLab, go to **Settings > CI/CD > Variables** and add:
- `CI_REGISTRY_USER` / `CI_REGISTRY_PASSWORD`: (Usually provided automatically by GitLab, but needed if using external registry).
- `KUBE_CONFIG`: Your Kubernetes cluster configuration (for deploying Review Apps).

#### Step 2: Enable Shared Runners
Ensure your project has access to GitLab Shared Runners (with Docker-in-Docker support) or configure your own runner.

#### Step 3: Dynamic Environments (Review Apps)
- When you open a **Merge Request**, the `deploy_review` job triggers.
- It creates a **new namespace** in Kubernetes: `review-<mr-id>`.
- It deploys your app there and provides a link in the MR UI.
- When the MR is merged or closed, the `stop_review` job runs automatically to delete the namespace.

#### Step 4: Security Scanning
- The pipeline includes templates: `Security/SAST.gitlab-ci.yml` and `Secret-Detection.gitlab-ci.yml`.
- GitLab will automatically scan your code and report vulnerabilities in the "Security" tab of the pipeline.

---

## 3. Advanced Jenkins

### File Structure
```
03-cicd-deployment/jenkins-advanced/
└── Jenkinsfile    # Declarative pipeline using Shared Libraries
```

### Implementation Steps

#### Step 1: Configure Shared Library
1.  Create a separate Git repo for your shared library (e.g., `my-jenkins-lib`).
2.  Structure it as:
    ```
    vars/
      trivyScan.groovy
      deployToK8s.groovy
    ```
3.  In Jenkins, go to **Manage Jenkins > Configure System > Global Pipeline Libraries**.
4.  Add a library named `my-shared-library` pointing to your Git repo.

#### Step 2: Configure Docker Agent
- Ensure your Jenkins agent has **Docker installed**.
- The `agent { docker { ... } }` block will spin up a Python container for the build steps, keeping your host clean.

#### Step 3: Run the Pipeline
- Create a "Multibranch Pipeline" project in Jenkins.
- Point it to your application repository.
- Jenkins will detect the `Jenkinsfile` and create the pipeline.
- The **Parallel Stages** will run Lint, Unit Tests, and Security Scan at the same time.
- The **Approval** stage will pause the pipeline and wait for your manual click to proceed to Production.

---

## Summary of Key Features

| Feature | GitHub Actions | GitLab CI | Jenkins |
| :--- | :--- | :--- | :--- |
| **Parallel Testing** | Matrix Strategy | `parallel` keyword | `parallel` block |
| **Security Scan** | Trivy Action | Built-in Templates | Trivy CLI (in Docker) |
| **Caching** | `setup-python` cache | `cache` keyword | Plugins / Volume mounts |
| **Environments** | Deployments API | Dynamic Environments | `input` step (Manual) |
| **Reusability** | Reusable Workflows | `include` / `extends` | Shared Libraries |
