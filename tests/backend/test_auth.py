"""
Tests for authentication middleware
"""

import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


def test_analyze_endpoint_without_token():
    """Test that /analyze endpoint returns 401 when no auth token is provided"""
    # Set required env vars for this test
    with patch.dict(os.environ, {
        "SENTRY_AUTH_TOKEN": "test_token",
        "SENTRY_ORG": "test_org",
        "SENTRY_PROJECT": "test_project",
        "OPENAI_API_KEY": "test_key",
        "SLACK_BOT_TOKEN": "test_slack_token",
        "SLACK_SIGNING_SECRET": "test_slack_secret",
        "APP_PASSWORD": "test_password",
        "ALLOWED_ORIGINS": "*"
    }):
        # Import after setting env vars to ensure config loads correctly
        from main import app
        client = TestClient(app)

        # Request without auth token (with valid body to pass validation)
        response = client.post("/analyze", json={
            "description": "Test issue",
            "timestamp": "2026-01-19T14:30:00Z",
            "customer_id": "usr_test123"
        })

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "Authentication failed"


def test_analyze_endpoint_with_wrong_token():
    """Test that /analyze endpoint returns 401 when wrong auth token is provided"""
    with patch.dict(os.environ, {
        "SENTRY_AUTH_TOKEN": "test_token",
        "SENTRY_ORG": "test_org",
        "SENTRY_PROJECT": "test_project",
        "OPENAI_API_KEY": "test_key",
        "SLACK_BOT_TOKEN": "test_slack_token",
        "SLACK_SIGNING_SECRET": "test_slack_secret",
        "APP_PASSWORD": "correct_password",
        "ALLOWED_ORIGINS": "*"
    }):
        from main import app
        client = TestClient(app)

        # Request with wrong auth token (with valid body to pass validation)
        response = client.post(
            "/analyze",
            json={
                "description": "Test issue",
                "timestamp": "2026-01-19T14:30:00Z",
                "customer_id": "usr_test123"
            },
            headers={"X-Auth-Token": "wrong_password"}
        )

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "Authentication failed"


def test_analyze_endpoint_with_correct_token():
    """Test that /analyze endpoint succeeds when correct auth token is provided"""
    from unittest.mock import AsyncMock, mock_open

    mock_llm_response = {
        "causes": [
            {"rank": 1, "cause": "Test", "explanation": "Test", "confidence": "high"},
            {"rank": 2, "cause": "Test", "explanation": "Test", "confidence": "medium"},
            {"rank": 3, "cause": "Test", "explanation": "Test", "confidence": "low"}
        ],
        "suggested_response": "Test response",
        "logs_summary": "Test summary"
    }

    with patch.dict(os.environ, {
        "SENTRY_AUTH_TOKEN": "test_token",
        "SENTRY_ORG": "test_org",
        "SENTRY_PROJECT": "test_project",
        "OPENAI_API_KEY": "test_key",
        "SLACK_BOT_TOKEN": "test_slack_token",
        "SLACK_SIGNING_SECRET": "test_slack_secret",
        "APP_PASSWORD": "correct_password",
        "ALLOWED_ORIGINS": "*"
    }), \
         patch("sentry_client.fetch_sentry_events", new_callable=AsyncMock) as mock_fetch, \
         patch("analyzer.analyze_logs", new_callable=AsyncMock) as mock_analyze, \
         patch("builtins.open", mock_open(read_data="Test docs")):

        mock_fetch.return_value = []
        mock_analyze.return_value = mock_llm_response

        from main import app
        client = TestClient(app)

        # Request with correct auth token (with valid body to pass validation)
        response = client.post(
            "/analyze",
            json={
                "description": "Test issue",
                "timestamp": "2026-01-19T14:30:00Z",
                "customer_id": "usr_test123"
            },
            headers={"X-Auth-Token": "correct_password"}
        )

        # Should succeed (200) and return response with success=True
        assert response.status_code == 200
        assert response.json()["success"] is True


def test_health_endpoint_without_auth():
    """Test that /health endpoint works without authentication"""
    with patch.dict(os.environ, {
        "SENTRY_AUTH_TOKEN": "test_token",
        "SENTRY_ORG": "test_org",
        "SENTRY_PROJECT": "test_project",
        "OPENAI_API_KEY": "test_key",
        "SLACK_BOT_TOKEN": "test_slack_token",
        "SLACK_SIGNING_SECRET": "test_slack_secret",
        "APP_PASSWORD": "test_password",
        "ALLOWED_ORIGINS": "*"
    }):
        from main import app
        client = TestClient(app)

        # Request without auth token - should still work
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert "version" in response.json()


def test_analyze_endpoint_with_empty_token():
    """Test that /analyze endpoint returns 401 when empty auth token is provided"""
    with patch.dict(os.environ, {
        "SENTRY_AUTH_TOKEN": "test_token",
        "SENTRY_ORG": "test_org",
        "SENTRY_PROJECT": "test_project",
        "OPENAI_API_KEY": "test_key",
        "SLACK_BOT_TOKEN": "test_slack_token",
        "SLACK_SIGNING_SECRET": "test_slack_secret",
        "APP_PASSWORD": "test_password",
        "ALLOWED_ORIGINS": "*"
    }):
        from main import app
        client = TestClient(app)

        # Request with empty auth token (with valid body to pass validation)
        response = client.post(
            "/analyze",
            json={
                "description": "Test issue",
                "timestamp": "2026-01-19T14:30:00Z",
                "customer_id": "usr_test123"
            },
            headers={"X-Auth-Token": ""}
        )

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "Authentication failed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
