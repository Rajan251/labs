// ============================================================================
// MULTIBRANCH PIPELINE - CONFIGURATION
// ============================================================================
// File: multibranch-pipelines/multibranch-config.groovy
// Purpose: Jenkinsfile for multibranch pipeline setup
// Auto-discovers branches and creates pipelines for each
// ============================================================================

pipeline {
    agent any
    
    environment {
        APP_NAME = 'my-multibranch-app'
        DOCKER_REGISTRY = 'registry.company.com'
        VERSION = "${env.BRANCH_NAME}-${env.BUILD_NUMBER}"
    }
    
    options {
        buildDiscarder(logRotator(numToKeepStr: '5'))
        timestamps()
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    echo "Branch: ${env.BRANCH_NAME}"
                    echo "Build: ${env.BUILD_NUMBER}"
                }
            }
        }
        
        stage('Build') {
            steps {
                sh 'npm ci && npm run build'
            }
        }
        
        stage('Test') {
            steps {
                sh 'npm test'
            }
        }
        
        stage('Docker Build') {
            steps {
                sh "docker build -t ${DOCKER_REGISTRY}/${APP_NAME}:${VERSION} ."
            }
        }
        
        // Branch-specific deployment
        stage('Deploy') {
            steps {
                script {
                    switch(env.BRANCH_NAME) {
                        case 'main':
                            echo "Deploying to PRODUCTION"
                            deployToEnvironment('prod', VERSION)
                            break
                        case 'develop':
                            echo "Deploying to DEVELOPMENT"
                            deployToEnvironment('dev', VERSION)
                            break
                        case ~/release\/.*/:
                            echo "Deploying to QA"
                            deployToEnvironment('qa', VERSION)
                            break
                        case ~/feature\/.*/:
                            echo "Feature branch - skipping deployment"
                            break
                        default:
                            echo "Unknown branch - skipping deployment"
                    }
                }
            }
        }
    }
    
    post {
        success {
            echo "✅ Build succeeded for branch ${env.BRANCH_NAME}"
        }
        failure {
            echo "❌ Build failed for branch ${env.BRANCH_NAME}"
        }
    }
}

def deployToEnvironment(env, version) {
    sh """
        kubectl set image deployment/${APP_NAME} \\
            ${APP_NAME}=${DOCKER_REGISTRY}/${APP_NAME}:${version} \\
            -n ${env}
        kubectl rollout status deployment/${APP_NAME} -n ${env}
    """
}
