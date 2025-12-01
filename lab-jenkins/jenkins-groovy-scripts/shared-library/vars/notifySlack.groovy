// ============================================================================
// SLACK NOTIFICATION HELPER
// ============================================================================
// File: vars/notifySlack.groovy
// Purpose: Send notifications to Slack channels
// ============================================================================

def call(Map config) {
    def status = config.status ?: 'INFO'
    def message = config.message ?: 'Build notification'
    def color = config.color ?: getColorForStatus(status)
    def channel = config.channel ?: '#ci-cd-alerts'
    
    def buildUrl = env.BUILD_URL ?: 'N/A'
    def jobName = env.JOB_NAME ?: 'Unknown Job'
    def buildNumber = env.BUILD_NUMBER ?: 'N/A'
    def branchName = env.BRANCH_NAME ?: 'N/A'
    
    def slackMessage = """
        *${status}*: ${jobName} #${buildNumber}
        *Branch*: ${branchName}
        *Message*: ${message}
        <${buildUrl}|View Build>
    """
    
    try {
        slackSend(
            color: color,
            channel: channel,
            message: slackMessage
        )
    } catch (Exception e) {
        echo "Failed to send Slack notification: ${e.message}"
    }
}

def getColorForStatus(status) {
    switch(status.toUpperCase()) {
        case 'SUCCESS':
            return 'good'
        case 'FAILURE':
            return 'danger'
        case 'UNSTABLE':
            return 'warning'
        default:
            return '#439FE0'  // Blue for INFO
    }
}
