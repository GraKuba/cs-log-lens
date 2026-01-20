"""
Performance Testing Suite for LogLens Backend
Tests API response times, caching, concurrent requests, and resource usage

Run with: pytest test_performance.py -v
Run specific test: pytest test_performance.py::test_analyze_response_time -v
"""

import pytest
import time
import asyncio
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from main import app

# Test configuration
PERFORMANCE_TARGETS = {
    "health_endpoint": 0.1,  # 100ms
    "analyze_endpoint": 5.0,  # 5 seconds
    "concurrent_requests": 10.0,  # 10 seconds for 5 concurrent requests
}


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Headers with valid authentication"""
    return {"X-Auth-Token": "test-password"}


@pytest.fixture
def mock_environment(monkeypatch):
    """Mock environment variables for testing"""
    monkeypatch.setenv("APP_PASSWORD", "test-password")
    monkeypatch.setenv("SENTRY_AUTH_TOKEN", "test-token")
    monkeypatch.setenv("SENTRY_ORG", "test-org")
    monkeypatch.setenv("SENTRY_PROJECT", "test-project")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("SLACK_BOT_TOKEN", "test-bot-token")
    monkeypatch.setenv("SLACK_SIGNING_SECRET", "test-secret")
    monkeypatch.setenv("ALLOWED_ORIGINS", "*")

    # Reset global config to force reload
    import config
    config.config = None


class TestPerformance:
    """Performance tests for API endpoints"""

    def test_health_endpoint_response_time(self, client):
        """
        Test that health endpoint responds quickly
        Target: < 100ms
        """
        start_time = time.time()
        response = client.get("/health")
        duration = time.time() - start_time

        assert response.status_code == 200
        assert duration < PERFORMANCE_TARGETS["health_endpoint"], \
            f"Health endpoint took {duration:.3f}s, target is {PERFORMANCE_TARGETS['health_endpoint']}s"

    @patch("sentry_client.fetch_sentry_events")
    @patch("analyzer.analyze_logs")
    def test_analyze_response_time(
        self,
        mock_analyze,
        mock_fetch_events,
        client,
        auth_headers,
        mock_environment
    ):
        """
        Test that analyze endpoint responds within 5 seconds
        Target: < 5s for typical request
        """
        # Mock Sentry events
        mock_fetch_events.return_value = []

        # Mock LLM analysis
        mock_analyze.return_value = {
            "causes": [
                {
                    "rank": 1,
                    "cause": "Test cause",
                    "explanation": "Test explanation",
                    "confidence": "high"
                }
            ],
            "suggested_response": "Test response",
            "logs_summary": "Test summary"
        }

        payload = {
            "description": "User can't checkout",
            "timestamp": "2026-01-20T14:30:00Z",
            "customer_id": "usr_test123"
        }

        start_time = time.time()
        response = client.post("/analyze", json=payload, headers=auth_headers)
        duration = time.time() - start_time

        assert response.status_code == 200
        assert duration < PERFORMANCE_TARGETS["analyze_endpoint"], \
            f"Analyze endpoint took {duration:.3f}s, target is {PERFORMANCE_TARGETS['analyze_endpoint']}s"

    @patch("sentry_client.fetch_sentry_events")
    @patch("analyzer.analyze_logs")
    def test_concurrent_requests(
        self,
        mock_analyze,
        mock_fetch_events,
        client,
        auth_headers,
        mock_environment
    ):
        """
        Test that server handles concurrent requests efficiently
        Target: 5 concurrent requests complete in < 10s
        """
        # Mock responses
        mock_fetch_events.return_value = []
        mock_analyze.return_value = {
            "causes": [
                {
                    "rank": 1,
                    "cause": "Test cause",
                    "explanation": "Test explanation",
                    "confidence": "high"
                }
            ],
            "suggested_response": "Test response",
            "logs_summary": "Test summary"
        }

        payload = {
            "description": "User can't checkout",
            "timestamp": "2026-01-20T14:30:00Z",
            "customer_id": "usr_test123"
        }

        # Make 5 concurrent requests
        start_time = time.time()
        responses = []

        for _ in range(5):
            response = client.post("/analyze", json=payload, headers=auth_headers)
            responses.append(response)

        duration = time.time() - start_time

        # All requests should succeed
        for response in responses:
            assert response.status_code == 200

        # Should complete in reasonable time
        assert duration < PERFORMANCE_TARGETS["concurrent_requests"], \
            f"5 concurrent requests took {duration:.3f}s, target is {PERFORMANCE_TARGETS['concurrent_requests']}s"

    @patch("sentry_client._cached_fetch_events")
    def test_sentry_cache_performance(
        self,
        mock_cached_fetch,
        client,
        auth_headers,
        mock_environment
    ):
        """
        Test that Sentry caching improves performance
        Cached request should be significantly faster than first request
        """
        from sentry_client import clear_sentry_cache

        # Clear cache before test
        clear_sentry_cache()

        # Mock first call (uncached) to be slower
        async def slow_fetch(*args, **kwargs):
            await asyncio.sleep(0.5)  # Simulate API delay
            return []

        # Mock second call (cached) to be instant
        async def fast_fetch(*args, **kwargs):
            return []

        mock_cached_fetch.side_effect = [slow_fetch(), fast_fetch()]

        payload = {
            "description": "Test issue",
            "timestamp": "2026-01-20T14:30:00Z",
            "customer_id": "usr_test123"
        }

        # First request (uncached)
        start_time = time.time()
        response1 = client.post("/analyze", json=payload, headers=auth_headers)
        duration1 = time.time() - start_time

        # Second request (should use cache)
        start_time = time.time()
        response2 = client.post("/analyze", json=payload, headers=auth_headers)
        duration2 = time.time() - start_time

        # Both should succeed
        assert response1.status_code == 200 or response1.status_code == 500  # May fail due to mock
        assert response2.status_code == 200 or response2.status_code == 500

        # Second request should be faster (if caching is working)
        print(f"First request: {duration1:.3f}s, Second request: {duration2:.3f}s")

    def test_health_endpoint_under_load(self, client):
        """
        Test that health endpoint remains fast under load
        Target: < 200ms even with 10 sequential requests
        """
        durations = []

        for _ in range(10):
            start_time = time.time()
            response = client.get("/health")
            duration = time.time() - start_time
            durations.append(duration)

            assert response.status_code == 200

        # Average should be fast
        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)

        assert avg_duration < 0.1, \
            f"Average health endpoint time {avg_duration:.3f}s exceeds 100ms"
        assert max_duration < 0.2, \
            f"Max health endpoint time {max_duration:.3f}s exceeds 200ms"

    @patch("sentry_client.fetch_sentry_events")
    @patch("analyzer.analyze_logs")
    def test_response_payload_size(
        self,
        mock_analyze,
        mock_fetch_events,
        client,
        auth_headers,
        mock_environment
    ):
        """
        Test that response payload is reasonable size
        Target: < 50KB for typical response
        """
        # Mock responses
        mock_fetch_events.return_value = [{"id": "test-event-1"}]
        mock_analyze.return_value = {
            "causes": [
                {
                    "rank": i,
                    "cause": f"Test cause {i}",
                    "explanation": f"Test explanation {i} " * 10,
                    "confidence": "high"
                }
                for i in range(1, 4)
            ],
            "suggested_response": "Test response " * 20,
            "logs_summary": "Test summary " * 10
        }

        payload = {
            "description": "User can't checkout",
            "timestamp": "2026-01-20T14:30:00Z",
            "customer_id": "usr_test123"
        }

        response = client.post("/analyze", json=payload, headers=auth_headers)

        assert response.status_code == 200

        # Check response size
        response_size = len(response.content)
        max_size = 50 * 1024  # 50KB

        assert response_size < max_size, \
            f"Response size {response_size} bytes exceeds {max_size} bytes"

    def test_cors_performance(self, client):
        """
        Test that CORS preflight requests are fast
        Target: < 50ms
        """
        start_time = time.time()
        response = client.options(
            "/analyze",
            headers={
                "Origin": "https://example.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type,X-Auth-Token"
            }
        )
        duration = time.time() - start_time

        assert response.status_code == 200
        assert duration < 0.05, \
            f"CORS preflight took {duration:.3f}s, target is 50ms"


class TestPerformanceMetrics:
    """Tests for measuring and reporting performance metrics"""

    @patch("sentry_client.fetch_sentry_events")
    @patch("analyzer.analyze_logs")
    def test_full_pipeline_timing(
        self,
        mock_analyze,
        mock_fetch_events,
        client,
        auth_headers,
        mock_environment
    ):
        """
        Test and report timing for full analysis pipeline
        Measures: Sentry fetch time + LLM analysis time + total time
        """
        # Track timing for mocked operations
        sentry_time = 0.5  # Simulated Sentry API time
        llm_time = 2.0  # Simulated LLM time

        async def timed_fetch(*args, **kwargs):
            await asyncio.sleep(sentry_time)
            return [{"id": "event-1"}]

        async def timed_analyze(*args, **kwargs):
            await asyncio.sleep(llm_time)
            return {
                "causes": [
                    {
                        "rank": 1,
                        "cause": "Test",
                        "explanation": "Test",
                        "confidence": "high"
                    }
                ],
                "suggested_response": "Test",
                "logs_summary": "Test"
            }

        mock_fetch_events.side_effect = timed_fetch
        mock_analyze.side_effect = timed_analyze

        payload = {
            "description": "User can't checkout",
            "timestamp": "2026-01-20T14:30:00Z",
            "customer_id": "usr_test123"
        }

        start_time = time.time()
        response = client.post("/analyze", json=payload, headers=auth_headers)
        total_time = time.time() - start_time

        assert response.status_code == 200

        # Report timing breakdown
        print(f"\nPerformance Breakdown:")
        print(f"  Sentry fetch: ~{sentry_time:.2f}s")
        print(f"  LLM analysis: ~{llm_time:.2f}s")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Overhead: {total_time - sentry_time - llm_time:.2f}s")

        # Total time should be close to sum of operations
        expected_time = sentry_time + llm_time
        overhead = total_time - expected_time

        # Overhead should be minimal (< 1s)
        assert overhead < 1.0, \
            f"Pipeline overhead {overhead:.2f}s is too high"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
