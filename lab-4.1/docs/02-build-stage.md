# GitHub Actions CI/CD Guide - Part 2: Build Stage

## Overview

The build stage compiles source code, resolves dependencies, and creates deployable artifacts. This section covers build configurations for multiple languages and platforms.

## Node.js Build

### Basic Node.js Workflow

```yaml
name: Node.js CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        node-version: [16.x, 18.x, 20.x]
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Setup Node.js ${{ matrix.node-version }}
        uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Build application
        run: npm run build
      
      - name: Upload build artifacts
        uses: actions/upload-artifact@v4
        with:
          name: build-${{ matrix.node-version }}
          path: dist/
          retention-days: 7
```

### Advanced Node.js with Caching

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20.x'
      
      # Cache node_modules
      - name: Cache dependencies
        uses: actions/cache@v4
        with:
          path: ~/.npm
          key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
          restore-keys: |
            ${{ runner.os }}-node-
      
      - name: Install dependencies
        run: npm ci
      
      - name: Lint code
        run: npm run lint
      
      - name: Build
        run: npm run build
        env:
          NODE_ENV: production
      
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: production-build
          path: |
            dist/
            package.json
```

## Python Build

### Basic Python Workflow

```yaml
name: Python CI

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        python-version: ['3.9', '3.10', '3.11', '3.12']
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      
      - name: Lint with flake8
        run: |
          pip install flake8
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
      
      - name: Build package
        run: |
          pip install build
          python -m build
      
      - name: Upload wheel
        uses: actions/upload-artifact@v4
        with:
          name: python-package-${{ matrix.python-version }}
          path: dist/*.whl
```

### Python with Poetry

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install Poetry
        uses: snok/install-poetry@v1
        with:
          version: 1.7.0
          virtualenvs-create: true
          virtualenvs-in-project: true
      
      - name: Load cached venv
        id: cached-poetry-dependencies
        uses: actions/cache@v4
        with:
          path: .venv
          key: venv-${{ runner.os }}-${{ hashFiles('**/poetry.lock') }}
      
      - name: Install dependencies
        if: steps.cached-poetry-dependencies.outputs.cache-hit != 'true'
        run: poetry install --no-interaction --no-root
      
      - name: Install project
        run: poetry install --no-interaction
      
      - name: Build
        run: poetry build
```

## Java Build

### Maven Build

```yaml
name: Java CI with Maven

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up JDK 17
        uses: actions/setup-java@v4
        with:
          java-version: '17'
          distribution: 'temurin'
          cache: 'maven'
      
      - name: Build with Maven
        run: mvn -B package --file pom.xml
      
      - name: Run tests
        run: mvn test
      
      - name: Upload JAR
        uses: actions/upload-artifact@v4
        with:
          name: application-jar
          path: target/*.jar
```

### Gradle Build

```yaml
name: Java CI with Gradle

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up JDK 17
        uses: actions/setup-java@v4
        with:
          java-version: '17'
          distribution: 'temurin'
          cache: 'gradle'
      
      - name: Grant execute permission for gradlew
        run: chmod +x gradlew
      
      - name: Build with Gradle
        run: ./gradlew build
      
      - name: Upload build reports
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: build-reports
          path: build/reports/
```

## Docker Build

### Basic Docker Build

```yaml
name: Docker Build

on:
  push:
    branches: [main]

jobs:
  docker-build:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Build Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: false
          tags: myapp:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### Multi-Platform Docker Build

```yaml
jobs:
  docker-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up QEMU
        uses: docker/setup-qemu-action@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          platforms: linux/amd64,linux/arm64
          push: true
          tags: |
            myapp:latest
            myapp:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

## Cache Strategies

### NPM Cache

```yaml
- name: Cache npm dependencies
  uses: actions/cache@v4
  with:
    path: ~/.npm
    key: ${{ runner.os }}-npm-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-npm-
```

### Pip Cache

```yaml
- name: Cache pip dependencies
  uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-
```

### Docker Layer Cache

```yaml
- name: Cache Docker layers
  uses: actions/cache@v4
  with:
    path: /tmp/.buildx-cache
    key: ${{ runner.os }}-buildx-${{ github.sha }}
    restore-keys: |
      ${{ runner.os }}-buildx-
```

## Common Build Problems & Solutions

### Problem 1: Cache Not Working

**Symptom**: Dependencies reinstall every time

**Solution**:
```yaml
# Ensure cache key includes dependency file hash
- uses: actions/cache@v4
  with:
    path: ~/.npm
    key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
    # Add restore-keys for partial matches
    restore-keys: |
      ${{ runner.os }}-node-
```

### Problem 2: Out of Memory During Build

**Symptom**: Build fails with OOM error

**Solution**:
```yaml
# Increase Node.js memory limit
- name: Build with increased memory
  run: NODE_OPTIONS="--max-old-space-size=4096" npm run build

# Or use larger runner
jobs:
  build:
    runs-on: ubuntu-latest-4-cores  # Larger runner
```

### Problem 3: Slow Docker Builds

**Symptom**: Docker builds take too long

**Solution**:
```yaml
# Use BuildKit and layer caching
- name: Build with cache
  uses: docker/build-push-action@v5
  with:
    context: .
    cache-from: type=gha
    cache-to: type=gha,mode=max
    # Use inline cache
    build-args: |
      BUILDKIT_INLINE_CACHE=1
```

### Problem 4: Matrix Build Failures

**Symptom**: One version fails, stops all builds

**Solution**:
```yaml
strategy:
  matrix:
    node-version: [16, 18, 20]
  fail-fast: false  # Continue other builds if one fails
```

### Problem 5: Artifact Upload Fails

**Symptom**: Artifacts not found or upload fails

**Solution**:
```yaml
- name: Upload artifacts
  uses: actions/upload-artifact@v4
  with:
    name: build-output
    path: dist/
    if-no-files-found: error  # Fail if no files found
```

## Build Optimization Tips

1. **Use caching aggressively**: Cache dependencies, build outputs, Docker layers
2. **Parallelize matrix builds**: Test multiple versions simultaneously
3. **Fail fast when appropriate**: Stop early on critical failures
4. **Use artifacts wisely**: Share build outputs between jobs
5. **Optimize Docker layers**: Order Dockerfile commands by change frequency
6. **Use BuildKit**: Enable for faster Docker builds
7. **Limit artifact retention**: Set appropriate retention days

---

> [!IMPORTANT]
> Always use `npm ci` instead of `npm install` in CI for reproducible builds. It's faster and ensures package-lock.json is respected.
