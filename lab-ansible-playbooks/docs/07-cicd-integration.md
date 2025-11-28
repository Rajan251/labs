# CI/CD Integration

This document provides comprehensive CI/CD integration examples for Ansible, including GitHub Actions, GitLab CI, Jenkins, and Azure DevOps pipelines.

## Table of Contents

1. [GitHub Actions](#github-actions)
2. [GitLab CI/CD](#gitlab-cicd)
3. [Jenkins Pipeline](#jenkins-pipeline)
4. [Azure DevOps](#azure-devops)
5. [Best Practices](#best-practices)

---

## GitHub Actions

### Complete Workflow

```yaml
# .github/workflows/ansible-ci.yml
name: Ansible CI/CD Pipeline

on:
  push:
    branches: [ main, develop, 'feature/**' ]
  pull_request:
    branches: [ main, develop ]
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to deploy'
        required: true
        type: choice
        options:
          - development
          - staging
          - production

env:
  ANSIBLE_FORCE_COLOR: 'true'
  ANSIBLE_HOST_KEY_CHECKING: 'false'

jobs:
  # ========================================
  # Lint and Validate
  # ========================================
  lint:
    name: Lint Ansible Code
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          pip install ansible ansible-lint yamllint
          ansible-galaxy install -r requirements.yml
      
      - name: Run yamllint
        run: yamllint .
      
      - name: Run ansible-lint
        run: ansible-lint playbooks/*.yml
      
      - name: Syntax check
        run: |
          find playbooks/ -name "*.yml" -exec ansible-playbook {} --syntax-check \;

  # ========================================
  # Security Scan
  # ========================================
  security:
    name: Security Scan
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'config'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'
      
      - name: Upload Trivy results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'

  # ========================================
  # Test in Docker
  # ========================================
  test:
    name: Test Playbooks
    runs-on: ubuntu-latest
    needs: [lint]
    strategy:
      matrix:
        os: [ubuntu2004, ubuntu2204, debian11]
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install ansible molecule molecule-docker docker
      
      - name: Test with Molecule
        run: |
          molecule test
        env:
          MOLECULE_DISTRO: ${{ matrix.os }}

  # ========================================
  # Deploy to Development
  # ========================================
  deploy-dev:
    name: Deploy to Development
    runs-on: ubuntu-latest
    needs: [lint, test]
    if: github.ref == 'refs/heads/develop'
    environment:
      name: development
      url: https://dev.example.com
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install Ansible
        run: |
          pip install ansible
          ansible-galaxy install -r requirements.yml
      
      - name: Configure SSH
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/ansible_key
          chmod 600 ~/.ssh/ansible_key
          ssh-keyscan -H ${{ secrets.DEV_HOST }} >> ~/.ssh/known_hosts
      
      - name: Create vault password file
        run: echo "${{ secrets.ANSIBLE_VAULT_PASSWORD }}" > .vault_pass
      
      - name: Run playbook
        run: |
          ansible-playbook playbooks/site.yml \
            -i inventories/development/hosts \
            --vault-password-file .vault_pass \
            -v
      
      - name: Cleanup
        if: always()
        run: |
          rm -f ~/.ssh/ansible_key .vault_pass

  # ========================================
  # Deploy to Staging
  # ========================================
  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: [lint, test]
    if: github.ref == 'refs/heads/main'
    environment:
      name: staging
      url: https://staging.example.com
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install Ansible
        run: |
          pip install ansible
          ansible-galaxy install -r requirements.yml
      
      - name: Configure SSH
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/ansible_key
          chmod 600 ~/.ssh/ansible_key
      
      - name: Create vault password file
        run: echo "${{ secrets.ANSIBLE_VAULT_PASSWORD }}" > .vault_pass
      
      - name: Run playbook
        run: |
          ansible-playbook playbooks/site.yml \
            -i inventories/staging/hosts \
            --vault-password-file .vault_pass \
            -v

  # ========================================
  # Deploy to Production
  # ========================================
  deploy-prod:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: [lint, test, deploy-staging]
    if: github.ref == 'refs/heads/main'
    environment:
      name: production
      url: https://example.com
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install Ansible
        run: |
          pip install ansible
          ansible-galaxy install -r requirements.yml
      
      - name: Configure SSH
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/ansible_key
          chmod 600 ~/.ssh/ansible_key
      
      - name: Create vault password file
        run: echo "${{ secrets.ANSIBLE_VAULT_PASSWORD }}" > .vault_pass
      
      - name: Dry run
        run: |
          ansible-playbook playbooks/site.yml \
            -i inventories/production/hosts \
            --vault-password-file .vault_pass \
            --check \
            --diff
      
      - name: Deploy to production
        run: |
          ansible-playbook playbooks/site.yml \
            -i inventories/production/hosts \
            --vault-password-file .vault_pass \
            -v
      
      - name: Notify Slack
        if: always()
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: 'Production deployment ${{ job.status }}'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

---

## GitLab CI/CD

### Complete Pipeline

```yaml
# .gitlab-ci.yml
stages:
  - validate
  - test
  - deploy-dev
  - deploy-staging
  - deploy-prod

variables:
  ANSIBLE_FORCE_COLOR: "true"
  ANSIBLE_HOST_KEY_CHECKING: "false"
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip

# ========================================
# Templates
# ========================================
.ansible_base:
  image: python:3.10
  before_script:
    - pip install ansible ansible-lint yamllint
    - ansible-galaxy install -r requirements.yml

.deploy_template:
  extends: .ansible_base
  before_script:
    - pip install ansible
    - ansible-galaxy install -r requirements.yml
    - mkdir -p ~/.ssh
    - echo "$SSH_PRIVATE_KEY" > ~/.ssh/ansible_key
    - chmod 600 ~/.ssh/ansible_key
    - echo "$ANSIBLE_VAULT_PASSWORD" > .vault_pass

# ========================================
# Validate Stage
# ========================================
yamllint:
  stage: validate
  extends: .ansible_base
  script:
    - yamllint .
  only:
    - branches

ansible-lint:
  stage: validate
  extends: .ansible_base
  script:
    - ansible-lint playbooks/*.yml
  only:
    - branches

syntax-check:
  stage: validate
  extends: .ansible_base
  script:
    - find playbooks/ -name "*.yml" -exec ansible-playbook {} --syntax-check \;
  only:
    - branches

# ========================================
# Test Stage
# ========================================
molecule-test:
  stage: test
  image: python:3.10
  services:
    - docker:dind
  variables:
    DOCKER_HOST: tcp://docker:2375
  before_script:
    - pip install ansible molecule molecule-docker docker
  script:
    - molecule test
  only:
    - branches

# ========================================
# Deploy Development
# ========================================
deploy:development:
  stage: deploy-dev
  extends: .deploy_template
  script:
    - ansible-playbook playbooks/site.yml
        -i inventories/development/hosts
        --vault-password-file .vault_pass
        -v
  environment:
    name: development
    url: https://dev.example.com
  only:
    - develop
  when: on_success

# ========================================
# Deploy Staging
# ========================================
deploy:staging:
  stage: deploy-staging
  extends: .deploy_template
  script:
    - ansible-playbook playbooks/site.yml
        -i inventories/staging/hosts
        --vault-password-file .vault_pass
        -v
  environment:
    name: staging
    url: https://staging.example.com
  only:
    - main
  when: on_success

# ========================================
# Deploy Production
# ========================================
deploy:production:
  stage: deploy-prod
  extends: .deploy_template
  script:
    # Dry run first
    - ansible-playbook playbooks/site.yml
        -i inventories/production/hosts
        --vault-password-file .vault_pass
        --check --diff
    # Actual deployment
    - ansible-playbook playbooks/site.yml
        -i inventories/production/hosts
        --vault-password-file .vault_pass
        -v
  environment:
    name: production
    url: https://example.com
  only:
    - main
  when: manual
  allow_failure: false
```

---

## Jenkins Pipeline

### Jenkinsfile

```groovy
// Jenkinsfile
pipeline {
    agent any
    
    environment {
        ANSIBLE_FORCE_COLOR = 'true'
        ANSIBLE_HOST_KEY_CHECKING = 'false'
    }
    
    parameters {
        choice(
            name: 'ENVIRONMENT',
            choices: ['development', 'staging', 'production'],
            description: 'Target environment'
        )
        booleanParam(
            name: 'DRY_RUN',
            defaultValue: true,
            description: 'Run in check mode'
        )
    }
    
    stages {
        // ========================================
        // Checkout
        // ========================================
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        // ========================================
        // Setup
        // ========================================
        stage('Setup') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install ansible ansible-lint yamllint
                    ansible-galaxy install -r requirements.yml
                '''
            }
        }
        
        // ========================================
        // Lint
        // ========================================
        stage('Lint') {
            parallel {
                stage('YAML Lint') {
                    steps {
                        sh '''
                            . venv/bin/activate
                            yamllint .
                        '''
                    }
                }
                stage('Ansible Lint') {
                    steps {
                        sh '''
                            . venv/bin/activate
                            ansible-lint playbooks/*.yml
                        '''
                    }
                }
                stage('Syntax Check') {
                    steps {
                        sh '''
                            . venv/bin/activate
                            find playbooks/ -name "*.yml" -exec ansible-playbook {} --syntax-check \\;
                        '''
                    }
                }
            }
        }
        
        // ========================================
        // Test
        // ========================================
        stage('Test') {
            steps {
                sh '''
                    . venv/bin/activate
                    ansible-playbook playbooks/site.yml \\
                        -i inventories/${ENVIRONMENT}/hosts \\
                        --check \\
                        --diff
                '''
            }
        }
        
        // ========================================
        // Deploy
        // ========================================
        stage('Deploy') {
            when {
                expression { params.DRY_RUN == false }
            }
            steps {
                script {
                    if (params.ENVIRONMENT == 'production') {
                        input message: 'Deploy to production?', ok: 'Deploy'
                    }
                }
                
                withCredentials([
                    file(credentialsId: 'ansible-vault-password', variable: 'VAULT_PASS'),
                    sshUserPrivateKey(credentialsId: 'ansible-ssh-key', keyFileVariable: 'SSH_KEY')
                ]) {
                    sh '''
                        . venv/bin/activate
                        
                        # Configure SSH
                        mkdir -p ~/.ssh
                        cp $SSH_KEY ~/.ssh/ansible_key
                        chmod 600 ~/.ssh/ansible_key
                        
                        # Run playbook
                        ansible-playbook playbooks/site.yml \\
                            -i inventories/${ENVIRONMENT}/hosts \\
                            --vault-password-file $VAULT_PASS \\
                            -v
                    '''
                }
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
        success {
            slackSend(
                color: 'good',
                message: "Deployment to ${params.ENVIRONMENT} succeeded: ${env.JOB_NAME} ${env.BUILD_NUMBER}"
            )
        }
        failure {
            slackSend(
                color: 'danger',
                message: "Deployment to ${params.ENVIRONMENT} failed: ${env.JOB_NAME} ${env.BUILD_NUMBER}"
            )
        }
    }
}
```

---

## Azure DevOps

### Azure Pipeline

```yaml
# azure-pipelines.yml
trigger:
  branches:
    include:
      - main
      - develop
  paths:
    include:
      - playbooks/*
      - roles/*
      - inventories/*

pr:
  branches:
    include:
      - main
      - develop

variables:
  - name: ANSIBLE_FORCE_COLOR
    value: 'true'
  - name: ANSIBLE_HOST_KEY_CHECKING
    value: 'false'

stages:
  # ========================================
  # Validate Stage
  # ========================================
  - stage: Validate
    displayName: 'Validate Ansible Code'
    jobs:
      - job: Lint
        displayName: 'Lint and Syntax Check'
        pool:
          vmImage: 'ubuntu-latest'
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: '3.10'
          
          - script: |
              pip install ansible ansible-lint yamllint
              ansible-galaxy install -r requirements.yml
            displayName: 'Install dependencies'
          
          - script: yamllint .
            displayName: 'YAML Lint'
          
          - script: ansible-lint playbooks/*.yml
            displayName: 'Ansible Lint'
          
          - script: |
              find playbooks/ -name "*.yml" -exec ansible-playbook {} --syntax-check \;
            displayName: 'Syntax Check'

  # ========================================
  # Test Stage
  # ========================================
  - stage: Test
    displayName: 'Test Playbooks'
    dependsOn: Validate
    jobs:
      - job: DryRun
        displayName: 'Dry Run Test'
        pool:
          vmImage: 'ubuntu-latest'
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: '3.10'
          
          - script: |
              pip install ansible
              ansible-galaxy install -r requirements.yml
            displayName: 'Install Ansible'
          
          - script: |
              ansible-playbook playbooks/site.yml \
                -i inventories/development/hosts \
                --check --diff
            displayName: 'Dry Run'

  # ========================================
  # Deploy Development
  # ========================================
  - stage: DeployDev
    displayName: 'Deploy to Development'
    dependsOn: Test
    condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/develop'))
    jobs:
      - deployment: DeployDevelopment
        displayName: 'Deploy to Dev'
        pool:
          vmImage: 'ubuntu-latest'
        environment: 'development'
        strategy:
          runOnce:
            deploy:
              steps:
                - checkout: self
                
                - task: UsePythonVersion@0
                  inputs:
                    versionSpec: '3.10'
                
                - script: |
                    pip install ansible
                    ansible-galaxy install -r requirements.yml
                  displayName: 'Install Ansible'
                
                - task: DownloadSecureFile@1
                  name: sshKey
                  inputs:
                    secureFile: 'ansible_ssh_key'
                
                - script: |
                    mkdir -p ~/.ssh
                    cp $(sshKey.secureFilePath) ~/.ssh/ansible_key
                    chmod 600 ~/.ssh/ansible_key
                  displayName: 'Configure SSH'
                
                - script: |
                    echo "$(ANSIBLE_VAULT_PASSWORD)" > .vault_pass
                    ansible-playbook playbooks/site.yml \
                      -i inventories/development/hosts \
                      --vault-password-file .vault_pass \
                      -v
                  displayName: 'Run Playbook'
                  env:
                    ANSIBLE_VAULT_PASSWORD: $(vaultPassword)

  # ========================================
  # Deploy Production
  # ========================================
  - stage: DeployProd
    displayName: 'Deploy to Production'
    dependsOn: Test
    condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
    jobs:
      - deployment: DeployProduction
        displayName: 'Deploy to Prod'
        pool:
          vmImage: 'ubuntu-latest'
        environment: 'production'
        strategy:
          runOnce:
            deploy:
              steps:
                - checkout: self
                
                - task: UsePythonVersion@0
                  inputs:
                    versionSpec: '3.10'
                
                - script: |
                    pip install ansible
                    ansible-galaxy install -r requirements.yml
                  displayName: 'Install Ansible'
                
                - task: DownloadSecureFile@1
                  name: sshKey
                  inputs:
                    secureFile: 'ansible_ssh_key'
                
                - script: |
                    mkdir -p ~/.ssh
                    cp $(sshKey.secureFilePath) ~/.ssh/ansible_key
                    chmod 600 ~/.ssh/ansible_key
                  displayName: 'Configure SSH'
                
                - script: |
                    echo "$(ANSIBLE_VAULT_PASSWORD)" > .vault_pass
                    ansible-playbook playbooks/site.yml \
                      -i inventories/production/hosts \
                      --vault-password-file .vault_pass \
                      -v
                  displayName: 'Run Playbook'
                  env:
                    ANSIBLE_VAULT_PASSWORD: $(vaultPassword)
```

---

## Best Practices

### 1. Secret Management

```yaml
# ✅ GOOD - Use CI/CD secrets
- name: Create vault password
  run: echo "${{ secrets.ANSIBLE_VAULT_PASSWORD }}" > .vault_pass

# ❌ BAD - Hardcoded passwords
- name: Create vault password
  run: echo "MyPassword123" > .vault_pass
```

### 2. SSH Key Management

```yaml
# ✅ GOOD - Secure SSH key handling
- name: Configure SSH
  run: |
    mkdir -p ~/.ssh
    echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/ansible_key
    chmod 600 ~/.ssh/ansible_key

# ❌ BAD - Insecure permissions
- name: Configure SSH
  run: |
    echo "${{ secrets.SSH_PRIVATE_KEY }}" > ansible_key
```

### 3. Environment Separation

```yaml
# ✅ GOOD - Separate environments
deploy-dev:
  environment: development
  if: github.ref == 'refs/heads/develop'

deploy-prod:
  environment: production
  if: github.ref == 'refs/heads/main'
  when: manual
```

### 4. Dry Run Before Deploy

```yaml
# ✅ GOOD - Always dry run first
- name: Dry run
  run: ansible-playbook site.yml --check --diff

- name: Deploy
  run: ansible-playbook site.yml
```

### 5. Cleanup Secrets

```yaml
# ✅ GOOD - Cleanup after use
- name: Cleanup
  if: always()
  run: |
    rm -f ~/.ssh/ansible_key .vault_pass
```

---

## Quick Reference

| Platform | Config File | Trigger | Secrets |
|----------|-------------|---------|---------|
| GitHub Actions | `.github/workflows/*.yml` | Push, PR, Manual | `secrets.SECRET_NAME` |
| GitLab CI | `.gitlab-ci.yml` | Push, MR, Manual | `$SECRET_NAME` |
| Jenkins | `Jenkinsfile` | SCM, Manual | `credentials()` |
| Azure DevOps | `azure-pipelines.yml` | Push, PR, Manual | `$(secretName)` |

---

**Project Complete!** 🎉
