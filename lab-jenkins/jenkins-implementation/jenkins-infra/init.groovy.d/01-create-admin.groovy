// jenkins-infra/init.groovy.d/01-create-admin.groovy
import jenkins.model.*
import hudson.security.*

def instance = Jenkins.getInstance()
def hudsonRealm = new HudsonPrivateSecurityRealm(false)
def users = hudsonRealm.getAllUsers()
def adminUser = users.find { it.id == 'admin' }

if (!adminUser) {
    hudsonRealm.createAccount('admin', 'admin')
    instance.setSecurityRealm(hudsonRealm)
    
    def strategy = new FullControlOnceLoggedInAuthorizationStrategy()
    instance.setAuthorizationStrategy(strategy)
    instance.save()
    println "Admin user created."
}
