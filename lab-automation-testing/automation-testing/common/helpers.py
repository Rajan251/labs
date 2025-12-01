"""
Common Test Utilities and Helpers
Shared utilities for both FastAPI and Django tests
"""

import random
import string
from datetime import datetime, timedelta
from typing import Dict, List, Any
from faker import Faker

fake = Faker()


# ============================================================================
# DATA GENERATORS
# ============================================================================

def generate_random_string(length: int = 10) -> str:
    """Generate random string of specified length"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_random_email() -> str:
    """Generate random email address"""
    return fake.email()


def generate_random_username() -> str:
    """Generate random username"""
    return fake.user_name()


def generate_random_password(length: int = 12) -> str:
    """Generate random secure password"""
    return ''.join(random.choices(
        string.ascii_letters + string.digits + string.punctuation,
        k=length
    ))


def generate_user_data() -> Dict[str, Any]:
    """Generate complete user data"""
    return {
        'username': generate_random_username(),
        'email': generate_random_email(),
        'password': generate_random_password(),
        'first_name': fake.first_name(),
        'last_name': fake.last_name(),
        'phone': fake.phone_number(),
        'address': fake.address(),
    }


def generate_item_data() -> Dict[str, Any]:
    """Generate item data"""
    return {
        'name': fake.word().title(),
        'description': fake.text(),
        'price': round(random.uniform(10, 1000), 2),
        'quantity': random.randint(1, 100),
        'sku': generate_random_string(8).upper(),
        'in_stock': random.choice([True, False]),
    }


# ============================================================================
# ASSERTION HELPERS
# ============================================================================

def assert_valid_uuid(value: str) -> bool:
    """Assert that value is a valid UUID"""
    import uuid
    try:
        uuid.UUID(str(value))
        return True
    except ValueError:
        return False


def assert_valid_email(email: str) -> bool:
    """Assert that email is valid format"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def assert_valid_url(url: str) -> bool:
    """Assert that URL is valid format"""
    import re
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url))


def assert_datetime_recent(dt: datetime, seconds: int = 60) -> bool:
    """Assert that datetime is within recent seconds"""
    now = datetime.now()
    delta = timedelta(seconds=seconds)
    return (now - delta) <= dt <= (now + delta)


def assert_response_time(response_time: float, max_ms: int = 200) -> bool:
    """Assert that response time is within acceptable range"""
    return response_time * 1000 <= max_ms


# ============================================================================
# WAIT HELPERS
# ============================================================================

def wait_for_condition(condition_func, timeout: int = 10, interval: float = 0.5) -> bool:
    """
    Wait for a condition to become true
    
    Args:
        condition_func: Function that returns True when condition is met
        timeout: Maximum seconds to wait
        interval: Seconds between checks
    
    Returns:
        bool: True if condition met, False if timeout
    """
    import time
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if condition_func():
            return True
        time.sleep(interval)
    
    return False


def wait_for_database_ready(max_attempts: int = 10):
    """Wait for database to be ready"""
    import time
    from django.db import connection
    from django.db.utils import OperationalError
    
    for attempt in range(max_attempts):
        try:
            connection.ensure_connection()
            return True
        except OperationalError:
            if attempt == max_attempts - 1:
                raise
            time.sleep(1)
    
    return False


# ============================================================================
# DATABASE HELPERS
# ============================================================================

def truncate_tables(table_names: List[str]):
    """Truncate specified database tables"""
    from django.db import connection
    
    with connection.cursor() as cursor:
        for table in table_names:
            cursor.execute(f'TRUNCATE TABLE {table} CASCADE')


def count_queries(func):
    """Decorator to count database queries"""
    from django.test.utils import override_settings
    from django.db import connection
    from django.test.utils import CaptureQueriesContext
    
    def wrapper(*args, **kwargs):
        with CaptureQueriesContext(connection) as context:
            result = func(*args, **kwargs)
        print(f"Number of queries: {len(context.captured_queries)}")
        return result
    
    return wrapper


