"""
Tests for Sentry Event Formatting
Testing Task 3.2: Format Sentry Events for LLM
"""

import os
import pytest
from unittest.mock import patch

from sentry_client import (
    format_events_for_llm,
    generate_sentry_link,
    _extract_stack_trace,
    _extract_breadcrumbs,
)


@pytest.fixture
def mock_config():
    """Mock config with test values"""
    with patch.dict(
        os.environ,
        {
            "SENTRY_AUTH_TOKEN": "test-token-123",
            "SENTRY_ORG": "test-org",
            "SENTRY_PROJECT": "test-project",
            "OPENAI_API_KEY": "test-openai-key",
            "SLACK_BOT_TOKEN": "test-slack-token",
            "SLACK_SIGNING_SECRET": "test-slack-secret",
            "APP_PASSWORD": "test-password",
            "ALLOWED_ORIGINS": "*",
        },
    ):
        # Reset global config
        import config as config_module
        config_module.config = None
        yield


@pytest.fixture
def minimal_event():
    """Minimal Sentry event with only required fields"""
    return {
        "id": "event-minimal-123",
        "datetime": "2025-01-19T14:30:15Z",
        "title": "Simple Error",
    }


@pytest.fixture
def complete_event():
    """Complete Sentry event with all fields populated"""
    return {
        "id": "event-complete-456",
        "dateCreated": "2025-01-19T14:30:15Z",
        "datetime": "2025-01-19T14:30:15Z",
        "type": "error",
        "title": "PaymentError: Token expired",
        "message": "Payment token expired after 10 minutes",
        "metadata": {
            "type": "PaymentTokenExpiredError",
            "value": "Token expired after 10 minutes of inactivity"
        },
        "tags": [
            {"key": "environment", "value": "production"},
            {"key": "release", "value": "v1.2.3"},
            {"key": "browser", "value": "Chrome 120"},
            {"key": "os", "value": "Windows 10"},
        ],
        "entries": [
            {
                "type": "exception",
                "data": {
                    "values": [
                        {
                            "type": "PaymentTokenExpiredError",
                            "value": "Token expired",
                            "stacktrace": {
                                "frames": [
                                    {
                                        "filename": "payment_service.py",
                                        "function": "process_payment",
                                        "lineNo": 42,
                                        "context": [
                                            [40, "    # Validate token"],
                                            [41, "    if not token.is_valid():"],
                                            [42, "        raise PaymentTokenExpiredError('Token expired')"],
                                            [43, "    return process_transaction(token)"],
                                        ]
                                    },
                                    {
                                        "filename": "checkout_handler.py",
                                        "function": "handle_checkout",
                                        "lineNo": 128,
                                        "context": [
                                            [126, "    try:"],
                                            [127, "        payment = PaymentService()"],
                                            [128, "        payment.process_payment(user_token)"],
                                            [129, "    except PaymentError as e:"],
                                        ]
                                    }
                                ]
                            }
                        }
                    ]
                }
            },
            {
                "type": "breadcrumbs",
                "data": {
                    "values": [
                        {
                            "timestamp": "2025-01-19T14:25:00Z",
                            "category": "navigation",
                            "message": "User navigated to /checkout",
                            "level": "info"
                        },
                        {
                            "timestamp": "2025-01-19T14:28:00Z",
                            "category": "ui.click",
                            "message": "Clicked 'Complete Purchase' button",
                            "level": "info"
                        },
                        {
                            "timestamp": "2025-01-19T14:30:00Z",
                            "category": "http",
                            "message": "",
                            "level": "info",
                            "data": {
                                "url": "/api/payment",
                                "method": "POST",
                                "status_code": 400
                            }
                        }
                    ]
                }
            }
        ]
    }


@pytest.fixture
def event_without_stack():
    """Event with breadcrumbs but no stack trace"""
    return {
        "id": "event-no-stack-789",
        "datetime": "2025-01-19T14:30:15Z",
        "title": "Network timeout",
        "message": "Request timed out after 30 seconds",
        "tags": [
            {"key": "environment", "value": "staging"},
        ],
        "entries": [
            {
                "type": "breadcrumbs",
                "data": {
                    "values": [
                        {
                            "timestamp": "2025-01-19T14:29:45Z",
                            "category": "http",
                            "message": "GET /api/data",
                            "level": "info"
                        }
                    ]
                }
            }
        ]
    }


