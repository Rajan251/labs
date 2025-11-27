# 7. CI/CD Pipeline Setup

## Overview

This guide covers creating complete CI/CD pipelines in Jenkins that build, test, containerize, and deploy applications to Kubernetes.

## Pipeline Architecture

```
Source Code (Git) → Jenkins Pipeline → Docker Build → Registry → Kubernetes Deployment
```

## Prerequisites

- Jenkins with Docker and Kubernetes plugins
- Docker installed and configured
- Kubernetes cluster access configured
- Git repository with application code

## GitHub/GitLab Integration

### Setup GitHub Webhook

1. Go to your GitHub repository
2. **Settings** → **Webhooks** → **Add webhook**
3. **Payload URL**: `http://<jenkins-url>:8080/github-webhook/`
4. **Content type**: `application/json`
5. **Events**: Select "Just the push event"
6. **Active**: Check
7. **Add webhook**

### Configure Jenkins Job

1. Create **New Item** → **Multibranch Pipeline** or **Pipeline**
2. **Build Triggers** → Check **GitHub hook trigger for GITScm polling**
3. **Pipeline** → **Definition**: Pipeline script from SCM
4. **SCM**: Git
5. **Repository URL**: Your repo URL
6. **Credentials**: Add GitHub token
7. **Script Path**: Jenkinsfile
8. **Save**

### Create GitHub Personal Access Token

1. GitHub → **Settings** → **Developer settings** → **Personal access tokens**
2. **Generate new token**
3. Scopes: `repo`, `admin:repo_hook`
4. Copy token
5. Add to Jenkins credentials

## Pipeline Stages Explained

### Stage 1: Checkout

Clones the repository:

```groovy
stage('Checkout') {
    steps {
        checkout scm
    }
}
```

### Stage 2: Build

Compiles/builds the application:

```groovy
stage('Build') {
    steps {
        sh 'npm install'
        sh 'npm run build'
    }
}
```

### Stage 3: Test

Runs automated tests:

```groovy
stage('Test') {
    steps {
        sh 'npm test'
    }
}
```

### Stage 4: Docker Build

Builds container image:

```groovy
stage('Docker Build') {
    steps {
        script {
            dockerImage = docker.build("${DOCKER_IMAGE}:${BUILD_NUMBER}")
        }
    }
}
```

### Stage 5: Docker Push

Pushes image to registry:

```groovy
stage('Docker Push') {
    steps {
        script {
            docker.withRegistry('https://docker.io', 'dockerhub-credentials') {
                dockerImage.push("${BUILD_NUMBER}")
                dockerImage.push("latest")
            }
        }
    }
}
```

### Stage 6: Deploy to Kubernetes

Deploys to cluster:

```groovy
stage('Deploy') {
    steps {
        script {
            withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                sh """
                    kubectl set image deployment/myapp \
                        myapp=${DOCKER_IMAGE}:${BUILD_NUMBER} \
                        -n production
                    kubectl rollout status deployment/myapp -n production
                """
            }
        }
    }
}
```

## Complete Pipeline Examples

See the `jenkins/` directory for complete Jenkinsfile examples:
- [Jenkinsfile](../jenkins/Jenkinsfile) - Basic pipeline
- [Jenkinsfile.helm](../jenkins/Jenkinsfile.helm) - Helm deployment
- [Jenkinsfile.advanced](../jenkins/Jenkinsfile.advanced) - Advanced with parallel stages

## Environment Variables

### Common Variables

```groovy
environment {
    DOCKER_REGISTRY = 'docker.io'
    DOCKER_IMAGE = 'username/myapp'
    DOCKER_CREDENTIALS_ID = 'dockerhub-credentials'
    KUBECONFIG_CREDENTIALS_ID = 'kubeconfig'
    APP_NAME = 'myapp'
    NAMESPACE = 'production'
    GIT_COMMIT_SHORT = sh(
        script: "git rev-parse --short HEAD",
        returnStdout: true
    ).trim()
}
```

## Parallel Stages

Run tests in parallel:

```groovy
stage('Tests') {
    parallel {
        stage('Unit Tests') {
            steps {
                sh 'npm run test:unit'
            }
        }
        stage('Integration Tests') {
            steps {
                sh 'npm run test:integration'
            }
        }
        stage('Lint') {
            steps {
                sh 'npm run lint'
            }
        }
    }
}
```

## Conditional Execution

Deploy only on main branch:

```groovy
stage('Deploy to Production') {
    when {
        branch 'main'
    }
    steps {
        // deployment steps
    }
}
```

## Error Handling

```groovy
pipeline {
    agent any
    
    stages {
        stage('Build') {
            steps {
                script {
                    try {
                        sh 'npm run build'
                    } catch (Exception e) {
                        currentBuild.result = 'FAILURE'
                        error("Build failed: ${e.message}")
                    }
                }
            }
        }
    }
    
    post {
        failure {
            echo 'Pipeline failed!'
            // Send notification
        }
    }
}
```

