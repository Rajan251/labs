"""
FastAPI Load Testing with Locust
Performance and load testing for FastAPI applications
"""

from locust import HttpUser, task, between, events
import random
import json


# ============================================================================
# BASE USER CLASS
# ============================================================================

class FastAPIUser(HttpUser):
    """Base user class for FastAPI load testing"""
    
    # Wait time between tasks (1-3 seconds)
    wait_time = between(1, 3)
    
    # API token (set this to your actual token)
    token = "test_token_12345"
    
    def on_start(self):
        """Called when a user starts - perform login"""
        # Login to get token
        response = self.client.post("/auth/login", json={
            "username": "testuser",
            "password": "testpass123"
        })
        
        if response.status_code == 200:
            self.token = response.json().get("access_token", self.token)
    
    @property
    def headers(self):
        """Return authorization headers"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }


# ============================================================================
# READ-HEAVY USER (70% reads)
# ============================================================================

class ReadHeavyUser(FastAPIUser):
    """User that performs mostly read operations"""
    
    weight = 7  # 70% of users
    
    @task(10)
    def get_items_list(self):
        """Get list of items"""
        page = random.randint(1, 10)
        self.client.get(f"/items/?page={page}&size=20")
    
    @task(5)
    def get_single_item(self):
        """Get single item by ID"""
        item_id = random.randint(1, 1000)
        self.client.get(f"/items/{item_id}")
    
    @task(3)
    def search_items(self):
        """Search items"""
        queries = ["laptop", "phone", "tablet", "monitor", "keyboard"]
        query = random.choice(queries)
        self.client.get(f"/items/search?q={query}")
    
    @task(2)
    def get_user_profile(self):
        """Get user profile"""
        self.client.get("/users/me", headers=self.headers)
    
    @task(1)
    def health_check(self):
        """Health check endpoint"""
        self.client.get("/health")


# ============================================================================
# WRITE-HEAVY USER (30% writes)
# ============================================================================

class WriteHeavyUser(FastAPIUser):
    """User that performs write operations"""
    
    weight = 3  # 30% of users
    
    @task(5)
    def create_item(self):
        """Create new item"""
        payload = {
            "name": f"Test Item {random.randint(1, 10000)}",
            "description": "Load test item",
            "price": round(random.uniform(10, 1000), 2),
            "in_stock": random.choice([True, False])
        }
        self.client.post("/items/", json=payload, headers=self.headers)
    
    @task(3)
    def update_item(self):
        """Update existing item"""
        item_id = random.randint(1, 1000)
        payload = {
            "price": round(random.uniform(10, 1000), 2),
            "in_stock": random.choice([True, False])
        }
        self.client.patch(f"/items/{item_id}", json=payload, headers=self.headers)
    
    @task(2)
    def delete_item(self):
        """Delete item"""
        item_id = random.randint(1, 1000)
        self.client.delete(f"/items/{item_id}", headers=self.headers)
    
    @task(1)
    def bulk_create(self):
        """Bulk create items"""
        items = [
            {
                "name": f"Bulk Item {i}",
                "price": round(random.uniform(10, 100), 2)
            }
            for i in range(5)
        ]
        self.client.post("/items/bulk", json=items, headers=self.headers)


# ============================================================================
# AUTHENTICATION USER
# ============================================================================

class AuthenticationUser(FastAPIUser):
    """User that tests authentication endpoints"""
    
    weight = 1  # 10% of users
    
    @task(5)
    def login(self):
        """User login"""
        self.client.post("/auth/login", json={
            "username": f"user{random.randint(1, 100)}",
            "password": "testpass123"
        })
    
    @task(2)
    def register(self):
        """User registration"""
        user_id = random.randint(10000, 99999)
        self.client.post("/auth/register", json={
            "username": f"newuser{user_id}",
            "email": f"user{user_id}@example.com",
            "password": "SecurePass123!"
        })
    
    @task(1)
    def refresh_token(self):
        """Refresh authentication token"""
        self.client.post("/auth/refresh", json={
            "refresh_token": self.token
        })


# ============================================================================
# SPIKE TEST USER
# ============================================================================

class SpikeTestUser(FastAPIUser):
    """User for spike testing - sudden traffic increase"""
    
    weight = 0  # Disabled by default, enable for spike tests
    
    @task
    def rapid_requests(self):
        """Make rapid consecutive requests"""
        for _ in range(10):
            self.client.get("/items/")


# ============================================================================
# STRESS TEST USER
# ============================================================================

class StressTestUser(FastAPIUser):
    """User for stress testing - heavy operations"""
    
    weight = 0  # Disabled by default, enable for stress tests
    
    wait_time = between(0.1, 0.5)  # Very short wait time
    
    @task
    def heavy_operation(self):
        """Perform heavy operations"""
        # Large pagination
        self.client.get("/items/?page=1&size=1000")
        
        # Complex search
        self.client.get("/items/search?q=test&category=all&sort=price&order=desc")
        
        # Bulk operations
        items = [{"name": f"Item {i}", "price": i} for i in range(50)]
        self.client.post("/items/bulk", json=items, headers=self.headers)


# ============================================================================
# EVENT HANDLERS
# ============================================================================

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts"""
    print("Load test starting...")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops"""
    print("Load test completed!")
    
    # Print statistics
    stats = environment.stats
    print(f"\nTotal requests: {stats.total.num_requests}")
    print(f"Total failures: {stats.total.num_failures}")
    print(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    print(f"Max response time: {stats.total.max_response_time:.2f}ms")
    print(f"Requests per second: {stats.total.total_rps:.2f}")


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Called for each request"""
    if exception:
        print(f"Request failed: {name} - {exception}")


