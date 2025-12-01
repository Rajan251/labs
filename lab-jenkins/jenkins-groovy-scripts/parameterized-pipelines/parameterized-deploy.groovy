// ============================================================================
// PARAMETERIZED PIPELINE - FLEXIBLE DEPLOYMENT
// ============================================================================
// File: parameterized-pipelines/parameterized-deploy.groovy
// Purpose: Pipeline with user-configurable parameters
// Use Case: Manual deployments, hotfixes, custom builds
// ============================================================================

pipeline {
    agent any
    
    // ========== BUILD PARAMETERS ==========
    parameters {
        choice(
            name: 'ENVIRONMENT',
            choices: ['dev', 'qa', 'staging', 'prod'],
            description: 'Target deployment environment'
        )
        
        choice(
            name: 'BUILD_TOOL',
            choices: ['npm', 'maven', 'gradle', 'python'],
            description: 'Build tool to use'
        )
        
        string(
            name: 'APP_NAME',
            defaultValue: 'my-app',
            description: 'Application name'
        )
        
        string(
            name: 'DOCKER_TAG',
            defaultValue: 'latest',
            description: 'Docker image tag to deploy'
        )
        
        booleanParam(
            name: 'RUN_TESTS',
            defaultValue: true,
            description: 'Run tests before deployment'
        )
        
        booleanParam(
            name: 'SKIP_BUILD',
            defaultValue: false,
            description: 'Skip build and use existing Docker image'
        )
        
        choice(
            name: 'DEPLOYMENT_STRATEGY',
            choices: ['rolling', 'blue-green', 'canary'],
            description: 'Deployment strategy'
        )
        
        text(
            name: 'RELEASE_NOTES',
            defaultValue: '',
            description: 'Release notes for this deployment'
        )
    }
    
    environment {
        DOCKER_REGISTRY = 'registry.company.com'
        IMAGE_TAG = "${params.DOCKER_TAG}"
    }
    
    stages {
        stage('Validate Parameters') {
            steps {
                script {
                    echo "========================================="
                    echo "DEPLOYMENT CONFIGURATION"
                    echo "========================================="
                    echo "App Name: ${params.APP_NAME}"
                    echo "Environment: ${params.ENVIRONMENT}"
                    echo "Build Tool: ${params.BUILD_TOOL}"
                    echo "Docker Tag: ${params.DOCKER_TAG}"
                    echo "Run Tests: ${params.RUN_TESTS}"
                    echo "Skip Build: ${params.SKIP_BUILD}"
                    echo "Strategy: ${params.DEPLOYMENT_STRATEGY}"
                    echo "========================================="
                    
                    // Require approval for production
                    if (params.ENVIRONMENT == 'prod') {
                        timeout(time: 1, unit: 'HOURS') {
                            input message: 'Confirm Production Deployment?', ok: 'Deploy'
                        }
                    }
                }
            }
        }
        
        stage('Checkout') {
            when {
                expression { !params.SKIP_BUILD }
            }
            steps {
                checkout scm
            }
        }
        
        stage('Build') {
            when {
                expression { !params.SKIP_BUILD }
            }
            steps {
                script {
                    switch(params.BUILD_TOOL) {
                        case 'npm':
                            sh 'npm ci && npm run build'
                            break
                        case 'maven':
                            sh 'mvn clean package -DskipTests'
                            break
                        case 'gradle':
                            sh './gradlew clean build -x test'
                            break
                        case 'python':
                            sh '''
                                python3 -m venv venv
                                . venv/bin/activate
                                pip install -r requirements.txt
                            '''
                            break
                    }
                }
            }
        }
        
        stage('Tests') {
            when {
                expression { params.RUN_TESTS && !params.SKIP_BUILD }
            }
            steps {
                script {
                    switch(params.BUILD_TOOL) {
                        case 'npm':
                            sh 'npm test'
                            break
                        case 'maven':
                            sh 'mvn test'
                            break
                        case 'gradle':
                            sh './gradlew test'
                            break
                        case 'python':
                            sh '''
                                . venv/bin/activate
                                pytest
                            '''
                            break
                    }
                }
            }
        }
        
        stage('Docker Build & Push') {
            when {
                expression { !params.SKIP_BUILD }
            }
            steps {
                script {
                    def imageTag = "${DOCKER_REGISTRY}/${params.APP_NAME}:${IMAGE_TAG}"
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
        
        stage('Deploy') {
            steps {
                script {
                    def imageTag = "${DOCKER_REGISTRY}/${params.APP_NAME}:${IMAGE_TAG}"
                    
                    echo "Deploying ${imageTag} to ${params.ENVIRONMENT} using ${params.DEPLOYMENT_STRATEGY} strategy"
                    
                    switch(params.DEPLOYMENT_STRATEGY) {
                        case 'rolling':
                            sh """
                                kubectl set image deployment/${params.APP_NAME} \\
                                    ${params.APP_NAME}=${imageTag} \\
                                    -n ${params.ENVIRONMENT}
                                kubectl rollout status deployment/${params.APP_NAME} -n ${params.ENVIRONMENT}
                            """
                            break
                            
                        case 'blue-green':
                            sh """
                                kubectl apply -f ci/deployment-green.yaml -n ${params.ENVIRONMENT}
                                kubectl set image deployment/${params.APP_NAME}-green \\
                                    ${params.APP_NAME}=${imageTag} \\
                                    -n ${params.ENVIRONMENT}
                                kubectl rollout status deployment/${params.APP_NAME}-green -n ${params.ENVIRONMENT}
                                kubectl patch service ${params.APP_NAME} \\
                                    -p '{"spec":{"selector":{"version":"green"}}}' \\
                                    -n ${params.ENVIRONMENT}
                            """
                            break
                            
                        case 'canary':
                            sh """
                                kubectl apply -f ci/deployment-canary.yaml -n ${params.ENVIRONMENT}
                                kubectl set image deployment/${params.APP_NAME}-canary \\
                                    ${params.APP_NAME}=${imageTag} \\
                                    -n ${params.ENVIRONMENT}
                                kubectl rollout status deployment/${params.APP_NAME}-canary -n ${params.ENVIRONMENT}
                            """
                            echo "⏳ Canary deployed. Monitor metrics before promoting to 100%"
                            break
                    }
                }
            }
        }
        
        stage('Post-Deployment Verification') {
            steps {
                script {
                    echo "Running health checks..."
                    sh "curl --fail http://${params.APP_NAME}.${params.ENVIRONMENT}.company.com/health"
                    echo "✅ Health check passed"
                }
            }
        }
    }
    
    post {
        success {
            script {
                def message = """
                    ✅ Deployment Successful
                    App: ${params.APP_NAME}
                    Environment: ${params.ENVIRONMENT}
                    Version: ${IMAGE_TAG}
                    Strategy: ${params.DEPLOYMENT_STRATEGY}
                    ${params.RELEASE_NOTES ? '\nRelease Notes:\n' + params.RELEASE_NOTES : ''}
                """
                slackSend color: 'good', message: message
            }
        }
        
        failure {
            script {
                slackSend(
                    color: 'danger',
                    message: "❌ Deployment failed for ${params.APP_NAME} to ${params.ENVIRONMENT}"
                )
            }
        }
    }
}
