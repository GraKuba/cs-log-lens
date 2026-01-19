"""
Tests for error handling in the LogLens API

Tests cover:
- Validation error formatting (422)
- Auth error formatting (401)
- Server error formatting (500)
- Error messages don't leak sensitive data
"""

import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables for each test"""
    os.environ["SENTRY_AUTH_TOKEN"] = "test-token"
    os.environ["SENTRY_ORG"] = "test-org"
    os.environ["SENTRY_PROJECT"] = "test-project"
    os.environ["OPENAI_API_KEY"] = "test-key"
    os.environ["SLACK_BOT_TOKEN"] = "test-bot-token"
    os.environ["SLACK_SIGNING_SECRET"] = "test-secret"
    os.environ["APP_PASSWORD"] = "test-password-123"
    os.environ["ALLOWED_ORIGINS"] = "*"
    yield
    # Cleanup is handled by pytest


@pytest.fixture
def client():
    """Create test client with fresh app import"""
    # Import here to ensure environment is set up first
    from main import app
    return TestClient(app)


# Validation Error Tests (422)

def test_validation_error_missing_description(client):
    """Test validation error when description is missing"""
    response = client.post(
        "/analyze",
        json={
            "timestamp": "2025-01-19T14:30:00Z",
            "customer_id": "usr_test123"
            # description missing
        },
        headers={"X-Auth-Token": "test-password-123"}
    )

    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert "description" in data["error"].lower()
    assert data["suggestion"] == "Description must not be empty"


def test_validation_error_invalid_timestamp(client):
    """Test validation error with invalid timestamp format"""
    response = client.post(
        "/analyze",
        json={
            "description": "User can't checkout",
            "timestamp": "not-a-timestamp",
            "customer_id": "usr_test123"
        },
        headers={"X-Auth-Token": "test-password-123"}
    )

    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert "timestamp" in data["error"].lower()
    assert "ISO 8601" in data["suggestion"]


def test_validation_error_empty_customer_id(client):
    """Test validation error with empty customer_id"""
    response = client.post(
        "/analyze",
        json={
            "description": "User can't checkout",
            "timestamp": "2025-01-19T14:30:00Z",
            "customer_id": ""
        },
        headers={"X-Auth-Token": "test-password-123"}
    )

    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert "customer_id" in data["error"].lower()
    assert data["suggestion"] == "Customer ID must not be empty"


def test_validation_error_response_format(client):
    """Test that validation errors return consistent format"""
    response = client.post(
        "/analyze",
        json={
            "description": "Test",
            "timestamp": "invalid",
            "customer_id": "usr_123"
        },
        headers={"X-Auth-Token": "test-password-123"}
    )

    assert response.status_code == 422
    data = response.json()

    # Check response structure
    assert "success" in data
    assert "error" in data
    assert "suggestion" in data
    assert data["success"] is False
    assert isinstance(data["error"], str)
    assert isinstance(data["suggestion"], str)


# Auth Error Tests (401)

def test_auth_error_missing_token(client):
    """Test auth error when token is missing"""
    response = client.post(
        "/analyze",
        json={
            "description": "User can't checkout",
            "timestamp": "2025-01-19T14:30:00Z",
            "customer_id": "usr_test123"
        }
        # No X-Auth-Token header
    )

    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"] == "Authentication failed"
    assert "authentication token" in data["suggestion"].lower()


def test_auth_error_wrong_token(client):
    """Test auth error with incorrect token"""
    response = client.post(
        "/analyze",
        json={
            "description": "User can't checkout",
            "timestamp": "2025-01-19T14:30:00Z",
            "customer_id": "usr_test123"
        },
        headers={"X-Auth-Token": "wrong-password"}
    )

    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"] == "Authentication failed"
    assert "authentication token" in data["suggestion"].lower()


def test_auth_error_response_format(client):
    """Test that auth errors return consistent format"""
    response = client.post(
        "/analyze",
        json={
            "description": "Test",
            "timestamp": "2025-01-19T14:30:00Z",
            "customer_id": "usr_123"
        },
        headers={"X-Auth-Token": "wrong"}
    )

    assert response.status_code == 401
    data = response.json()

    # Check response structure
    assert "success" in data
    assert "error" in data
    assert "suggestion" in data
    assert data["success"] is False


# Server Error Tests (500)

def test_server_error_handler_directly():
    """Test the global exception handler directly"""
    from main import global_exception_handler, app
    from fastapi import Request

    # Create a mock request
    class MockRequest:
        def __init__(self):
            self.url = type('obj', (object,), {'path': '/test'})

    request = MockRequest()
    exc = RuntimeError("Database connection failed")

    # Call handler directly (it's async, so we need to await it)
    import asyncio
    response = asyncio.run(global_exception_handler(request, exc))

    # Check response
    assert response.status_code == 500
    assert response.body is not None

    # Parse JSON from response
    import json
    data = json.loads(response.body.decode())
    assert data["success"] is False
    assert data["error"] == "An internal error occurred"
    assert "try again later" in data["suggestion"].lower()


def test_server_error_response_format():
    """Test that server error responses have consistent format"""
    from main import global_exception_handler

    # Create a mock request
    class MockRequest:
        def __init__(self):
            self.url = type('obj', (object,), {'path': '/test'})

    request = MockRequest()
    exc = Exception("Unexpected error")

    import asyncio
    response = asyncio.run(global_exception_handler(request, exc))

    # Check response structure
    assert response.status_code == 500
    import json
    data = json.loads(response.body.decode())

    assert "success" in data
    assert "error" in data
    assert "suggestion" in data
    assert data["success"] is False


# Sensitive Data Protection Tests

def test_errors_dont_leak_config_values():
    """Test that errors don't expose environment variables or config"""
    from main import global_exception_handler

    # Create a mock request
    class MockRequest:
        def __init__(self):
            self.url = type('obj', (object,), {'path': '/test'})

    request = MockRequest()
    # Exception contains a secret
    exc = RuntimeError("Secret: test-password-123")

    import asyncio
    response = asyncio.run(global_exception_handler(request, exc))

    import json
    data = json.loads(response.body.decode())

    # Should NOT contain the actual secret from the exception
    assert "test-password-123" not in str(data)
    assert "Secret:" not in str(data)
    # Should have generic error message
    assert data["error"] == "An internal error occurred"


