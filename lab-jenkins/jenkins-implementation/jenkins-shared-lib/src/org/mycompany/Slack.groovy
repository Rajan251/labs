// src/org/mycompany/Slack.groovy
package org.mycompany

class Slack implements Serializable {
    def script
    
    Slack(script) {
        this.script = script
    }
    
    def send(String status, String channel = '#builds') {
        def color = 'good'
        if (status == 'FAILURE') {
            color = 'danger'
        } else if (status == 'UNSTABLE') {
            color = 'warning'
        }
        
        script.slackSend(
            color: color,
            channel: channel,
            message: "Build ${status}: ${script.env.JOB_NAME} #${script.env.BUILD_NUMBER} (<${script.env.BUILD_URL}|Open>)"
        )
    }
}
