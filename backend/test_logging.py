"""
Tests for logging configuration and functionality

Tests verify:
- Structured logging with JSON format in production
- Human-readable format in development
- Sensitive data redaction
- Request/response logging middleware
- Different log levels (DEBUG, INFO, WARNING, ERROR)
"""

import logging
import json
import os
import pytest
from io import StringIO
from fastapi.testclient import TestClient
from unittest.mock import patch

# Import the logging components
from main import app, StructuredFormatter, setup_logging


class TestStructuredFormatter:
    """Test the StructuredFormatter class"""

    def test_json_format(self):
        """Test that JSON format works correctly"""
        formatter = StructuredFormatter(use_json=True)

        # Create a log record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.funcName = "test_function"
        record.module = "test_module"

        # Format the record
        output = formatter.format(record)

        # Parse JSON
        log_data = json.loads(output)

        # Verify structure
        assert log_data["level"] == "INFO"
        assert log_data["logger"] == "test"
        assert log_data["message"] == "Test message"
        assert log_data["module"] == "test_module"
        assert log_data["function"] == "test_function"
        assert log_data["line"] == 10
        assert "timestamp" in log_data

    def test_human_readable_format(self):
        """Test that human-readable format works correctly"""
        formatter = StructuredFormatter(use_json=False)

        # Create a log record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )

        # Format the record
        output = formatter.format(record)

        # Verify format
        assert "test" in output
        assert "INFO" in output
        assert "Test message" in output
        assert "-" in output  # Human-readable format uses dashes

    def test_redact_api_key(self):
        """Test that API keys are redacted"""
        formatter = StructuredFormatter(use_json=False)

        # Create a log record with an API key
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="API key: sk-1234567890abcdefghijklmnop",
            args=(),
            exc_info=None
        )

        # Format the record
        output = formatter.format(record)

        # Verify API key is redacted
        assert "sk-1234567890abcdefghijklmnop" not in output
        assert "***REDACTED***" in output

    def test_redact_bearer_token(self):
        """Test that Bearer tokens are redacted"""
        formatter = StructuredFormatter(use_json=False)

        # Create a log record with a Bearer token
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Authorization: Bearer abc123xyz",
            args=(),
            exc_info=None
        )

        # Format the record
        output = formatter.format(record)

        # Verify Bearer token is redacted
        assert "abc123xyz" not in output
        assert "***REDACTED***" in output

    def test_redact_slack_token(self):
        """Test that Slack tokens are redacted"""
        formatter = StructuredFormatter(use_json=False)

        # Create a log record with a Slack token
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Slack token: xoxb-1234-5678-abcd",
            args=(),
            exc_info=None
        )

        # Format the record
        output = formatter.format(record)

        # Verify Slack token is redacted
        assert "xoxb-1234-5678-abcd" not in output
        assert "***REDACTED***" in output

    def test_redact_sentry_token(self):
        """Test that Sentry tokens are redacted"""
        formatter = StructuredFormatter(use_json=False)

        # Create a log record with a Sentry token
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Sentry token: sntrys_abc123xyz",
            args=(),
            exc_info=None
        )

        # Format the record
        output = formatter.format(record)

        # Verify Sentry token is redacted
        assert "sntrys_abc123xyz" not in output
        assert "***REDACTED***" in output

    def test_redact_password(self):
        """Test that passwords are redacted"""
        formatter = StructuredFormatter(use_json=False)

        # Create a log record with a password
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="password=secret123",
            args=(),
            exc_info=None
        )

        # Format the record
        output = formatter.format(record)

        # Verify password is redacted
        assert "secret123" not in output
        assert "***REDACTED***" in output

    def test_extra_fields_in_json(self):
        """Test that extra fields are included in JSON format"""
        formatter = StructuredFormatter(use_json=True)

        # Create a log record with extra fields
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.funcName = "test_function"
        record.module = "test_module"
        record.request_id = "12345"
        record.duration_ms = 123.45
        record.status_code = 200
        record.path = "/test"

        # Format the record
        output = formatter.format(record)

        # Parse JSON
        log_data = json.loads(output)

        # Verify extra fields
        assert log_data["request_id"] == "12345"
        assert log_data["duration_ms"] == 123.45
        assert log_data["status_code"] == 200
        assert log_data["path"] == "/test"