def test_validation_errors_dont_leak_internal_paths(client):
    """Test that validation errors don't expose internal file paths"""
    response = client.post(
        "/analyze",
        json={
            "description": "",  # Empty description
            "timestamp": "2025-01-19T14:30:00Z",
            "customer_id": "usr_123"
        },
        headers={"X-Auth-Token": "test-password-123"}
    )

    data = response.json()
    # Should not contain file paths like "/backend/main.py"
    assert "/backend/" not in str(data)
    assert ".py" not in str(data)
    # Should have user-friendly error
    assert "description" in data["error"].lower()


def test_auth_errors_dont_expose_actual_password(client):
    """Test that auth errors don't expose the actual password"""
    response = client.post(
        "/analyze",
        json={
            "description": "Test",
            "timestamp": "2025-01-19T14:30:00Z",
            "customer_id": "usr_123"
        },
        headers={"X-Auth-Token": "wrong"}
    )

    data = response.json()
    # Should NOT reveal the actual password
    assert "test-password-123" not in str(data)
    assert data["error"] == "Authentication failed"


# Edge Cases

def test_404_error_format():
    """Test that 404 errors use consistent format"""
    from main import http_exception_handler
    from fastapi import HTTPException

    # Create a mock request
    class MockRequest:
        def __init__(self):
            self.url = type('obj', (object,), {'path': '/nonexistent'})

    request = MockRequest()
    exc = HTTPException(status_code=404, detail="Not Found")

    import asyncio
    response = asyncio.run(http_exception_handler(request, exc))

    assert response.status_code == 404
    import json
    data = json.loads(response.body.decode())
    assert data["success"] is False
    assert "error" in data
    assert "suggestion" in data
    assert data["error"] == "Endpoint not found"


def test_multiple_validation_errors(client):
    """Test error handling with multiple validation issues"""
    response = client.post(
        "/analyze",
        json={
            "description": "",  # Empty
            "timestamp": "invalid",  # Invalid format
            "customer_id": ""  # Empty
        },
        headers={"X-Auth-Token": "test-password-123"}
    )

    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    # Should report at least one error
    assert len(data["error"]) > 0
    assert len(data["suggestion"]) > 0
