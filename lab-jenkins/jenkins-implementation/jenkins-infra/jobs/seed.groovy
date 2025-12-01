// jenkins-infra/jobs/seed.groovy
def repoList = ['service-a', 'service-b', 'frontend-app']

repoList.each { repoName ->
    multibranchPipelineJob(repoName) {
        branchSources {
            git {
                remote("https://github.com/myorg/${repoName}.git")
                credentialsId('git-creds')
            }
        }
        orphanedItemStrategy {
            discardOldItems {
                numToKeep(10)
            }
        }
        triggers {
            periodic(1)
        }
    }
}
