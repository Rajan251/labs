# GitHub Actions CI/CD Guide - Part 4: Deployment Stage

## Overview

The deployment stage pushes your application to production environments. This section covers deployments to Kubernetes, AWS, Docker registries, and other platforms.

## Kubernetes Deployment

### Basic kubectl Deployment

```yaml
name: Deploy to Kubernetes

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure kubectl
        uses: azure/k8s-set-context@v3
        with:
          method: kubeconfig
          kubeconfig: ${{ secrets.KUBE_CONFIG }}
      
      - name: Deploy to Kubernetes
        run: |
          kubectl apply -f k8s-manifests/
          kubectl rollout status deployment/myapp -n production
      
      - name: Verify deployment
        run: |
          kubectl get pods -n production
          kubectl get svc -n production
```

### Helm Deployment

```yaml
jobs:
  deploy-helm:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Install Helm
        uses: azure/setup-helm@v3
        with:
          version: '3.13.0'
      
      - name: Configure kubectl
        uses: azure/k8s-set-context@v3
        with:
          method: kubeconfig
          kubeconfig: ${{ secrets.KUBE_CONFIG }}
      
      - name: Deploy with Helm
        run: |
          helm upgrade --install myapp ./helm-chart \
            --namespace production \
            --create-namespace \
            --set image.tag=${{ github.sha }} \
            --set image.repository=myregistry/myapp \
            --wait \
            --timeout 5m
      
      - name: Helm test
        run: helm test myapp -n production
```

### Advanced Kubernetes with Kustomize

```yaml
jobs:
  deploy-kustomize:
    runs-on: ubuntu-latest
    environment: production
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Kustomize
        uses: imranismail/setup-kustomize@v2
      
      - name: Configure kubectl
        uses: azure/k8s-set-context@v3
        with:
          method: kubeconfig
          kubeconfig: ${{ secrets.KUBE_CONFIG }}
      
      - name: Update image tag
        working-directory: k8s/overlays/production
        run: |
          kustomize edit set image myapp=myregistry/myapp:${{ github.sha }}
      
      - name: Deploy
        run: |
          kustomize build k8s/overlays/production | kubectl apply -f -
          kubectl rollout status deployment/myapp -n production
```

## AWS Deployments

### Deploy to AWS ECS

```yaml
name: Deploy to AWS ECS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2
      
      - name: Build and push image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: myapp
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
      
      - name: Update ECS task definition
        id: task-def
        uses: aws-actions/amazon-ecs-render-task-definition@v1
        with:
          task-definition: task-definition.json
          container-name: myapp
          image: ${{ steps.login-ecr.outputs.registry }}/myapp:${{ github.sha }}
      
      - name: Deploy to ECS
        uses: aws-actions/amazon-ecs-deploy-task-definition@v1
        with:
          task-definition: ${{ steps.task-def.outputs.task-definition }}
          service: myapp-service
          cluster: production-cluster
          wait-for-service-stability: true
```

### Deploy to AWS Lambda

```yaml
jobs:
  deploy-lambda:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsRole
          aws-region: us-east-1
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt -t package/
          cp -r src/* package/
      
      - name: Package Lambda
        run: |
          cd package
          zip -r ../lambda.zip .
      
      - name: Deploy to Lambda
        run: |
          aws lambda update-function-code \
            --function-name myapp \
            --zip-file fileb://lambda.zip
```

### Deploy to AWS S3 (Static Site)

```yaml
jobs:
  deploy-s3:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20.x'
      
      - name: Build
        run: |
          npm ci
          npm run build
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Deploy to S3
        run: |
          aws s3 sync dist/ s3://my-website-bucket --delete
      
      - name: Invalidate CloudFront
        run: |
          aws cloudfront create-invalidation \
            --distribution-id ${{ secrets.CLOUDFRONT_DISTRIBUTION_ID }} \
            --paths "/*"
```

## Docker Hub Deployment

### Build and Push to Docker Hub

```yaml
name: Docker Hub Deploy

on:
  push:
    tags:
      - 'v*'

jobs:
  docker:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Docker meta
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: |
            username/myapp
          tags: |
            type=ref,event=branch
            type=ref,event=pr
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
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

## GitHub Pages Deployment

### Deploy Static Site to GitHub Pages

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [main]

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20.x'
      
      - name: Install and build
        run: |
          npm ci
          npm run build
      
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: dist/
  
  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

## Environment Protection Rules

### Using Environments

```yaml
jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - name: Deploy to staging
        run: echo "Deploying to staging"
  
  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://myapp.com
    steps:
      - name: Deploy to production
        run: echo "Deploying to production"
