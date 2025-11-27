# GitHub Actions CI/CD Guide - Part 7: Real-World Examples

## Example 1: Node.js App to AWS EKS

### Project Structure
```
my-nodejs-app/
├── .github/
│   └── workflows/
│       └── eks-deploy.yml
├── src/
│   ├── index.js
│   └── routes/
├── k8s/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── ingress.yaml
├── Dockerfile
├── package.json
└── README.md
```

### Complete Workflow

```yaml
name: Deploy Node.js to EKS

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  AWS_REGION: us-east-1
  EKS_CLUSTER_NAME: production-cluster
  ECR_REPOSITORY: my-nodejs-app

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
      
      - run: npm ci
      - run: npm test
      - run: npm run lint

  build-and-push:
    needs: test
    if: github.event_name == 'push'
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    outputs:
      image-tag: ${{ steps.meta.outputs.version }}
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsRole
          aws-region: ${{ env.AWS_REGION }}
      
      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2
      
      - name: Docker meta
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ steps.login-ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}
          tags: |
            type=sha,prefix={{branch}}-
            type=ref,event=branch
      
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    environment: production
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsRole
          aws-region: ${{ env.AWS_REGION }}
      
      - name: Update kubeconfig
        run: |
          aws eks update-kubeconfig \
            --name ${{ env.EKS_CLUSTER_NAME }} \
            --region ${{ env.AWS_REGION }}
      
      - name: Deploy to EKS
        run: |
          kubectl set image deployment/nodejs-app \
            nodejs-app=${{ needs.build-and-push.outputs.image-tag }} \
            -n production
          kubectl rollout status deployment/nodejs-app -n production
      
      - name: Verify deployment
        run: |
          kubectl get pods -n production
          kubectl get svc -n production
```

## Example 2: Python API to Docker Hub

### Project Structure
```
python-api/
├── .github/
│   └── workflows/
│       └── docker-publish.yml
├── src/
│   ├── main.py
│   ├── api/
│   └── models/
├── tests/
├── Dockerfile
├── requirements.txt
└── docker-compose.yml
```

### Workflow

```yaml
name: Python API Docker Build

on:
  push:
    tags:
      - 'v*'
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run tests
        run: pytest --cov=src --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml

  docker:
    needs: test
    if: startsWith(github.ref, 'refs/tags/')
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Docker meta
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: dockerhub-username/python-api
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha
      
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
          tags: ${{ steps.meta.outputs.tags }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

## Example 3: Microservices Monorepo

### Project Structure
```
microservices/
├── .github/
│   └── workflows/
│       ├── service-a.yml
│       ├── service-b.yml
│       └── shared.yml
├── services/
│   ├── service-a/
│   │   ├── src/
│   │   ├── Dockerfile
│   │   └── package.json
│   └── service-b/
│       ├── src/
│       ├── Dockerfile
│       └── requirements.txt
└── k8s/
    ├── service-a/
    └── service-b/
```

### Smart Monorepo Workflow

```yaml
name: Microservices CI/CD

on:
  push:
    branches: [main]

jobs:
  detect-changes:
    runs-on: ubuntu-latest
    outputs:
      service-a: ${{ steps.filter.outputs.service-a }}
      service-b: ${{ steps.filter.outputs.service-b }}
    steps:
      - uses: actions/checkout@v4
      
      - name: Detect changed services
        uses: dorny/paths-filter@v2
        id: filter
        with:
          filters: |
            service-a:
              - 'services/service-a/**'
            service-b:
              - 'services/service-b/**'

  build-service-a:
    needs: detect-changes
    if: needs.detect-changes.outputs.service-a == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build Service A
        working-directory: services/service-a
        run: |
          npm ci
          npm test
          npm run build
      
      - name: Build Docker image
        uses: docker/build-push-action@v5
        with:
          context: services/service-a
          push: true
          tags: myregistry/service-a:${{ github.sha }}

  build-service-b:
    needs: detect-changes
    if: needs.detect-changes.outputs.service-b == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build Service B
        working-directory: services/service-b
        run: |
          pip install -r requirements.txt
          pytest
      
      - name: Build Docker image
        uses: docker/build-push-action@v5
        with:
          context: services/service-b
          push: true
          tags: myregistry/service-b:${{ github.sha }}

  deploy:
    needs: [build-service-a, build-service-b]
    if: always() && (needs.build-service-a.result == 'success' || needs.build-service-b.result == 'success')
    runs-on: ubuntu-latest
    steps:
      - name: Deploy changed services
        run: |
          if [ "${{ needs.detect-changes.outputs.service-a }}" == "true" ]; then
            kubectl set image deployment/service-a service-a=myregistry/service-a:${{ github.sha }}
          fi
          if [ "${{ needs.detect-changes.outputs.service-b }}" == "true" ]; then
            kubectl set image deployment/service-b service-b=myregistry/service-b:${{ github.sha }}
          fi
```

## Example 4: Scheduled Nightly Builds

```yaml
name: Nightly Build & Test

on:
  schedule:
    - cron: '0 2 * * *'  # 2 AM UTC daily
  workflow_dispatch:

jobs:
  full-test-suite:
    runs-on: ubuntu-latest
    timeout-minutes: 120
    
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history
      
      - name: Setup environment
        run: |
          npm ci
          docker-compose up -d
      
      - name: Run full test suite
        run: |
          npm run test:unit
          npm run test:integration
          npm run test:e2e
      
      - name: Performance benchmarks
        run: npm run benchmark
      
      - name: Generate reports
        if: always()
        run: |
          npm run report:coverage
          npm run report:performance
      
      - name: Upload reports
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: nightly-reports-${{ github.run_number }}
          path: reports/
      
      - name: Notify on failure
        if: failure()
        uses: slackapi/slack-github-action@v1
        with:
          webhook-url: ${{ secrets.SLACK_WEBHOOK }}
          payload: |
            {
              "text": "❌ Nightly build failed",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*Nightly Build Failed*\n*Run:* ${{ github.run_number }}\n*Logs:* ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"
                  }
                }
              ]
            }
```

## Example 5: Multi-Stage Production Pipeline

```yaml
name: Production Pipeline

on:
  push:
    tags:
      - 'v*.*.*'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Validate version
        run: |
          TAG=${GITHUB_REF#refs/tags/}
          if [[ ! $TAG =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            echo "Invalid version tag: $TAG"
            exit 1
          fi

  build:
    needs: validate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build
        run: npm ci && npm run build
      - uses: actions/upload-artifact@v4
        with:
          name: build
          path: dist/

  test:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v4
        with:
          name: build
          path: dist/
      - name: Test
        run: npm test

  security-scan:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Snyk
        uses: snyk/actions/node@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}

  deploy-staging:
    needs: [test, security-scan]
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - name: Deploy to staging
        run: ./deploy.sh staging

  smoke-test-staging:
    needs: deploy-staging
    runs-on: ubuntu-latest
    steps:
      - name: Run smoke tests
        run: ./smoke-tests.sh https://staging.myapp.com

  deploy-production:
    needs: smoke-test-staging
    runs-on: ubuntu-latest
    environment: production  # Requires manual approval
    steps:
      - name: Deploy to production
        run: ./deploy.sh production
      
      - name: Create GitHub release
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: ${{ github.ref }}
          release_name: Release ${{ github.ref }}
          draft: false
          prerelease: false
```

---

> [!TIP]
> These examples demonstrate production-ready patterns. Adapt them to your specific needs, but keep the core principles: test thoroughly, deploy incrementally, and always have rollback capabilities.
