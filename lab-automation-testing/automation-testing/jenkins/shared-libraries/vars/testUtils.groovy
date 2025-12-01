// ============================================================================
// JENKINS SHARED LIBRARY - TESTING UTILITIES
// Location: vars/testUtils.groovy
// ============================================================================

/**
 * Run pytest with custom arguments
 * @param marker Test marker (unit, integration, e2e, etc.)
 * @param additionalArgs Additional pytest arguments
 */
def runPytest(String marker = '', String additionalArgs = '') {
    def markerArg = marker ? "-m ${marker}" : ''
    
    sh """
        . ${env.VENV_PATH}/bin/activate
        pytest ${markerArg} ${additionalArgs} \
            -v \
            --cov=app \
            --cov-report=xml \
            --cov-report=html \
            --cov-report=term-missing \
            --junitxml=junit-${marker ?: 'all'}.xml \
            --html=report-${marker ?: 'all'}.html \
            --self-contained-html
    """
}

/**
 * Check code coverage threshold
 * @param threshold Minimum coverage percentage (default: 80)
 */
def checkCoverage(int threshold = 80) {
    sh """
        . ${env.VENV_PATH}/bin/activate
        coverage report --fail-under=${threshold}
    """
}

/**
 * Run code quality checks
 */
def runCodeQuality() {
    parallel(
        'Black': {
            sh """
                . ${env.VENV_PATH}/bin/activate
                black --check . || echo "Black formatting issues found"
            """
        },
        'Flake8': {
            sh """
                . ${env.VENV_PATH}/bin/activate
                flake8 . --count --statistics --output-file=flake8-report.txt || true
            """
        },
        'MyPy': {
            sh """
                . ${env.VENV_PATH}/bin/activate
                mypy . --ignore-missing-imports || true
            """
        }
    )
}

/**
 * Run security scans
 */
def runSecurityScans() {
    parallel(
        'Bandit': {
            sh """
                . ${env.VENV_PATH}/bin/activate
                bandit -r . -f json -o bandit-report.json || true
            """
        },
        'Safety': {
            sh """
                . ${env.VENV_PATH}/bin/activate
                safety check --json || true
            """
        }
    )
}

/**
 * Start test services (PostgreSQL, Redis, etc.)
 */
def startTestServices() {
    sh """
        # Start PostgreSQL
        docker run -d --name postgres-test \
            -e POSTGRES_USER=testuser \
            -e POSTGRES_PASSWORD=testpass \
            -e POSTGRES_DB=testdb \
            -p 5432:5432 \
            postgres:15 || true
        
        # Start Redis
        docker run -d --name redis-test \
            -p 6379:6379 \
            redis:7 || true
        
        # Wait for services
        sleep 10
    """
}

/**
 * Stop and remove test services
 */
def stopTestServices() {
    sh """
        docker stop postgres-test redis-test || true
        docker rm postgres-test redis-test || true
    """
}

/**
 * Run load tests with Locust
 * @param users Number of concurrent users
 * @param duration Test duration
 * @param host Target host URL
 */
def runLoadTests(int users = 100, String duration = '5m', String host = 'http://localhost:8000') {
    sh """
        . ${env.VENV_PATH}/bin/activate
        
        # Start application
        uvicorn app.main:app --host 0.0.0.0 --port 8000 &
        APP_PID=\$!
        echo \$APP_PID > app.pid
        sleep 10
        
        # Run Locust
        locust -f fastapi-tests/load_tests.py \
            --host=${host} \
            --headless \
            --users ${users} \
            --spawn-rate 10 \
            --run-time ${duration} \
            --html=locust-report.html \
            --csv=locust-stats
        
        # Stop application
        kill \$(cat app.pid) || true
    """
}

/**
 * Send Slack notification
 * @param status Build status (success, failure, warning)
 * @param message Custom message
 */
def sendSlackNotification(String status, String message = '') {
    def color = [
        'success': 'good',
        'failure': 'danger',
        'warning': 'warning'
    ][status] ?: 'warning'
    
    def emoji = [
        'success': '✅',
        'failure': '❌',
        'warning': '⚠️'
    ][status] ?: '📢'
    
    def defaultMessage = "${emoji} Build #${env.BUILD_NUMBER} ${status} for ${env.JOB_NAME}\nBranch: ${env.GIT_BRANCH}\nCommit: ${env.GIT_COMMIT_SHORT}"
    
    slackSend(
        channel: env.SLACK_CHANNEL ?: '#ci-cd',
        color: color,
        message: message ?: defaultMessage
    )
}

/**
 * Publish test reports
 * @param reportType Type of report (unit, integration, load, etc.)
 */
def publishTestReports(String reportType = 'test') {
    // Publish JUnit results
    junit "junit-${reportType}.xml"
    
    // Publish HTML report
    publishHTML([
        allowMissing: false,
        alwaysLinkToLastBuild: true,
        keepAll: true,
        reportDir: '.',
        reportFiles: "report-${reportType}.html",
        reportName: "${reportType.capitalize()} Test Report"
    ])
}

/**
 * Build and tag Docker image
 * @param imageName Docker image name
 * @param tags List of tags to apply
 */
def buildDockerImage(String imageName, List<String> tags = ['latest']) {
    def tagArgs = tags.collect { "-t ${imageName}:${it}" }.join(' ')
    
    sh """
        docker build ${tagArgs} \
            --build-arg BUILD_DATE=\$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
            --build-arg VCS_REF=${env.GIT_COMMIT_SHORT} \
            .
    """
}

/**
 * Push Docker image to registry
 * @param imageName Docker image name
 * @param tags List of tags to push
 */
def pushDockerImage(String imageName, List<String> tags = ['latest']) {
    tags.each { tag ->
        sh "docker push ${imageName}:${tag}"
    }
}

return this
