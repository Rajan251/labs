// ============================================================================
// KUBERNETES UTILITY CLASS
// ============================================================================
// File: src/org/company/K8s.groovy
// Purpose: Reusable Kubernetes operations
// ============================================================================

package org.company

class K8s implements Serializable {
    def script
    
    K8s(script) {
        this.script = script
    }
    
    /**
     * Deploy application to Kubernetes
     */
    def deploy(String appName, String namespace, String imageTag) {
        script.echo "Deploying ${appName} to ${namespace}"
        
        script.sh """
            kubectl set image deployment/${appName} \\
                ${appName}=${imageTag} \\
                -n ${namespace}
        """
    }
    
    /**
     * Wait for rollout to complete
     */
    def waitForRollout(String appName, String namespace, int timeoutMinutes = 5) {
        script.echo "Waiting for rollout of ${appName} in ${namespace}..."
        
        script.sh """
            kubectl rollout status deployment/${appName} \\
                -n ${namespace} \\
                --timeout=${timeoutMinutes}m
        """
    }
    
    /**
     * Rollback deployment
     */
    def rollback(String appName, String namespace, String revision = null) {
        script.echo "Rolling back ${appName} in ${namespace}"
        
        if (revision) {
            script.sh "kubectl rollout undo deployment/${appName} --to-revision=${revision} -n ${namespace}"
        } else {
            script.sh "kubectl rollout undo deployment/${appName} -n ${namespace}"
        }
        
        waitForRollout(appName, namespace)
    }
    
    /**
     * Get deployment status
     */
    def getStatus(String appName, String namespace) {
        return script.sh(
            script: "kubectl get deployment/${appName} -n ${namespace} -o jsonpath='{.status.conditions[?(@.type==\"Available\")].status}'",
            returnStdout: true
        ).trim()
    }
    
    /**
     * Scale deployment
     */
    def scale(String appName, String namespace, int replicas) {
        script.echo "Scaling ${appName} to ${replicas} replicas in ${namespace}"
        
        script.sh """
            kubectl scale deployment/${appName} \\
                --replicas=${replicas} \\
                -n ${namespace}
        """
    }
    
    /**
     * Run health check
     */
    def healthCheck(String appName, String namespace) {
        script.echo "Running health check for ${appName}..."
        
        script.sh """
            kubectl exec deployment/${appName} -n ${namespace} -- \\
                curl --fail http://localhost:8080/health
        """
    }
}