```

### Manual Approval

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: production
      # Requires manual approval in GitHub UI
    steps:
      - name: Deploy
        run: ./deploy.sh
```

## Rollback Strategy

### Automated Rollback on Failure

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy new version
        id: deploy
        run: |
          kubectl set image deployment/myapp myapp=myapp:${{ github.sha }}
          kubectl rollout status deployment/myapp
        continue-on-error: true
      
      - name: Rollback on failure
        if: steps.deploy.outcome == 'failure'
        run: |
          kubectl rollout undo deployment/myapp
          echo "Deployment failed, rolled back to previous version"
          exit 1
      
      - name: Run smoke tests
        id: smoke-test
        run: ./smoke-tests.sh
        continue-on-error: true
      
      - name: Rollback if smoke tests fail
        if: steps.smoke-test.outcome == 'failure'
        run: |
          kubectl rollout undo deployment/myapp
          echo "Smoke tests failed, rolled back"
          exit 1
```

## Blue-Green Deployment

```yaml
jobs:
  blue-green-deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to green environment
        run: |
          kubectl apply -f k8s/green-deployment.yaml
          kubectl rollout status deployment/myapp-green
      
      - name: Run health checks
        run: ./health-check.sh green
      
      - name: Switch traffic to green
        run: |
          kubectl patch service myapp -p '{"spec":{"selector":{"version":"green"}}}'
      
      - name: Monitor for 5 minutes
        run: sleep 300
      
      - name: Cleanup blue environment
        run: kubectl delete deployment myapp-blue
```

## Common Deployment Problems & Solutions

### Problem 1: Kubernetes Authentication Fails

**Symptom**: `kubectl` commands fail with auth errors

**Solution**:
```yaml
- name: Configure kubectl
  uses: azure/k8s-set-context@v3
  with:
    method: kubeconfig
    kubeconfig: ${{ secrets.KUBE_CONFIG }}  # Base64 encoded kubeconfig

# Or use service account token
- name: Set kubectl context
  run: |
    kubectl config set-cluster mycluster --server=${{ secrets.K8S_SERVER }}
    kubectl config set-credentials github --token=${{ secrets.K8S_TOKEN }}
    kubectl config set-context default --cluster=mycluster --user=github
    kubectl config use-context default
```

### Problem 2: Docker Push Rate Limit

**Symptom**: Docker Hub rate limit exceeded

**Solution**:
```yaml
# Always authenticate to get higher limits
- name: Login to Docker Hub
  uses: docker/login-action@v3
  with:
    username: ${{ secrets.DOCKERHUB_USERNAME }}
    password: ${{ secrets.DOCKERHUB_TOKEN }}

# Or use GitHub Container Registry
- name: Login to GHCR
  uses: docker/login-action@v3
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}
```

### Problem 3: Deployment Timeout

**Symptom**: Deployment hangs and times out

**Solution**:
```yaml
- name: Deploy with timeout
  timeout-minutes: 10
  run: |
    kubectl apply -f k8s/
    kubectl rollout status deployment/myapp --timeout=5m
```

### Problem 4: AWS Credentials Invalid

**Symptom**: AWS API calls fail

**Solution**:
```yaml
# Use OIDC instead of long-lived credentials
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsRole
    aws-region: us-east-1
    # No access keys needed!
```

### Problem 5: Helm Deployment Fails

**Symptom**: Helm upgrade fails

**Solution**:
```yaml
- name: Helm upgrade with rollback
  run: |
    helm upgrade --install myapp ./chart \
      --atomic \  # Rollback on failure
      --cleanup-on-fail \
      --wait \
      --timeout 5m
```

## Deployment Best Practices

1. **Use environment protection**: Require manual approval for production
2. **Implement health checks**: Verify deployment before marking success
3. **Enable rollback**: Always have a rollback strategy
4. **Use OIDC**: Avoid long-lived credentials
5. **Tag images properly**: Use semantic versioning or commit SHA
6. **Monitor deployments**: Set up alerts for failures
7. **Test in staging first**: Deploy to staging before production
8. **Use blue-green or canary**: Minimize downtime and risk

---

> [!WARNING]
> Never commit AWS credentials or kubeconfig files to your repository. Always use GitHub Secrets and consider using OIDC for AWS authentication.
