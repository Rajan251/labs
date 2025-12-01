"""
FastAPI Test Configuration and Fixtures
This file contains pytest fixtures and configuration for FastAPI testing
"""

import pytest
from typing import Generator, AsyncGenerator
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Example: Import your FastAPI app and database models
# from app.main import app
# from app.database import Base, get_db
# from app.models import User


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def test_db_engine():
    """Create a test database engine (in-memory SQLite)"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def test_db_session(test_db_engine) -> Generator[Session, None, None]:
    """Create a new database session for each test"""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_db_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


# ============================================================================
# FASTAPI APP FIXTURES
# ============================================================================

@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    """Create a FastAPI test application"""
    from fastapi import FastAPI
    
    app = FastAPI(title="Test API")
    
    # Add test routes
    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}
    
    @app.get("/items/{item_id}")
    async def read_item(item_id: int, q: str = None):
        return {"item_id": item_id, "q": q}
    
    @app.post("/items/")
    async def create_item(name: str, price: float):
        return {"name": name, "price": price, "id": 1}
    
    return app


@pytest.fixture(scope="function")
def client(test_app: FastAPI) -> Generator[TestClient, None, None]:
    """Create a synchronous test client"""
    with TestClient(test_app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
async def async_client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create an asynchronous test client"""
    async with AsyncClient(
        app=test_app, 
        base_url="http://testserver"
    ) as ac:
        yield ac


# ============================================================================
# AUTHENTICATION FIXTURES
# ============================================================================

@pytest.fixture
def auth_headers() -> dict:
    """Mock authentication headers"""
    return {
        "Authorization": "Bearer test_token_12345",
        "Content-Type": "application/json"
    }


@pytest.fixture
def mock_user() -> dict:
    """Mock user data"""
    return {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "is_active": True,
        "is_superuser": False
    }


@pytest.fixture
def admin_user() -> dict:
    """Mock admin user data"""
    return {
        "id": 2,
        "username": "admin",
        "email": "admin@example.com",
        "is_active": True,
        "is_superuser": True
    }


# ============================================================================
# DATA FIXTURES
# ============================================================================

@pytest.fixture
def sample_item_data() -> dict:
    """Sample item data for testing"""
    return {
        "name": "Test Item",
        "description": "This is a test item",
        "price": 99.99,
        "tax": 10.5,
        "in_stock": True
    }


@pytest.fixture
def sample_items_list() -> list:
    """List of sample items for testing"""
    return [
        {"id": 1, "name": "Item 1", "price": 10.0},
        {"id": 2, "name": "Item 2", "price": 20.0},
        {"id": 3, "name": "Item 3", "price": 30.0},
    ]


# ============================================================================
# MOCK FIXTURES
# ============================================================================

@pytest.fixture
def mock_external_api(monkeypatch):
    """Mock external API calls"""
    async def mock_get(*args, **kwargs):
        class MockResponse:
            status_code = 200
            def json(self):
                return {"data": "mocked"}
        return MockResponse()
    
    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)


# ============================================================================
# CLEANUP FIXTURES
# ============================================================================

@pytest.fixture(autouse=True)
def reset_database(test_db_session):
    """Automatically reset database after each test"""
    yield
    # Clean up database after test
    test_db_session.rollback()


# ============================================================================
# PERFORMANCE FIXTURES
# ============================================================================

@pytest.fixture
def benchmark_config():
    """Configuration for performance benchmarks"""
    return {
        "min_rounds": 5,
        "max_time": 1.0,
        "warmup": True
    }
