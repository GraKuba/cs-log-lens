"""
End-to-End Integration Tests for LogLens MVP

This test suite verifies the complete flow from frontend/Slack to backend to Sentry to LLM.
Tests are designed to be run against a deployed instance or local development environment.

Test Cases (from Tech Spec lines 518-525):
1. Submit with valid inputs → Returns causes + response
2. Submit with invalid customer ID → Returns "no events found"
3. Submit with wrong password → Returns 401
4. Slack command with valid inputs → Posts formatted response
5. Slack command with missing params → Posts usage instructions

Usage:
    # Test against local development server
    python test_e2e_integration.py

    # Test against deployed Railway backend
    python test_e2e_integration.py --url https://your-app.railway.app

    # Test with real Sentry data
    python test_e2e_integration.py --real-data

    # Run specific test cases
    python test_e2e_integration.py --tests 1,2,3
"""

import asyncio
import argparse
import json
import time
import hmac
import hashlib
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import httpx
from dataclasses import dataclass


@dataclass
class TestResult:
    """Test result data structure"""
    test_id: str
    name: str
    passed: bool
    duration: float
    details: str
    error: Optional[str] = None


@dataclass
class E2EConfig:
    """Configuration for E2E tests"""
    backend_url: str
    auth_token: str
    slack_signing_secret: Optional[str] = None
    use_real_data: bool = False
    timeout: int = 30