# ============================================================================
# CUSTOM LOAD SHAPES
# ============================================================================

from locust import LoadTestShape

class StepLoadShape(LoadTestShape):
    """
    Step load pattern - gradually increase load
    """
    
    step_time = 60  # Each step lasts 60 seconds
    step_load = 10  # Increase by 10 users each step
    spawn_rate = 5  # Spawn 5 users per second
    time_limit = 600  # Total test duration: 10 minutes
    
    def tick(self):
        run_time = self.get_run_time()
        
        if run_time > self.time_limit:
            return None
        
        current_step = run_time // self.step_time
        user_count = (current_step + 1) * self.step_load
        
        return (user_count, self.spawn_rate)


class SpikeLoadShape(LoadTestShape):
    """
    Spike load pattern - sudden traffic spikes
    """
    
    def tick(self):
        run_time = self.get_run_time()
        
        if run_time < 60:
            return (10, 5)  # Baseline: 10 users
        elif run_time < 120:
            return (100, 50)  # Spike: 100 users
        elif run_time < 180:
            return (10, 5)  # Back to baseline
        elif run_time < 240:
            return (200, 100)  # Larger spike: 200 users
        else:
            return None  # End test


# ============================================================================
# USAGE INSTRUCTIONS
# ============================================================================

"""
RUNNING LOAD TESTS:

1. Basic load test:
   locust -f load_tests.py --host=http://localhost:8000

2. Headless mode (no web UI):
   locust -f load_tests.py --host=http://localhost:8000 --headless -u 100 -r 10 -t 5m

3. With specific user class:
   locust -f load_tests.py --host=http://localhost:8000 ReadHeavyUser

4. With custom load shape:
   locust -f load_tests.py --host=http://localhost:8000 StepLoadShape

5. Generate HTML report:
   locust -f load_tests.py --host=http://localhost:8000 --headless -u 100 -r 10 -t 5m --html=report.html

6. Distributed load testing (master):
   locust -f load_tests.py --host=http://localhost:8000 --master

7. Distributed load testing (worker):
   locust -f load_tests.py --host=http://localhost:8000 --worker --master-host=<master-ip>

PARAMETERS:
  -u, --users       Number of concurrent users
  -r, --spawn-rate  Rate to spawn users (users per second)
  -t, --run-time    Stop after specified time (e.g., 5m, 1h)
  --headless        Run without web UI
  --html            Generate HTML report
  --csv             Generate CSV reports

PERFORMANCE TARGETS:
  - Response time: < 200ms (p95)
  - Error rate: < 1%
  - Throughput: > 1000 req/s
  - Concurrent users: > 500
"""
