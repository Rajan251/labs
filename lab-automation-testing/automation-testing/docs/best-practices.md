# Python Automation Testing - Best Practices Guide

## 🎯 Testing Philosophy

### The Testing Pyramid
```
        /\
       /E2E\      10% - End-to-End Tests (Slow, Expensive)
      /------\
     /  INT   \   20% - Integration Tests (Medium Speed)
    /----------\
   /   UNIT     \ 70% - Unit Tests (Fast, Cheap)
  /--------------\
```

### Key Principles
1. **Fast Feedback** - Tests should run quickly
2. **Isolation** - Tests should not depend on each other
3. **Repeatability** - Same input = Same output
4. **Maintainability** - Easy to understand and update
5. **Coverage** - Aim for >80% code coverage

---

## 📋 Testing Best Practices

### 1. Test Organization

#### ✅ DO:
```python
# Good: Clear, descriptive test names
def test_user_login_with_valid_credentials_returns_token():
    """Test that valid credentials return an auth token"""
    # Test implementation
```

#### ❌ DON'T:
```python
# Bad: Vague test name
def test_login():
    # What does this test?
```

### 2. AAA Pattern (Arrange, Act, Assert)

```python
def test_create_user():
    # Arrange - Set up test data
    user_data = {"username": "test", "email": "test@example.com"}
    
    # Act - Perform the action
    user = User.objects.create(**user_data)
    
    # Assert - Verify the result
    assert user.username == "test"
    assert user.email == "test@example.com"
```

### 3. Use Fixtures for Setup

```python
@pytest.fixture
def authenticated_user(client):
    """Reusable fixture for authenticated user"""
    user = User.objects.create_user(username="test", password="pass")
    client.force_login(user)
    return user

def test_profile_access(client, authenticated_user):
    """Test uses the fixture"""
    response = client.get("/profile/")
    assert response.status_code == 200
```

### 4. Parametrize for Multiple Cases

```python
@pytest.mark.parametrize("username,email,expected_valid", [
    ("valid_user", "valid@example.com", True),
    ("", "valid@example.com", False),  # Empty username
    ("valid_user", "invalid-email", False),  # Invalid email
    ("ab", "valid@example.com", False),  # Too short
])
def test_user_validation(username, email, expected_valid):
    is_valid = validate_user(username, email)
    assert is_valid == expected_valid
```

### 5. Mock External Dependencies

```python
from unittest.mock import patch, Mock

@patch('app.services.external_api.get_data')
def test_process_external_data(mock_get_data):
    """Mock external API call"""
    # Arrange
    mock_get_data.return_value = {"status": "success", "data": [1, 2, 3]}
    
    # Act
    result = process_data()
    
    # Assert
    assert result == [1, 2, 3]
    mock_get_data.assert_called_once()
```

### 6. Test Edge Cases

```python
def test_divide_by_zero():
    """Test edge case - division by zero"""
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)

def test_empty_list():
    """Test edge case - empty list"""
    assert sum_list([]) == 0

def test_null_input():
    """Test edge case - null input"""
    with pytest.raises(ValueError):
        process_data(None)
```

### 7. Use Markers for Test Categories

```python
@pytest.mark.unit
def test_simple_function():
    """Fast unit test"""
    pass

@pytest.mark.integration
def test_database_interaction():
    """Slower integration test"""
    pass

@pytest.mark.slow
def test_complex_operation():
    """Very slow test"""
    pass

# Run only unit tests:
# pytest -m unit
```

### 8. Test Database Transactions

```python
@pytest.mark.django_db(transaction=True)
def test_atomic_operation():
    """Test that uses database transactions"""
    with transaction.atomic():
        User.objects.create(username="user1")
        User.objects.create(username="user2")
    
    assert User.objects.count() == 2
```

### 9. Clean Up After Tests

```python
@pytest.fixture
def temp_file():
    """Fixture that cleans up after itself"""
    file_path = "/tmp/test_file.txt"
    
    # Setup
    with open(file_path, 'w') as f:
        f.write("test data")
    
    yield file_path
    
    # Teardown
    if os.path.exists(file_path):
        os.remove(file_path)
```

### 10. Test Error Messages

```python
def test_validation_error_message():
    """Test that error messages are helpful"""
    with pytest.raises(ValidationError) as exc_info:
        validate_email("invalid-email")
    
    assert "Invalid email format" in str(exc_info.value)
```

---

## 🚀 Performance Testing Best Practices

### 1. Set Realistic Load Targets

```python
# Define performance targets
TARGET_RESPONSE_TIME = 200  # ms
TARGET_THROUGHPUT = 1000  # requests/second
TARGET_ERROR_RATE = 0.01  # 1%

def test_api_performance(benchmark):
    """Test API performance meets targets"""
    result = benchmark(api_call)
    assert result.stats.mean < TARGET_RESPONSE_TIME / 1000
```

### 2. Gradual Load Increase

```python
# Locust load shape for gradual increase
class GradualLoadShape(LoadTestShape):
    def tick(self):
        run_time = self.get_run_time()
        
        if run_time < 60:
            return (10, 1)  # 10 users
        elif run_time < 120:
            return (50, 5)  # 50 users
        elif run_time < 180:
            return (100, 10)  # 100 users
        else:
            return None
```

### 3. Monitor System Resources

```python
import psutil

def test_memory_usage():
    """Test that memory usage stays within limits"""
    process = psutil.Process()
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # Perform operations
    for _ in range(1000):
        process_data()
    
    final_memory = process.memory_info().rss / 1024 / 1024
    memory_increase = final_memory - initial_memory
    
    assert memory_increase < 100  # Less than 100MB increase
```

