"""
Tests for main FastAPI application
Tests health endpoint, CORS configuration, and basic app setup
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_endpoint_returns_200():
    """Test that GET /health returns 200 status code"""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_endpoint_response_format():
    """Test that /health returns correct response format with status and version"""
    response = client.get("/health")
    data = response.json()

    # Check that response contains expected fields
    assert "status" in data
    assert "version" in data

    # Check that values are correct
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"


def test_cors_headers_are_set():
    """Test that CORS headers are set correctly when Origin header is present"""
    response = client.get(
        "/health",
        headers={"Origin": "https://example.com"}
    )

    # Check for CORS headers
    assert "access-control-allow-origin" in response.headers
    # Should allow credentials
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_preflight_request():
    """Test that CORS preflight (OPTIONS) requests work correctly"""
    response = client.options(
        "/health",
        headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "GET",
        }
    )

    # Preflight should return 200
    assert response.status_code == 200

    # Should have CORS headers
    assert "access-control-allow-origin" in response.headers
    assert "access-control-allow-methods" in response.headers
    # Allow methods should include GET, POST, etc.
    assert "GET" in response.headers.get("access-control-allow-methods", "")


def test_app_metadata():
    """Test that FastAPI app has correct metadata"""
    assert app.title == "LogLens API"
    assert app.description == "AI-powered log analysis for customer support"
    assert app.version == "0.1.0"


def test_health_endpoint_is_async():
    """Test that health endpoint is async (proper FastAPI pattern)"""
    import inspect
    from main import health_check

    assert inspect.iscoroutinefunction(health_check)
