# Jenkins CI/CD Implementation

This directory contains the reference implementation for the Jenkins CI/CD Guide.

## Directory Structure

*   `jenkins-shared-lib/`: The Shared Library containing reusable pipeline code (`vars/`) and utility classes (`src/`).
*   `jenkins-infra/`: Infrastructure as Code for Jenkins itself (JCasC, Job DSL, Dockerfile).
*   `my-app-repo/`: An example application repository showing how to consume the Shared Library.

## How to Use

### 1. Test the Shared Library
You can run unit tests for the shared library using Gradle.
```bash
cd jenkins-shared-lib
./gradlew test
```

### 2. Build the Custom Jenkins Image
Build a Jenkins image pre-configured with plugins and JCasC.
```bash
cd jenkins-infra
docker build -t my-jenkins:latest .
```

### 3. Run Jenkins
Run the container (ensure you set `ADMIN_PASSWORD`).
```bash
docker run -d -p 8080:8080 -p 50000:50000 \
  -e ADMIN_PASSWORD=admin \
  --name jenkins \
  my-jenkins:latest
```

### 4. Configure Seed Job
Once Jenkins is up, the `seed-job` defined in `jenkins.yaml` will be created. Run it to generate the pipelines defined in `jobs/seed.groovy`.

## Files Overview
*   `jenkins-shared-lib/vars/ciPipeline.groovy`: The main pipeline wrapper used by apps.
*   `jenkins-infra/jenkins.yaml`: Configuration as Code file defining system settings.
*   `my-app-repo/Jenkinsfile`: Shows how simple the pipeline definition becomes for developers.
