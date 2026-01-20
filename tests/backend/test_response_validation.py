"""
Tests for Task 4.2: Validate and Structure LLM Response

Tests the integration of LLM analyzer with the /analyze endpoint,
including response parsing, validation, and Sentry link injection.
"""

import pytest
from unittest.mock import patch, mock_open, AsyncMock
from fastapi.testclient import TestClient
from main import app
from analyzer import LLMResponseFormatError, LLMAPIError, LLMAnalysisError


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture
def mock_env(monkeypatch):
    """Mock environment variables for testing"""
    monkeypatch.setenv("SENTRY_AUTH_TOKEN", "test-token")
    monkeypatch.setenv("SENTRY_ORG", "test-org")
    monkeypatch.setenv("SENTRY_PROJECT", "test-project")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("SLACK_BOT_TOKEN", "test-bot-token")
    monkeypatch.setenv("SLACK_SIGNING_SECRET", "test-secret")
    monkeypatch.setenv("APP_PASSWORD", "test-password")
    monkeypatch.setenv("ALLOWED_ORIGINS", "*")


@pytest.fixture
def valid_llm_response():
    """Valid LLM response for testing"""
    return {
        "causes": [
            {
                "rank": 1,
                "cause": "Payment token expired",
                "explanation": "User session timed out after 15 minutes",
                "confidence": "high"
            },
            {
                "rank": 2,
                "cause": "Cart session timeout",
                "explanation": "Cart was cleared due to session expiry",
                "confidence": "medium"
            },
            {
                "rank": 3,
                "cause": "Inventory conflict",
                "explanation": "Item may have gone out of stock",
                "confidence": "low"
            }
        ],
        "suggested_response": "Hi, it looks like your session timed out. Please try again.",
        "logs_summary": "Found 3 error events related to session timeout"
    }


@pytest.fixture
def valid_request():
    """Valid analyze request"""
    return {
        "description": "User couldn't complete checkout",
        "timestamp": "2025-01-19T14:30:00Z",
        "customer_id": "usr_abc123"
    }


@pytest.fixture
def mock_sentry_events():
    """Mock Sentry events"""
    return [
        {
            "id": "event-1",
            "message": "PaymentTokenExpiredError",
            "datetime": "2025-01-19T14:30:15Z"
        },
        {
            "id": "event-2",
            "message": "CartSessionExpiredError",
            "datetime": "2025-01-19T14:30:20Z"
        }
    ]


