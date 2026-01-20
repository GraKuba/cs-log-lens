"""
Test authentication endpoint to verify password validation works correctly
"""

import pytest
from fastapi.testclient import TestClient
from main import app
import os


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture
def correct_password():
    """Get the correct password from environment"""
    return os.getenv("APP_PASSWORD", "test-password")


def test_auth_verify_with_correct_password(client, correct_password):
    """Test that /auth/verify returns 200 with correct password"""
    response = client.get(
        "/auth/verify",
        headers={"X-Auth-Token": correct_password}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["authenticated"] is True
    assert "message" in data


def test_auth_verify_with_incorrect_password(client):
    """Test that /auth/verify returns 401 with incorrect password"""
    response = client.get(
        "/auth/verify",
        headers={"X-Auth-Token": "wrong-password"}
    )

    assert response.status_code == 401


def test_auth_verify_without_token(client):
    """Test that /auth/verify returns 401 without token"""
    response = client.get("/auth/verify")

    assert response.status_code == 401


def test_auth_verify_with_empty_token(client):
    """Test that /auth/verify returns 401 with empty token"""
    response = client.get(
        "/auth/verify",
        headers={"X-Auth-Token": ""}
    )

    assert response.status_code == 401


def test_health_endpoint_no_auth_required(client):
    """Test that /health endpoint does not require authentication"""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_analyze_endpoint_requires_auth(client):
    """Test that /analyze endpoint requires authentication"""
    response = client.post(
        "/analyze",
        json={
            "description": "User can't log in",
            "timestamp": "2024-01-20T10:00:00Z",
            "customer_id": "usr_123"
        }
    )

    assert response.status_code == 401


def test_analyze_endpoint_with_correct_auth(client, correct_password):
    """Test that /analyze endpoint works with correct authentication"""
    # Note: This will fail if Sentry/OpenAI credentials are not set up,
    # but it should at least pass the auth check
    response = client.post(
        "/analyze",
        json={
            "description": "User can't log in",
            "timestamp": "2024-01-20T10:00:00Z",
            "customer_id": "usr_123"
        },
        headers={"X-Auth-Token": correct_password}
    )

    # Should either succeed (200) or fail due to missing credentials (500/422),
    # but NOT fail with 401 (auth error)
    assert response.status_code != 401