class TestLoggingSetup:
    """Test the logging setup function"""

    def test_development_format(self):
        """Test that development format is used when not in production"""
        with patch.dict(os.environ, {}, clear=True):
            # Clear RAILWAY_ENVIRONMENT to simulate development
            logger = setup_logging()

            # Get the handler
            root_logger = logging.getLogger()
            assert len(root_logger.handlers) > 0

            handler = root_logger.handlers[0]
            formatter = handler.formatter

            # Verify it's using human-readable format
            assert isinstance(formatter, StructuredFormatter)
            assert formatter.use_json is False

    def test_production_format(self):
        """Test that JSON format is used in production"""
        with patch.dict(os.environ, {"RAILWAY_ENVIRONMENT": "production"}):
            logger = setup_logging()

            # Get the handler
            root_logger = logging.getLogger()
            assert len(root_logger.handlers) > 0

            handler = root_logger.handlers[0]
            formatter = handler.formatter

            # Verify it's using JSON format
            assert isinstance(formatter, StructuredFormatter)
            assert formatter.use_json is True

    def test_log_level_configuration(self):
        """Test that log level can be configured via environment variable"""
        with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}):
            logger = setup_logging()

            # Get the root logger
            root_logger = logging.getLogger()

            # Verify log level
            assert root_logger.level == logging.DEBUG

    def test_log_levels_work(self):
        """Test that different log levels work correctly"""
        logger = setup_logging()

        # Create a string buffer to capture logs
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter(use_json=False))

        # Add handler to logger
        test_logger = logging.getLogger("test_logger")
        test_logger.addHandler(handler)
        test_logger.setLevel(logging.DEBUG)

        # Log at different levels
        test_logger.debug("Debug message")
        test_logger.info("Info message")
        test_logger.warning("Warning message")
        test_logger.error("Error message")

        # Get log output
        output = stream.getvalue()

        # Verify all levels are present
        assert "DEBUG" in output
        assert "INFO" in output
        assert "WARNING" in output
        assert "ERROR" in output


class TestRequestLogging:
    """Test request/response logging middleware"""

    def test_request_logging(self):
        """Test that requests are logged"""
        client = TestClient(app)

        # Capture logs
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter(use_json=False))

        # Add handler to main logger
        main_logger = logging.getLogger("main")
        main_logger.addHandler(handler)
        main_logger.setLevel(logging.INFO)

        # Make a request
        response = client.get("/health")

        # Get log output
        output = stream.getvalue()

        # Verify request was logged
        assert "GET" in output
        assert "/health" in output
        assert "Request:" in output
        assert "Response:" in output

    def test_response_status_logged(self):
        """Test that response status codes are logged"""
        client = TestClient(app)

        # Capture logs
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter(use_json=False))

        # Add handler to main logger
        main_logger = logging.getLogger("main")
        main_logger.addHandler(handler)
        main_logger.setLevel(logging.INFO)

        # Make a successful request
        response = client.get("/health")

        # Get log output
        output = stream.getvalue()

        # Verify status code was logged
        assert "200" in output

    def test_timing_logged(self):
        """Test that request timing is logged in JSON format"""
        client = TestClient(app)

        # Capture logs
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter(use_json=True))

        # Add handler to main logger
        main_logger = logging.getLogger("main")
        main_logger.addHandler(handler)
        main_logger.setLevel(logging.INFO)

        # Make a request
        response = client.get("/health")

        # Get log output
        output = stream.getvalue()

        # Parse JSON logs
        logs = [json.loads(line) for line in output.strip().split("\n") if line]

        # Find response log
        response_logs = [log for log in logs if "Response:" in log.get("message", "")]

        # Verify timing information is present
        assert len(response_logs) > 0
        assert "duration_ms" in response_logs[0]
        assert response_logs[0]["duration_ms"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
