// ============================================================================
// PRODUCTION-GRADE SHARED LIBRARY: STANDARD CI/CD PIPELINE
// ============================================================================
// File: vars/standardPipeline.groovy
// Purpose: Reusable pipeline template for all microservices
// Usage: @Library('jenkins-shared-library') _ 
//        standardPipeline(appName: 'my-app', buildTool: 'npm')
// ============================================================================

def call(Map config) {
    // ========== CONFIGURATION DEFAULTS ==========
    def appName = config.appName ?: 'app'
    def buildTool = config.buildTool ?: 'maven'
    def dockerRegistry = config.dockerRegistry ?: 'registry.company.com'
    def deployEnvs = config.deployEnvs ?: ['dev']
    def runTests = config.runTests != false  // Default true
    def enableSonar = config.enableSonar ?: true
    
    pipeline {
        agent any
        
        // ========== ENVIRONMENT VARIABLES ==========
        environment {
            APP_NAME = "${appName}"
            DOCKER_REGISTRY = "${dockerRegistry}"
            VERSION = "${env.BUILD_NUMBER}"
            GIT_COMMIT_SHORT = sh(
                script: "git rev-parse --short HEAD",
                returnStdout: true
            ).trim()
            IMAGE_TAG = "${dockerRegistry}/${appName}:${env.BUILD_NUMBER}-${GIT_COMMIT_SHORT}"
        }
        
        // ========== BUILD PARAMETERS ==========
        parameters {
            choice(
                name: 'DEPLOY_ENV',
                choices: deployEnvs,
                description: 'Target deployment environment'
            )
            booleanParam(
                name: 'SKIP_TESTS',
                defaultValue: false,
                description: 'Skip test execution (not recommended for production)'
            )
            booleanParam(
                name: 'FORCE_DEPLOY',
                defaultValue: false,
                description: 'Force deployment even if tests fail'
            )
            string(
                name: 'CUSTOM_TAG',
                defaultValue: '',
                description: 'Custom Docker tag (optional)'
            )
        }
        
        // ========== PIPELINE OPTIONS ==========
        options {
            buildDiscarder(logRotator(numToKeepStr: '10'))
            timestamps()
            timeout(time: 1, unit: 'HOURS')
            disableConcurrentBuilds()
        }
        
        // ========== PIPELINE STAGES ==========
        stages {
            stage('Initialize') {
                steps {
                    script {
                        currentBuild.description = "Branch: ${env.BRANCH_NAME} | Env: ${params.DEPLOY_ENV}"
                        echo "========================================="
                        echo "Pipeline: ${appName}"
                        echo "Version: ${env.VERSION}"
                        echo "Commit: ${GIT_COMMIT_SHORT}"
                        echo "========================================="
                    }
                }
            }
            
            stage('Checkout') {
                steps {
                    checkout scm
                    sh 'git log -1 --pretty=format:"%h - %an: %s"'
                }
            }
            
            stage('Build') {
                steps {
                    script {
                        echo "Building with ${buildTool}..."
                        switch(buildTool) {
                            case 'npm':
                                sh 'npm ci'
                                sh 'npm run build'
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
                            default:
                                error "Unsupported build tool: ${buildTool}"
                        }
                    }
                }
            }
            
            stage('Unit Tests') {
                when {
                    expression { runTests && !params.SKIP_TESTS }
                }
                steps {
                    script {
                        switch(buildTool) {
                            case 'npm':
                                sh 'npm run test:unit'
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
                                    pytest tests/unit -v --junitxml=test-results/unit.xml
                                '''
                                break
                        }
                    }
                }
                post {
                    always {
                        junit '**/test-results/**/*.xml'
                    }
                }
            }
            
            stage('Code Quality & Security') {
                parallel {
                    stage('SonarQube Scan') {
                        when {
                            expression { enableSonar }
                        }
                        steps {
                            withSonarQubeEnv('SonarQube') {
                                sh 'sonar-scanner'
                            }
                        }
                    }
                    
                    stage('Dependency Check') {
                        steps {
                            script {
                                switch(buildTool) {
                                    case 'npm':
                                        sh 'npm audit --audit-level=moderate || true'
                                        break
                                    case 'maven':
                                        sh 'mvn dependency-check:check || true'
                                        break
                                    case 'python':
                                        sh 'pip-audit || true'
                                        break
                                }
                            }
                        }
                    }
                    
                    stage('SAST Scan') {
                        steps {
                            sh 'trivy fs . --severity HIGH,CRITICAL || true'
                        }
                    }
                }
            }
            
            stage('Integration Tests') {
                when {
                    expression { runTests && !params.SKIP_TESTS }
                }
                steps {
                    script {
                        switch(buildTool) {
                            case 'npm':
                                sh 'npm run test:integration'
                                break
                            case 'maven':
                                sh 'mvn verify -DskipUnitTests'
                                break
                            case 'python':
                                sh '''
                                    . venv/bin/activate
                                    pytest tests/integration -v
                                '''
                                break
                        }
                    }
                }
            }
            
            stage('Docker Build') {
                steps {
                    script {
                        def tag = params.CUSTOM_TAG ?: IMAGE_TAG
                        echo "Building Docker image: ${tag}"
                        sh "docker build -t ${tag} ."
                        sh "docker tag ${tag} ${DOCKER_REGISTRY}/${APP_NAME}:latest"
                    }
                }
            }
            
            stage('Docker Push') {
                steps {
                    script {
                        def tag = params.CUSTOM_TAG ?: IMAGE_TAG
                        withCredentials([usernamePassword(
                            credentialsId: 'docker-registry-creds',
                            usernameVariable: 'DOCKER_USER',
                            passwordVariable: 'DOCKER_PASS'
                        )]) {
                            sh """
                                echo \$DOCKER_PASS | docker login -u \$DOCKER_USER --password-stdin ${DOCKER_REGISTRY}
                                docker push ${tag}
                                docker push ${DOCKER_REGISTRY}/${APP_NAME}:latest
                            """
                        }
                    }
                }
            }
            
            stage('Deploy to DEV') {
                when {
                    anyOf {
                        branch 'develop'
                        expression { params.DEPLOY_ENV == 'dev' }
                    }
                }
                steps {
                    deployApp(
                        appName: appName,
                        environment: 'dev',
                        version: env.VERSION,
                        strategy: 'rolling'
                    )
                }
            }
            
            stage('Deploy to QA') {
                when {
                    anyOf {
                        branch 'release/*'
                        expression { params.DEPLOY_ENV == 'qa' }
                    }
                }
                steps {
                    deployApp(
                        appName: appName,
                        environment: 'qa',
                        version: env.VERSION,
                        strategy: 'rolling'
                    )
                }
            }
            
            stage('Approval for PROD') {
                when {
                    anyOf {
                        branch 'main'
                        expression { params.DEPLOY_ENV == 'prod' }
                    }
                }
                steps {
                    timeout(time: 24, unit: 'HOURS') {
                        input(
                            message: 'Deploy to Production?',
                            ok: 'Deploy',
                            submitter: 'admin-group,release-managers'
                        )
                    }
                }
            }
            
            stage('Deploy to PROD') {
                when {
                    anyOf {
                        branch 'main'
                        expression { params.DEPLOY_ENV == 'prod' }
                    }
                }
                steps {
                    deployApp(
                        appName: appName,
                        environment: 'prod',
                        version: env.VERSION,
                        strategy: 'blue-green'
                    )
                }
            }
        }
        
        // ========== POST-BUILD ACTIONS ==========
        post {
            always {
                cleanWs()
            }
            
            success {
                script {
                    notifySlack(
                        status: 'SUCCESS',
                        message: "✅ Build ${env.BUILD_NUMBER} succeeded for ${appName}",
                        color: 'good'
                    )
                }
            }
            
            failure {
                script {
                    notifySlack(
                        status: 'FAILURE',
                        message: "❌ Build ${env.BUILD_NUMBER} failed for ${appName}",
                        color: 'danger'
                    )
                    
                    // Auto-rollback on production failure
                    if (env.BRANCH_NAME == 'main' && !params.FORCE_DEPLOY) {
                        echo "Initiating automatic rollback..."
                        rollbackApp(
                            appName: appName,
                            environment: 'prod'
                        )
                    }
                }
            }
            
            unstable {
                script {
                    notifySlack(
                        status: 'UNSTABLE',
                        message: "⚠️ Build ${env.BUILD_NUMBER} is unstable for ${appName}",
                        color: 'warning'
                    )
                }
            }
        }
    }
}