# Test 1: Valid LLM response parsing
@pytest.mark.asyncio
async def test_valid_llm_response_parsing(client, mock_env, valid_request, valid_llm_response, mock_sentry_events):
    """Test that valid LLM response is parsed and structured correctly"""
    with patch("sentry_client.fetch_sentry_events", new_callable=AsyncMock) as mock_fetch, \
         patch("analyzer.analyze_logs", new_callable=AsyncMock) as mock_analyze, \
         patch("builtins.open", mock_open(read_data="Test docs")):

        mock_fetch.return_value = mock_sentry_events
        mock_analyze.return_value = valid_llm_response

        response = client.post(
            "/analyze",
            json=valid_request,
            headers={"X-Auth-Token": "test-password"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify structure
        assert data["success"] is True
        assert len(data["causes"]) == 3
        assert data["suggested_response"] == valid_llm_response["suggested_response"]
        assert data["logs_summary"] == valid_llm_response["logs_summary"]
        assert data["events_found"] == 2

        # Verify causes are properly structured
        for i, cause in enumerate(data["causes"]):
            assert cause["rank"] == valid_llm_response["causes"][i]["rank"]
            assert cause["cause"] == valid_llm_response["causes"][i]["cause"]
            assert cause["explanation"] == valid_llm_response["causes"][i]["explanation"]
            assert cause["confidence"] == valid_llm_response["causes"][i]["confidence"]


# Test 2: Sentry link injection
@pytest.mark.asyncio
async def test_sentry_link_injection(client, mock_env, valid_request, valid_llm_response, mock_sentry_events):
    """Test that Sentry links are added to the response"""
    with patch("sentry_client.fetch_sentry_events", new_callable=AsyncMock) as mock_fetch, \
         patch("analyzer.analyze_logs", new_callable=AsyncMock) as mock_analyze, \
         patch("builtins.open", mock_open(read_data="Test docs")):

        mock_fetch.return_value = mock_sentry_events
        mock_analyze.return_value = valid_llm_response

        response = client.post(
            "/analyze",
            json=valid_request,
            headers={"X-Auth-Token": "test-password"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify Sentry links are present
        assert "sentry_links" in data
        assert len(data["sentry_links"]) == 2
        assert "sentry.io" in data["sentry_links"][0]
        assert "event-1" in data["sentry_links"][0]
        assert "event-2" in data["sentry_links"][1]


# Test 3: Missing fields handling
@pytest.mark.asyncio
async def test_missing_fields_handling(client, mock_env, valid_request, mock_sentry_events):
    """Test handling of LLM response with missing fields"""
    invalid_response = {
        "causes": [
            {"rank": 1, "cause": "Test", "explanation": "Test", "confidence": "high"}
        ]
        # Missing suggested_response and logs_summary
    }

    with patch("sentry_client.fetch_sentry_events", new_callable=AsyncMock) as mock_fetch, \
         patch("analyzer.analyze_logs", new_callable=AsyncMock) as mock_analyze, \
         patch("builtins.open", mock_open(read_data="Test docs")):

        mock_fetch.return_value = mock_sentry_events
        mock_analyze.side_effect = LLMResponseFormatError("Missing required fields: ['suggested_response', 'logs_summary']")

        response = client.post(
            "/analyze",
            json=valid_request,
            headers={"X-Auth-Token": "test-password"}
        )

        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        # Error is caught by global exception handler which returns generic message
        assert "internal error" in data["error"].lower()


# Test 4: Invalid confidence levels
@pytest.mark.asyncio
async def test_invalid_confidence_levels(client, mock_env, valid_request, valid_llm_response, mock_sentry_events):
    """Test that invalid confidence levels are handled (logged but not rejected)"""
    invalid_response = valid_llm_response.copy()
    invalid_response["causes"] = [
        {
            "rank": 1,
            "cause": "Test",
            "explanation": "Test",
            "confidence": "very_high"  # Invalid confidence level
        },
        {
            "rank": 2,
            "cause": "Test",
            "explanation": "Test",
            "confidence": "medium"
        },
        {
            "rank": 3,
            "cause": "Test",
            "explanation": "Test",
            "confidence": "low"
        }
    ]

    with patch("sentry_client.fetch_sentry_events", new_callable=AsyncMock) as mock_fetch, \
         patch("analyzer.analyze_logs", new_callable=AsyncMock) as mock_analyze, \
         patch("builtins.open", mock_open(read_data="Test docs")):

        mock_fetch.return_value = mock_sentry_events
        mock_analyze.return_value = invalid_response

        # This should succeed but log a warning
        response = client.post(
            "/analyze",
            json=valid_request,
            headers={"X-Auth-Token": "test-password"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


# Test 5: LLM API error handling
@pytest.mark.asyncio
async def test_llm_api_error_handling(client, mock_env, valid_request, mock_sentry_events):
    """Test handling of LLM API errors"""
    with patch("sentry_client.fetch_sentry_events", new_callable=AsyncMock) as mock_fetch, \
         patch("analyzer.analyze_logs", new_callable=AsyncMock) as mock_analyze, \
         patch("builtins.open", mock_open(read_data="Test docs")):

        mock_fetch.return_value = mock_sentry_events
        mock_analyze.side_effect = LLMAPIError("OpenAI API call failed: Rate limit exceeded")

        response = client.post(
            "/analyze",
            json=valid_request,
            headers={"X-Auth-Token": "test-password"}
        )

        assert response.status_code == 503
        data = response.json()
        assert data["success"] is False
        # Error is caught by global exception handler
        assert "internal error" in data["error"].lower()


# Test 6: Generic LLM error handling
@pytest.mark.asyncio
async def test_generic_llm_error_handling(client, mock_env, valid_request, mock_sentry_events):
    """Test handling of generic LLM analysis errors"""
    with patch("sentry_client.fetch_sentry_events", new_callable=AsyncMock) as mock_fetch, \
         patch("analyzer.analyze_logs", new_callable=AsyncMock) as mock_analyze, \
         patch("builtins.open", mock_open(read_data="Test docs")):

        mock_fetch.return_value = mock_sentry_events
        mock_analyze.side_effect = LLMAnalysisError("Unexpected analysis error")

        response = client.post(
            "/analyze",
            json=valid_request,
            headers={"X-Auth-Token": "test-password"}
        )

        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        # Error is caught by global exception handler
        assert "internal error" in data["error"].lower()


# Test 7: Response with no Sentry events
@pytest.mark.asyncio
async def test_response_with_no_sentry_events(client, mock_env, valid_request, valid_llm_response):
    """Test response structure when no Sentry events are found"""
    with patch("sentry_client.fetch_sentry_events", new_callable=AsyncMock) as mock_fetch, \
         patch("analyzer.analyze_logs", new_callable=AsyncMock) as mock_analyze, \
         patch("builtins.open", mock_open(read_data="Test docs")):

        mock_fetch.return_value = []  # No events found
        mock_analyze.return_value = valid_llm_response

        response = client.post(
            "/analyze",
            json=valid_request,
            headers={"X-Auth-Token": "test-password"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["events_found"] == 0
        assert data["sentry_links"] == []


# Test 8: Ensure 3 causes are returned
@pytest.mark.asyncio
async def test_ensure_three_causes(client, mock_env, valid_request, valid_llm_response, mock_sentry_events):
    """Test that exactly 3 causes are expected (warning if not)"""
    response_with_two_causes = valid_llm_response.copy()
    response_with_two_causes["causes"] = [
        {
            "rank": 1,
            "cause": "Test",
            "explanation": "Test",
            "confidence": "high"
        },
        {
            "rank": 2,
            "cause": "Test",
            "explanation": "Test",
            "confidence": "medium"
        }
    ]

    with patch("sentry_client.fetch_sentry_events", new_callable=AsyncMock) as mock_fetch, \
         patch("analyzer.analyze_logs", new_callable=AsyncMock) as mock_analyze, \
         patch("builtins.open", mock_open(read_data="Test docs")):

        mock_fetch.return_value = mock_sentry_events
        mock_analyze.return_value = response_with_two_causes

        # This should succeed but log a warning about cause count
        response = client.post(
            "/analyze",
            json=valid_request,
            headers={"X-Auth-Token": "test-password"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["causes"]) == 2  # Not exactly 3, but allowed


# Test 9: Knowledge base files not found
@pytest.mark.asyncio
async def test_knowledge_base_not_found(client, mock_env, valid_request, valid_llm_response, mock_sentry_events):
    """Test that missing knowledge base files don't break the analysis"""
    with patch("sentry_client.fetch_sentry_events", new_callable=AsyncMock) as mock_fetch, \
         patch("analyzer.analyze_logs", new_callable=AsyncMock) as mock_analyze, \
         patch("builtins.open", side_effect=FileNotFoundError()):

        mock_fetch.return_value = mock_sentry_events
        mock_analyze.return_value = valid_llm_response

        response = client.post(
            "/analyze",
            json=valid_request,
            headers={"X-Auth-Token": "test-password"}
        )

        # Should still succeed with fallback messages
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify analyze_logs was called with fallback messages
        call_args = mock_analyze.call_args[1]
        assert "No workflow documentation available" in call_args["workflow_docs"]
        assert "No known error patterns available" in call_args["known_errors"]


# Test 10: Unexpected error during analysis
@pytest.mark.asyncio
async def test_unexpected_error_during_analysis(client, mock_env, valid_request, mock_sentry_events):
    """Test handling of unexpected errors during analysis"""
    with patch("sentry_client.fetch_sentry_events", new_callable=AsyncMock) as mock_fetch, \
         patch("analyzer.analyze_logs", new_callable=AsyncMock) as mock_analyze, \
         patch("builtins.open", mock_open(read_data="Test docs")):

        mock_fetch.return_value = mock_sentry_events
        mock_analyze.side_effect = Exception("Unexpected error")

        response = client.post(
            "/analyze",
            json=valid_request,
            headers={"X-Auth-Token": "test-password"}
        )

        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        # Error is caught by global exception handler which returns generic message
        assert "internal error" in data["error"].lower()


# Test 11: Verify all required fields exist in response
@pytest.mark.asyncio
async def test_all_required_fields_in_response(client, mock_env, valid_request, valid_llm_response, mock_sentry_events):
    """Test that all required fields are present in the final response"""
    with patch("sentry_client.fetch_sentry_events", new_callable=AsyncMock) as mock_fetch, \
         patch("analyzer.analyze_logs", new_callable=AsyncMock) as mock_analyze, \
         patch("builtins.open", mock_open(read_data="Test docs")):

        mock_fetch.return_value = mock_sentry_events
        mock_analyze.return_value = valid_llm_response

        response = client.post(
            "/analyze",
            json=valid_request,
            headers={"X-Auth-Token": "test-password"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify all required fields
        required_fields = ["success", "causes", "suggested_response", "sentry_links", "logs_summary", "events_found"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Verify causes structure
        for cause in data["causes"]:
            assert "rank" in cause
            assert "cause" in cause
            assert "explanation" in cause
            assert "confidence" in cause


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
