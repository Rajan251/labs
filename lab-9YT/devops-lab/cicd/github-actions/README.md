# GitHub Actions Lab

## 1. Introduction
**GitHub Actions** makes it easy to automate all your software workflows, now with world-class CI/CD.

## 2. Lab Setup

Since GitHub Actions runs on GitHub, this lab provides a sample workflow file you can add to any repository.

### Step 1: Create Workflow File
Create `.github/workflows/ci.yaml` in your repository.

### Step 2: Sample Workflow
See `sample-workflow.yaml`.

### Step 3: Self-Hosted Runner (Advanced)
You can run actions on your own Kubernetes cluster.
1.  Go to Repo Settings > Actions > Runners > New self-hosted runner.
2.  Follow instructions to download and run the runner agent in a pod.
