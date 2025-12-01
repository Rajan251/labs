// ============================================================================
// BLUE-GREEN DEPLOYMENT STRATEGY
// ============================================================================
// File: deployment-strategies/blue-green-deployment.groovy
// Purpose: Standalone blue-green deployment script
// ============================================================================

def call(Map config) {
    def appName = config.appName
    def namespace = config.namespace ?: 'prod'
    def imageTag = config.imageTag
    def healthCheckUrl = config.healthCheckUrl
    
    stage('Blue-Green Deployment') {
        echo "========================================="
        echo "BLUE-GREEN DEPLOYMENT"
        echo "App: ${appName}"
        echo "Namespace: ${namespace}"
        echo "Image: ${imageTag}"
        echo "========================================="
        
        // Step 1: Deploy Green environment
        echo "Step 1: Deploying to Green environment..."
        sh """
            kubectl apply -f ci/deployment-green.yaml -n ${namespace}
            kubectl set image deployment/${appName}-green \\
                ${appName}=${imageTag} \\
                -n ${namespace}
        """
        
        // Step 2: Wait for Green to be ready
        echo "Step 2: Waiting for Green deployment to be ready..."
        sh "kubectl rollout status deployment/${appName}-green -n ${namespace} --timeout=10m"
        
        // Step 3: Run smoke tests on Green
        echo "Step 3: Running smoke tests on Green..."
        retry(3) {
            sleep 10
            if (healthCheckUrl) {
                sh "curl --fail ${healthCheckUrl}"
            } else {
                sh "kubectl exec deployment/${appName}-green -n ${namespace} -- curl --fail http://localhost:8080/health"
            }
        }
        
        // Step 4: Switch traffic to Green
        echo "Step 4: Switching traffic to Green..."
        sh """
            kubectl patch service ${appName} \\
                -p '{"spec":{"selector":{"version":"green"}}}' \\
                -n ${namespace}
        """
        
        echo "✅ Traffic successfully switched to Green"
        
        // Step 5: Monitor Green for 2 minutes
        echo "Step 5: Monitoring Green environment..."
        sleep 120
        
        // Step 6: Scale down Blue (keep 1 replica for quick rollback)
        echo "Step 6: Scaling down Blue environment..."
        sh "kubectl scale deployment/${appName}-blue --replicas=1 -n ${namespace} || true"
        
        echo "========================================="
        echo "✅ BLUE-GREEN DEPLOYMENT COMPLETED"
        echo "========================================="
    }
}