class E2ETestRunner:
    """End-to-end integration test runner"""

    def __init__(self, config: E2EConfig):
        self.config = config
        self.results: List[TestResult] = []
        self.client = httpx.AsyncClient(timeout=config.timeout)

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    def _create_slack_signature(self, timestamp: str, body: str) -> str:
        """Create HMAC-SHA256 signature for Slack request"""
        if not self.config.slack_signing_secret:
            return ""

        sig_basestring = f"v0:{timestamp}:{body}"
        signature = hmac.new(
            self.config.slack_signing_secret.encode(),
            sig_basestring.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"v0={signature}"

    async def test_health_endpoint(self) -> TestResult:
        """Test 0: Health endpoint is accessible"""
        start_time = time.time()
        test_id = "0"
        name = "Health Endpoint"

        try:
            response = await self.client.get(f"{self.config.backend_url}/health")
            duration = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    return TestResult(
                        test_id=test_id,
                        name=name,
                        passed=True,
                        duration=duration,
                        details=f"Health check passed. Version: {data.get('version', 'unknown')}"
                    )
                else:
                    return TestResult(
                        test_id=test_id,
                        name=name,
                        passed=False,
                        duration=duration,
                        details="Health check returned non-healthy status",
                        error=f"Status: {data.get('status')}"
                    )
            else:
                return TestResult(
                    test_id=test_id,
                    name=name,
                    passed=False,
                    duration=duration,
                    details="Health endpoint returned non-200 status",
                    error=f"Status code: {response.status_code}"
                )

        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_id=test_id,
                name=name,
                passed=False,
                duration=duration,
                details="Failed to connect to health endpoint",
                error=str(e)
            )

    async def test_valid_analysis_request(self) -> TestResult:
        """Test 1: Submit with valid inputs → Returns causes + response"""
        start_time = time.time()
        test_id = "1"
        name = "Valid Analysis Request"

        # Use test data or real data based on config
        if self.config.use_real_data:
            # User should provide real customer ID via environment
            customer_id = "usr_real_customer"  # Replace with real ID
            timestamp = (datetime.utcnow() - timedelta(minutes=5)).isoformat() + "Z"
        else:
            customer_id = "usr_test123"
            timestamp = "2025-01-19T14:30:00Z"

        request_data = {
            "description": "User says checkout button does nothing when clicked",
            "timestamp": timestamp,
            "customer_id": customer_id
        }

        try:
            response = await self.client.post(
                f"{self.config.backend_url}/analyze",
                json=request_data,
                headers={"X-Auth-Token": self.config.auth_token}
            )
            duration = time.time() - start_time

            if response.status_code == 200:
                data = response.json()

                # Verify response structure
                if (data.get("success") and
                    "causes" in data and
                    "suggested_response" in data and
                    len(data["causes"]) > 0):

                    return TestResult(
                        test_id=test_id,
                        name=name,
                        passed=True,
                        duration=duration,
                        details=f"Analysis completed. Found {len(data['causes'])} causes. Events: {data.get('events_found', 0)}"
                    )
                else:
                    return TestResult(
                        test_id=test_id,
                        name=name,
                        passed=False,
                        duration=duration,
                        details="Response missing required fields",
                        error=f"Response: {json.dumps(data, indent=2)}"
                    )
            else:
                return TestResult(
                    test_id=test_id,
                    name=name,
                    passed=False,
                    duration=duration,
                    details=f"Request failed with status {response.status_code}",
                    error=response.text
                )

        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_id=test_id,
                name=name,
                passed=False,
                duration=duration,
                details="Request failed with exception",
                error=str(e)
            )

    async def test_invalid_customer_id(self) -> TestResult:
        """Test 2: Submit with invalid customer ID → Returns 'no events found'"""
        start_time = time.time()
        test_id = "2"
        name = "Invalid Customer ID"

        request_data = {
            "description": "Test with non-existent customer",
            "timestamp": "2025-01-19T14:30:00Z",
            "customer_id": "usr_nonexistent_12345"
        }

        try:
            response = await self.client.post(
                f"{self.config.backend_url}/analyze",
                json=request_data,
                headers={"X-Auth-Token": self.config.auth_token}
            )
            duration = time.time() - start_time

            if response.status_code == 200:
                data = response.json()

                # Should still succeed but indicate no events found
                if data.get("events_found") == 0:
                    return TestResult(
                        test_id=test_id,
                        name=name,
                        passed=True,
                        duration=duration,
                        details="Correctly handled invalid customer ID (no events found)"
                    )
                else:
                    return TestResult(
                        test_id=test_id,
                        name=name,
                        passed=False,
                        duration=duration,
                        details="Expected no events but found some",
                        error=f"Events found: {data.get('events_found')}"
                    )
            else:
                # May also return error response
                return TestResult(
                    test_id=test_id,
                    name=name,
                    passed=True,
                    duration=duration,
                    details=f"Returned error status (acceptable): {response.status_code}"
                )

        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_id=test_id,
                name=name,
                passed=False,
                duration=duration,
                details="Request failed with exception",
                error=str(e)
            )

    async def test_wrong_password(self) -> TestResult:
        """Test 3: Submit with wrong password → Returns 401"""
        start_time = time.time()
        test_id = "3"
        name = "Wrong Password"

        request_data = {
            "description": "Test authentication",
            "timestamp": "2025-01-19T14:30:00Z",
            "customer_id": "usr_test123"
        }

        try:
            response = await self.client.post(
                f"{self.config.backend_url}/analyze",
                json=request_data,
                headers={"X-Auth-Token": "wrong_password_12345"}
            )
            duration = time.time() - start_time

            if response.status_code == 401:
                return TestResult(
                    test_id=test_id,
                    name=name,
                    passed=True,
                    duration=duration,
                    details="Correctly rejected invalid authentication"
                )
            else:
                return TestResult(
                    test_id=test_id,
                    name=name,
                    passed=False,
                    duration=duration,
                    details=f"Expected 401 but got {response.status_code}",
                    error=response.text
                )

        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_id=test_id,
                name=name,
                passed=False,
                duration=duration,
                details="Request failed with exception",
                error=str(e)
            )

    async def test_slack_valid_command(self) -> TestResult:
        """Test 4: Slack command with valid inputs → Posts formatted response"""
        start_time = time.time()
        test_id = "4"
        name = "Slack Valid Command"

        if not self.config.slack_signing_secret:
            return TestResult(
                test_id=test_id,
                name=name,
                passed=False,
                duration=0,
                details="Skipped - SLACK_SIGNING_SECRET not provided",
                error="Set SLACK_SIGNING_SECRET to run this test"
            )

        timestamp = str(int(time.time()))
        command_text = "User can't checkout | 2025-01-19T14:30:00Z | usr_test123"
        body = f"command=/loglens&text={command_text}"

        signature = self._create_slack_signature(timestamp, body)

        try:
            response = await self.client.post(
                f"{self.config.backend_url}/slack/commands",
                data=body,
                headers={
                    "X-Slack-Request-Timestamp": timestamp,
                    "X-Slack-Signature": signature,
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            )
            duration = time.time() - start_time

            if response.status_code == 200:
                data = response.json()

                # Check for formatted Slack response
                if ("blocks" in data or "text" in data):
                    return TestResult(
                        test_id=test_id,
                        name=name,
                        passed=True,
                        duration=duration,
                        details="Slack command processed successfully"
                    )
                else:
                    return TestResult(
                        test_id=test_id,
                        name=name,
                        passed=False,
                        duration=duration,
                        details="Response missing Slack formatting",
                        error=f"Response: {json.dumps(data, indent=2)}"
                    )
            else:
                return TestResult(
                    test_id=test_id,
                    name=name,
                    passed=False,
                    duration=duration,
                    details=f"Request failed with status {response.status_code}",
                    error=response.text
                )

        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_id=test_id,
                name=name,
                passed=False,
                duration=duration,
                details="Request failed with exception",
                error=str(e)
            )

    async def test_slack_missing_params(self) -> TestResult:
        """Test 5: Slack command with missing params → Posts usage instructions"""
        start_time = time.time()
        test_id = "5"
        name = "Slack Missing Params"

        if not self.config.slack_signing_secret:
            return TestResult(
                test_id=test_id,
                name=name,
                passed=False,
                duration=0,
                details="Skipped - SLACK_SIGNING_SECRET not provided",
                error="Set SLACK_SIGNING_SECRET to run this test"
            )

        timestamp = str(int(time.time()))
        command_text = "incomplete command"
        body = f"command=/loglens&text={command_text}"

        signature = self._create_slack_signature(timestamp, body)

        try:
            response = await self.client.post(
                f"{self.config.backend_url}/slack/commands",
                data=body,
                headers={
                    "X-Slack-Request-Timestamp": timestamp,
                    "X-Slack-Signature": signature,
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            )
            duration = time.time() - start_time

            if response.status_code == 200:
                data = response.json()

                # Should return usage instructions
                response_text = data.get("text", "")
                if "usage" in response_text.lower() or "format" in response_text.lower():
                    return TestResult(
                        test_id=test_id,
                        name=name,
                        passed=True,
                        duration=duration,
                        details="Correctly returned usage instructions"
                    )
                else:
                    return TestResult(
                        test_id=test_id,
                        name=name,
                        passed=False,
                        duration=duration,
                        details="Expected usage instructions but got different response",
                        error=f"Response: {response_text}"
                    )
            else:
                return TestResult(
                    test_id=test_id,
                    name=name,
                    passed=False,
                    duration=duration,
                    details=f"Request failed with status {response.status_code}",
                    error=response.text
                )

        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_id=test_id,
                name=name,
                passed=False,
                duration=duration,
                details="Request failed with exception",
                error=str(e)
            )

    async def test_concurrent_requests(self) -> TestResult:
        """Test 6: Multiple concurrent requests are handled correctly"""
        start_time = time.time()
        test_id = "6"
        name = "Concurrent Requests"

        request_data = {
            "description": "Concurrent test request",
            "timestamp": "2025-01-19T14:30:00Z",
            "customer_id": "usr_test123"
        }

        try:
            # Send 3 requests concurrently
            tasks = [
                self.client.post(
                    f"{self.config.backend_url}/analyze",
                    json=request_data,
                    headers={"X-Auth-Token": self.config.auth_token}
                )
                for _ in range(3)
            ]

            responses = await asyncio.gather(*tasks, return_exceptions=True)
            duration = time.time() - start_time

            # Check all responses succeeded
            success_count = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code == 200)

            if success_count == 3:
                return TestResult(
                    test_id=test_id,
                    name=name,
                    passed=True,
                    duration=duration,
                    details=f"All {success_count}/3 concurrent requests succeeded"
                )
            else:
                return TestResult(
                    test_id=test_id,
                    name=name,
                    passed=False,
                    duration=duration,
                    details=f"Only {success_count}/3 concurrent requests succeeded",
                    error="Some requests failed"
                )

        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_id=test_id,
                name=name,
                passed=False,
                duration=duration,
                details="Concurrent requests failed with exception",
                error=str(e)
            )

    async def test_response_time(self) -> TestResult:
        """Test 7: Response time is acceptable (< 5 seconds)"""
        start_time = time.time()
        test_id = "7"
        name = "Response Time"

        request_data = {
            "description": "Response time test",
            "timestamp": "2025-01-19T14:30:00Z",
            "customer_id": "usr_test123"
        }

        try:
            response = await self.client.post(
                f"{self.config.backend_url}/analyze",
                json=request_data,
                headers={"X-Auth-Token": self.config.auth_token}
            )
            duration = time.time() - start_time

            if duration < 5.0:
                return TestResult(
                    test_id=test_id,
                    name=name,
                    passed=True,
                    duration=duration,
                    details=f"Response time: {duration:.2f}s (target: < 5s)"
                )
            else:
                return TestResult(
                    test_id=test_id,
                    name=name,
                    passed=False,
                    duration=duration,
                    details=f"Response time too slow: {duration:.2f}s (target: < 5s)",
                    error="Performance issue detected"
                )

        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_id=test_id,
                name=name,
                passed=False,
                duration=duration,
                details="Request failed with exception",
                error=str(e)
            )

    async def run_tests(self, test_ids: Optional[List[str]] = None) -> List[TestResult]:
        """Run all tests or specific tests"""
        all_tests = [
            ("0", self.test_health_endpoint),
            ("1", self.test_valid_analysis_request),
            ("2", self.test_invalid_customer_id),
            ("3", self.test_wrong_password),
            ("4", self.test_slack_valid_command),
            ("5", self.test_slack_missing_params),
            ("6", self.test_concurrent_requests),
            ("7", self.test_response_time),
        ]

        # Filter tests if specific IDs requested
        if test_ids:
            tests_to_run = [(tid, func) for tid, func in all_tests if tid in test_ids]
        else:
            tests_to_run = all_tests

        print(f"\n{'='*60}")
        print(f"Running {len(tests_to_run)} E2E Integration Tests")
        print(f"Backend URL: {self.config.backend_url}")
        print(f"{'='*60}\n")

        for test_id, test_func in tests_to_run:
            print(f"Running Test {test_id}...", end=" ", flush=True)
            result = await test_func()
            self.results.append(result)

            status = "✅ PASS" if result.passed else "❌ FAIL"
            print(f"{status} ({result.duration:.2f}s)")
            print(f"  {result.details}")
            if result.error:
                print(f"  Error: {result.error}")
            print()

        return self.results

    def print_summary(self):
        """Print test summary"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed

        print(f"\n{'='*60}")
        print(f"Test Summary")
        print(f"{'='*60}")
        print(f"Total Tests:  {total}")
        print(f"Passed:       {passed} ✅")
        print(f"Failed:       {failed} ❌")
        print(f"Pass Rate:    {(passed/total*100):.1f}%")
        print(f"{'='*60}\n")

        if failed > 0:
            print("Failed Tests:")
            for result in self.results:
                if not result.passed:
                    print(f"  - Test {result.test_id}: {result.name}")
                    print(f"    {result.details}")
            print()

    def save_results(self, filename: str = "e2e_test_results.json"):
        """Save test results to JSON file"""
        results_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "backend_url": self.config.backend_url,
            "total_tests": len(self.results),
            "passed": sum(1 for r in self.results if r.passed),
            "failed": sum(1 for r in self.results if not r.passed),
            "tests": [
                {
                    "test_id": r.test_id,
                    "name": r.name,
                    "passed": r.passed,
                    "duration": r.duration,
                    "details": r.details,
                    "error": r.error
                }
                for r in self.results
            ]
        }

        with open(filename, "w") as f:
            json.dump(results_data, f, indent=2)

        print(f"Results saved to {filename}")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Run E2E integration tests for LogLens MVP")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Backend URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--auth-token",
        default="test_password",
        help="Authentication token (default: test_password)"
    )
    parser.add_argument(
        "--slack-secret",
        help="Slack signing secret (optional, for Slack tests)"
    )
    parser.add_argument(
        "--real-data",
        action="store_true",
        help="Use real Sentry data instead of test data"
    )
    parser.add_argument(
        "--tests",
        help="Comma-separated list of test IDs to run (e.g., '1,2,3')"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Request timeout in seconds (default: 30)"
    )
    parser.add_argument(
        "--output",
        default="e2e_test_results.json",
        help="Output file for test results (default: e2e_test_results.json)"
    )

    args = parser.parse_args()

    # Parse test IDs if provided
    test_ids = None
    if args.tests:
        test_ids = [tid.strip() for tid in args.tests.split(",")]

    # Create config
    config = E2EConfig(
        backend_url=args.url.rstrip("/"),
        auth_token=args.auth_token,
        slack_signing_secret=args.slack_secret,
        use_real_data=args.real_data,
        timeout=args.timeout
    )

    # Run tests
    runner = E2ETestRunner(config)
    try:
        await runner.run_tests(test_ids)
        runner.print_summary()
        runner.save_results(args.output)

        # Exit with error code if any tests failed
        failed_count = sum(1 for r in runner.results if not r.passed)
        exit(0 if failed_count == 0 else 1)
    finally:
        await runner.close()


if __name__ == "__main__":
    asyncio.run(main())
