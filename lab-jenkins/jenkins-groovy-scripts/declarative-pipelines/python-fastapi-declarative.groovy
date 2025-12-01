// ============================================================================
// DECLARATIVE PIPELINE - PYTHON FASTAPI APPLICATION
// ============================================================================
// File: declarative-pipelines/python-fastapi-declarative.groovy
// Purpose: Production-ready declarative pipeline for FastAPI apps
// ============================================================================

pipeline {
    agent {
        docker {
            image 'python:3.11-slim'
        }
    }
    
    environment {
        APP_NAME = 'my-fastapi-app'
        DOCKER_REGISTRY = 'registry.company.com'
        VERSION = "${env.BUILD_NUMBER}"
        PYTHONUNBUFFERED = '1'
    }
    
    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timestamps()
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Setup Python Environment') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }
        
        stage('Lint & Type Check') {
            parallel {
                stage('Ruff Lint') {
                    steps {
                        sh '''
                            . venv/bin/activate
                            ruff check .
                        '''
                    }
                }
                stage('MyPy Type Check') {
                    steps {
                        sh '''
                            . venv/bin/activate
                            mypy src/
                        '''
                    }
                }
            }
        }
        
        stage('Unit Tests') {
            steps {
                sh '''
                    . venv/bin/activate
                    pytest tests/unit -v --junitxml=test-results/unit.xml
                '''
            }
            post {
                always {
                    junit 'test-results/unit.xml'
                }
            }
        }
        
        stage('Integration Tests') {
            steps {
                sh '''
                    . venv/bin/activate
                    pytest tests/integration -v --junitxml=test-results/integration.xml
                '''
            }
        }
        
        stage('Coverage Report') {
            steps {
                sh '''
                    . venv/bin/activate
                    pytest --cov=src --cov-report=xml --cov-report=html
                '''
            }
            post {
                always {
                    publishHTML([
                        reportDir: 'htmlcov',
                        reportFiles: 'index.html',
                        reportName: 'Coverage Report'
                    ])
                }
            }
        }
        
        stage('Security Scan') {
            steps {
                sh '''
                    . venv/bin/activate
                    pip-audit || true
                    trivy fs . --severity HIGH,CRITICAL || true
                '''
            }
        }
        
        stage('Docker Build & Push') {
            steps {
                script {
                    def imageTag = "${DOCKER_REGISTRY}/${APP_NAME}:${VERSION}"
                    sh "docker build -t ${imageTag} ."
                    
                    withCredentials([usernamePassword(
                        credentialsId: 'docker-creds',
                        usernameVariable: 'USER',
                        passwordVariable: 'PASS'
                    )]) {
                        sh """
                            echo \$PASS | docker login -u \$USER --password-stdin ${DOCKER_REGISTRY}
                            docker push ${imageTag}
                        """
                    }
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
    }
    
    post {
        always {
            cleanWs()
        }
        success {
            slackSend color: 'good', message: "✅ FastAPI build ${env.BUILD_NUMBER} succeeded"
        }
        failure {
            slackSend color: 'danger', message: "❌ FastAPI build ${env.BUILD_NUMBER} failed"
        }
    }
}
