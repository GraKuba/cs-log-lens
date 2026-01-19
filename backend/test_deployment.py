"""
Deployment verification tests for Railway deployment.
Run these tests after deploying to verify the deployment is working correctly.

Usage:
    python test_deployment.py <DEPLOYMENT_URL> <APP_PASSWORD>

Example:
    python test_deployment.py https://your-app.railway.app mypassword123
"""

import sys
import httpx
import asyncio
from datetime import datetime, timezone


class DeploymentTester:
    def __init__(self, base_url: str, app_password: str):
        self.base_url = base_url.rstrip('/')
        self.app_password = app_password
        self.results = []

    def log_result(self, test_name: str, passed: bool, details: str = ""):
        status = "✅ PASS" if passed else "❌ FAIL"
        self.results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
        print(f"{status} - {test_name}")
        if details:
            print(f"   {details}")

    async def test_health_endpoint(self):
        """Test that the health endpoint is accessible."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/health", timeout=10.0)

                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "healthy":
                        self.log_result(
                            "Health Endpoint",
                            True,
                            f"Version: {data.get('version')}"
                        )
                        return True
                    else:
                        self.log_result(
                            "Health Endpoint",
                            False,
                            f"Invalid response: {data}"
                        )
                        return False
                else:
                    self.log_result(
                        "Health Endpoint",
                        False,
                        f"Status code: {response.status_code}"
                    )
                    return False
        except Exception as e:
            self.log_result("Health Endpoint", False, f"Error: {str(e)}")
            return False

    async def test_cors_headers(self):
        """Test that CORS headers are set correctly."""
        try:
            async with httpx.AsyncClient() as client:
                # Test preflight request
                response = await client.options(
                    f"{self.base_url}/health",
                    headers={
                        "Origin": "https://example.com",
                        "Access-Control-Request-Method": "GET"
                    },
                    timeout=10.0
                )

                cors_header = response.headers.get("access-control-allow-origin")
                if cors_header:
                    self.log_result(
                        "CORS Headers",
                        True,
                        f"Allowed origins: {cors_header}"
                    )
                    return True
                else:
                    self.log_result(
                        "CORS Headers",
                        False,
                        "No CORS headers found"
                    )
                    return False
        except Exception as e:
            self.log_result("CORS Headers", False, f"Error: {str(e)}")
            return False

    async def test_auth_middleware_reject(self):
        """Test that requests without auth are rejected."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/analyze",
                    json={
                        "description": "Test",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "customer_id": "usr_test"
                    },
                    timeout=10.0
                )

                if response.status_code == 401:
                    self.log_result(
                        "Auth Middleware (Reject)",
                        True,
                        "Correctly rejected unauthorized request"
                    )
                    return True
                else:
                    self.log_result(
                        "Auth Middleware (Reject)",
                        False,
                        f"Expected 401, got {response.status_code}"
                    )
                    return False
        except Exception as e:
            self.log_result("Auth Middleware (Reject)", False, f"Error: {str(e)}")
            return False

    async def test_auth_middleware_accept(self):
        """Test that requests with valid auth are accepted."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/analyze",
                    json={
                        "description": "Test deployment",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "customer_id": "usr_test123"
                    },
                    headers={"X-Auth-Token": self.app_password},
                    timeout=30.0  # Longer timeout for actual analysis
                )

                # We expect either 200 (success) or an error related to Sentry/OpenAI
                # (not 401 which would indicate auth failure)
                if response.status_code in [200, 500]:
                    # Check if it's not an auth error
                    if response.status_code == 200:
                        self.log_result(
                            "Auth Middleware (Accept)",
                            True,
                            "Successfully authenticated and processed request"
                        )
                        return True
                    else:
                        # 500 error - check if it's due to missing Sentry events or API issues
                        data = response.json()
                        if "authentication" not in data.get("error", "").lower():
                            self.log_result(
                                "Auth Middleware (Accept)",
                                True,
                                "Auth passed, failed on API call (expected for test data)"
                            )
                            return True
                        else:
                            self.log_result(
                                "Auth Middleware (Accept)",
                                False,
                                "Auth failed"
                            )
                            return False
                elif response.status_code == 401:
                    self.log_result(
                        "Auth Middleware (Accept)",
                        False,
                        "Valid auth token was rejected"
                    )
                    return False
                else:
                    self.log_result(
                        "Auth Middleware (Accept)",
                        False,
                        f"Unexpected status code: {response.status_code}"
                    )
                    return False
        except Exception as e:
            self.log_result("Auth Middleware (Accept)", False, f"Error: {str(e)}")
            return False

    async def test_ssl_enabled(self):
        """Test that SSL/HTTPS is enabled."""
        if not self.base_url.startswith("https://"):
            self.log_result(
                "SSL Enabled",
                False,
                "URL does not use HTTPS"
            )
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/health", timeout=10.0)
                self.log_result(
                    "SSL Enabled",
                    True,
                    "HTTPS connection successful"
                )
                return True
        except Exception as e:
            self.log_result("SSL Enabled", False, f"Error: {str(e)}")
            return False

    async def run_all_tests(self):
        """Run all deployment tests."""
        print(f"\n{'='*60}")
        print(f"LogLens Deployment Verification")
        print(f"Testing: {self.base_url}")
        print(f"{'='*60}\n")

        tests = [
            self.test_ssl_enabled(),
            self.test_health_endpoint(),
            self.test_cors_headers(),
            self.test_auth_middleware_reject(),
            self.test_auth_middleware_accept(),
        ]

        await asyncio.gather(*tests)

        # Print summary
        print(f"\n{'='*60}")
        print("Test Summary")
        print(f"{'='*60}")

        passed = sum(1 for r in self.results if r["passed"])
        total = len(self.results)

        print(f"\nPassed: {passed}/{total}")

        if passed == total:
            print("\n🎉 All tests passed! Deployment is working correctly.")
            return 0
        else:
            print(f"\n⚠️  {total - passed} test(s) failed. Please review the issues above.")
            return 1


async def main():
    if len(sys.argv) != 3:
        print("Usage: python test_deployment.py <DEPLOYMENT_URL> <APP_PASSWORD>")
        print("\nExample:")
        print("  python test_deployment.py https://your-app.railway.app mypassword123")
        sys.exit(1)

    deployment_url = sys.argv[1]
    app_password = sys.argv[2]

    tester = DeploymentTester(deployment_url, app_password)
    exit_code = await tester.run_all_tests()
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())
