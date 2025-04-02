# FastAPI Tests

This document outlines the testing approach for the FastAPI implementation of the MonitorPy API.

## Overview

The FastAPI API is tested using FastAPI's TestClient, which is based on HTTPX. The tests are designed to:

- Verify that API endpoints return expected responses
- Test authentication and authorization mechanisms
- Validate request and response schemas
- Mock database operations and Redis integration
- Ensure proper error handling

## Test Files

The FastAPI tests are organized into the following files:

- `tests/test_fastapi.py`: Tests for unauthenticated endpoints and authorization requirements
- `tests/test_fastapi_auth.py`: Tests for authenticated endpoints with mocked authentication
- `tests/conftest.py`: Contains pytest fixtures for testing including mock database and authentication

## Test Fixtures

The following fixtures are used in FastAPI tests:

### Basic Fixtures

- `client`: Creates a basic TestClient instance for testing unauthenticated endpoints
- `mock_redis`: Mocks Redis functionality to avoid external dependencies
- `mock_access_token`: Generates a dummy JWT token for authentication tests
- `mock_auth_headers`: Creates headers with authorization tokens for authenticated requests
- `temp_db_path`: Creates a temporary database path for testing

### Authentication Fixtures

- `authenticated_client`: A TestClient with authentication dependencies overridden
- `mock_db`: A mock database session for testing without a real database

## Running FastAPI Tests

To run the FastAPI tests, you need to install the required dependencies:

```bash
pip install fastapi uvicorn httpx python-multipart python-jose redis pydantic-settings
```

Then run the tests:

```bash
# Run all FastAPI tests
pytest tests/test_fastapi*.py

# Run just the unauthenticated endpoint tests
pytest tests/test_fastapi.py

# Run authenticated endpoint tests
pytest tests/test_fastapi_auth.py
```

## Test Examples

### Testing Unauthenticated Endpoints

```python
def test_health_endpoint(client):
    """Test the health endpoint returns OK status."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "timestamp" in response.json()
```

### Testing Authentication Requirements

```python
def test_unauthenticated_routes(client):
    """Test that protected routes require authentication."""
    checks_response = client.get("/api/v1/checks")
    assert checks_response.status_code == 401
```

### Testing Authenticated Endpoints

```python
def test_plugins_endpoint(authenticated_client):
    """Test the plugins endpoint with authentication."""
    response = authenticated_client.get("/api/v1/plugins")
    assert response.status_code == 200
    assert "plugins" in response.json()
    assert "count" in response.json()
```

## Mock Database

The tests use a mock database implementation to avoid the need for a real database. The mock database:

- Stores objects in memory
- Provides basic query functionality
- Simulates SQLAlchemy's session interface
- Allows tests to run without external dependencies

Example mock database usage:

```python
def test_with_mock_db(authenticated_client, mock_db):
    # Add a test item to the mock database
    from monitorpy.fastapi_api.models import Check
    check = Check()
    check.id = "test-id"
    check.name = "Test Check"
    mock_db.add(check)
    
    # Test API endpoint that uses the database
    response = authenticated_client.get("/api/v1/checks/test-id")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Check"
```

## Writing New FastAPI Tests

When adding new FastAPI endpoints or features, follow these guidelines:

1. Add tests for both authenticated and unauthenticated access
2. Test both valid and invalid inputs
3. Ensure proper error responses for invalid inputs
4. Mock any external dependencies or database operations
5. Verify response schemas match the expected formats

Use the existing fixtures and mock implementations to keep tests isolated and fast.