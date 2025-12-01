// vars/ciPipeline.groovy
def call(Map config = [:]) {
    pipeline {
        agent any
        
        options {
            timestamps()
            buildDiscarder(logRotator(numToKeepStr: '10'))
            disableConcurrentBuilds()
        }
        
        environment {
            APP_NAME = "${env.JOB_NAME.split('/')[0]}"
            REGISTRY = "${config.registry ?: 'registry.example.com'}"
        }
        
        stages {
            stage('Checkout') {
                steps {
                    checkout scm
                }
            }
            
            stage('Build') {
                steps {
                    script {
                        if (config.type == 'maven') {
                            sh 'mvn clean package -DskipTests=false'
                        } else if (config.type == 'npm') {
                            sh 'npm install && npm run build'
                        } else {
                            echo "Unknown project type: ${config.type}"
                        }
                    }
                }
            }
            
            stage('Test') {
                steps {
                    script {
                        if (config.type == 'maven') {
                            junit 'target/surefire-reports/*.xml'
                        } else if (config.type == 'npm') {
                            // Assuming npm test generates junit report
                            sh 'npm test'
                        }
                    }
                }
            }
            
            stage('Docker Build') {
                when { expression { config.dockerBuild != false } }
                steps {
                    script {
                        docker.build("${REGISTRY}/${APP_NAME}:${env.BUILD_NUMBER}")
                    }
                }
            }
        }
        
        post {
            always {
                cleanWs()
            }
            failure {
                echo "Pipeline failed!"
                // slackSend color: 'danger', message: "Failed: ${env.JOB_NAME}"
            }
        }
    }
}
