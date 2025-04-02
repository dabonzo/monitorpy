"""
Tests for the FastAPI implementation of the MonitorPy API.
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

# Mock dependencies before importing app
with patch("monitorpy.fastapi_api.redis.Redis"), patch("monitorpy.fastapi_api.database.engine"):
    from monitorpy.fastapi_api.main import app


@pytest.fixture
def client():
    """
    Test client fixture for FastAPI app.
    """
    return TestClient(app)


def test_root_endpoint(client):
    """Test the root endpoint returns correct data."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["name"] == "MonitorPy API"
    assert "version" in response.json()
    assert "docs" in response.json()
    assert "endpoints" in response.json()


def test_health_endpoint(client):
    """Test the health endpoint returns OK status."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "timestamp" in response.json()
    assert "redis_available" in response.json()


def test_docs_endpoints(client):
    """Test that the API docs endpoints are available."""
    # Test OpenAPI JSON
    openapi_response = client.get("/api/v1/openapi.json")
    assert openapi_response.status_code == 200
    assert "paths" in openapi_response.json()
    
    # Test Swagger UI
    swagger_response = client.get("/api/v1/docs")
    assert swagger_response.status_code == 200
    assert "swagger-ui" in swagger_response.text.lower()
    
    # Test ReDoc
    redoc_response = client.get("/api/v1/redoc")
    assert redoc_response.status_code == 200
    assert "redoc" in redoc_response.text.lower()


def test_plugins_endpoint(client):
    """Test the plugins endpoint lists available plugins."""
    response = client.get("/api/v1/plugins")
    assert response.status_code == 401  # Should be unauthorized without auth


def test_unauthenticated_routes(client):
    """Test that protected routes require authentication."""
    # Checks endpoint
    checks_response = client.get("/api/v1/checks")
    assert checks_response.status_code == 401
    
    # Results endpoint
    results_response = client.get("/api/v1/results")
    assert results_response.status_code == 401
    
    # Batch endpoint
    batch_response = client.post("/api/v1/batch/run", json={"checks": []})
    assert batch_response.status_code == 401