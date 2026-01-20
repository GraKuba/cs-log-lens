"""
Tests for Sentry API Client
"""

import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

import httpx

from sentry_client import (
    fetch_sentry_events,
    clear_sentry_cache,
    _parse_iso_timestamp,
    _format_datetime_for_sentry,
    _make_sentry_request,
    SentryAuthError,
    SentryRateLimitError,
    SentryAPIError,
)
from config import Config


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
def sample_sentry_events():
    """Sample Sentry event data for testing"""
    return [
        {
            "id": "event-123",
            "title": "PaymentError: Token expired",
            "message": "Payment token expired after 10 minutes",
            "datetime": "2025-01-19T14:30:15Z",
            "user": {"id": "usr_abc123"},
            "tags": [{"key": "environment", "value": "production"}],
        },
        {
            "id": "event-456",
            "title": "ValidationError: Invalid card",
            "message": "Card number validation failed",
            "datetime": "2025-01-19T14:32:00Z",
            "user": {"id": "usr_abc123"},
            "tags": [{"key": "environment", "value": "production"}],
        },
    ]


class TestTimestampParsing:
    """Test timestamp parsing and formatting"""

    def test_parse_iso_timestamp_with_z(self):
        """Test parsing ISO timestamp with Z suffix"""
        timestamp = "2025-01-19T14:30:00Z"
        result = _parse_iso_timestamp(timestamp)
        assert isinstance(result, datetime)
        assert result.year == 2025
        assert result.month == 1
        assert result.day == 19
        assert result.hour == 14
        assert result.minute == 30

    def test_parse_iso_timestamp_with_offset(self):
        """Test parsing ISO timestamp with timezone offset"""
        timestamp = "2025-01-19T14:30:00+00:00"
        result = _parse_iso_timestamp(timestamp)
        assert isinstance(result, datetime)
        assert result.year == 2025

    def test_parse_iso_timestamp_invalid(self):
        """Test parsing invalid timestamp raises ValueError"""
        with pytest.raises(ValueError, match="Invalid timestamp format"):
            _parse_iso_timestamp("not-a-timestamp")

    def test_parse_iso_timestamp_empty(self):
        """Test parsing empty timestamp raises ValueError"""
        with pytest.raises(ValueError):
            _parse_iso_timestamp("")

    def test_format_datetime_for_sentry(self):
        """Test formatting datetime for Sentry API"""
        dt = datetime(2025, 1, 19, 14, 30, 0)
        result = _format_datetime_for_sentry(dt)
        assert isinstance(result, str)
        assert "2025-01-19" in result
        assert "14:30:00" in result


