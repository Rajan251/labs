"""
Django Test Configuration and Fixtures
This file contains pytest fixtures and configuration for Django testing
"""

import pytest
from django.test import Client
from django.contrib.auth import get_user_model
from django.core.management import call_command
from rest_framework.test import APIClient
from faker import Faker

User = get_user_model()
fake = Faker()


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """Setup test database"""
    with django_db_blocker.unblock():
        call_command('migrate', '--noinput')


@pytest.fixture
def db_with_data(db):
    """Database with sample data"""
    # Create sample users
    User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123'
    )
    return db


# ============================================================================
# CLIENT FIXTURES
# ============================================================================

@pytest.fixture
def client():
    """Django test client"""
    return Client()


@pytest.fixture
def api_client():
    """Django REST Framework API client"""
    return APIClient()


@pytest.fixture
def authenticated_client(client, django_user):
    """Authenticated Django client"""
    client.force_login(django_user)
    return client


@pytest.fixture
def authenticated_api_client(api_client, django_user):
    """Authenticated DRF API client"""
    api_client.force_authenticate(user=django_user)
    return api_client


# ============================================================================
# USER FIXTURES
# ============================================================================

@pytest.fixture
def django_user(db):
    """Create a regular user"""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )


@pytest.fixture
def admin_user(db):
    """Create an admin user"""
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123'
    )


@pytest.fixture
def multiple_users(db):
    """Create multiple users"""
    users = []
    for i in range(5):
        user = User.objects.create_user(
            username=f'user{i}',
            email=f'user{i}@example.com',
            password='testpass123'
        )
        users.append(user)
    return users


# ============================================================================
# MODEL FIXTURES (Example - adjust to your models)
# ============================================================================

@pytest.fixture
def sample_item(db):
    """Create a sample item"""
    # from myapp.models import Item
    # return Item.objects.create(
    #     name='Test Item',
    #     description='Test description',
    #     price=99.99
    # )
    pass


@pytest.fixture
def sample_items(db):
    """Create multiple sample items"""
    # from myapp.models import Item
    # items = []
    # for i in range(10):
    #     item = Item.objects.create(
    #         name=f'Item {i}',
    #         price=10.0 * (i + 1)
    #     )
    #     items.append(item)
    # return items
    pass


# ============================================================================
# FAKER FIXTURES
# ============================================================================

@pytest.fixture
def fake_user_data():
    """Generate fake user data"""
    return {
        'username': fake.user_name(),
        'email': fake.email(),
        'first_name': fake.first_name(),
        'last_name': fake.last_name(),
        'password': fake.password()
    }


@pytest.fixture
def fake_item_data():
    """Generate fake item data"""
    return {
        'name': fake.word(),
        'description': fake.text(),
        'price': fake.pydecimal(left_digits=3, right_digits=2, positive=True)
    }


# ============================================================================
# REQUEST FIXTURES
# ============================================================================

@pytest.fixture
def request_factory():
    """Django request factory"""
    from django.test import RequestFactory
    return RequestFactory()


@pytest.fixture
def mock_request(request_factory, django_user):
    """Mock HTTP request with authenticated user"""
    request = request_factory.get('/')
    request.user = django_user
    return request


# ============================================================================
# FILE UPLOAD FIXTURES
# ============================================================================

@pytest.fixture
def sample_image():
    """Create a sample image file for testing"""
    from django.core.files.uploadedfile import SimpleUploadedFile
    from PIL import Image
    import io
    
    image = Image.new('RGB', (100, 100), color='red')
    image_io = io.BytesIO()
    image.save(image_io, format='JPEG')
    image_io.seek(0)
    
    return SimpleUploadedFile(
        'test_image.jpg',
        image_io.read(),
        content_type='image/jpeg'
    )


@pytest.fixture
def sample_file():
    """Create a sample file for testing"""
    from django.core.files.uploadedfile import SimpleUploadedFile
    
    return SimpleUploadedFile(
        'test_file.txt',
        b'Test file content',
        content_type='text/plain'
    )


# ============================================================================
# CACHE FIXTURES
# ============================================================================

@pytest.fixture
def clear_cache():
    """Clear Django cache before and after test"""
    from django.core.cache import cache
    cache.clear()
    yield
    cache.clear()


# ============================================================================
# EMAIL FIXTURES
# ============================================================================

@pytest.fixture
def mailoutbox():
    """Access Django mail outbox"""
    from django.core import mail
    return mail.outbox


# ============================================================================
# SETTINGS FIXTURES
# ============================================================================

@pytest.fixture
def settings_debug_true(settings):
    """Override DEBUG setting"""
    settings.DEBUG = True
    return settings


@pytest.fixture
def settings_with_custom_config(settings):
    """Override multiple settings"""
    settings.DEBUG = False
    settings.ALLOWED_HOSTS = ['testserver']
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    return settings


# ============================================================================
# TRANSACTION FIXTURES
# ============================================================================

@pytest.fixture
def transactional_db_with_data(transactional_db):
    """Transactional database with data"""
    # Use this for tests that need to test transactions
    User.objects.create_user(
        username='transactional_user',
        email='trans@example.com',
        password='testpass123'
    )
    return transactional_db


# ============================================================================
# CLEANUP FIXTURES
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_media_files():
    """Clean up media files after tests"""
    yield
    # Add cleanup logic for uploaded files
    import shutil
    from django.conf import settings
    # shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
