// ============================================================================
// CANARY DEPLOYMENT STRATEGY
// ============================================================================
// File: deployment-strategies/canary-deployment.groovy
// Purpose: Standalone canary deployment script with gradual rollout
// ============================================================================

def call(Map config) {
    def appName = config.appName
    def namespace = config.namespace ?: 'prod'
    def imageTag = config.imageTag
    def canaryPercentage = config.canaryPercentage ?: 10
    def monitoringDuration = config.monitoringDuration ?: 300  // 5 minutes
    
    stage('Canary Deployment') {
        echo "========================================="
        echo "CANARY DEPLOYMENT"
        echo "App: ${appName}"
        echo "Namespace: ${namespace}"
        echo "Image: ${imageTag}"
        echo "Canary Traffic: ${canaryPercentage}%"
        echo "========================================="
        
        // Step 1: Deploy canary
        echo "Step 1: Deploying canary with ${canaryPercentage}% traffic..."
        sh """
            kubectl apply -f ci/deployment-canary.yaml -n ${namespace}
            kubectl set image deployment/${appName}-canary \\
                ${appName}=${imageTag} \\
                -n ${namespace}
        """
        
        // Step 2: Wait for canary to be ready
        echo "Step 2: Waiting for canary to be ready..."
        sh "kubectl rollout status deployment/${appName}-canary -n ${namespace} --timeout=5m"
        
        // Step 3: Monitor canary metrics
        echo "Step 3: Monitoring canary for ${monitoringDuration} seconds..."
        def startTime = System.currentTimeMillis()
        
        while ((System.currentTimeMillis() - startTime) < (monitoringDuration * 1000)) {
            sleep 30
            
            // Check error rate (simplified - integrate with Prometheus in production)
            def errorRate = getErrorRate(appName, namespace)
            echo "Current error rate: ${errorRate}%"
            
            if (errorRate > 5.0) {
                error "❌ Canary error rate too high: ${errorRate}%. Aborting deployment."
            }
        }
        
        // Step 4: Promote canary to 100%
        echo "Step 4: Canary metrics look good. Promoting to 100%..."
        timeout(time: 1, unit: 'HOURS') {
            input message: 'Promote canary to 100%?', ok: 'Promote'
        }
        
        sh """
            kubectl set image deployment/${appName} \\
                ${appName}=${imageTag} \\
                -n ${namespace}
            kubectl rollout status deployment/${appName} -n ${namespace}
        """
        
        // Step 5: Remove canary deployment
        echo "Step 5: Removing canary deployment..."
        sh "kubectl delete deployment/${appName}-canary -n ${namespace}"
        
        echo "========================================="
        echo "✅ CANARY DEPLOYMENT COMPLETED"
        echo "========================================="
    }
}

def getErrorRate(appName, namespace) {
    // Simplified error rate check
    // In production, query Prometheus or your monitoring system
    try {
        def result = sh(
            script: """
                kubectl exec deployment/${appName}-canary -n ${namespace} -- \\
                    curl -s http://localhost:9090/metrics | grep error_rate | awk '{print \$2}'
            """,
            returnStdout: true
        ).trim()
        
        return result ? result.toFloat() : 0.0
    } catch (Exception e) {
        echo "Warning: Could not fetch error rate: ${e.message}"
        return 0.0
    }
}
