# GitHub Actions CI/CD Guide - Part 3: Test Stage

## Overview

The test stage validates code quality, runs automated tests, and generates coverage reports. This section covers unit testing, integration testing, and test reporting strategies.

## Node.js Testing

### Jest Testing Workflow

```yaml
name: Node.js Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20.x'
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run tests
        run: npm test -- --coverage
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          files: ./coverage/coverage-final.json
          flags: unittests
          name: codecov-umbrella
```

### Parallel Test Matrix

```yaml
jobs:
  test:
    runs-on: ${{ matrix.os }}
    
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        node-version: [16.x, 18.x, 20.x]
      fail-fast: false
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js ${{ matrix.node-version }}
        uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
      
      - run: npm ci
      - run: npm test
      
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: test-results-${{ matrix.os }}-${{ matrix.node-version }}
          path: test-results/
```

## Python Testing

### Pytest Workflow

```yaml
name: Python Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        python-version: ['3.9', '3.10', '3.11', '3.12']
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-xdist
      
      - name: Run tests with coverage
        run: |
          pytest --cov=src --cov-report=xml --cov-report=html -n auto
      
      - name: Upload coverage reports
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
          flags: python-${{ matrix.python-version }}
      
      - name: Upload HTML coverage report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report-${{ matrix.python-version }}
          path: htmlcov/
```

### Tox Multi-Environment Testing

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        python-version: ['3.9', '3.10', '3.11']
        toxenv: [py, lint, type]
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install tox
        run: pip install tox
      
      - name: Run tox
        run: tox -e ${{ matrix.toxenv }}
```

## Java Testing

### JUnit with Maven

```yaml
name: Java Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up JDK 17
        uses: actions/setup-java@v4
        with:
          java-version: '17'
          distribution: 'temurin'
          cache: 'maven'
      
      - name: Run tests
        run: mvn test
      
      - name: Publish test report
        uses: dorny/test-reporter@v1
        if: always()
        with:
          name: Maven Tests
          path: target/surefire-reports/*.xml
          reporter: java-junit
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          files: target/site/jacoco/jacoco.xml
```

## Test Reporting

### Generate Test Summary

```yaml
- name: Publish Test Results
  uses: EnricoMi/publish-unit-test-result-action@v2
  if: always()
  with:
    files: |
      test-results/**/*.xml
      **/test-results/**/*.json
    check_name: Test Results
    comment_mode: always
```

### JUnit Report Visualization

```yaml
- name: Test Report
  uses: dorny/test-reporter@v1
  if: success() || failure()
  with:
    name: Test Results
    path: 'test-results/*.xml'
    reporter: jest-junit
    fail-on-error: true
```

## Integration Testing

### Docker Compose Services

```yaml
jobs:
  integration-test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: testdb
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20.x'
      
      - run: npm ci
      
      - name: Run integration tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/testdb
          REDIS_URL: redis://localhost:6379
        run: npm run test:integration
```

### End-to-End Testing

```yaml
jobs:
  e2e-test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20.x'
      
      - run: npm ci
      
      - name: Install Playwright
        run: npx playwright install --with-deps
      
      - name: Build application
        run: npm run build
      
      - name: Run E2E tests
        run: npm run test:e2e
      
      - name: Upload Playwright report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 30
```

## Test Coverage Enforcement

### Coverage Threshold Check

```yaml
- name: Check coverage threshold
  run: |
    npm test -- --coverage --coverageThreshold='{"global":{"branches":80,"functions":80,"lines":80,"statements":80}}'
```

### Coverage Comment on PR

```yaml
- name: Coverage comment
  uses: romeovs/lcov-reporter-action@v0.3.1
  with:
    lcov-file: ./coverage/lcov.info
    github-token: ${{ secrets.GITHUB_TOKEN }}
    delete-old-comments: true
```

## Handling Test Failures

### Continue on Error

```yaml
- name: Run flaky tests
  continue-on-error: true
  run: npm run test:flaky

- name: Run critical tests
  run: npm run test:critical
```

### Retry Failed Tests

```yaml
- name: Run tests with retry
  uses: nick-fields/retry@v2
  with:
    timeout_minutes: 10
    max_attempts: 3
    command: npm test
```

### Conditional Test Execution

```yaml
- name: Run tests only if source changed
  if: contains(github.event.head_commit.modified, 'src/')
  run: npm test
```

## Common Testing Problems & Solutions

### Problem 1: Tests Timeout

**Symptom**: Tests hang and timeout

**Solution**:
```yaml
- name: Run tests with timeout
  run: npm test
  timeout-minutes: 10  # Kill after 10 minutes
```

### Problem 2: Flaky Tests

**Symptom**: Tests pass/fail randomly

**Solution**:
```yaml
# Retry flaky tests
- name: Run tests with retries
  uses: nick-fields/retry@v2
  with:
    timeout_minutes: 5
    max_attempts: 3
    retry_on: error
    command: npm test
```

### Problem 3: Database Connection Fails

**Symptom**: Integration tests can't connect to database

**Solution**:
```yaml
services:
  postgres:
    image: postgres:15
    options: >-
      --health-cmd pg_isready
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5  # Wait for DB to be ready
    ports:
      - 5432:5432

steps:
  - name: Wait for database
    run: |
      until pg_isready -h localhost -p 5432; do
        echo "Waiting for postgres..."
        sleep 2
      done
```

### Problem 4: Out of Memory During Tests

**Symptom**: Tests crash with OOM

**Solution**:
```yaml
- name: Run tests with increased memory
  run: NODE_OPTIONS="--max-old-space-size=4096" npm test
```

### Problem 5: Test Reports Not Generated

**Symptom**: Test reporter action fails

**Solution**:
```yaml
- name: Run tests
  run: npm test -- --reporters=default --reporters=jest-junit
  env:
    JEST_JUNIT_OUTPUT_DIR: ./test-results

- name: Publish results
  if: always()  # Run even if tests fail
  uses: EnricoMi/publish-unit-test-result-action@v2
  with:
    files: test-results/**/*.xml
```

## Test Optimization Tips

1. **Parallelize tests**: Use test runners that support parallel execution (`-n auto` for pytest, `--maxWorkers` for Jest)
2. **Use test matrix**: Run tests across multiple OS/versions simultaneously
3. **Cache dependencies**: Speed up test setup with caching
4. **Fail fast**: Stop on first failure for quick feedback
5. **Split test suites**: Separate unit, integration, and E2E tests
6. **Use services**: Leverage GitHub Actions services for databases
7. **Generate reports**: Always upload test results for debugging

---

> [!TIP]
> Use `if: always()` when uploading test artifacts to ensure reports are available even when tests fail.