class TestGenerateSentryLink:
    """Test Sentry link generation"""

    def test_generate_link_with_defaults(self, mock_config):
        """Test link generation using config defaults"""
        event_id = "abc123def456"
        link = generate_sentry_link(event_id)

        assert link == "https://sentry.io/organizations/test-org/issues/?project=test-project&query=abc123def456"
        assert "test-org" in link
        assert "test-project" in link
        assert event_id in link

    def test_generate_link_with_custom_org_project(self, mock_config):
        """Test link generation with custom org and project"""
        event_id = "xyz789"
        link = generate_sentry_link(event_id, org="custom-org", project="custom-project")

        assert "custom-org" in link
        assert "custom-project" in link
        assert event_id in link


class TestFormatEventsForLLM:
    """Test main event formatting function"""

    def test_format_empty_events(self):
        """Test formatting with empty event list"""
        result = format_events_for_llm([])
        assert result == "No Sentry events found."

    def test_format_minimal_event(self, minimal_event):
        """Test formatting event with minimal fields"""
        result = format_events_for_llm([minimal_event])

        # Check basic structure
        assert "Event 1:" in result
        assert "Time: 2025-01-19T14:30:15Z" in result
        assert "Simple Error" in result
        assert "event-minimal-123" in result

    def test_format_complete_event(self, mock_config, complete_event):
        """Test formatting event with all fields populated"""
        result = format_events_for_llm([complete_event])

        # Check timestamp
        assert "Time: 2025-01-19T14:30:15Z" in result

        # Check error type and message
        assert "PaymentTokenExpiredError" in result
        assert "Token expired after 10 minutes of inactivity" in result

        # Check stack trace
        assert "Stack Trace:" in result
        assert "payment_service.py:42" in result
        assert "process_payment()" in result
        assert "raise PaymentTokenExpiredError('Token expired')" in result
        assert "checkout_handler.py:128" in result

        # Check breadcrumbs
        assert "Breadcrumbs" in result
        assert "User navigated to /checkout" in result
        assert "Clicked 'Complete Purchase' button" in result

        # Check context tags
        assert "Context:" in result
        assert "environment=production" in result
        assert "release=v1.2.3" in result

        # Check Sentry link
        assert "Link:" in result
        assert "https://sentry.io" in result
        assert "event-complete-456" in result

    def test_format_event_without_stack(self, mock_config, event_without_stack):
        """Test formatting event without stack trace"""
        result = format_events_for_llm([event_without_stack])

        # Should have breadcrumbs but not stack trace
        assert "Breadcrumbs" in result
        assert "GET /api/data" in result
        assert "Stack Trace:" not in result

        # Check other fields
        assert "Request timed out after 30 seconds" in result
        assert "environment=staging" in result

    def test_format_multiple_events(self, mock_config, minimal_event, complete_event):
        """Test formatting multiple events"""
        result = format_events_for_llm([minimal_event, complete_event])

        # Check both events are present
        assert "Event 1:" in result
        assert "Event 2:" in result

        # Check they're separated
        assert result.count("\n\n") >= 1  # At least one double newline separator

        # Check both event IDs
        assert "event-minimal-123" in result
        assert "event-complete-456" in result

    def test_format_handles_missing_fields(self):
        """Test formatting gracefully handles missing fields"""
        event = {
            "id": "test-event",
            # Missing datetime, title, message, etc.
        }

        result = format_events_for_llm([event])

        # Should not crash and should have basic structure
        assert "Event 1:" in result
        assert "test-event" in result
        # Should handle missing timestamp gracefully
        assert "Time:" in result


