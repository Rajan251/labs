# Python Automation Testing Guide - FastAPI & Django

## 🎯 Best Approach for Modern Organizations

### **Recommended Testing Stack (Industry Standard)**

1. **pytest** - The de-facto standard testing framework (used by 90%+ Python projects)
2. **pytest-asyncio** - For async FastAPI endpoints
3. **httpx** - Modern async HTTP client for API testing
4. **Faker** - Generate realistic test data
5. **pytest-cov** - Code coverage reporting
6. **pytest-xdist** - Parallel test execution
7. **Locust** - Load/performance testing
8. **Allure** - Beautiful test reporting
9. **GitHub Actions/GitLab CI** - CI/CD integration

---

## 📊 Why This Stack?

| Tool | Purpose | Industry Adoption |
|------|---------|-------------------|
| pytest | Unit, Integration, E2E Testing | 95%+ |
| httpx | API Testing (async support) | 80%+ |
| Faker | Test Data Generation | 70%+ |
| Locust | Load Testing | 60%+ |
| Allure | Test Reporting | 50%+ |

---

## 🏗️ Project Structure

```
automation-testing/
├── fastapi-tests/          # FastAPI specific tests
│   ├── conftest.py         # Pytest fixtures
│   ├── test_api.py         # API endpoint tests
│   ├── test_auth.py        # Authentication tests
│   ├── test_crud.py        # CRUD operation tests
│   ├── test_integration.py # Integration tests
│   └── load_tests.py       # Locust load tests
├── django-tests/           # Django specific tests
│   ├── conftest.py
│   ├── test_views.py       # View tests
│   ├── test_models.py      # Model tests
│   ├── test_api.py         # DRF API tests
│   ├── test_forms.py       # Form tests
│   └── load_tests.py       # Locust load tests
├── common/                 # Shared utilities
│   ├── fixtures.py         # Common fixtures
│   ├── helpers.py          # Test helpers
│   └── data_factory.py     # Faker data generators
├── ci-cd/                  # CI/CD configurations
│   ├── github-actions.yml
│   ├── gitlab-ci.yml
│   └── jenkins.groovy
└── docs/                   # Documentation
    ├── best-practices.md
    ├── testing-strategy.md
    └── troubleshooting.md
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install testing dependencies
pip install pytest pytest-asyncio pytest-cov pytest-xdist
pip install httpx faker locust allure-pytest
pip install fastapi[all] django djangorestframework  # If not already installed
```

### 2. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run in parallel
pytest -n auto

# Run specific test file
pytest fastapi-tests/test_api.py

# Run with markers
pytest -m "not slow"

# Generate Allure report
pytest --alluredir=./allure-results
allure serve ./allure-results
```

### 3. Run Load Tests

```bash
# FastAPI load test
locust -f fastapi-tests/load_tests.py --host=http://localhost:8000

# Django load test
locust -f django-tests/load_tests.py --host=http://localhost:8000
```

---

## 📋 Testing Levels

### 1. **Unit Tests** (70% of tests)
- Test individual functions/methods
- Fast execution (< 1ms per test)
- No external dependencies

### 2. **Integration Tests** (20% of tests)
- Test component interactions
- Database, cache, external APIs
- Moderate execution time

### 3. **End-to-End Tests** (10% of tests)
- Test complete user flows
- Full stack testing
- Slower execution

### 4. **Load/Performance Tests**
- Stress testing
- Scalability validation
- Performance benchmarking

---

## 🎯 Best Practices

### ✅ DO's
- ✅ Use fixtures for setup/teardown
- ✅ Mock external dependencies
- ✅ Use parametrize for multiple test cases
- ✅ Follow AAA pattern (Arrange, Act, Assert)
- ✅ Keep tests independent
- ✅ Use meaningful test names
- ✅ Maintain >80% code coverage
- ✅ Run tests in CI/CD pipeline

### ❌ DON'Ts
- ❌ Don't test framework code
- ❌ Don't use sleep() in tests
- ❌ Don't share state between tests
- ❌ Don't ignore flaky tests
- ❌ Don't skip writing tests for "simple" code

---

## 🔧 Configuration Files

### pytest.ini
```ini
[pytest]
testpaths = fastapi-tests django-tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    slow: marks tests as slow
    integration: integration tests
    unit: unit tests
    smoke: smoke tests
addopts = 
    -v
    --strict-markers
    --tb=short
    --cov-report=term-missing
```

### .coveragerc
```ini
[run]
source = .
omit = 
    */tests/*
    */venv/*
    */migrations/*
    */__pycache__/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
```

---

## 📊 Continuous Integration

All CI/CD examples are in the `ci-cd/` directory with:
- GitHub Actions workflow
- GitLab CI pipeline
- Jenkins pipeline
- Docker integration
- Automated reporting

---

## 📚 Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Django Testing](https://docs.djangoproject.com/en/stable/topics/testing/)
- [Locust Documentation](https://docs.locust.io/)

---

## 🤝 Contributing

1. Write tests for new features
2. Ensure all tests pass
3. Maintain code coverage >80%
4. Follow naming conventions
5. Update documentation

---

## 📝 License

MIT License - Feel free to use in your projects!
