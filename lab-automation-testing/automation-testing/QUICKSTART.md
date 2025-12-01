# 🚀 Quick Start Guide - Python Automation Testing

## ⚡ 5-Minute Setup

### 1. Install Dependencies
```bash
cd automation-testing
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run Your First Test
```bash
# Run all tests
pytest

# Run FastAPI tests only
pytest fastapi-tests/

# Run Django tests only
pytest django-tests/

# Run with coverage
pytest --cov=app --cov-report=html
```

### 3. View Coverage Report
```bash
# Open coverage report in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

---

## 📝 Common Commands

### Running Tests

```bash
# Run specific test file
pytest fastapi-tests/test_api.py

# Run specific test function
pytest fastapi-tests/test_api.py::test_health_check

# Run tests matching pattern
pytest -k "test_create"

# Run tests with markers
pytest -m unit  # Only unit tests
pytest -m "not slow"  # Skip slow tests
pytest -m "integration or e2e"  # Integration OR E2E

# Run in parallel
pytest -n auto  # Use all CPU cores
pytest -n 4  # Use 4 workers

# Verbose output
pytest -v  # Verbose
pytest -vv  # Very verbose

# Stop on first failure
pytest -x

# Show print statements
pytest -s

# Run last failed tests
pytest --lf

# Debug mode
pytest --pdb  # Drop into debugger on failure
```

### Coverage

```bash
# Generate coverage report
pytest --cov=app --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=app --cov-report=html

# Generate XML coverage report (for CI/CD)
pytest --cov=app --cov-report=xml

# Fail if coverage below threshold
pytest --cov=app --cov-fail-under=80
```

### Load Testing

```bash
# Start Locust web UI
locust -f fastapi-tests/load_tests.py --host=http://localhost:8000

# Headless mode
locust -f fastapi-tests/load_tests.py \
  --host=http://localhost:8000 \
  --headless \
  --users 100 \
  --spawn-rate 10 \
  --run-time 5m \
  --html=report.html
```

---

## 🎯 FastAPI Testing Example

### 1. Create Your FastAPI App
```python
# app/main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}
```

### 2. Write Tests
```python
# tests/test_main.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

def test_read_item():
    response = client.get("/items/1")
    assert response.status_code == 200
    assert response.json() == {"item_id": 1}
```

### 3. Run Tests
```bash
pytest tests/test_main.py -v
```

---

## 🎯 Django Testing Example

### 1. Create Django Model
```python
# myapp/models.py
from django.db import models

class Item(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return self.name
```

### 2. Write Tests
```python
# tests/test_models.py
import pytest
from myapp.models import Item

@pytest.mark.django_db
def test_create_item():
    item = Item.objects.create(name="Test Item", price=99.99)
    assert item.name == "Test Item"
    assert item.price == 99.99

@pytest.mark.django_db
def test_item_str():
    item = Item.objects.create(name="Test Item", price=99.99)
    assert str(item) == "Test Item"
```

### 3. Run Tests
```bash
pytest tests/test_models.py -v
```

---

## 🔧 Configuration

### pytest.ini
Already configured with:
- Test discovery patterns
- Markers for categorizing tests
- Coverage settings
- Default options

### requirements.txt
All necessary dependencies included:
- pytest and plugins
- httpx for API testing
- Faker for test data
- Locust for load testing
- Code quality tools

---

## 📊 CI/CD Integration

### GitHub Actions
```yaml
# .github/workflows/tests.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest --cov=app --cov-report=xml
      - uses: codecov/codecov-action@v3
```

### GitLab CI
```yaml
# .gitlab-ci.yml
test:
  image: python:3.11
  script:
    - pip install -r requirements.txt
    - pytest --cov=app --cov-report=xml
  coverage: '/(?i)total.*? (100(?:\.0+)?\%|[1-9]?\d(?:\.\d+)?\%)$/'
```

---

## 🎓 Next Steps

1. **Read Documentation**
   - `docs/best-practices.md` - Testing best practices
   - `docs/testing-strategy.md` - Comprehensive testing strategy
   - `README.md` - Full documentation

2. **Explore Examples**
   - `fastapi-tests/` - FastAPI test examples
   - `django-tests/` - Django test examples
   - `common/` - Shared utilities

3. **Customize for Your Project**
   - Update fixtures in `conftest.py`
   - Add your models and endpoints
   - Adjust coverage thresholds
   - Configure CI/CD pipelines

4. **Run Load Tests**
   - Start your application
   - Run Locust tests
   - Analyze performance reports

---

## 💡 Pro Tips

1. **Use markers** to categorize tests:
   ```python
   @pytest.mark.unit
   @pytest.mark.integration
   @pytest.mark.slow
   ```

2. **Use fixtures** for reusable setup:
   ```python
   @pytest.fixture
   def sample_data():
       return {"name": "Test", "price": 10.0}
   ```

3. **Use parametrize** for multiple test cases:
   ```python
   @pytest.mark.parametrize("input,expected", [
       (1, 2),
       (2, 4),
       (3, 6),
   ])
   def test_double(input, expected):
       assert double(input) == expected
   ```

4. **Mock external services**:
   ```python
   @patch('app.services.external_api')
   def test_with_mock(mock_api):
       mock_api.return_value = {"status": "success"}
       result = my_function()
       assert result == expected
   ```

---

## 🆘 Troubleshooting

### Tests not discovered?
```bash
# Check test discovery
pytest --collect-only

# Ensure files start with test_
# Ensure functions start with test_
```

### Import errors?
```bash
# Install in editable mode
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Database errors in Django tests?
```bash
# Create test database
python manage.py migrate --settings=myproject.settings.test

# Use pytest-django
pip install pytest-django
```

### Slow tests?
```bash
# Run in parallel
pytest -n auto

# Skip slow tests
pytest -m "not slow"

# Profile tests
pytest --durations=10  # Show 10 slowest tests
```

---

## 📚 Resources

- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Django Testing](https://docs.djangoproject.com/en/stable/topics/testing/)
- [Locust Documentation](https://docs.locust.io/)

---

**Happy Testing! 🎉**
