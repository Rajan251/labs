// ============================================================================
// DOCKER UTILITY CLASS
// ============================================================================
// File: src/org/company/Docker.groovy
// Purpose: Reusable Docker operations
// ============================================================================

package org.company

class Docker implements Serializable {
    def script
    
    Docker(script) {
        this.script = script
    }
    
    /**
     * Build Docker image with best practices
     */
    def build(String imageName, String tag, String dockerfile = 'Dockerfile') {
        script.echo "Building Docker image: ${imageName}:${tag}"
        
        script.sh """
            docker build \\
                -f ${dockerfile} \\
                -t ${imageName}:${tag} \\
                --build-arg BUILD_DATE=\$(date -u +'%Y-%m-%dT%H:%M:%SZ') \\
                --build-arg VCS_REF=\$(git rev-parse --short HEAD) \\
                .
        """
        
        return "${imageName}:${tag}"
    }
    
    /**
     * Push image to registry with retry logic
     */
    def push(String imageTag, String registry, String credentialsId) {
        script.echo "Pushing ${imageTag} to ${registry}"
        
        script.withCredentials([script.usernamePassword(
            credentialsId: credentialsId,
            usernameVariable: 'DOCKER_USER',
            passwordVariable: 'DOCKER_PASS'
        )]) {
            script.retry(3) {
                script.sh """
                    echo \$DOCKER_PASS | docker login -u \$DOCKER_USER --password-stdin ${registry}
                    docker push ${imageTag}
                """
            }
        }
    }
    
    /**
     * Scan image for vulnerabilities
     */
    def scan(String imageTag) {
        script.echo "Scanning ${imageTag} for vulnerabilities..."
        
        script.sh """
            trivy image --severity HIGH,CRITICAL ${imageTag} || true
        """
    }
    
    /**
     * Tag image
     */
    def tag(String sourceTag, String targetTag) {
        script.sh "docker tag ${sourceTag} ${targetTag}"
    }
    
    /**
     * Clean up old images
     */
    def cleanup() {
        script.echo "Cleaning up Docker images..."
        script.sh """
            docker image prune -f
            docker container prune -f
        """
    }
}
