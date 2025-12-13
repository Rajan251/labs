# Contributing to K8s Master Lab

First off, thank you for considering contributing to K8s Master Lab! It's people like you that make this project a great learning resource for the Kubernetes community.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Process](#development-process)
- [Style Guidelines](#style-guidelines)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

### Our Pledge

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on what is best for the community
- Show empathy towards other community members

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce**
- **Expected behavior**
- **Actual behavior**
- **Environment details** (K8s version, OS, etc.)
- **Screenshots** (if applicable)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- **Clear title and description**
- **Use case** - why is this enhancement needed?
- **Proposed solution**
- **Alternatives considered**

### Contributing Examples

We always welcome new examples! To contribute:

1. Ensure the example is production-ready and follows best practices
2. Add comprehensive comments explaining each section
3. Include a README with:
   - Purpose of the example
   - Prerequisites
   - Deployment instructions
   - Expected output
   - Cleanup instructions

### Contributing Labs

Labs should be:

- **Progressive** - build on previous knowledge
- **Hands-on** - include practical exercises
- **Complete** - include objectives, steps, and solutions
- **Tested** - verify all steps work as described

Lab structure:
```markdown
# Lab X: Title

## Objectives
- Learning objective 1
- Learning objective 2

## Prerequisites
- Required knowledge
- Required tools

## Steps

### Step 1: Description
Instructions...

### Step 2: Description
Instructions...

## Verification
How to verify the lab was completed successfully

## Cleanup
How to clean up resources

## Solution
Complete solution with explanations
```

### Contributing Documentation

Documentation contributions are highly valued:

- **Fix typos and grammar**
- **Improve clarity**
- **Add missing information**
- **Update outdated content**
- **Add diagrams and visuals**

## Development Process

### Setting Up Development Environment

1. **Fork the repository**
   ```bash
   # Click "Fork" on GitHub, then:
   git clone https://github.com/YOUR-USERNAME/k8s-master-lab.git
   cd k8s-master-lab
   ```

2. **Add upstream remote**
   ```bash
   git remote add upstream https://github.com/ORIGINAL-OWNER/k8s-master-lab.git
   ```

3. **Set up Kubernetes cluster**
   ```bash
   # Use Minikube, K3d, or Kind
   ./scripts/setup/setup-minikube.sh
   ```

4. **Install development tools**
   ```bash
   # YAML validation
   brew install kubeval kube-score
   
   # Helm
   brew install helm
   
   # Pre-commit hooks
   pip install pre-commit
   pre-commit install
   ```

### Making Changes

1. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. **Make your changes**
   - Follow the style guidelines
   - Add tests if applicable
   - Update documentation

3. **Test your changes**
   ```bash
   # Validate YAML files
   find . -name "*.yaml" -exec kubeval {} \;
   find . -name "*.yaml" -exec kube-score score {} \;
   
   # Test Helm charts
   helm lint helm/your-chart/
   
   # Deploy and test
   kubectl apply -f your-changes.yaml
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "type: description"
   ```

5. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

## Style Guidelines

### YAML Files

```yaml
# Use 2 spaces for indentation
apiVersion: v1
kind: Pod
metadata:
  # Use descriptive names
  name: my-application-pod
  # Add labels for organization
  labels:
    app: my-application
    tier: backend
    environment: production
  # Add annotations for documentation
  annotations:
    description: "This pod runs the backend API"
spec:
  containers:
  - name: api
    image: myapp:1.0.0
    # Always specify resource requests and limits
    resources:
      requests:
        memory: "128Mi"
        cpu: "100m"
      limits:
        memory: "256Mi"
        cpu: "200m"
    # Add comments explaining non-obvious configurations
    env:
    - name: DATABASE_URL
      valueFrom:
        secretKeyRef:
          name: db-credentials
          key: url
```

### Best Practices for Examples

1. **Use meaningful names**
   - ✅ `frontend-deployment.yaml`
   - ❌ `deploy1.yaml`

2. **Include resource limits**
   - Always specify requests and limits
   - Use realistic values

3. **Add security contexts**
   ```yaml
   securityContext:
     runAsNonRoot: true
     runAsUser: 1000
     allowPrivilegeEscalation: false
   ```

4. **Use namespaces**
   - Don't deploy to `default` namespace
   - Create dedicated namespaces for examples

5. **Add health checks**
   ```yaml
   livenessProbe:
     httpGet:
       path: /health
       port: 8080
   readinessProbe:
     httpGet:
       path: /ready
       port: 8080
   ```

### Documentation Style

- Use clear, concise language
- Include code examples
- Add diagrams where helpful
- Use proper markdown formatting
- Link to related resources

### Markdown Formatting

```markdown
# H1 for main title
## H2 for sections
### H3 for subsections

**Bold** for emphasis
*Italic* for terms
`code` for commands and filenames

\`\`\`bash
# Code blocks with language specification
kubectl get pods
\`\`\`

> Note: Use blockquotes for important notes

- Bullet points for lists
1. Numbered lists for steps
```

## Commit Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification.

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks

### Examples

```bash
# Adding a new example
git commit -m "feat(pods): add sidecar pattern example"

# Fixing documentation
git commit -m "docs(setup): fix minikube installation command"

# Updating a lab
git commit -m "fix(labs): correct step 3 in beginner lab 5"

# Adding tests
git commit -m "test(helm): add validation tests for database chart"
```

## Pull Request Process

### Before Submitting

1. **Update documentation** if needed
2. **Add tests** for new features
3. **Ensure all tests pass**
4. **Update CHANGELOG.md** if applicable
5. **Rebase on latest main**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

### PR Template

When creating a PR, include:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Breaking change

## Testing
How has this been tested?

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] YAML files validated
```

### Review Process

1. **Automated checks** must pass
   - YAML validation
   - Linting
   - Tests

2. **Code review** by maintainers
   - At least one approval required
   - Address all comments

3. **Final approval** and merge
   - Squash and merge for clean history

## Testing Guidelines

### YAML Validation

```bash
# Validate all YAML files
./scripts/test/validate-yaml.sh

# Or manually
kubeval your-file.yaml
kube-score score your-file.yaml
```

### Integration Testing

```bash
# Deploy to test cluster
kubectl apply -f your-changes.yaml

# Verify deployment
kubectl get all

# Test functionality
# (specific to your changes)

# Clean up
kubectl delete -f your-changes.yaml
```

### Helm Chart Testing

```bash
# Lint chart
helm lint helm/your-chart/

# Template and validate
helm template helm/your-chart/ | kubeval

# Install to test cluster
helm install test-release helm/your-chart/

# Run tests
helm test test-release

# Clean up
helm uninstall test-release
```

## Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- GitHub contributors page

## Questions?

- **General questions**: [GitHub Discussions](https://github.com/yourusername/k8s-master-lab/discussions)
- **Bug reports**: [GitHub Issues](https://github.com/yourusername/k8s-master-lab/issues)
- **Security issues**: Email security@example.com

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to K8s Master Lab! 🎉**
