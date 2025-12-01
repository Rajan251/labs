// ============================================================================
// DEPLOYMENT HELPER - SUPPORTS MULTIPLE STRATEGIES
// ============================================================================
// File: vars/deployApp.groovy
// Purpose: Handle deployments with different strategies
// Strategies: rolling, blue-green, canary
// ============================================================================

def call(Map config) {
    def appName = config.appName
    def environment = config.environment
    def version = config.version
    def strategy = config.strategy ?: 'rolling'
    def namespace = config.namespace ?: environment
    
    echo "========================================="
    echo "Deploying: ${appName}"
    echo "Environment: ${environment}"
    echo "Version: ${version}"
    echo "Strategy: ${strategy}"
    echo "========================================="
    
    switch(strategy) {
        case 'blue-green':
            blueGreenDeploy(appName, namespace, version)
            break
        case 'canary':
            canaryDeploy(appName, namespace, version)
            break
        case 'rolling':
        default:
            rollingDeploy(appName, namespace, version)
    }
}

// ========== ROLLING DEPLOYMENT ==========
def rollingDeploy(appName, namespace, version) {
    echo "Executing Rolling Deployment..."
    
    sh """
        kubectl set image deployment/${appName} \\
            ${appName}=registry.company.com/${appName}:${version} \\
            -n ${namespace}
        
        kubectl rollout status deployment/${appName} -n ${namespace} --timeout=5m
    """
    
    // Health check
    sh "kubectl get pods -n ${namespace} -l app=${appName}"
    echo "✅ Rolling deployment completed successfully"
}

// ========== BLUE-GREEN DEPLOYMENT ==========
def blueGreenDeploy(appName, namespace, version) {
    echo "Executing Blue-Green Deployment..."
    
    // Step 1: Deploy to Green
    sh """
        kubectl apply -f ci/deployment-green.yaml -n ${namespace}
        kubectl set image deployment/${appName}-green \\
            ${appName}=registry.company.com/${appName}:${version} \\
            -n ${namespace}
    """
    
    // Step 2: Wait for Green to be ready
    sh "kubectl rollout status deployment/${appName}-green -n ${namespace} --timeout=5m"
    
    // Step 3: Run smoke tests
    sh "curl --fail http://green.${namespace}.company.com/health || exit 1"
    
    // Step 4: Switch traffic to Green
    sh """
        kubectl patch service ${appName} \\
            -p '{"spec":{"selector":{"version":"green"}}}' \\
            -n ${namespace}
    """
    
    echo "✅ Traffic switched to Green environment"
    
    // Step 5: Scale down Blue (optional, after validation period)
    sleep 60
    sh "kubectl scale deployment/${appName}-blue --replicas=0 -n ${namespace} || true"
    
    echo "✅ Blue-Green deployment completed successfully"
}

// ========== CANARY DEPLOYMENT ==========
def canaryDeploy(appName, namespace, version) {
    echo "Executing Canary Deployment..."
    
    // Step 1: Deploy canary with 10% traffic
    sh """
        kubectl apply -f ci/deployment-canary.yaml -n ${namespace}
        kubectl set image deployment/${appName}-canary \\
            ${appName}=registry.company.com/${appName}:${version} \\
            -n ${namespace}
    """
    
    // Step 2: Wait for canary to be ready
    sh "kubectl rollout status deployment/${appName}-canary -n ${namespace} --timeout=5m"
    
    echo "⏳ Canary deployed with 10% traffic. Monitoring for 5 minutes..."
    sleep 300
    
    // Step 3: Check metrics (simplified - in production, integrate with Prometheus/Grafana)
    def errorRate = sh(
        script: "curl -s http://prometheus.company.com/api/v1/query?query=error_rate | jq -r '.data.result[0].value[1]'",
        returnStdout: true
    ).trim().toFloat()
    
    if (errorRate > 5.0) {
        error "❌ Canary error rate too high: ${errorRate}%. Rolling back..."
    }
    
    // Step 4: Promote canary to 100%
    echo "✅ Canary metrics look good. Promoting to 100%..."
    sh """
        kubectl set image deployment/${appName} \\
            ${appName}=registry.company.com/${appName}:${version} \\
            -n ${namespace}
        kubectl rollout status deployment/${appName} -n ${namespace}
    """
    
    // Step 5: Remove canary
    sh "kubectl delete deployment/${appName}-canary -n ${namespace}"
    
    echo "✅ Canary deployment completed successfully"
}
