"""
Tests for the /analyze endpoint

Tests cover:
- Valid request with all fields
- Missing required fields
- Invalid timestamp format
- Invalid customer_id format
- Authentication enforcement
"""

import os
import pytest
from unittest.mock import patch, mock_open, AsyncMock
from fastapi.testclient import TestClient
from main import app

# Set up test environment
os.environ["SENTRY_AUTH_TOKEN"] = "test_token"
os.environ["SENTRY_ORG"] = "test_org"
os.environ["SENTRY_PROJECT"] = "test_project"
os.environ["OPENAI_API_KEY"] = "test_key"
os.environ["SLACK_BOT_TOKEN"] = "test_slack_token"
os.environ["SLACK_SIGNING_SECRET"] = "test_slack_secret"
os.environ["APP_PASSWORD"] = "test_password"
os.environ["ALLOWED_ORIGINS"] = "*"

client = TestClient(app)


def test_analyze_with_valid_request():
    """Test that a valid request returns 200 and expected response structure"""
    mock_llm_response = {
        "causes": [
            {"rank": 1, "cause": "Test", "explanation": "Test", "confidence": "high"},
            {"rank": 2, "cause": "Test", "explanation": "Test", "confidence": "medium"},
            {"rank": 3, "cause": "Test", "explanation": "Test", "confidence": "low"}
        ],
        "suggested_response": "Test response",
        "logs_summary": "Test summary"
    }

    with patch("sentry_client.fetch_sentry_events", new_callable=AsyncMock) as mock_fetch, \
         patch("analyzer.analyze_logs", new_callable=AsyncMock) as mock_analyze, \
         patch("builtins.open", mock_open(read_data="Test docs")):

        mock_fetch.return_value = []
        mock_analyze.return_value = mock_llm_response

        response = client.post(
            "/analyze",
            json={
                "description": "User couldn't complete checkout",
                "timestamp": "2025-01-19T14:30:00Z",
                "customer_id": "usr_abc123"
            },
            headers={"X-Auth-Token": "test_password"}
        )

        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        assert data["success"] is True
        assert "causes" in data
        assert isinstance(data["causes"], list)
        assert len(data["causes"]) > 0

        # Validate cause structure
        cause = data["causes"][0]
        assert "rank" in cause
        assert "cause" in cause
        assert "explanation" in cause
        assert "confidence" in cause

        # Validate other response fields
        assert "suggested_response" in data
        assert "sentry_links" in data
        assert "logs_summary" in data
        assert "events_found" in data


def test_analyze_missing_description():
    """Test that missing description field returns 422"""
    response = client.post(
        "/analyze",
        json={
            "timestamp": "2025-01-19T14:30:00Z",
            "customer_id": "usr_abc123"
        },
        headers={"X-Auth-Token": "test_password"}
    )

    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert "error" in data
    assert "suggestion" in data


def test_analyze_missing_timestamp():
    """Test that missing timestamp field returns 422"""
    response = client.post(
        "/analyze",
        json={
            "description": "User couldn't complete checkout",
            "customer_id": "usr_abc123"
        },
        headers={"X-Auth-Token": "test_password"}
    )

    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert "error" in data
    assert "suggestion" in data


def test_analyze_missing_customer_id():
    """Test that missing customer_id field returns 422"""
    response = client.post(
        "/analyze",
        json={
            "description": "User couldn't complete checkout",
            "timestamp": "2025-01-19T14:30:00Z"
        },
        headers={"X-Auth-Token": "test_password"}
    )

    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert "error" in data
    assert "suggestion" in data


def test_analyze_invalid_timestamp():
    """Test that invalid timestamp format returns 422"""
    response = client.post(
        "/analyze",
        json={
            "description": "User couldn't complete checkout",
            "timestamp": "not-a-valid-timestamp",
            "customer_id": "usr_abc123"
        },
        headers={"X-Auth-Token": "test_password"}
    )

    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert "error" in data
    assert "suggestion" in data


def test_analyze_empty_description():
    """Test that empty description returns 422"""
    response = client.post(
        "/analyze",
        json={
            "description": "",
            "timestamp": "2025-01-19T14:30:00Z",
            "customer_id": "usr_abc123"
        },
        headers={"X-Auth-Token": "test_password"}
    )

    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert "error" in data
    assert "suggestion" in data


