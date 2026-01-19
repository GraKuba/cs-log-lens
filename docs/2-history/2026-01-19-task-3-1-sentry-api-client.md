# Task 3.1: Implement Sentry API Client

**Date/Time:** 2026-01-19
**Tool:** Claude Code
**Task ID:** 3.1
**Status:** ✅ Completed

## Summary

Implemented a complete Sentry API client with event fetching, error handling, retry logic, and caching functionality. Created a comprehensive test suite with 21 tests covering all functionality.

## Key Changes

### Files Created
- `backend/test_sentry_client.py` - Comprehensive test suite (21 tests, all passing)

### Files Modified
- `backend/sentry_client.py` - Replaced stub implementation with full Sentry API client
- `backend/requirements.txt` - Added tenacity==8.2.3 and pytest-asyncio==1.3.0
- `docs/tasks.md` - Updated Task 3.1 status to completed

## Implementation Details

### Core Functionality
1. **Event Fetching** (`fetch_sentry_events`)
   - Accepts customer_id, timestamp, and optional time_window_minutes
   - Builds Sentry API URL from config (org/project)
   - Calculates time range (±5 minutes by default)
   - Constructs query with `user.id:{customer_id}`
   - Returns list of Sentry event dictionaries

2. **Timestamp Parsing**
   - `_parse_iso_timestamp()` - Handles ISO 8601 timestamps with 'Z' or timezone offset
   - `_format_datetime_for_sentry()` - Formats datetime for Sentry API

3. **HTTP Request Handling** (`_make_sentry_request`)
   - Uses httpx for async HTTP requests
   - Retry logic with tenacity (3 attempts, exponential backoff)
   - Comprehensive error handling for different HTTP status codes:
     - 401: SentryAuthError (invalid/expired token)
     - 404: SentryAPIError (project not found)
     - 429: SentryRateLimitError (rate limit exceeded)
     - 500+: SentryAPIError (server errors)

4. **Caching** (`_cached_fetch_events`)
   - In-memory cache using SHA-256 hash keys
   - Cache key includes: url, customer_id, timestamp, time_window_minutes
   - Maximum 100 entries (FIFO eviction)
   - `clear_sentry_cache()` function for testing

5. **Custom Exceptions**
   - `SentryClientError` - Base exception
   - `SentryAuthError` - Authentication failures
   - `SentryRateLimitError` - Rate limiting
   - `SentryAPIError` - General API errors

### Test Coverage
Created `test_sentry_client.py` with 21 tests organized into 4 test classes:

1. **TestTimestampParsing** (5 tests)
   - ISO timestamp with 'Z' suffix
   - ISO timestamp with timezone offset
   - Invalid timestamp formats
   - Empty timestamps
   - Datetime formatting for Sentry

2. **TestMakeSentryRequest** (5 tests)
   - Successful API requests
   - Rate limit handling (429)
   - Authentication errors (401)
   - Not found errors (404)
   - Server errors (500)

3. **TestFetchSentryEvents** (8 tests)
   - Successful event fetching
   - No events found
   - Invalid timestamp handling
   - Empty customer ID
   - Custom time windows
   - Error propagation (auth, rate limit)
   - Caching behavior

4. **TestIntegration** (3 tests)
   - URL construction
   - Query parameter construction
   - Authorization header

All 21 tests passing.

### Dependencies Added
- `tenacity==8.2.3` - Retry logic with exponential backoff
- `pytest-asyncio==1.3.0` - Async test support (upgraded from pytest 7.4.3 to 9.0.2)

## Tasks Completed from Acceptance Criteria
- ✅ `sentry_client.py` implements event fetching
- ✅ Fetches events from Sentry API
- ✅ Filters by customer ID
- ✅ Filters by time range (±5 minutes)
- ✅ Handles Sentry API errors gracefully
- ✅ Returns structured event data
- ✅ All required tests implemented and passing

## Technical Decisions

1. **Caching Implementation**: Used custom in-memory cache instead of `functools.lru_cache` because LRU cache doesn't work with async functions (cannot reuse already awaited coroutine).

2. **Retry Logic**: Used tenacity library for robust retry with exponential backoff, retrying only on transient errors (RequestError, TimeoutException).

3. **Error Granularity**: Created specific exception types for different Sentry errors to allow callers to handle different scenarios appropriately.

4. **Cache Key**: Used SHA-256 hash of JSON-serialized parameters to create stable, consistent cache keys.

## Next Steps
- Task 3.2: Format Sentry Events for LLM
- Task 3.3: Wire Sentry Client to Analyze Endpoint

## Notes
- All tests passing (21/21)
- Comprehensive error handling for production use
- Ready for integration with analyze endpoint
- Cache helps avoid Sentry API rate limits