class TestMakeSentryRequest:
    """Test HTTP request handling"""

    @pytest.mark.asyncio
    async def test_successful_request(self, sample_sentry_events):
        """Test successful API request"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_sentry_events
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await _make_sentry_request(
                url="https://sentry.io/api/0/test",
                headers={"Authorization": "Bearer test"},
                params={"query": "test"},
            )

            assert result == sample_sentry_events

    @pytest.mark.asyncio
    async def test_rate_limit_error(self):
        """Test handling of rate limit (429) response"""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            with pytest.raises(SentryRateLimitError, match="Rate limit exceeded"):
                await _make_sentry_request(
                    url="https://sentry.io/api/0/test",
                    headers={"Authorization": "Bearer test"},
                    params={"query": "test"},
                )

    @pytest.mark.asyncio
    async def test_auth_error(self):
        """Test handling of authentication error (401)"""
        mock_response = MagicMock()
        mock_response.status_code = 401

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            with pytest.raises(SentryAuthError, match="Invalid or expired"):
                await _make_sentry_request(
                    url="https://sentry.io/api/0/test",
                    headers={"Authorization": "Bearer test"},
                    params={"query": "test"},
                )

    @pytest.mark.asyncio
    async def test_not_found_error(self):
        """Test handling of 404 not found"""
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            with pytest.raises(SentryAPIError, match="project not found"):
                await _make_sentry_request(
                    url="https://sentry.io/api/0/test",
                    headers={"Authorization": "Bearer test"},
                    params={"query": "test"},
                )

    @pytest.mark.asyncio
    async def test_server_error(self):
        """Test handling of server error (500)"""
        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            with pytest.raises(SentryAPIError, match="server error"):
                await _make_sentry_request(
                    url="https://sentry.io/api/0/test",
                    headers={"Authorization": "Bearer test"},
                    params={"query": "test"},
                )


class TestFetchSentryEvents:
    """Test main fetch_sentry_events function"""

    @pytest.mark.asyncio
    async def test_successful_fetch(self, mock_config, sample_sentry_events):
        """Test successful event fetching"""
        # Clear cache before test
        clear_sentry_cache()

        with patch(
            "sentry_client._make_sentry_request",
            new=AsyncMock(return_value=sample_sentry_events),
        ):
            events = await fetch_sentry_events(
                customer_id="usr_abc123",
                timestamp="2025-01-19T14:30:00Z",
            )

            assert len(events) == 2
            assert events[0]["id"] == "event-123"
            assert events[1]["id"] == "event-456"

    @pytest.mark.asyncio
    async def test_no_events_found(self, mock_config):
        """Test when no events are found"""
        # Clear cache before test
        clear_sentry_cache()

        with patch(
            "sentry_client._make_sentry_request",
            new=AsyncMock(return_value=[]),
        ):
            events = await fetch_sentry_events(
                customer_id="usr_nonexistent",
                timestamp="2025-01-19T14:30:00Z",
            )

            assert events == []

    @pytest.mark.asyncio
    async def test_invalid_timestamp(self, mock_config):
        """Test with invalid timestamp format"""
        with pytest.raises(ValueError, match="Invalid timestamp format"):
            await fetch_sentry_events(
                customer_id="usr_abc123",
                timestamp="invalid-timestamp",
            )

    @pytest.mark.asyncio
    async def test_empty_customer_id(self, mock_config, sample_sentry_events):
        """Test with empty customer ID (should still make request)"""
        # Clear cache before test
        clear_sentry_cache()

        with patch(
            "sentry_client._make_sentry_request",
            new=AsyncMock(return_value=[]),
        ):
            events = await fetch_sentry_events(
                customer_id="",
                timestamp="2025-01-19T14:30:00Z",
            )

            assert events == []

    @pytest.mark.asyncio
    async def test_custom_time_window(self, mock_config, sample_sentry_events):
        """Test with custom time window"""
        # Clear cache before test
        clear_sentry_cache()

        with patch(
            "sentry_client._make_sentry_request",
            new=AsyncMock(return_value=sample_sentry_events),
        ):
            events = await fetch_sentry_events(
                customer_id="usr_abc123",
                timestamp="2025-01-19T14:30:00Z",
                time_window_minutes=10,
            )

            assert len(events) == 2

    @pytest.mark.asyncio
    async def test_auth_error_propagation(self, mock_config):
        """Test that auth errors are propagated"""
        # Clear cache before test
        clear_sentry_cache()

        with patch(
            "sentry_client._make_sentry_request",
            new=AsyncMock(side_effect=SentryAuthError("Invalid token")),
        ):
            with pytest.raises(SentryAuthError, match="Invalid token"):
                await fetch_sentry_events(
                    customer_id="usr_abc123",
                    timestamp="2025-01-19T14:30:00Z",
                )

    @pytest.mark.asyncio
    async def test_rate_limit_error_propagation(self, mock_config):
        """Test that rate limit errors are propagated"""
        # Clear cache before test
        clear_sentry_cache()

        with patch(
            "sentry_client._make_sentry_request",
            new=AsyncMock(side_effect=SentryRateLimitError("Rate limited")),
        ):
            with pytest.raises(SentryRateLimitError, match="Rate limited"):
                await fetch_sentry_events(
                    customer_id="usr_abc123",
                    timestamp="2025-01-19T14:30:00Z",
                )

    @pytest.mark.asyncio
    async def test_caching_behavior(self, mock_config, sample_sentry_events):
        """Test that caching works for identical requests"""
        # Clear cache before test
        clear_sentry_cache()

        mock_request = AsyncMock(return_value=sample_sentry_events)

        with patch("sentry_client._make_sentry_request", new=mock_request):
            # First call
            events1 = await fetch_sentry_events(
                customer_id="usr_abc123",
                timestamp="2025-01-19T14:30:00Z",
            )

            # Second call with same parameters (should use cache)
            events2 = await fetch_sentry_events(
                customer_id="usr_abc123",
                timestamp="2025-01-19T14:30:00Z",
            )

            # Both should return same data
            assert events1 == events2
            assert len(events1) == 2


class TestIntegration:
    """Integration tests for Sentry client"""

    @pytest.mark.asyncio
    async def test_url_construction(self, mock_config, sample_sentry_events):
        """Test that URL is constructed correctly"""
        # Clear cache before test
        clear_sentry_cache()

        called_url = None

        async def capture_url(url, headers, params, **kwargs):
            nonlocal called_url
            called_url = url
            return sample_sentry_events

        with patch("sentry_client._make_sentry_request", new=capture_url):
            await fetch_sentry_events(
                customer_id="usr_abc123",
                timestamp="2025-01-19T14:30:00Z",
            )

            assert called_url == "https://sentry.io/api/0/projects/test-org/test-project/events/"

    @pytest.mark.asyncio
    async def test_query_parameters(self, mock_config, sample_sentry_events):
        """Test that query parameters are constructed correctly"""
        # Clear cache before test
        clear_sentry_cache()

        called_params = None

        async def capture_params(url, headers, params, **kwargs):
            nonlocal called_params
            called_params = params
            return sample_sentry_events

        with patch("sentry_client._make_sentry_request", new=capture_params):
            await fetch_sentry_events(
                customer_id="usr_abc123",
                timestamp="2025-01-19T14:30:00Z",
                time_window_minutes=5,
            )

            assert called_params["query"] == "user.id:usr_abc123"
            assert called_params["full"] == "true"
            assert "start" in called_params
            assert "end" in called_params

    @pytest.mark.asyncio
    async def test_authorization_header(self, mock_config, sample_sentry_events):
        """Test that authorization header is set correctly"""
        # Clear cache before test
        clear_sentry_cache()

        called_headers = None

        async def capture_headers(url, headers, params, **kwargs):
            nonlocal called_headers
            called_headers = headers
            return sample_sentry_events

        with patch("sentry_client._make_sentry_request", new=capture_headers):
            await fetch_sentry_events(
                customer_id="usr_abc123",
                timestamp="2025-01-19T14:30:00Z",
            )

            assert called_headers["Authorization"] == "Bearer test-token-123"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
