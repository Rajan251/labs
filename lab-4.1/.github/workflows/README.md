# Additional Workflow Examples

This directory contains additional workflow examples for specific use cases.

## Available Workflows

### 1. Node.js Workflow
- **File**: `nodejs-ci.yml`
- **Purpose**: Build and test Node.js applications
- **Features**: Multi-version testing, caching, coverage reports

### 2. Python Workflow
- **File**: `python-ci.yml`
- **Purpose**: Build and test Python applications
- **Features**: Multiple Python versions, pytest, coverage

### 3. Docker Workflow
- **File**: `docker-build.yml`
- **Purpose**: Build and push Docker images
- **Features**: Multi-platform builds, layer caching, security scanning

### 4. Kubernetes Deployment
- **File**: `k8s-deploy.yml`
- **Purpose**: Deploy to Kubernetes clusters
- **Features**: Helm support, rollback on failure, smoke tests

## Usage

Copy the desired workflow to your `.github/workflows/` directory:

```bash
cp .github/workflows/examples/nodejs-ci.yml .github/workflows/
```

Customize the workflow for your specific needs.