# ============================================================================
# HTTP HELPERS
# ============================================================================

def create_auth_header(token: str) -> Dict[str, str]:
    """Create authorization header"""
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }


def create_multipart_form_data(data: Dict[str, Any], files: Dict[str, Any] = None) -> Dict:
    """Create multipart form data for file uploads"""
    form_data = data.copy()
    if files:
        form_data.update(files)
    return form_data


# ============================================================================
# MOCK HELPERS
# ============================================================================

class MockResponse:
    """Mock HTTP response object"""
    
    def __init__(self, json_data: Dict = None, status_code: int = 200, text: str = ""):
        self.json_data = json_data or {}
        self.status_code = status_code
        self.text = text
    
    def json(self):
        return self.json_data
    
    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


def mock_external_api_success():
    """Mock successful external API response"""
    return MockResponse(
        json_data={'status': 'success', 'data': []},
        status_code=200
    )


def mock_external_api_failure():
    """Mock failed external API response"""
    return MockResponse(
        json_data={'status': 'error', 'message': 'API Error'},
        status_code=500
    )


# ============================================================================
# FILE HELPERS
# ============================================================================

def create_temp_file(content: str = "test content", suffix: str = ".txt") -> str:
    """Create temporary file for testing"""
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
        f.write(content)
        return f.name


def create_temp_image(width: int = 100, height: int = 100, format: str = 'PNG'):
    """Create temporary image file for testing"""
    from PIL import Image
    import tempfile
    
    image = Image.new('RGB', (width, height), color='red')
    temp_file = tempfile.NamedTemporaryFile(suffix=f'.{format.lower()}', delete=False)
    image.save(temp_file.name, format=format)
    return temp_file.name


# ============================================================================
# COMPARISON HELPERS
# ============================================================================

def compare_dicts(dict1: Dict, dict2: Dict, ignore_keys: List[str] = None) -> bool:
    """Compare two dictionaries, optionally ignoring certain keys"""
    if ignore_keys:
        dict1 = {k: v for k, v in dict1.items() if k not in ignore_keys}
        dict2 = {k: v for k, v in dict2.items() if k not in ignore_keys}
    
    return dict1 == dict2


def assert_dict_contains(subset: Dict, superset: Dict) -> bool:
    """Assert that superset contains all keys and values from subset"""
    for key, value in subset.items():
        if key not in superset:
            return False
        if superset[key] != value:
            return False
    return True


# ============================================================================
# PERFORMANCE HELPERS
# ============================================================================

def measure_execution_time(func):
    """Decorator to measure function execution time"""
    import time
    
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = (end_time - start_time) * 1000  # Convert to ms
        print(f"{func.__name__} executed in {execution_time:.2f}ms")
        return result
    
    return wrapper


def benchmark_function(func, iterations: int = 100):
    """Benchmark a function over multiple iterations"""
    import time
    
    times = []
    for _ in range(iterations):
        start = time.time()
        func()
        end = time.time()
        times.append((end - start) * 1000)
    
    return {
        'min': min(times),
        'max': max(times),
        'avg': sum(times) / len(times),
        'total': sum(times)
    }


# ============================================================================
# CLEANUP HELPERS
# ============================================================================

class CleanupManager:
    """Context manager for cleanup operations"""
    
    def __init__(self):
        self.cleanup_functions = []
    
    def add_cleanup(self, func, *args, **kwargs):
        """Add cleanup function to be called on exit"""
        self.cleanup_functions.append((func, args, kwargs))
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        for func, args, kwargs in reversed(self.cleanup_functions):
            try:
                func(*args, **kwargs)
            except Exception as e:
                print(f"Cleanup error: {e}")


# ============================================================================
# RETRY HELPERS
# ============================================================================

def retry_on_exception(max_attempts: int = 3, delay: float = 1.0, exceptions=(Exception,)):
    """Decorator to retry function on exception"""
    import time
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts - 1:
                        raise
                    time.sleep(delay)
        return wrapper
    return decorator