class TestExtractStackTrace:
    """Test stack trace extraction"""

    def test_extract_stack_from_complete_event(self, complete_event):
        """Test extracting stack trace from complete event"""
        frames = _extract_stack_trace(complete_event)

        assert len(frames) == 2
        assert "payment_service.py:42 in process_payment()" in frames[0]
        assert "raise PaymentTokenExpiredError('Token expired')" in frames[0]
        assert "checkout_handler.py:128 in handle_checkout()" in frames[1]

    def test_extract_stack_from_event_without_stack(self, event_without_stack):
        """Test extracting stack trace from event without stack"""
        frames = _extract_stack_trace(event_without_stack)
        assert frames == []

    def test_extract_stack_handles_missing_entries(self):
        """Test stack extraction with missing entries field"""
        event = {"id": "test", "title": "Error"}
        frames = _extract_stack_trace(event)
        assert frames == []

    def test_extract_stack_handles_no_context(self):
        """Test stack extraction when context is missing"""
        event = {
            "entries": [
                {
                    "type": "exception",
                    "data": {
                        "values": [
                            {
                                "stacktrace": {
                                    "frames": [
                                        {
                                            "filename": "test.py",
                                            "function": "test_func",
                                            "lineNo": 10,
                                            # No context field
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                }
            ]
        }

        frames = _extract_stack_trace(event)
        assert len(frames) == 1
        assert "test.py:10 in test_func()" in frames[0]
        # Should not include code line if context missing
        assert "->" not in frames[0]


class TestExtractBreadcrumbs:
    """Test breadcrumb extraction"""

    def test_extract_breadcrumbs_from_complete_event(self, complete_event):
        """Test extracting breadcrumbs from complete event"""
        crumbs = _extract_breadcrumbs(complete_event)

        assert len(crumbs) == 3
        assert "[info] navigation: User navigated to /checkout" in crumbs[0]
        assert "[info] ui.click: Clicked 'Complete Purchase' button" in crumbs[1]
        # Third breadcrumb has no message but has data
        assert "[info] http:" in crumbs[2]
        assert "url=/api/payment" in crumbs[2]

    def test_extract_breadcrumbs_from_event_without_breadcrumbs(self, minimal_event):
        """Test extracting breadcrumbs from event without breadcrumbs"""
        crumbs = _extract_breadcrumbs(minimal_event)
        assert crumbs == []

    def test_extract_breadcrumbs_handles_missing_entries(self):
        """Test breadcrumb extraction with missing entries field"""
        event = {"id": "test", "title": "Error"}
        crumbs = _extract_breadcrumbs(event)
        assert crumbs == []

    def test_extract_breadcrumbs_with_data_only(self):
        """Test breadcrumb extraction when only data field exists"""
        event = {
            "entries": [
                {
                    "type": "breadcrumbs",
                    "data": {
                        "values": [
                            {
                                "category": "http",
                                "level": "info",
                                "data": {
                                    "method": "GET",
                                    "url": "/api/test",
                                    "status": 200
                                }
                            }
                        ]
                    }
                }
            ]
        }

        crumbs = _extract_breadcrumbs(event)
        assert len(crumbs) == 1
        assert "[info] http:" in crumbs[0]
        assert "method=GET" in crumbs[0]

    def test_extract_breadcrumbs_limits_data_fields(self):
        """Test that breadcrumb data is limited to 3 fields"""
        event = {
            "entries": [
                {
                    "type": "breadcrumbs",
                    "data": {
                        "values": [
                            {
                                "category": "test",
                                "level": "info",
                                "data": {
                                    "field1": "value1",
                                    "field2": "value2",
                                    "field3": "value3",
                                    "field4": "value4",
                                    "field5": "value5"
                                }
                            }
                        ]
                    }
                }
            ]
        }

        crumbs = _extract_breadcrumbs(event)
        assert len(crumbs) == 1
        # Should only show first 3 fields
        parts = crumbs[0].split(", ")
        # [info] test: field1=value1, field2=value2, field3=value3
        # Split gives us ["[info] test: field1=value1", "field2=value2", "field3=value3"]
        assert len(parts) == 3


class TestStackTraceTruncation:
    """Test that long stack traces are truncated properly"""

    def test_long_stack_trace_truncated(self, mock_config):
        """Test that stack traces longer than 5 frames are truncated"""
        event = {
            "id": "long-stack",
            "datetime": "2025-01-19T14:30:15Z",
            "title": "Deep stack error",
            "entries": [
                {
                    "type": "exception",
                    "data": {
                        "values": [
                            {
                                "stacktrace": {
                                    "frames": [
                                        {
                                            "filename": f"file{i}.py",
                                            "function": f"func{i}",
                                            "lineNo": i * 10
                                        }
                                        for i in range(10)  # 10 frames
                                    ]
                                }
                            }
                        ]
                    }
                }
            ]
        }

        result = format_events_for_llm([event])

        # Should show first 5 frames
        assert "file0.py:0" in result
        assert "file4.py:40" in result

        # Should not show frames 5-9
        assert "file9.py:90" not in result

        # Should indicate truncation
        assert "(5 more frames)" in result


class TestBreadcrumbTruncation:
    """Test that long breadcrumb lists show only last 5"""

    def test_many_breadcrumbs_shows_last_five(self, mock_config):
        """Test that only the last 5 breadcrumbs are shown"""
        event = {
            "id": "many-crumbs",
            "datetime": "2025-01-19T14:30:15Z",
            "title": "Error with many breadcrumbs",
            "entries": [
                {
                    "type": "breadcrumbs",
                    "data": {
                        "values": [
                            {
                                "category": f"action{i}",
                                "message": f"Action {i}",
                                "level": "info"
                            }
                            for i in range(10)  # 10 breadcrumbs
                        ]
                    }
                }
            ]
        }

        result = format_events_for_llm([event])

        # Should show last 5 (indices 5-9)
        assert "Action 5" in result
        assert "Action 9" in result

        # Should not show first ones (indices 0-4)
        assert "Action 0" not in result
        assert "Action 4" not in result
