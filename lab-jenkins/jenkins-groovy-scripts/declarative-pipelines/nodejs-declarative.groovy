// ============================================================================
// DECLARATIVE PIPELINE - NODE.JS APPLICATION
// ============================================================================
// File: declarative-pipelines/nodejs-declarative.groovy
// Purpose: Production-ready declarative pipeline for Node.js apps
// Most Popular Approach: 70% of modern teams use this
// ============================================================================

pipeline {
    agent {
        docker {
            image 'node:18-alpine'
            args '-v /var/run/docker.sock:/var/run/docker.sock'
        }
    }
    
    environment {
        APP_NAME = 'my-nodejs-app'
        DOCKER_REGISTRY = 'registry.company.com'
        VERSION = "${env.BUILD_NUMBER}"
        NODE_ENV = 'production'
    }
    
    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
                sh 'git log -1 --pretty=format:"%h - %an: %s"'
            }
        }
        
        stage('Install Dependencies') {
            steps {
                sh 'npm ci'
            }
        }
        
        stage('Lint') {
            steps {
                sh 'npm run lint'
            }
        }
        
        stage('Unit Tests') {
            steps {
                sh 'npm run test:unit'
            }
            post {
                always {
                    junit 'test-results/unit/**/*.xml'
                }
            }
        }
        
        stage('Build') {
            steps {
                sh 'npm run build'
            }
        }
        
        stage('Integration Tests') {
            steps {
                sh 'npm run test:integration'
            }
        }
        
        stage('Security Scan') {
            parallel {
                stage('NPM Audit') {
                    steps {
                        sh 'npm audit --audit-level=moderate || true'
                    }
                }
                stage('Trivy Scan') {
                    steps {
                        sh 'trivy fs . --severity HIGH,CRITICAL || true'
                    }
                }
            }
        }
        
        stage('Docker Build') {
            steps {
                script {
                    sh "docker build -t ${DOCKER_REGISTRY}/${APP_NAME}:${VERSION} ."
                    sh "docker tag ${DOCKER_REGISTRY}/${APP_NAME}:${VERSION} ${DOCKER_REGISTRY}/${APP_NAME}:latest"
                }
            }
        }
        
        stage('Docker Push') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'docker-creds',
                    usernameVariable: 'USER',
                    passwordVariable: 'PASS'
                )]) {
                    sh """
                        echo \$PASS | docker login -u \$USER --password-stdin ${DOCKER_REGISTRY}
                        docker push ${DOCKER_REGISTRY}/${APP_NAME}:${VERSION}
                        docker push ${DOCKER_REGISTRY}/${APP_NAME}:latest
                    """
                }
            }
        }
        
        stage('Deploy to DEV') {
            when {
                branch 'develop'
            }
            steps {
                sh """
                    kubectl set image deployment/${APP_NAME} \\
                        ${APP_NAME}=${DOCKER_REGISTRY}/${APP_NAME}:${VERSION} \\
                        -n dev
                    kubectl rollout status deployment/${APP_NAME} -n dev
                """
            }
        }
        
        stage('Deploy to QA') {
            when {
                branch 'release/*'
            }
            steps {
                sh """
                    kubectl set image deployment/${APP_NAME} \\
                        ${APP_NAME}=${DOCKER_REGISTRY}/${APP_NAME}:${VERSION} \\
                        -n qa
                    kubectl rollout status deployment/${APP_NAME} -n qa
                """
            }
        }
        
        stage('Approval for PROD') {
            when {
                branch 'main'
            }
            steps {
                timeout(time: 24, unit: 'HOURS') {
                    input message: 'Deploy to Production?', ok: 'Deploy'
                }
            }
        }
        
        stage('Deploy to PROD') {
            when {
                branch 'main'
            }
            steps {
                sh """
                    kubectl set image deployment/${APP_NAME} \\
                        ${APP_NAME}=${DOCKER_REGISTRY}/${APP_NAME}:${VERSION} \\
                        -n prod
                    kubectl rollout status deployment/${APP_NAME} -n prod
                """
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
        success {
            slackSend color: 'good', message: "✅ Build ${env.BUILD_NUMBER} succeeded"
        }
        failure {
            slackSend color: 'danger', message: "❌ Build ${env.BUILD_NUMBER} failed"
        }
    }
}
