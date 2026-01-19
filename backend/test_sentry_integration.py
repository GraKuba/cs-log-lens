"""
Tests for Sentry integration with the /analyze endpoint (Task 3.3)
"""

import os
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

# Set environment variables before importing main
os.environ["SENTRY_AUTH_TOKEN"] = "test_token"
os.environ["SENTRY_ORG"] = "test_org"
os.environ["SENTRY_PROJECT"] = "test_project"
os.environ["OPENAI_API_KEY"] = "test_key"
os.environ["SLACK_BOT_TOKEN"] = "test_bot_token"
os.environ["SLACK_SIGNING_SECRET"] = "test_secret"
os.environ["APP_PASSWORD"] = "test_password"
os.environ["ALLOWED_ORIGINS"] = "http://localhost:3000"

from main import app
from sentry_client import SentryAuthError, SentryRateLimitError, SentryAPIError


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Authentication headers for requests"""
    return {"X-Auth-Token": "test_password"}


@pytest.fixture
def valid_request():
    """Valid analyze request payload"""
    return {
        "description": "User couldn't complete checkout",
        "timestamp": "2025-01-19T14:30:00Z",
        "customer_id": "usr_abc123"
    }


@pytest.fixture
def mock_sentry_events():
    """Sample Sentry events response"""
    return [
        {
            "id": "event123",
            "dateCreated": "2025-01-19T14:30:15Z",
            "type": "error",
            "title": "PaymentTokenExpiredError",
            "message": "Token expired after 10 minutes",
            "metadata": {
                "type": "PaymentTokenExpiredError",
                "value": "Token expired after 10 minutes"
            },
            "entries": [
                {
                    "type": "exception",
                    "data": {
                        "values": [
                            {
                                "stacktrace": {
                                    "frames": [
                                        {
                                            "filename": "payment.py",
                                            "function": "process_payment",
                                            "lineNo": 42,
                                            "context": [
                                                [41, "    if token.is_expired():"],
                                                [42, "        raise PaymentTokenExpiredError()"],
                                                [43, "    return process()"]
                                            ]
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                }
            ]
        },
        {
            "id": "event456",
            "dateCreated": "2025-01-19T14:31:00Z",
            "type": "error",
            "title": "DatabaseConnectionError",
            "message": "Connection timed out",
        }
    ]


@pytest.fixture
def mock_llm_response():
    """Sample LLM analyzer response"""
    return {
        "causes": [
            {"rank": 1, "cause": "Payment token expired", "explanation": "Session timeout", "confidence": "high"},
            {"rank": 2, "cause": "DB connection error", "explanation": "Connection timeout", "confidence": "medium"},
            {"rank": 3, "cause": "Network issue", "explanation": "Possible network problem", "confidence": "low"}
        ],
        "suggested_response": "Hi, it looks like your session timed out. Please try again.",
        "logs_summary": "Found 2 error events related to payment and database issues"
    }


@pytest.fixture(autouse=True)
def mock_llm_analyzer(mock_llm_response):
    """Automatically mock the LLM analyzer and knowledge base files for all tests in this file"""
    from unittest.mock import mock_open
    # Mock both the LLM analyzer and file reads for knowledge base
    with patch('analyzer.analyze_logs', new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = mock_llm_response
        # Also mock the file operations in main.py for loading knowledge base
        with patch('main.open', mock_open(read_data="Test docs"), create=True):
            yield mock_analyze


# Test: With events found
@patch('sentry_client.fetch_sentry_events', new_callable=AsyncMock)
def test_analyze_with_events_found(mock_fetch, client, auth_headers, valid_request, mock_sentry_events):
    """Test /analyze endpoint when Sentry events are found"""
    mock_fetch.return_value = mock_sentry_events

    response = client.post("/analyze", json=valid_request, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert data["success"] is True
    assert data["events_found"] == 2
    assert len(data["sentry_links"]) == 2
    assert data["logs_summary"] != ""

    # Verify Sentry client was called correctly
    mock_fetch.assert_called_once_with(
        customer_id="usr_abc123",
        timestamp="2025-01-19T14:30:00Z",
        time_window_minutes=5
    )

    # Verify Sentry links are generated correctly
    assert "event123" in data["sentry_links"][0]
    assert "event456" in data["sentry_links"][1]

    # Verify logs summary comes from LLM
    assert data["logs_summary"] == "Found 2 error events related to payment and database issues"

    # Verify causes come from LLM
    assert len(data["causes"]) == 3
    assert data["causes"][0]["cause"] == "Payment token expired"


# Test: With no events found
@patch('sentry_client.fetch_sentry_events', new_callable=AsyncMock)
def test_analyze_with_no_events_found(mock_fetch, client, auth_headers, valid_request):
    """Test /analyze endpoint when no Sentry events are found"""
    mock_fetch.return_value = []

    response = client.post("/analyze", json=valid_request, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert data["success"] is True
    assert data["events_found"] == 0
    assert data["sentry_links"] == []
    # logs_summary now comes from LLM, not from Sentry formatting
    assert data["logs_summary"] == "Found 2 error events related to payment and database issues"

    # Verify Sentry client was called
    mock_fetch.assert_called_once()


# Test: With Sentry API error
@patch('sentry_client.fetch_sentry_events', new_callable=AsyncMock)
def test_analyze_with_sentry_api_error(mock_fetch, client, auth_headers, valid_request):
    """Test /analyze endpoint when Sentry API returns an error"""
    mock_fetch.side_effect = SentryAPIError("Sentry server error: 500")

    response = client.post("/analyze", json=valid_request, headers=auth_headers)

    # Should not fail the entire request, just return empty events
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["events_found"] == 0
    assert data["sentry_links"] == []


# Test: With Sentry auth error
@patch('sentry_client.fetch_sentry_events', new_callable=AsyncMock)
def test_analyze_with_sentry_auth_error(mock_fetch, client, auth_headers, valid_request):
    """Test /analyze endpoint when Sentry authentication fails"""
    mock_fetch.side_effect = SentryAuthError("Invalid or expired Sentry auth token")

    response = client.post("/analyze", json=valid_request, headers=auth_headers)

    # Should return 500 error for auth failures
    assert response.status_code == 500
    data = response.json()

    assert data["success"] is False
    # Global exception handler sanitizes the message for security
    assert "internal error" in data["error"].lower()


# Test: With Sentry rate limit error
@patch('sentry_client.fetch_sentry_events', new_callable=AsyncMock)
def test_analyze_with_sentry_rate_limit(mock_fetch, client, auth_headers, valid_request):
    """Test /analyze endpoint when Sentry rate limit is exceeded"""
    mock_fetch.side_effect = SentryRateLimitError("Rate limit exceeded. Retry after 60 seconds.")

    response = client.post("/analyze", json=valid_request, headers=auth_headers)

    # Should return 429 Too Many Requests
    assert response.status_code == 429
    data = response.json()

    assert data["success"] is False
    assert "rate limit" in data["error"].lower()


# Test: Time range calculation
@patch('sentry_client.fetch_sentry_events', new_callable=AsyncMock)
def test_analyze_time_range_calculation(mock_fetch, client, auth_headers):
    """Test that time range is calculated correctly (±5 minutes)"""
    mock_fetch.return_value = []

    request_data = {
        "description": "Test issue",
        "timestamp": "2025-01-19T14:30:00Z",
        "customer_id": "usr_test"
    }

    response = client.post("/analyze", json=request_data, headers=auth_headers)

    assert response.status_code == 200

    # Verify the time window parameter is 5 minutes
    mock_fetch.assert_called_once_with(
        customer_id="usr_test",
        timestamp="2025-01-19T14:30:00Z",
        time_window_minutes=5
    )


# Test: Events count in response
@patch('sentry_client.fetch_sentry_events', new_callable=AsyncMock)
def test_analyze_events_count(mock_fetch, client, auth_headers, valid_request):
    """Test that events_found count is accurate"""
    # Test with 3 events
    mock_events = [
        {"id": "event1", "title": "Error 1"},
        {"id": "event2", "title": "Error 2"},
        {"id": "event3", "title": "Error 3"},
    ]
    mock_fetch.return_value = mock_events

    response = client.post("/analyze", json=valid_request, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert data["events_found"] == 3
    assert len(data["sentry_links"]) == 3


# Test: Sentry links format
@patch('sentry_client.fetch_sentry_events', new_callable=AsyncMock)
def test_analyze_sentry_links_format(mock_fetch, client, auth_headers, valid_request):
    """Test that Sentry links are formatted correctly"""
    mock_events = [
        {"id": "abc123", "title": "Test Error"}
    ]
    mock_fetch.return_value = mock_events

    response = client.post("/analyze", json=valid_request, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    # Verify link format
    assert len(data["sentry_links"]) == 1
    link = data["sentry_links"][0]
    assert link.startswith("https://sentry.io/organizations/")
    assert "test_org" in link
    assert "test_project" in link
    assert "abc123" in link


# Test: Events without IDs don't break link generation
@patch('sentry_client.fetch_sentry_events', new_callable=AsyncMock)
def test_analyze_events_without_ids(mock_fetch, client, auth_headers, valid_request):
    """Test that events without IDs don't cause errors"""
    mock_events = [
        {"title": "Error without ID"},
        {"id": "event123", "title": "Error with ID"}
    ]
    mock_fetch.return_value = mock_events

    response = client.post("/analyze", json=valid_request, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    # Should only have one link (for the event with ID)
    assert data["events_found"] == 2
    assert len(data["sentry_links"]) == 1
    assert "event123" in data["sentry_links"][0]


# Test: Logs summary formatting
@patch('sentry_client.fetch_sentry_events', new_callable=AsyncMock)
def test_analyze_logs_summary_formatting(mock_fetch, client, auth_headers, valid_request, mock_sentry_events):
    """Test that logs summary now comes from LLM, not direct Sentry formatting"""
    mock_fetch.return_value = mock_sentry_events

    response = client.post("/analyze", json=valid_request, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    logs = data["logs_summary"]

    # Verify logs summary comes from LLM mock
    assert logs == "Found 2 error events related to payment and database issues"

    # Verify LLM received formatted Sentry events as input (tested elsewhere)
    # The actual formatting of Sentry events is tested in test_event_formatting.py


# Test: Authentication is still enforced
def test_analyze_requires_authentication(client, valid_request):
    """Test that authentication is still required for /analyze endpoint"""
    # Request without auth header
    response = client.post("/analyze", json=valid_request)

    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False


# Test: Unexpected exceptions are handled gracefully
@patch('sentry_client.fetch_sentry_events', new_callable=AsyncMock)
def test_analyze_with_unexpected_exception(mock_fetch, client, auth_headers, valid_request):
    """Test that unexpected exceptions don't crash the endpoint"""
    mock_fetch.side_effect = RuntimeError("Unexpected error")

    response = client.post("/analyze", json=valid_request, headers=auth_headers)

    # Should not fail entire request, return empty events
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["events_found"] == 0
