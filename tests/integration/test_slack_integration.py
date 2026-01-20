#!/usr/bin/env python3
"""
Test script to verify Slack integration is working correctly.
This script simulates Slack webhook requests to test the /slack/commands endpoint.

Usage:
    python test_slack_integration.py <RAILWAY_URL> <SLACK_SIGNING_SECRET>

Example:
    python test_slack_integration.py https://your-app.railway.app abc123secretxyz
"""

import sys
import hmac
import hashlib
import time
import json
import requests
from urllib.parse import urlencode

def generate_slack_signature(signing_secret: str, timestamp: str, body: str) -> str:
    """Generate Slack request signature for verification."""
    sig_basestring = f"v0:{timestamp}:{body}"
    signature = 'v0=' + hmac.new(
        signing_secret.encode(),
        sig_basestring.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature

def test_slack_command(base_url: str, signing_secret: str, command_text: str, test_name: str):
    """Test a Slack command by simulating a Slack webhook request."""
    print(f"\n{'='*60}")
    print(f"Test: {test_name}")
    print(f"{'='*60}")

    # Prepare request body (Slack sends form data)
    timestamp = str(int(time.time()))
    body_dict = {
        'token': 'test_token',
        'team_id': 'T12345',
        'team_domain': 'testteam',
        'channel_id': 'C12345',
        'channel_name': 'general',
        'user_id': 'U12345',
        'user_name': 'testuser',
        'command': '/loglens',
        'text': command_text,
        'response_url': 'https://hooks.slack.com/commands/test',
        'trigger_id': 'test_trigger'
    }
    body = urlencode(body_dict)

    # Generate signature
    signature = generate_slack_signature(signing_secret, timestamp, body)

    # Prepare headers
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Slack-Request-Timestamp': timestamp,
        'X-Slack-Signature': signature
    }

    # Make request
    url = f"{base_url}/slack/commands"
    print(f"URL: {url}")
    print(f"Command: /loglens {command_text}")

    try:
        response = requests.post(url, data=body, headers=headers, timeout=30)

        print(f"\nStatus Code: {response.status_code}")

        if response.status_code == 200:
            print("✅ SUCCESS")
            try:
                result = response.json()
                print(f"\nResponse Type: {result.get('response_type', 'N/A')}")

                # Pretty print the response
                if 'blocks' in result:
                    print("\nFormatted Response:")
                    print("-" * 60)
                    for block in result['blocks']:
                        if block['type'] == 'section' and 'text' in block:
                            text = block['text'].get('text', '')
                            print(text)
                    print("-" * 60)
                else:
                    print(f"\nResponse: {json.dumps(result, indent=2)}")

            except json.JSONDecodeError:
                print(f"\nRaw Response: {response.text}")
        else:
            print("❌ FAILED")
            print(f"Response: {response.text}")

    except requests.exceptions.Timeout:
        print("❌ TIMEOUT - Request took longer than 30 seconds")
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR - Could not connect to backend")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

def test_invalid_signature(base_url: str):
    """Test that invalid signatures are rejected."""
    print(f"\n{'='*60}")
    print("Test: Invalid Signature (Should Reject)")
    print(f"{'='*60}")

    timestamp = str(int(time.time()))
    body_dict = {
        'command': '/loglens',
        'text': 'test | 2025-01-19T14:30:00Z | usr_test',
    }
    body = urlencode(body_dict)

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Slack-Request-Timestamp': timestamp,
        'X-Slack-Signature': 'v0=invalid_signature_here'
    }

    url = f"{base_url}/slack/commands"
    print(f"URL: {url}")

    try:
        response = requests.post(url, data=body, headers=headers, timeout=10)

        if response.status_code == 401:
            print("✅ SUCCESS - Invalid signature rejected (401)")
        else:
            print(f"❌ FAILED - Expected 401, got {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

def test_old_timestamp(base_url: str, signing_secret: str):
    """Test that old timestamps are rejected (replay attack prevention)."""
    print(f"\n{'='*60}")
    print("Test: Old Timestamp (Should Reject)")
    print(f"{'='*60}")

    # Use timestamp from 10 minutes ago (should be rejected)
    timestamp = str(int(time.time()) - 600)
    body_dict = {
        'command': '/loglens',
        'text': 'test | 2025-01-19T14:30:00Z | usr_test',
    }
    body = urlencode(body_dict)

    signature = generate_slack_signature(signing_secret, timestamp, body)

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Slack-Request-Timestamp': timestamp,
        'X-Slack-Signature': signature
    }

    url = f"{base_url}/slack/commands"
    print(f"URL: {url}")
    print(f"Timestamp: {timestamp} (10 minutes old)")

    try:
        response = requests.post(url, data=body, headers=headers, timeout=10)

        if response.status_code == 401:
            print("✅ SUCCESS - Old timestamp rejected (401)")
        else:
            print(f"❌ FAILED - Expected 401, got {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

def main():
    if len(sys.argv) != 3:
        print("Usage: python test_slack_integration.py <RAILWAY_URL> <SLACK_SIGNING_SECRET>")
        print("\nExample:")
        print("  python test_slack_integration.py https://your-app.railway.app abc123secretxyz")
        sys.exit(1)

    base_url = sys.argv[1].rstrip('/')
    signing_secret = sys.argv[2]

    print("="*60)
    print("LogLens Slack Integration Test")
    print("="*60)
    print(f"Backend URL: {base_url}")
    print(f"Signing Secret: {signing_secret[:8]}..." + "*" * (len(signing_secret) - 8))

    # Test 1: Valid command with proper format
    test_slack_command(
        base_url,
        signing_secret,
        "User can't checkout | 2025-01-19T14:30:00Z | usr_test123",
        "Valid Command Format"
    )

    # Test 2: Invalid format - missing parts
    test_slack_command(
        base_url,
        signing_secret,
        "User can't checkout | 2025-01-19T14:30:00Z",
        "Invalid Format - Missing Customer ID"
    )

    # Test 3: Invalid timestamp format
    test_slack_command(
        base_url,
        signing_secret,
        "Test error | not-a-timestamp | usr_test",
        "Invalid Timestamp Format"
    )

    # Test 4: Empty command
    test_slack_command(
        base_url,
        signing_secret,
        "",
        "Empty Command"
    )

    # Test 5: Invalid signature (security test)
    test_invalid_signature(base_url)

    # Test 6: Old timestamp (replay attack prevention)
    test_old_timestamp(base_url, signing_secret)

    print(f"\n{'='*60}")
    print("Test Suite Complete")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
