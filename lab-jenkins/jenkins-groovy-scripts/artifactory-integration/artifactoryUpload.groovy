// ============================================================================
// ARTIFACTORY INTEGRATION - SHARED LIBRARY
// ============================================================================
// File: artifactory-integration/artifactoryUpload.groovy
// Purpose: Upload artifacts to JFrog Artifactory
// ============================================================================

def call(Map config) {
    def artifactoryUrl = config.artifactoryUrl ?: 'https://artifactory.company.com'
    def repository = config.repository ?: 'libs-release-local'
    def artifactPath = config.artifactPath
    def artifactName = config.artifactName
    def version = config.version ?: env.BUILD_NUMBER
    def credentialsId = config.credentialsId ?: 'artifactory-creds'
    
    echo "========================================="
    echo "UPLOADING TO ARTIFACTORY"
    echo "URL: ${artifactoryUrl}"
    echo "Repository: ${repository}"
    echo "Artifact: ${artifactName}"
    echo "Version: ${version}"
    echo "========================================="
    
    // Upload using curl with authentication
    withCredentials([usernamePassword(
        credentialsId: credentialsId,
        usernameVariable: 'ARTIFACTORY_USER',
        passwordVariable: 'ARTIFACTORY_PASSWORD'
    )]) {
        sh """
            curl -u \${ARTIFACTORY_USER}:\${ARTIFACTORY_PASSWORD} \\
                -X PUT \\
                -T ${artifactPath} \\
                "${artifactoryUrl}/${repository}/${artifactName}/${version}/${artifactName}-${version}.jar"
        """
    }
    
    echo "✅ Artifact uploaded successfully"
    
    // Return artifact URL
    return "${artifactoryUrl}/${repository}/${artifactName}/${version}/${artifactName}-${version}.jar"
}