## Post Actions

```groovy
post {
    always {
        cleanWs()  // Clean workspace
    }
    success {
        echo 'Pipeline succeeded!'
        // slackSend color: 'good', message: "Build ${BUILD_NUMBER} succeeded"
    }
    failure {
        echo 'Pipeline failed!'
        // slackSend color: 'danger', message: "Build ${BUILD_NUMBER} failed"
    }
    unstable {
        echo 'Pipeline is unstable'
    }
}
```

## Notifications

### Slack Integration

1. Install **Slack Notification** plugin
2. Configure Slack in **Manage Jenkins** → **Configure System**
3. Add to Jenkinsfile:

```groovy
post {
    success {
        slackSend (
            color: 'good',
            message: "Build Successful: ${env.JOB_NAME} ${env.BUILD_NUMBER}"
        )
    }
    failure {
        slackSend (
            color: 'danger',
            message: "Build Failed: ${env.JOB_NAME} ${env.BUILD_NUMBER}"
        )
    }
}
```

### Email Notification

```groovy
post {
    failure {
        emailext (
            subject: "Build Failed: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
            body: "Check console output at ${env.BUILD_URL}",
            to: 'team@example.com'
        )
    }
}
```

## Multi-Environment Deployment

```groovy
pipeline {
    agent any
    
    parameters {
        choice(
            name: 'ENVIRONMENT',
            choices: ['dev', 'staging', 'production'],
            description: 'Target environment'
        )
    }
    
    stages {
        stage('Deploy') {
            steps {
                script {
                    def namespace = params.ENVIRONMENT
                    withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                        sh """
                            kubectl set image deployment/myapp \
                                myapp=${DOCKER_IMAGE}:${BUILD_NUMBER} \
                                -n ${namespace}
                        """
                    }
                }
            }
        }
    }
}
```

## Blue-Green Deployment

```groovy
stage('Blue-Green Deploy') {
    steps {
        script {
            withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                // Deploy green version
                sh """
                    kubectl apply -f k8s/deployment-green.yaml
                    kubectl wait --for=condition=available deployment/myapp-green -n production
                """
                
                // Switch traffic
                sh """
                    kubectl patch service myapp-service -n production \
                        -p '{"spec":{"selector":{"version":"green"}}}'
                """
                
                // Delete blue version
                sh "kubectl delete deployment myapp-blue -n production --ignore-not-found"
            }
        }
    }
}
```

## Canary Deployment

```groovy
stage('Canary Deploy') {
    steps {
        script {
            withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                // Deploy canary with 10% traffic
                sh """
                    kubectl apply -f k8s/deployment-canary.yaml
                    kubectl scale deployment myapp-canary --replicas=1 -n production
                """
                
                // Wait and monitor
                sleep(time: 5, unit: 'MINUTES')
                
                // If successful, roll out to all
                sh """
                    kubectl set image deployment/myapp \
                        myapp=${DOCKER_IMAGE}:${BUILD_NUMBER} \
                        -n production
                    kubectl delete deployment myapp-canary -n production
                """
            }
        }
    }
}
```

## Rollback Strategy

```groovy
stage('Deploy with Rollback') {
    steps {
        script {
            withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                try {
                    sh """
                        kubectl set image deployment/myapp \
                            myapp=${DOCKER_IMAGE}:${BUILD_NUMBER} \
                            -n production
                        kubectl rollout status deployment/myapp -n production --timeout=5m
                    """
                } catch (Exception e) {
                    echo "Deployment failed, rolling back..."
                    sh "kubectl rollout undo deployment/myapp -n production"
                    error("Deployment failed and rolled back")
                }
            }
        }
    }
}
```

## Security Scanning

### Image Scanning with Trivy

```groovy
stage('Security Scan') {
    steps {
        script {
            sh """
                docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
                    aquasec/trivy image --severity HIGH,CRITICAL \
                    ${DOCKER_IMAGE}:${BUILD_NUMBER}
            """
        }
    }
}
```

## Best Practices

1. ✅ **Use Jenkinsfile** in source control
2. ✅ **Implement parallel stages** for faster builds
3. ✅ **Use environment variables** for configuration
4. ✅ **Implement proper error handling**
5. ✅ **Add notifications** for build status
6. ✅ **Use credentials securely**
7. ✅ **Implement rollback strategies**
8. ✅ **Add security scanning**
9. ✅ **Use specific image tags**, not `latest`
10. ✅ **Clean workspace** after builds

## Troubleshooting

### Pipeline Fails at Checkout

**Solution**: Check Git credentials and repository URL

### Docker Build Fails

**Solution**: Verify Dockerfile and Docker daemon access

### Kubernetes Deployment Fails

**Solution**: Check kubeconfig, RBAC permissions, and cluster connectivity

### Image Push Fails

**Solution**: Verify registry credentials and network access

## Next Steps

Proceed to [Monitoring & Logs](08-monitoring-logs.md) to set up monitoring for your CI/CD pipeline.