def test_analyze_empty_customer_id():
    """Test that empty customer_id returns 422"""
    response = client.post(
        "/analyze",
        json={
            "description": "User couldn't complete checkout",
            "timestamp": "2025-01-19T14:30:00Z",
            "customer_id": ""
        },
        headers={"X-Auth-Token": "test_password"}
    )

    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert "error" in data
    assert "suggestion" in data


def test_analyze_whitespace_customer_id():
    """Test that whitespace-only customer_id returns 422"""
    response = client.post(
        "/analyze",
        json={
            "description": "User couldn't complete checkout",
            "timestamp": "2025-01-19T14:30:00Z",
            "customer_id": "   "
        },
        headers={"X-Auth-Token": "test_password"}
    )

    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert "error" in data
    assert "suggestion" in data


def test_analyze_various_timestamp_formats():
    """Test that various valid ISO 8601 timestamp formats work"""
    valid_timestamps = [
        "2025-01-19T14:30:00Z",
        "2025-01-19T14:30:00+00:00",
        "2025-01-19T14:30:00.123Z",
        "2025-01-19T14:30:00",
    ]

    mock_llm_response = {
        "causes": [
            {"rank": 1, "cause": "Test", "explanation": "Test", "confidence": "high"},
            {"rank": 2, "cause": "Test", "explanation": "Test", "confidence": "medium"},
            {"rank": 3, "cause": "Test", "explanation": "Test", "confidence": "low"}
        ],
        "suggested_response": "Test response",
        "logs_summary": "Test summary"
    }

    for timestamp in valid_timestamps:
        with patch("sentry_client.fetch_sentry_events", new_callable=AsyncMock) as mock_fetch, \
             patch("analyzer.analyze_logs", new_callable=AsyncMock) as mock_analyze, \
             patch("builtins.open", mock_open(read_data="Test docs")):

            mock_fetch.return_value = []
            mock_analyze.return_value = mock_llm_response

            response = client.post(
                "/analyze",
                json={
                    "description": "Test issue",
                    "timestamp": timestamp,
                    "customer_id": "usr_test"
                },
                headers={"X-Auth-Token": "test_password"}
            )

            assert response.status_code == 200, f"Failed for timestamp format: {timestamp}"


def test_analyze_requires_authentication():
    """Test that analyze endpoint requires authentication"""
    # Test without auth header
    response = client.post(
        "/analyze",
        json={
            "description": "User couldn't complete checkout",
            "timestamp": "2025-01-19T14:30:00Z",
            "customer_id": "usr_abc123"
        }
    )

    assert response.status_code == 401

    # Test with wrong password
    response = client.post(
        "/analyze",
        json={
            "description": "User couldn't complete checkout",
            "timestamp": "2025-01-19T14:30:00Z",
            "customer_id": "usr_abc123"
        },
        headers={"X-Auth-Token": "wrong_password"}
    )

    assert response.status_code == 401


def test_analyze_trims_customer_id():
    """Test that customer_id is trimmed of whitespace"""
    mock_llm_response = {
        "causes": [
            {"rank": 1, "cause": "Test", "explanation": "Test", "confidence": "high"},
            {"rank": 2, "cause": "Test", "explanation": "Test", "confidence": "medium"},
            {"rank": 3, "cause": "Test", "explanation": "Test", "confidence": "low"}
        ],
        "suggested_response": "Test response",
        "logs_summary": "Test summary"
    }

    with patch("sentry_client.fetch_sentry_events", new_callable=AsyncMock) as mock_fetch, \
         patch("analyzer.analyze_logs", new_callable=AsyncMock) as mock_analyze, \
         patch("builtins.open", mock_open(read_data="Test docs")):

        mock_fetch.return_value = []
        mock_analyze.return_value = mock_llm_response

        response = client.post(
            "/analyze",
            json={
                "description": "User couldn't complete checkout",
                "timestamp": "2025-01-19T14:30:00Z",
                "customer_id": "  usr_abc123  "
            },
            headers={"X-Auth-Token": "test_password"}
        )

        # Should succeed after trimming
        assert response.status_code == 200
