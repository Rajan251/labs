// ============================================================================
// ROLLBACK HELPER
// ============================================================================
// File: vars/rollbackApp.groovy
// Purpose: Rollback deployments to previous version
// ============================================================================

def call(Map config) {
    def appName = config.appName
    def environment = config.environment
    def targetRevision = config.targetRevision ?: 'previous'
    def namespace = config.namespace ?: environment
    
    echo "========================================="
    echo "ROLLBACK INITIATED"
    echo "App: ${appName}"
    echo "Environment: ${environment}"
    echo "Target: ${targetRevision}"
    echo "========================================="
    
    try {
        if (targetRevision == 'previous') {
            // Rollback to previous deployment
            sh "kubectl rollout undo deployment/${appName} -n ${namespace}"
        } else {
            // Rollback to specific revision
            sh "kubectl rollout undo deployment/${appName} --to-revision=${targetRevision} -n ${namespace}"
        }
        
        // Wait for rollback to complete
        sh "kubectl rollout status deployment/${appName} -n ${namespace} --timeout=5m"
        
        // Verify rollback
        sh "kubectl get pods -n ${namespace} -l app=${appName}"
        
        echo "✅ Rollback completed successfully"
        
        notifySlack(
            status: 'WARNING',
            message: "🔄 Rolled back ${appName} in ${environment} to ${targetRevision}",
            color: 'warning'
        )
        
    } catch (Exception e) {
        echo "❌ Rollback failed: ${e.message}"
        notifySlack(
            status: 'FAILURE',
            message: "❌ Rollback failed for ${appName} in ${environment}",
            color: 'danger'
        )
        throw e
    }
}
