// ============================================================================
// ARTIFACTORY INTEGRATION - DOWNLOAD ARTIFACT
// ============================================================================
// File: artifactory-integration/artifactoryDownload.groovy
// Purpose: Download artifacts from JFrog Artifactory
// ============================================================================

def call(Map config) {
    def artifactoryUrl = config.artifactoryUrl ?: 'https://artifactory.company.com'
    def repository = config.repository ?: 'libs-release-local'
    def artifactName = config.artifactName
    def version = config.version
    def downloadPath = config.downloadPath ?: '.'
    def credentialsId = config.credentialsId ?: 'artifactory-creds'
    
    echo "========================================="
    echo "DOWNLOADING FROM ARTIFACTORY"
    echo "Artifact: ${artifactName}"
    echo "Version: ${version}"
    echo "========================================="
    
    withCredentials([usernamePassword(
        credentialsId: credentialsId,
        usernameVariable: 'ARTIFACTORY_USER',
        passwordVariable: 'ARTIFACTORY_PASSWORD'
    )]) {
        sh """
            curl -u \${ARTIFACTORY_USER}:\${ARTIFACTORY_PASSWORD} \\
                -O \\
                "${artifactoryUrl}/${repository}/${artifactName}/${version}/${artifactName}-${version}.jar"
            
            mv ${artifactName}-${version}.jar ${downloadPath}/
        """
    }
    
    echo "✅ Artifact downloaded to ${downloadPath}"
}
