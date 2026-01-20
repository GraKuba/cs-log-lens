#!/usr/bin/env python3
"""Test Sentry authentication and permissions"""

import os
import httpx
from dotenv import load_dotenv
from pathlib import Path

# Load .env
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

SENTRY_BASE_URL = os.getenv("SENTRY_BASE_URL", "https://sentry.io")
SENTRY_AUTH_TOKEN = os.getenv("SENTRY_AUTH_TOKEN")
SENTRY_ORG = os.getenv("SENTRY_ORG")
SENTRY_PROJECT = os.getenv("SENTRY_PROJECT")

headers = {
    "Authorization": f"Bearer {SENTRY_AUTH_TOKEN}",
}

print("Testing Sentry API Access")
print("=" * 60)
print(f"Base URL: {SENTRY_BASE_URL}")
print(f"Org: {SENTRY_ORG}")
print(f"Project: {SENTRY_PROJECT}")
print(f"Token (first 20 chars): {SENTRY_AUTH_TOKEN[:20]}...")
print("=" * 60)

async def test_endpoints():
    async with httpx.AsyncClient() as client:
        # Test 1: List organizations
        print("\n1. Testing: GET /api/0/organizations/")
        try:
            response = await client.get(
                f"{SENTRY_BASE_URL}/api/0/organizations/",
                headers=headers,
                timeout=10.0
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                orgs = response.json()
                print(f"   Organizations: {[org['slug'] for org in orgs]}")
            else:
                print(f"   Error: {response.text[:200]}")
        except Exception as e:
            print(f"   Exception: {e}")

        # Test 2: Get specific organization
        print(f"\n2. Testing: GET /api/0/organizations/{SENTRY_ORG}/")
        try:
            response = await client.get(
                f"{SENTRY_BASE_URL}/api/0/organizations/{SENTRY_ORG}/",
                headers=headers,
                timeout=10.0
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   Organization exists: ✓")
            else:
                print(f"   Error: {response.text[:200]}")
        except Exception as e:
            print(f"   Exception: {e}")

        # Test 3: List projects in organization
        print(f"\n3. Testing: GET /api/0/organizations/{SENTRY_ORG}/projects/")
        try:
            response = await client.get(
                f"{SENTRY_BASE_URL}/api/0/organizations/{SENTRY_ORG}/projects/",
                headers=headers,
                timeout=10.0
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                projects = response.json()
                print(f"   Projects: {[p['slug'] for p in projects]}")
            else:
                print(f"   Error: {response.text[:200]}")
        except Exception as e:
            print(f"   Exception: {e}")

        # Test 4: Get specific project
        print(f"\n4. Testing: GET /api/0/projects/{SENTRY_ORG}/{SENTRY_PROJECT}/")
        try:
            response = await client.get(
                f"{SENTRY_BASE_URL}/api/0/projects/{SENTRY_ORG}/{SENTRY_PROJECT}/",
                headers=headers,
                timeout=10.0
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   Project exists: ✓")
            else:
                print(f"   Error: {response.text[:200]}")
        except Exception as e:
            print(f"   Exception: {e}")

        # Test 5: List events (the failing endpoint)
        print(f"\n5. Testing: GET /api/0/projects/{SENTRY_ORG}/{SENTRY_PROJECT}/events/")
        try:
            response = await client.get(
                f"{SENTRY_BASE_URL}/api/0/projects/{SENTRY_ORG}/{SENTRY_PROJECT}/events/",
                headers=headers,
                params={"full": "true"},
                timeout=10.0
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                events = response.json()
                print(f"   Events endpoint accessible: ✓")
                print(f"   Found {len(events)} events")
            else:
                print(f"   Error: {response.text[:200]}")
        except Exception as e:
            print(f"   Exception: {e}")

print("\n")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_endpoints())
