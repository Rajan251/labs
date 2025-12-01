// ============================================================================
// SCRIPTED PIPELINE - ADVANCED USE CASE
// ============================================================================
// File: scripted-pipelines/advanced-scripted.groovy
// Purpose: Scripted pipeline with complex logic and dynamic stages
// Use When: You need maximum flexibility and complex conditionals
// ============================================================================

// Import libraries
import groovy.json.JsonSlurper

// Global variables
def appName = 'my-app'
def dockerRegistry = 'registry.company.com'
def deploymentEnvs = []

node {
    try {
        // ========== STAGE: CHECKOUT ==========
        stage('Checkout') {
            echo "Checking out code..."
            checkout scm
            
            // Get commit info
            def commitHash = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
            def commitAuthor = sh(script: 'git log -1 --pretty=format:"%an"', returnStdout: true).trim()
            def commitMessage = sh(script: 'git log -1 --pretty=format:"%s"', returnStdout: true).trim()
            
            echo "Commit: ${commitHash} by ${commitAuthor}"
            echo "Message: ${commitMessage}"
            
            currentBuild.description = "Commit: ${commitHash}"
        }
        
        // ========== STAGE: DETERMINE BUILD TYPE ==========
        stage('Determine Build Type') {
            def branchName = env.BRANCH_NAME
            
            if (branchName == 'main') {
                deploymentEnvs = ['dev', 'qa', 'prod']
                echo "Production build - will deploy to all environments"
            } else if (branchName.startsWith('release/')) {
                deploymentEnvs = ['dev', 'qa']
                echo "Release build - will deploy to dev and qa"
            } else if (branchName == 'develop') {
                deploymentEnvs = ['dev']
                echo "Development build - will deploy to dev only"
            } else {
                deploymentEnvs = []
                echo "Feature branch - no deployment"
            }
        }
        
        // ========== STAGE: BUILD ==========
        stage('Build') {
            // Detect build tool from project files
            def buildTool = detectBuildTool()
            echo "Detected build tool: ${buildTool}"
            
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
                    error "Unknown build tool"
            }
        }
        
        // ========== STAGE: PARALLEL TESTS ==========
        stage('Tests') {
            parallel(
                'Unit Tests': {
                    echo "Running unit tests..."
                    sh 'npm run test:unit || true'
                },
                'Integration Tests': {
                    echo "Running integration tests..."
                    sh 'npm run test:integration || true'
                },
                'Security Scan': {
                    echo "Running security scan..."
                    sh 'npm audit --audit-level=moderate || true'
                }
            )
        }
        
        // ========== STAGE: DOCKER BUILD ==========
        stage('Docker Build') {
            def version = env.BUILD_NUMBER
            def imageTag = "${dockerRegistry}/${appName}:${version}"
            
            echo "Building Docker image: ${imageTag}"
            sh "docker build -t ${imageTag} ."
            
            // Tag as latest
            sh "docker tag ${imageTag} ${dockerRegistry}/${appName}:latest"
            
            // Push to registry
            withCredentials([usernamePassword(
                credentialsId: 'docker-creds',
                usernameVariable: 'USER',
                passwordVariable: 'PASS'
            )]) {
                sh """
                    echo \$PASS | docker login -u \$USER --password-stdin ${dockerRegistry}
                    docker push ${imageTag}
                    docker push ${dockerRegistry}/${appName}:latest
                """
            }
        }
        
        // ========== DYNAMIC DEPLOYMENT STAGES ==========
        for (env in deploymentEnvs) {
            stage("Deploy to ${env.toUpperCase()}") {
                if (env == 'prod') {
                    // Require approval for production
                    timeout(time: 24, unit: 'HOURS') {
                        input message: "Deploy to Production?", ok: 'Deploy'
                    }
                }
                
                echo "Deploying to ${env}..."
                sh """
                    kubectl set image deployment/${appName} \\
                        ${appName}=${dockerRegistry}/${appName}:${env.BUILD_NUMBER} \\
                        -n ${env}
                    kubectl rollout status deployment/${appName} -n ${env}
                """
                
                // Run smoke tests
                runSmokeTests(env)
            }
        }
        
        // ========== SUCCESS ==========
        currentBuild.result = 'SUCCESS'
        notifySuccess()
        
    } catch (Exception e) {
        // ========== FAILURE ==========
        currentBuild.result = 'FAILURE'
        echo "Build failed: ${e.message}"
        notifyFailure(e.message)
        throw e
        
    } finally {
        // ========== CLEANUP ==========
        stage('Cleanup') {
            cleanWs()
        }
    }
}

// ========== HELPER FUNCTIONS ==========

def detectBuildTool() {
    if (fileExists('package.json')) {
        return 'npm'
    } else if (fileExists('pom.xml')) {
        return 'maven'
    } else if (fileExists('build.gradle')) {
        return 'gradle'
    } else if (fileExists('requirements.txt')) {
        return 'python'
    } else {
        return 'unknown'
    }
}

def runSmokeTests(environment) {
    echo "Running smoke tests for ${environment}..."
    def healthUrl = "http://${appName}.${environment}.company.com/health"
    
    retry(3) {
        sh "curl --fail ${healthUrl}"
    }
    
    echo "✅ Smoke tests passed for ${environment}"
}

def notifySuccess() {
    slackSend(
        color: 'good',
        message: "✅ Build ${env.BUILD_NUMBER} succeeded for ${appName}"
    )
}

def notifyFailure(message) {
    slackSend(
        color: 'danger',
        message: "❌ Build ${env.BUILD_NUMBER} failed for ${appName}: ${message}"
    )
}
