# 🚀 Advanced Testing Concepts & New Feature Testing

## 📋 Table of Contents
1. [Advanced Testing Patterns](#advanced-testing-patterns)
2. [Test-Driven Development (TDD)](#test-driven-development-tdd)
3. [Behavior-Driven Development (BDD)](#behavior-driven-development-bdd)
4. [Testing New Features](#testing-new-features)
5. [Advanced Pytest Techniques](#advanced-pytest-techniques)
6. [Performance Testing](#performance-testing)
7. [Contract Testing](#contract-testing)
8. [Mutation Testing](#mutation-testing)

---

## 🎯 Advanced Testing Patterns

### 1. Property-Based Testing

Test with automatically generated test cases using Hypothesis:

```python
# Install: pip install hypothesis

from hypothesis import given, strategies as st
import pytest

@given(st.integers(), st.integers())
def test_addition_commutative(a, b):
    """Test that addition is commutative"""
    assert a + b == b + a

@given(st.lists(st.integers()))
def test_reverse_twice_is_identity(lst):
    """Test that reversing twice returns original list"""
    assert list(reversed(list(reversed(lst)))) == lst

@given(st.text(), st.text())
def test_string_concatenation(s1, s2):
    """Test string concatenation properties"""
    result = s1 + s2
    assert len(result) == len(s1) + len(s2)
    assert result.startswith(s1)
    assert result.endswith(s2)

# Advanced example with custom strategies
from hypothesis import strategies as st

user_strategy = st.fixed_dictionaries({
    'username': st.text(min_size=3, max_size=20),
    'email': st.emails(),
    'age': st.integers(min_value=18, max_value=120)
})

@given(user_strategy)
def test_user_creation(user_data):
    """Test user creation with various inputs"""
    user = create_user(**user_data)
    assert user.username == user_data['username']
    assert user.email == user_data['email']
    assert user.age == user_data['age']
```

### 2. Snapshot Testing

Compare output against saved snapshots:

```python
# Install: pip install pytest-snapshot

def test_api_response_snapshot(snapshot, client):
    """Test API response matches snapshot"""
    response = client.get("/api/users/1")
    snapshot.assert_match(response.json())

def test_html_rendering_snapshot(snapshot):
    """Test HTML output matches snapshot"""
    html = render_template('user_profile.html', user=test_user)
    snapshot.assert_match(html)

# Update snapshots with: pytest --snapshot-update
```

### 3. Approval Testing

```python
# Install: pip install approvaltests

from approvaltests import verify

def test_complex_report_generation():
    """Test complex report output"""
    report = generate_monthly_report(year=2024, month=12)
    verify(report)

# First run creates .approved file
# Subsequent runs compare against it
```

### 4. Chaos Engineering Tests

```python
import random
import pytest
from unittest.mock import patch

@pytest.mark.chaos
def test_api_handles_random_failures(client):
    """Test API resilience to random failures"""
    
    # Randomly fail database calls
    with patch('app.database.get_connection') as mock_db:
        if random.random() < 0.3:  # 30% failure rate
            mock_db.side_effect = Exception("Database unavailable")
        
        response = client.get("/api/items/")
        
        # Should handle gracefully
        assert response.status_code in [200, 503]
        if response.status_code == 503:
            assert "retry" in response.json()

@pytest.mark.chaos
def test_timeout_handling():
    """Test handling of slow responses"""
    import time
    
    with patch('app.services.external_api.call') as mock_api:
        # Simulate slow response
        def slow_response(*args, **kwargs):
            time.sleep(random.uniform(0, 5))
            return {"data": "test"}
        
        mock_api.side_effect = slow_response
        
        # Should timeout and handle gracefully
        result = call_with_timeout(timeout=2)
        assert result is not None or "timeout" in str(result)
```

---

## 🔴 Test-Driven Development (TDD)

### TDD Workflow: Red → Green → Refactor

#### Step 1: Write Failing Test (RED)
```python
# tests/test_user_service.py

def test_create_user_with_valid_data():
    """Test creating user with valid data"""
    # This test will FAIL initially
    user_data = {
        'username': 'newuser',
        'email': 'new@example.com',
        'password': 'SecurePass123!'
    }
    
    user = UserService.create_user(user_data)
    
    assert user.id is not None
    assert user.username == 'newuser'
    assert user.email == 'new@example.com'
    assert user.password != 'SecurePass123!'  # Should be hashed
    assert user.created_at is not None
```

#### Step 2: Write Minimal Code (GREEN)
```python
# app/services/user_service.py

class UserService:
    @staticmethod
    def create_user(user_data):
        """Create a new user"""
        from app.models import User
        from app.core.security import hash_password
        
        user = User(
            username=user_data['username'],
            email=user_data['email'],
            password=hash_password(user_data['password'])
        )
        user.save()
        return user
```

#### Step 3: Refactor (REFACTOR)
```python
# app/services/user_service.py (improved)

class UserService:
    @staticmethod
    def create_user(user_data):
        """Create a new user with validation"""
        # Validate input
        UserValidator.validate(user_data)
        
        # Hash password
        hashed_password = SecurityService.hash_password(
            user_data['password']
        )
        
        # Create user
        user = User.objects.create(
            username=user_data['username'],
            email=user_data['email'],
            password=hashed_password
        )
        
        # Send welcome email
        EmailService.send_welcome_email(user)
        
        return user
```

---

## 🥒 Behavior-Driven Development (BDD)

### Using pytest-bdd

```python
# Install: pip install pytest-bdd

# features/user_registration.feature
"""
Feature: User Registration
  As a new user
  I want to register an account
  So that I can access the application

  Scenario: Successful registration
    Given I am on the registration page
    When I fill in the registration form with valid data
    And I submit the form
    Then I should see a success message
    And I should receive a welcome email
    And I should be redirected to the dashboard

  Scenario: Registration with existing email
    Given I am on the registration page
    And a user with email "existing@example.com" already exists
    When I fill in the registration form with email "existing@example.com"
    And I submit the form
    Then I should see an error message "Email already registered"
    And I should remain on the registration page
"""

# tests/step_defs/test_user_registration.py
from pytest_bdd import scenarios, given, when, then, parsers

scenarios('../features/user_registration.feature')

@given('I am on the registration page')
def on_registration_page(browser):
    browser.visit('/register')

@given(parsers.parse('a user with email "{email}" already exists'))
def existing_user(email):
    User.objects.create(email=email, username='existing')

@when('I fill in the registration form with valid data')
def fill_registration_form(browser):
    browser.fill('username', 'newuser')
    browser.fill('email', 'new@example.com')
    browser.fill('password', 'SecurePass123!')

@when(parsers.parse('I fill in the registration form with email "{email}"'))
def fill_form_with_email(browser, email):
    browser.fill('email', email)

@when('I submit the form')
def submit_form(browser):
    browser.find_by_css('button[type="submit"]').click()

@then('I should see a success message')
def see_success_message(browser):
    assert browser.is_text_present('Registration successful')

@then(parsers.parse('I should see an error message "{message}"'))
def see_error_message(browser, message):
    assert browser.is_text_present(message)
```

---

## 🆕 Testing New Features - Complete Workflow

### Scenario: Adding a "User Profile Picture Upload" Feature

#### Step 1: Create Feature Branch
```bash
git checkout -b feature/profile-picture-upload
```

#### Step 2: Write Tests FIRST (TDD Approach)

##### 2.1 Unit Tests
```python
# tests/unit/test_profile_service.py

import pytest
from app.services.profile_service import ProfileService

class TestProfilePictureUpload:
    """Test suite for profile picture upload feature"""
    
    def test_upload_valid_image(self, sample_image):
        """Test uploading valid image file"""
        result = ProfileService.upload_profile_picture(
            user_id=1,
            image_file=sample_image
        )
        
        assert result['success'] is True
        assert result['url'].startswith('https://')
        assert result['url'].endswith('.jpg')
    
    def test_upload_invalid_file_type(self, sample_pdf):
        """Test uploading invalid file type"""
        with pytest.raises(ValidationError) as exc:
            ProfileService.upload_profile_picture(
                user_id=1,
                image_file=sample_pdf
            )
        
        assert 'Invalid file type' in str(exc.value)
    
    def test_upload_oversized_image(self, large_image):
        """Test uploading image exceeding size limit"""
        with pytest.raises(ValidationError) as exc:
            ProfileService.upload_profile_picture(
                user_id=1,
                image_file=large_image
            )
        
        assert 'File too large' in str(exc.value)
    
    def test_image_resizing(self, large_valid_image):
        """Test that large images are resized"""
        result = ProfileService.upload_profile_picture(
            user_id=1,
            image_file=large_valid_image
        )
        
        # Verify image was resized
        from PIL import Image
        img = Image.open(result['path'])
        assert img.width <= 500
        assert img.height <= 500
    
    def test_delete_old_profile_picture(self, user_with_picture):
        """Test that old picture is deleted when uploading new one"""
        old_picture_path = user_with_picture.profile_picture
        
        ProfileService.upload_profile_picture(
            user_id=user_with_picture.id,
            image_file=sample_image
        )
        
        # Old picture should be deleted
        assert not os.path.exists(old_picture_path)
```

##### 2.2 Integration Tests
```python
# tests/integration/test_profile_api.py

import pytest
from fastapi.testclient import TestClient

class TestProfilePictureAPI:
    """Integration tests for profile picture API"""
    
    def test_upload_endpoint(self, authenticated_client, sample_image):
        """Test POST /api/profile/picture endpoint"""
        files = {'file': ('test.jpg', sample_image, 'image/jpeg')}
        
        response = authenticated_client.post(
            '/api/profile/picture',
            files=files
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'url' in data
        assert data['url'].startswith('https://')
    
    def test_upload_without_authentication(self, client, sample_image):
        """Test upload requires authentication"""
        files = {'file': ('test.jpg', sample_image, 'image/jpeg')}
        
        response = client.post('/api/profile/picture', files=files)
        
        assert response.status_code == 401
    
    def test_get_profile_picture(self, authenticated_client, user_with_picture):
        """Test GET /api/profile/picture endpoint"""
        response = authenticated_client.get('/api/profile/picture')
        
        assert response.status_code == 200
        assert response.headers['content-type'].startswith('image/')
    
    def test_delete_profile_picture(self, authenticated_client, user_with_picture):
        """Test DELETE /api/profile/picture endpoint"""
        response = authenticated_client.delete('/api/profile/picture')
        
        assert response.status_code == 204
        
        # Verify picture is deleted
        response = authenticated_client.get('/api/profile/picture')
        assert response.status_code == 404
```

##### 2.3 E2E Tests
```python
# tests/e2e/test_profile_picture_flow.py

import pytest

@pytest.mark.e2e
class TestProfilePictureUserFlow:
    """End-to-end tests for profile picture feature"""
    
    def test_complete_upload_flow(self, browser, logged_in_user):
        """Test complete user flow for uploading profile picture"""
        # Navigate to profile page
        browser.visit('/profile')
        
        # Click upload button
        browser.find_by_id('upload-picture-btn').click()
        
        # Select file
        browser.attach_file('picture', '/path/to/test-image.jpg')
        
        # Submit
        browser.find_by_id('submit-upload').click()
        
        # Wait for upload to complete
        browser.is_text_present('Picture uploaded successfully', wait_time=5)
        
        # Verify picture is displayed
        assert browser.find_by_css('.profile-picture').first['src']
        
        # Verify picture persists after page reload
        browser.reload()
        assert browser.find_by_css('.profile-picture').first['src']
```

#### Step 3: Implement the Feature

```python
# app/api/routes/profile.py

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from app.services.profile_service import ProfileService
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/api/profile", tags=["profile"])

@router.post("/picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    """Upload profile picture"""
    try:
        result = await ProfileService.upload_profile_picture(
            user_id=current_user.id,
            image_file=file
        )
        return result
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/picture")
async def get_profile_picture(current_user = Depends(get_current_user)):
    """Get current user's profile picture"""
    picture = await ProfileService.get_profile_picture(current_user.id)
    if not picture:
        raise HTTPException(status_code=404, detail="No profile picture")
    return FileResponse(picture)

@router.delete("/picture")
async def delete_profile_picture(current_user = Depends(get_current_user)):
    """Delete profile picture"""
    await ProfileService.delete_profile_picture(current_user.id)
    return {"message": "Picture deleted"}
```

```python
# app/services/profile_service.py

from PIL import Image
import os
from app.core.storage import upload_to_s3, delete_from_s3

class ProfileService:
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}
    MAX_DIMENSIONS = (500, 500)
    
    @classmethod
    async def upload_profile_picture(cls, user_id: int, image_file):
        """Upload and process profile picture"""
        # Validate file type
        cls._validate_file_type(image_file.filename)
        
        # Validate file size
        cls._validate_file_size(image_file)
        
        # Process image (resize, optimize)
        processed_image = cls._process_image(image_file)
        
        # Delete old picture if exists
        user = await User.get(id=user_id)
        if user.profile_picture:
            await delete_from_s3(user.profile_picture)
        
        # Upload to storage
        url = await upload_to_s3(
            processed_image,
            f"profiles/{user_id}/picture.jpg"
        )
        
        # Update user record
        user.profile_picture = url
        await user.save()
        
        return {
            'success': True,
            'url': url
        }
    
    @staticmethod
    def _validate_file_type(filename: str):
        """Validate file extension"""
        ext = filename.rsplit('.', 1)[1].lower()
        if ext not in ProfileService.ALLOWED_EXTENSIONS:
            raise ValidationError(f"Invalid file type: {ext}")
    
    @staticmethod
    def _validate_file_size(file):
        """Validate file size"""
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        
        if size > ProfileService.MAX_FILE_SIZE:
            raise ValidationError("File too large")
    
    @classmethod
    def _process_image(cls, image_file):
        """Resize and optimize image"""
        img = Image.open(image_file)
        
        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize if too large
        img.thumbnail(cls.MAX_DIMENSIONS, Image.LANCZOS)
        
        # Save optimized
        from io import BytesIO
        output = BytesIO()
        img.save(output, format='JPEG', quality=85, optimize=True)
        output.seek(0)
        
        return output
```

#### Step 4: Run Tests Locally

```bash
# Run unit tests
pytest tests/unit/test_profile_service.py -v

# Run integration tests
pytest tests/integration/test_profile_api.py -v

# Run E2E tests
pytest tests/e2e/test_profile_picture_flow.py -v

# Run all tests with coverage
pytest --cov=app --cov-report=html

# Check coverage for new feature
coverage report --include="app/services/profile_service.py,app/api/routes/profile.py"
```

#### Step 5: Commit and Push

```bash
git add .
git commit -m "feat: Add profile picture upload feature

- Add profile picture upload endpoint
- Add image validation and processing
- Add unit, integration, and E2E tests
- Coverage: 95%"

git push origin feature/profile-picture-upload
```

#### Step 6: Create Pull Request

```markdown
## Feature: Profile Picture Upload

### Description
Adds ability for users to upload and manage profile pictures.

### Changes
- New API endpoint: POST /api/profile/picture
- Image validation (type, size)
- Automatic resizing and optimization
- S3 storage integration
- Old picture cleanup

### Testing
- ✅ Unit tests: 12 tests, 100% coverage
- ✅ Integration tests: 5 tests
- ✅ E2E tests: 1 complete user flow
- ✅ Overall coverage: 95%

### Screenshots
[Add screenshots here]

### Checklist
- [x] Tests written and passing
- [x] Code coverage >80%
- [x] Documentation updated
- [x] No security vulnerabilities
- [x] Performance tested
```

#### Step 7: CI/CD Pipeline Runs Automatically

```
Jenkins Pipeline Execution:
✅ Checkout code
✅ Setup environment
✅ Code quality checks
✅ Security scan
✅ Unit tests (12/12 passed)
✅ Integration tests (5/5 passed)
✅ Coverage check (95% > 80% threshold)
✅ Build Docker image
✅ Push to registry
✅ Deploy to staging

Manual approval required for production →
```

#### Step 8: Review and Merge

```bash
# After approval, merge to main
git checkout main
git merge feature/profile-picture-upload
git push origin main

# Pipeline automatically deploys to production
```

---

## 🔬 Advanced Pytest Techniques

### 1. Custom Markers
```python
# pytest.ini
[pytest]
markers =
    slow: marks tests as slow
    integration: integration tests
    feature: marks tests for specific features
    bug: marks tests for bug fixes
    smoke: critical smoke tests
    regression: regression tests

# Usage
@pytest.mark.feature('profile-picture')
@pytest.mark.slow
def test_large_image_upload():
    pass

# Run specific features
pytest -m "feature('profile-picture')"
```

### 2. Fixtures with Scope
```python
@pytest.fixture(scope="session")
def database_connection():
    """Create database connection once per session"""
    conn = create_connection()
    yield conn
    conn.close()

@pytest.fixture(scope="module")
def test_data():
    """Create test data once per module"""
    data = setup_test_data()
    yield data
    cleanup_test_data()

@pytest.fixture(scope="function")
def clean_database(database_connection):
    """Clean database before each test"""
    database_connection.execute("TRUNCATE TABLE users CASCADE")
    yield
```

### 3. Parametrized Fixtures
```python
@pytest.fixture(params=[
    {'username': 'user1', 'email': 'user1@example.com'},
    {'username': 'user2', 'email': 'user2@example.com'},
    {'username': 'user3', 'email': 'user3@example.com'},
])
def user_data(request):
    return request.param

def test_user_creation(user_data):
    """Test runs 3 times with different user data"""
    user = create_user(**user_data)
    assert user.username == user_data['username']
```

### 4. Async Testing
```python
import pytest

@pytest.mark.asyncio
async def test_async_api_call():
    """Test async API call"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/users/")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_concurrent_requests():
    """Test multiple concurrent requests"""
    import asyncio
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        tasks = [
            ac.get("/api/items/1"),
            ac.get("/api/items/2"),
            ac.get("/api/items/3"),
        ]
        responses = await asyncio.gather(*tasks)
    
    assert all(r.status_code == 200 for r in responses)
```

---

## 📊 Performance Testing

### 1. Benchmark Tests
```python
# Install: pip install pytest-benchmark

def test_user_creation_performance(benchmark):
    """Benchmark user creation"""
    result = benchmark(create_user, username='test', email='test@example.com')
    assert result.id is not None

def test_database_query_performance(benchmark, db):
    """Benchmark database query"""
    def query():
        return User.objects.filter(is_active=True).count()
    
    result = benchmark(query)
    assert result >= 0

# Run with: pytest --benchmark-only
```

### 2. Load Testing with Locust
```python
# Advanced Locust example

from locust import HttpUser, task, between, events
import logging

class AdvancedAPIUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login before starting tasks"""
        response = self.client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "testpass"
        })
        self.token = response.json()['access_token']
    
    @task(3)
    def view_items(self):
        """View items list (high frequency)"""
        self.client.get(
            "/api/items/",
            headers={"Authorization": f"Bearer {self.token}"}
        )
    
    @task(1)
    def create_item(self):
        """Create new item (low frequency)"""
        self.client.post(
            "/api/items/",
            json={"name": "Test Item", "price": 99.99},
            headers={"Authorization": f"Bearer {self.token}"}
        )
    
    @task(2)
    def upload_picture(self):
        """Upload profile picture"""
        files = {'file': ('test.jpg', open('test.jpg', 'rb'), 'image/jpeg')}
        self.client.post(
            "/api/profile/picture",
            files=files,
            headers={"Authorization": f"Bearer {self.token}"}
        )

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    logging.info("Load test starting...")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    logging.info("Load test completed!")
    stats = environment.stats
    logging.info(f"Total requests: {stats.total.num_requests}")
    logging.info(f"Failures: {stats.total.num_failures}")
    logging.info(f"Average response time: {stats.total.avg_response_time}ms")
```

---

## 🔗 Contract Testing

```python
# Install: pip install pact-python

from pact import Consumer, Provider

# Consumer test
pact = Consumer('UserService').has_pact_with(Provider('ProfileService'))

pact.given(
    'user 1 exists'
).upon_receiving(
    'a request for user profile picture'
).with_request(
    'GET', '/api/profile/1/picture'
).will_respond_with(200, body={
    'url': 'https://example.com/pictures/1.jpg'
})

with pact:
    result = profile_service.get_picture(user_id=1)
    assert result['url'] == 'https://example.com/pictures/1.jpg'
```

---

## 🧬 Mutation Testing

```python
# Install: pip install mutpy

# Run mutation testing
mutpy --target app/services/profile_service.py \
      --unit-test tests/unit/test_profile_service.py \
      --report-html mutation-report

# Checks if tests catch intentional bugs (mutations)
```

---

## 📝 Summary Checklist for New Features

- [ ] Write tests FIRST (TDD)
- [ ] Unit tests (>90% coverage)
- [ ] Integration tests
- [ ] E2E tests (critical paths)
- [ ] Performance tests (if applicable)
- [ ] Security tests
- [ ] Run all tests locally
- [ ] Check coverage
- [ ] Commit with descriptive message
- [ ] Create pull request
- [ ] CI/CD pipeline passes
- [ ] Code review
- [ ] Merge to main
- [ ] Deploy to staging
- [ ] Test in staging
- [ ] Deploy to production
- [ ] Monitor in production
