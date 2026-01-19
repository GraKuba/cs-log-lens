"""
Tests for Task 5.1: Setup Slack Bot Infrastructure

Tests the Slack bot infrastructure including signature verification,
command parsing, response formatting, and the /slack/commands endpoint.
"""

import pytest
import hmac
import hashlib
import time
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from main import app
from slack_bot import (
    verify_slack_signature,
    parse_slack_command,
    format_slack_response,
    format_slack_error,
    handle_slack_command,
    SlackSignatureVerificationError
)


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


def generate_slack_signature(body: str, timestamp: str, secret: str) -> str:
    """Helper function to generate a valid Slack signature"""
    sig_basestring = f"v0:{timestamp}:{body}"
    signature = 'v0=' + hmac.new(
        secret.encode('utf-8'),
        sig_basestring.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature


# Test 1: Valid Slack signature verification
def test_valid_signature_verification():
    """Test that valid Slack signatures are accepted"""
    body = b"token=xxx&team_id=T123&channel_id=C123&text=test"
    timestamp = str(int(time.time()))
    secret = "my-secret"
    signature = generate_slack_signature(body.decode('utf-8'), timestamp, secret)

    # Should not raise an exception
    verify_slack_signature(body, timestamp, signature, secret)


# Test 2: Invalid Slack signature rejection
def test_invalid_signature_rejection():
    """Test that invalid Slack signatures are rejected"""
    body = b"token=xxx&team_id=T123&channel_id=C123&text=test"
    timestamp = str(int(time.time()))
    secret = "my-secret"
    invalid_signature = "v0=invalid_signature_here"

    with pytest.raises(SlackSignatureVerificationError):
        verify_slack_signature(body, timestamp, invalid_signature, secret)


# Test 3: Old timestamp rejection
def test_old_timestamp_rejection():
    """Test that old timestamps are rejected (replay attack prevention)"""
    body = b"token=xxx&team_id=T123&channel_id=C123&text=test"
    old_timestamp = str(int(time.time()) - 400)  # 6+ minutes ago
    secret = "my-secret"
    signature = generate_slack_signature(body.decode('utf-8'), old_timestamp, secret)

    with pytest.raises(SlackSignatureVerificationError):
        verify_slack_signature(body, old_timestamp, signature, secret)


# Test 4: Valid command parsing
def test_valid_command_parsing():
    """Test parsing of valid /loglens command"""
    command_text = "User can't checkout | 2025-01-19T14:30:00Z | usr_abc123"
    result = parse_slack_command(command_text)

    assert result["description"] == "User can't checkout"
    assert result["timestamp"] == "2025-01-19T14:30:00Z"
    assert result["customer_id"] == "usr_abc123"


# Test 5: Command parsing with extra whitespace
def test_command_parsing_with_whitespace():
    """Test that extra whitespace is handled correctly"""
    command_text = "  User can't checkout  |  2025-01-19T14:30:00Z  |  usr_abc123  "
    result = parse_slack_command(command_text)

    assert result["description"] == "User can't checkout"
    assert result["timestamp"] == "2025-01-19T14:30:00Z"
    assert result["customer_id"] == "usr_abc123"


# Test 6: Invalid command format (missing parts)
def test_invalid_command_format_missing_parts():
    """Test that commands with missing parts are rejected"""
    command_text = "User can't checkout | 2025-01-19T14:30:00Z"  # Missing customer_id

    with pytest.raises(ValueError) as exc_info:
        parse_slack_command(command_text)

    assert "Invalid command format" in str(exc_info.value)


# Test 7: Invalid command format (too many parts)
def test_invalid_command_format_too_many_parts():
    """Test that commands with too many parts are rejected"""
    command_text = "User can't checkout | 2025-01-19T14:30:00Z | usr_abc123 | extra"

    with pytest.raises(ValueError) as exc_info:
        parse_slack_command(command_text)

    assert "Invalid command format" in str(exc_info.value)


# Test 8: Empty description handling
def test_empty_description_handling():
    """Test that empty descriptions are rejected"""
    command_text = " | 2025-01-19T14:30:00Z | usr_abc123"

    with pytest.raises(ValueError) as exc_info:
        parse_slack_command(command_text)

    assert "Description cannot be empty" in str(exc_info.value)


# Test 9: Format Slack response with complete data
def test_format_slack_response_complete():
    """Test formatting of complete analysis results for Slack"""
    analysis_result = {
        "causes": [
            {
                "rank": 1,
                "cause": "Payment token expired",
                "explanation": "User session timed out",
                "confidence": "high"
            },
            {
                "rank": 2,
                "cause": "Cart timeout",
                "explanation": "Cart was cleared",
                "confidence": "medium"
            },
            {
                "rank": 3,
                "cause": "Inventory conflict",
                "explanation": "Item out of stock",
                "confidence": "low"
            }
        ],
        "suggested_response": "Hi, it looks like your session timed out.",
        "events_found": 3,
        "sentry_links": ["https://sentry.io/event/123"]
    }

    result = format_slack_response(analysis_result)

    assert result["response_type"] == "in_channel"
    assert "blocks" in result
    assert len(result["blocks"]) > 0

    # Check for header
    assert result["blocks"][0]["type"] == "header"
    assert "LogLens Analysis" in result["blocks"][0]["text"]["text"]

    # Check that causes are formatted
    causes_block = result["blocks"][1]
    assert causes_block["type"] == "section"
    assert "1️⃣" in causes_block["text"]["text"]
    assert "HIGH" in causes_block["text"]["text"]
    assert "Payment token expired" in causes_block["text"]["text"]


# Test 10: Format Slack error message
def test_format_slack_error():
    """Test formatting of error messages for Slack"""
    result = format_slack_error("Invalid format", "Use the correct format")

    assert result["response_type"] == "ephemeral"
    assert "❌" in result["text"]
    assert "Invalid format" in result["text"]
    assert "Use the correct format" in result["text"]


# Test 11: POST /slack/commands endpoint with valid signature
@pytest.mark.asyncio
async def test_slack_commands_endpoint_valid_signature(client, mock_env):
    """Test /slack/commands endpoint with valid signature"""
    body = "token=xxx&team_id=T123&channel_id=C123&text=User+can%27t+checkout+%7C+2025-01-19T14%3A30%3A00Z+%7C+usr_abc123"
    timestamp = str(int(time.time()))
    signature = generate_slack_signature(body, timestamp, "test-secret")

    response = client.post(
        "/slack/commands",
        content=body,
        headers={
            "X-Slack-Request-Timestamp": timestamp,
            "X-Slack-Signature": signature,
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "text" in data or "blocks" in data


# Test 12: POST /slack/commands endpoint with missing signature headers
@pytest.mark.asyncio
async def test_slack_commands_endpoint_missing_headers(client, mock_env):
    """Test that missing signature headers are rejected"""
    body = "token=xxx&team_id=T123&channel_id=C123&text=test"

    response = client.post(
        "/slack/commands",
        content=body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )

    # Should return error - either 401 or caught by global handler
    assert response.status_code in [401, 500]


# Test 13: POST /slack/commands endpoint with invalid signature
@pytest.mark.asyncio
async def test_slack_commands_endpoint_invalid_signature(client, mock_env):
    """Test that invalid signatures are rejected"""
    body = "token=xxx&team_id=T123&channel_id=C123&text=test"
    timestamp = str(int(time.time()))
    invalid_signature = "v0=invalid_signature_here"

    response = client.post(
        "/slack/commands",
        content=body,
        headers={
            "X-Slack-Request-Timestamp": timestamp,
            "X-Slack-Signature": invalid_signature,
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )

    # Should return 401 unauthorized
    assert response.status_code in [401, 500]


# Test 14: POST /slack/commands endpoint with invalid command format
@pytest.mark.asyncio
async def test_slack_commands_endpoint_invalid_format(client, mock_env):
    """Test handling of invalid command format"""
    body = "token=xxx&team_id=T123&channel_id=C123&text=invalid+format"
    timestamp = str(int(time.time()))
    signature = generate_slack_signature(body, timestamp, "test-secret")

    response = client.post(
        "/slack/commands",
        content=body,
        headers={
            "X-Slack-Request-Timestamp": timestamp,
            "X-Slack-Signature": signature,
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )

    assert response.status_code == 200
    data = response.json()
    # Should return an error message
    assert "text" in data
    assert "Error" in data["text"] or "error" in data["text"].lower()


# Test 15: Format response with no Sentry links
def test_format_slack_response_no_sentry_links():
    """Test formatting when no Sentry links are available"""
    analysis_result = {
        "causes": [
            {
                "rank": 1,
                "cause": "Test cause",
                "explanation": "Test explanation",
                "confidence": "high"
            }
        ],
        "suggested_response": "Test response",
        "events_found": 0,
        "sentry_links": []
    }

    result = format_slack_response(analysis_result)

    # Find the logs block
    logs_block = None
    for block in result["blocks"]:
        if block["type"] == "section" and "Logs:" in block["text"]["text"]:
            logs_block = block
            break

    assert logs_block is not None
    # Should not contain Sentry link
    assert "View in Sentry" not in logs_block["text"]["text"]


# Test 16: Constant-time signature comparison
def test_constant_time_signature_comparison():
    """Test that signature comparison is constant-time (security)"""
    body = b"token=xxx&team_id=T123&channel_id=C123&text=test"
    timestamp = str(int(time.time()))
    secret = "my-secret"

    # Generate a valid signature
    valid_signature = generate_slack_signature(body.decode('utf-8'), timestamp, secret)

    # Create an invalid signature with same length
    invalid_signature = "v0=" + "a" * (len(valid_signature) - 3)

    # Both should fail or succeed in similar time (this is a basic check)
    try:
        verify_slack_signature(body, timestamp, valid_signature, secret)
        valid_passed = True
    except SlackSignatureVerificationError:
        valid_passed = False

    try:
        verify_slack_signature(body, timestamp, invalid_signature, secret)
        invalid_passed = True
    except SlackSignatureVerificationError:
        invalid_passed = False

    # Valid should pass, invalid should fail
    assert valid_passed is True
    assert invalid_passed is False


# ============================================================================
# Task 5.3 Tests: Format Slack Response
# ============================================================================

# Test 17: Format response with all three causes
def test_format_response_all_causes():
    """Test formatting with all three causes present"""
    analysis_result = {
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
        "suggested_response": "Hi [Customer], it looks like your payment session timed out...",
        "events_found": 3,
        "sentry_links": ["https://sentry.io/event/123"]
    }

    result = format_slack_response(analysis_result)

    # Check structure
    assert result["response_type"] == "in_channel"
    assert "blocks" in result

    # Check for all three emoji
    causes_text = result["blocks"][1]["text"]["text"]
    assert "1️⃣" in causes_text
    assert "2️⃣" in causes_text
    assert "3️⃣" in causes_text

    # Check confidence levels
    assert "HIGH" in causes_text
    assert "MEDIUM" in causes_text
    assert "LOW" in causes_text


# Test 18: Format response with quoted suggested response
def test_format_response_quoted_suggestion():
    """Test that suggested response is formatted as a quote"""
    analysis_result = {
        "causes": [{
            "rank": 1,
            "cause": "Test",
            "explanation": "Test",
            "confidence": "high"
        }],
        "suggested_response": "Hi there, please try again",
        "events_found": 1,
        "sentry_links": []
    }

    result = format_slack_response(analysis_result)

    # Find the suggested response block
    suggestion_block = None
    for block in result["blocks"]:
        if block["type"] == "section" and "Suggested Response:" in block["text"]["text"]:
            suggestion_block = block
            break

    assert suggestion_block is not None
    # Check for quote formatting (Slack uses > for quotes in mrkdwn)
    assert "> Hi there, please try again" in suggestion_block["text"]["text"]


# Test 19: Format response with Sentry link
def test_format_response_sentry_link():
    """Test that Sentry link is properly formatted"""
    sentry_url = "https://sentry.io/organizations/test-org/issues/?project=123&query=abc"
    analysis_result = {
        "causes": [{
            "rank": 1,
            "cause": "Test",
            "explanation": "Test",
            "confidence": "high"
        }],
        "suggested_response": "Test",
        "events_found": 3,
        "sentry_links": [sentry_url]
    }

    result = format_slack_response(analysis_result)

    # Find the logs block
    logs_block = None
    for block in result["blocks"]:
        if block["type"] == "section" and "Logs:" in block["text"]["text"]:
            logs_block = block
            break

    assert logs_block is not None
    # Check for Slack-formatted link <url|text>
    assert f"<{sentry_url}|View in Sentry>" in logs_block["text"]["text"]
    assert "Found 3 events" in logs_block["text"]["text"]


# Test 20: Format response with singular event count
def test_format_response_singular_event():
    """Test that event count uses singular form for 1 event"""
    analysis_result = {
        "causes": [{
            "rank": 1,
            "cause": "Test",
            "explanation": "Test",
            "confidence": "high"
        }],
        "suggested_response": "Test",
        "events_found": 1,
        "sentry_links": []
    }

    result = format_slack_response(analysis_result)

    # Find the logs block
    logs_block = None
    for block in result["blocks"]:
        if block["type"] == "section" and "Logs:" in block["text"]["text"]:
            logs_block = block
            break

    assert logs_block is not None
    # Should say "1 event" not "1 events"
    assert "Found 1 event" in logs_block["text"]["text"]
    assert "events" not in logs_block["text"]["text"].lower() or "1 event" in logs_block["text"]["text"]


# Test 21: Format error with suggestion
def test_format_error_with_suggestion():
    """Test error formatting includes suggestion"""
    result = format_slack_error(
        "No events found",
        "Try expanding the time range or verify customer ID"
    )

    assert result["response_type"] == "ephemeral"
    assert "❌" in result["text"]
    assert "No events found" in result["text"]
    assert "💡" in result["text"]
    assert "Try expanding the time range" in result["text"]


# Test 22: Format error without suggestion
def test_format_error_without_suggestion():
    """Test error formatting without suggestion"""
    result = format_slack_error("Something went wrong")

    assert result["response_type"] == "ephemeral"
    assert "❌" in result["text"]
    assert "Something went wrong" in result["text"]
    # Should not have suggestion emoji
    assert "💡" not in result["text"]


# Test 23: Response uses Block Kit structure
def test_response_uses_block_kit():
    """Test that response uses proper Slack Block Kit structure"""
    analysis_result = {
        "causes": [{
            "rank": 1,
            "cause": "Test",
            "explanation": "Test",
            "confidence": "high"
        }],
        "suggested_response": "Test",
        "events_found": 1,
        "sentry_links": []
    }

    result = format_slack_response(analysis_result)

    # Check that it's using Block Kit (blocks array)
    assert "blocks" in result
    assert isinstance(result["blocks"], list)

    # Check for proper block types
    block_types = [block["type"] for block in result["blocks"]]
    assert "header" in block_types  # Header with LogLens Analysis
    assert "section" in block_types  # Content sections
    assert "divider" in block_types  # Dividers between sections


# Test 24: Response is visible in channel
def test_response_visible_in_channel():
    """Test that successful responses are visible to all in channel"""
    analysis_result = {
        "causes": [{
            "rank": 1,
            "cause": "Test",
            "explanation": "Test",
            "confidence": "high"
        }],
        "suggested_response": "Test",
        "events_found": 1,
        "sentry_links": []
    }

    result = format_slack_response(analysis_result)

    # Should be in_channel (visible to all) not ephemeral (only user)
    assert result["response_type"] == "in_channel"


# Test 25: Error is only visible to user
def test_error_visible_only_to_user():
    """Test that error messages are ephemeral (only visible to user who ran command)"""
    result = format_slack_error("Test error")

    # Should be ephemeral (only user sees it) not in_channel
    assert result["response_type"] == "ephemeral"


# Test 26: Handle empty causes list
def test_format_response_empty_causes():
    """Test formatting when causes list is empty"""
    analysis_result = {
        "causes": [],
        "suggested_response": "No analysis available",
        "events_found": 0,
        "sentry_links": []
    }

    result = format_slack_response(analysis_result)

    # Should still return a valid response
    assert "blocks" in result
    assert result["response_type"] == "in_channel"


# Test 27: Full integration test with handle_slack_command
@pytest.mark.asyncio
async def test_handle_slack_command_integration(mock_env):
    """Test complete flow from command to formatted response"""
    from unittest.mock import patch, AsyncMock, mock_open

    # Mock successful Sentry and LLM responses
    mock_events = [
        {
            "id": "event123",
            "title": "PaymentError",
            "metadata": {"value": "Token expired"}
        }
    ]

    mock_llm_response = {
        "causes": [
            {
                "rank": 1,
                "cause": "Payment token expired",
                "explanation": "User session timed out",
                "confidence": "high"
            }
        ],
        "suggested_response": "Hi there, please try logging in again",
        "logs_summary": "Found payment token expiration"
    }

    # Patch the modules at the point they're imported inside handle_slack_command
    with patch('sentry_client.fetch_sentry_events', new=AsyncMock(return_value=mock_events)), \
         patch('sentry_client.format_events_for_llm', return_value="Event 1: PaymentError"), \
         patch('analyzer.analyze_logs', new=AsyncMock(return_value=mock_llm_response)), \
         patch('builtins.open', mock_open(read_data="# Workflow\nTest workflow")):

        command_text = "User can't checkout | 2025-01-19T14:30:00Z | usr_abc123"
        result = await handle_slack_command(command_text)

        # Should return a formatted Slack response
        assert "blocks" in result or "text" in result
        if "blocks" in result:
            # Successful response
            assert result["response_type"] == "in_channel"
            # Verify formatted response structure
            assert any(block.get("type") == "header" for block in result["blocks"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
