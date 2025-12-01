// vars/deployApp.groovy
def call(String envName, String version) {
    echo "Deploying version ${version} to ${envName}..."
    
    // Simulate deployment logic
    if (envName == 'production') {
        input message: "Approve deployment of ${version} to PRODUCTION?", ok: 'Deploy'
    }
    
    sh "echo 'Helm upgrade --install myapp --set version=${version} --namespace ${envName}'"
    echo "Deployment successful."
}
