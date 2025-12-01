// ============================================================================
// JENKINS PIPELINE WITH ARTIFACTORY + ARGOCD
// ============================================================================
// File: artifactory-integration/pipeline-with-artifactory-argocd.groovy
// Purpose: Complete CI/CD pipeline with Artifactory and ArgoCD
// ============================================================================

@Library('jenkins-shared-library') _

pipeline {
    agent any
    
    environment {
        APP_NAME = 'my-app'
        DOCKER_REGISTRY = 'registry.company.com'
        ARTIFACTORY_URL = 'https://artifactory.company.com'
        ARTIFACTORY_REPO = 'docker-local'
        VERSION = "${env.BUILD_NUMBER}"
        GIT_COMMIT_SHORT = sh(script: "git rev-parse --short HEAD", returnStdout: true).trim()
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
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
                script {
                    sh "docker build -t ${APP_NAME}:${VERSION} ."
                }
            }
        }
        
        stage('Push to Artifactory') {
            steps {
                script {
                    // Tag image for Artifactory
                    def artifactoryImage = "${ARTIFACTORY_URL}/${ARTIFACTORY_REPO}/${APP_NAME}:${VERSION}"
                    
                    sh "docker tag ${APP_NAME}:${VERSION} ${artifactoryImage}"
                    
                    // Push to Artifactory
                    withCredentials([usernamePassword(
                        credentialsId: 'artifactory-creds',
                        usernameVariable: 'USER',
                        passwordVariable: 'PASS'
                    )]) {
                        sh """
                            echo \$PASS | docker login -u \$USER --password-stdin ${ARTIFACTORY_URL}
                            docker push ${artifactoryImage}
                        """
                    }
                    
                    echo "✅ Image pushed to Artifactory: ${artifactoryImage}"
                }
            }
        }
        
        stage('Update GitOps Repo') {
            steps {
                script {
                    // Clone GitOps repository
                    sh """
                        git clone https://github.com/your-org/gitops-repo.git
                        cd gitops-repo
                    """
                    
                    // Update image tag in manifest
                    def manifestFile = "gitops-repo/manifests/${env.BRANCH_NAME}/deployment.yaml"
                    
                    sh """
                        cd gitops-repo
                        sed -i 's|image: .*|image: ${ARTIFACTORY_URL}/${ARTIFACTORY_REPO}/${APP_NAME}:${VERSION}|g' manifests/${env.BRANCH_NAME}/deployment.yaml
                        
                        git config user.email "jenkins@company.com"
                        git config user.name "Jenkins CI"
                        git add manifests/${env.BRANCH_NAME}/deployment.yaml
                        git commit -m "Update ${APP_NAME} to version ${VERSION}"
                        git push origin main
                    """
                    
                    echo "✅ GitOps repository updated. ArgoCD will sync automatically."
                }
            }
        }
        
        stage('Trigger ArgoCD Sync') {
            steps {
                script {
                    // Optional: Manually trigger ArgoCD sync
                    withCredentials([string(credentialsId: 'argocd-token', variable: 'ARGOCD_TOKEN')]) {
                        sh """
                            argocd app sync ${APP_NAME} \\
                                --auth-token \$ARGOCD_TOKEN \\
                                --server argocd.company.com
                        """
                    }
                    
                    echo "✅ ArgoCD sync triggered"
                }
            }
        }
        
        stage('Wait for ArgoCD Deployment') {
            steps {
                script {
                    withCredentials([string(credentialsId: 'argocd-token', variable: 'ARGOCD_TOKEN')]) {
                        sh """
                            argocd app wait ${APP_NAME} \\
                                --auth-token \$ARGOCD_TOKEN \\
                                --server argocd.company.com \\
                                --timeout 300
                        """
                    }
                    
                    echo "✅ Deployment completed successfully"
                }
            }
        }
    }
    
    post {
        success {
            slackSend color: 'good', message: "✅ ${APP_NAME} v${VERSION} deployed successfully via ArgoCD"
        }
        failure {
            slackSend color: 'danger', message: "❌ Deployment failed for ${APP_NAME} v${VERSION}"
        }
    }
}
