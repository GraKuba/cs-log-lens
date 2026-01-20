#!/usr/bin/env python3
"""Quick test script to debug the analyze endpoint"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add backend to path (works from any location)
backend_dir = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

async def test_sentry():
    """Test Sentry API connection"""
    from sentry_client import fetch_sentry_events

    try:
        print("Testing Sentry API connection...")
        events = await fetch_sentry_events(
            customer_id="test_customer",
            timestamp="2026-01-16T19:22:11.883Z",
            time_window_minutes=5,
        )
        print(f"✓ Sentry API working - found {len(events)} events")
        return True
    except Exception as e:
        print(f"✗ Sentry API failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_analyzer():
    """Test LLM analyzer"""
    from analyzer import analyze_logs

    try:
        print("\nTesting LLM analyzer...")
        result = await analyze_logs(
            description="Test issue",
            timestamp="2026-01-16T19:22:11.883Z",
            customer_id="test_customer",
            formatted_events="No events found",
            workflow_docs="Test workflow",
            known_errors="Test errors"
        )
        print(f"✓ LLM analyzer working")
        return True
    except Exception as e:
        print(f"✗ LLM analyzer failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("=" * 60)
    print("CS Log Lens - Quick Diagnostic Test")
    print("=" * 60)

    sentry_ok = await test_sentry()
    analyzer_ok = await test_analyzer()

    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  Sentry API: {'✓ OK' if sentry_ok else '✗ FAILED'}")
    print(f"  LLM Analyzer: {'✓ OK' if analyzer_ok else '✗ FAILED'}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