---

## 🔒 Security Testing Best Practices

### 1. Test Authentication

```python
def test_unauthenticated_access_denied(client):
    """Test that protected endpoints require authentication"""
    response = client.get("/api/protected/")
    assert response.status_code == 401

def test_invalid_token_rejected(client):
    """Test that invalid tokens are rejected"""
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/api/protected/", headers=headers)
    assert response.status_code == 401
```

### 2. Test Authorization

```python
def test_user_cannot_access_admin_endpoint(authenticated_client):
    """Test that regular users cannot access admin endpoints"""
    response = authenticated_client.get("/admin/users/")
    assert response.status_code == 403

def test_user_cannot_modify_other_users_data(authenticated_client):
    """Test that users can only modify their own data"""
    response = authenticated_client.put("/users/999/", {"name": "Hacked"})
    assert response.status_code in [403, 404]
```

### 3. Test Input Validation

```python
def test_sql_injection_prevention(client):
    """Test that SQL injection is prevented"""
    malicious_input = "'; DROP TABLE users; --"
    response = client.get(f"/search?q={malicious_input}")
    assert response.status_code in [200, 400]
    # Verify database is intact
    assert User.objects.count() > 0

def test_xss_prevention(client):
    """Test that XSS attacks are prevented"""
    malicious_script = "<script>alert('XSS')</script>"
    response = client.post("/comments/", {"text": malicious_script})
    # Verify script is escaped in response
    assert "<script>" not in response.content.decode()
```

---

## 📊 Coverage Best Practices

### 1. Aim for Meaningful Coverage

```bash
# Generate coverage report
pytest --cov=app --cov-report=html --cov-report=term-missing

# View missing lines
pytest --cov=app --cov-report=term-missing
```

### 2. Exclude Irrelevant Code

```ini
# .coveragerc
[run]
omit =
    */tests/*
    */migrations/*
    */venv/*
    */__pycache__/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if __name__ == .__main__.:
```

### 3. Set Coverage Thresholds

```bash
# Fail if coverage is below 80%
pytest --cov=app --cov-fail-under=80
```

---

## 🐛 Debugging Failed Tests

### 1. Use pytest -vv for Verbose Output

```bash
pytest -vv  # Very verbose
pytest -vvv  # Even more verbose
```

### 2. Use pytest --pdb for Debugging

```bash
pytest --pdb  # Drop into debugger on failure
pytest --pdb --maxfail=1  # Stop after first failure
```

### 3. Print Debug Information

```python
def test_complex_calculation():
    result = complex_calculation(10, 20)
    print(f"DEBUG: Result = {result}")  # Use -s flag to see prints
    assert result == 30
```

```bash
pytest -s  # Show print statements
```

### 4. Use pytest-timeout

```python
@pytest.mark.timeout(5)  # Timeout after 5 seconds
def test_slow_operation():
    slow_operation()
```

---

## 📝 Documentation Best Practices

### 1. Document Test Purpose

```python
def test_user_registration_sends_welcome_email():
    """
    Test that user registration triggers a welcome email.
    
    Given: A new user registration request
    When: The user is successfully created
    Then: A welcome email should be sent to the user's email address
    """
    # Test implementation
```

### 2. Document Complex Test Setup

```python
@pytest.fixture
def complex_test_data():
    """
    Create complex test data structure.
    
    Creates:
    - 5 users with different roles
    - 10 items with various categories
    - 20 orders linking users and items
    
    Returns:
        dict: Dictionary containing all created objects
    """
    # Setup implementation
```

---

## 🎓 Common Pitfalls to Avoid

### ❌ 1. Tests Depending on Each Other

```python
# BAD: Tests depend on execution order
def test_create_user():
    global user_id
    user_id = create_user()

def test_update_user():
    update_user(user_id)  # Fails if test_create_user didn't run
```

### ❌ 2. Using sleep() in Tests

```python
# BAD: Using sleep
def test_async_operation():
    trigger_async_task()
    time.sleep(5)  # Unreliable and slow
    assert task_completed()

# GOOD: Use proper waiting
def test_async_operation():
    trigger_async_task()
    wait_for_condition(lambda: task_completed(), timeout=5)
```

### ❌ 3. Testing Implementation Instead of Behavior

```python
# BAD: Testing implementation details
def test_user_creation_calls_save():
    with patch.object(User, 'save') as mock_save:
        create_user()
        mock_save.assert_called_once()

# GOOD: Testing behavior
def test_user_creation_persists_to_database():
    create_user(username="test")
    assert User.objects.filter(username="test").exists()
```

### ❌ 4. Overly Complex Tests

```python
# BAD: Testing too much in one test
def test_entire_user_workflow():
    # Register user
    # Login user
    # Update profile
    # Create post
    # Comment on post
    # Logout
    # ... 50 more assertions

# GOOD: Split into focused tests
def test_user_registration():
    # Test only registration

def test_user_login():
    # Test only login
```

---

## 🔄 Continuous Improvement

1. **Review test failures** - Don't ignore flaky tests
2. **Refactor tests** - Keep tests maintainable
3. **Update tests** - When requirements change
4. **Monitor coverage** - Track trends over time
5. **Share knowledge** - Document learnings

---

## 📚 Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Testing Best Practices](https://testdriven.io/blog/testing-best-practices/)
- [Python Testing with pytest (Book)](https://pragprog.com/titles/bopytest/)
- [Test-Driven Development](https://www.obeythetestinggoat.com/)
