# Task 3.2: Format Sentry Events for LLM

**Date/Time:** 2026-01-19, ~16:00
**Tool:** Claude Code
**Task ID:** Task 3.2 from tasks.md

## Summary

Implemented Task 3.2: Format Sentry Events for LLM. Created a comprehensive event formatting system that extracts error messages, stack traces, breadcrumbs, and other relevant information from Sentry events and formats them in a readable way for LLM analysis.

## Key Changes

### Files Created
- `backend/test_event_formatting.py` - Comprehensive test suite with 19 tests covering all formatting scenarios

### Files Modified
- `backend/sentry_client.py` - Implemented event formatting functions:
  - `format_events_for_llm()` - Main formatting function
  - `generate_sentry_link()` - Creates direct links to Sentry UI
  - `_extract_stack_trace()` - Helper to extract and format stack traces
  - `_extract_breadcrumbs()` - Helper to extract and format breadcrumbs
- `docs/tasks.md` - Updated Task 3.2 status to completed and updated progress counters

## Tasks Completed

1. ✅ Task 3.2: Format Sentry Events for LLM
   - All acceptance criteria met
   - 19 tests written and passing
   - Documentation updated

## Implementation Details

### format_events_for_llm()
Main function that formats a list of Sentry events into readable text for LLM analysis. Features:
- Extracts error type and message from multiple possible fields (title, message, metadata)
- Formats stack traces with code context (limited to 5 frames for brevity)
- Shows last 5 breadcrumbs (user actions leading to error)
- Includes relevant context tags (environment, release, browser, os)
- Generates direct links to Sentry UI for each event
- Handles missing fields gracefully

### generate_sentry_link()
Generates direct URLs to Sentry events in the UI. Uses config values by default but allows custom org/project overrides.

### _extract_stack_trace()
Helper function that:
- Navigates Sentry's nested event structure (entries -> exception -> values -> stacktrace -> frames)
- Extracts filename, function name, line number, and code context
- Formats as readable strings: `filename:lineno in function() -> code_line`
- Returns empty list if no stack trace available

### _extract_breadcrumbs()
Helper function that:
- Extracts breadcrumbs from Sentry event structure
- Formats as `[level] category: message` or `[level] category: key=value` for data-only breadcrumbs
- Limits data fields to 3 for brevity
- Returns empty list if no breadcrumbs available

## Test Coverage

Created comprehensive test suite in `test_event_formatting.py` with 19 tests:

1. **Link Generation Tests** (2 tests)
   - Test with default config values
   - Test with custom org/project

2. **Main Formatting Tests** (6 tests)
   - Empty event list
   - Minimal event (only required fields)
   - Complete event (all fields populated)
   - Event without stack trace
   - Multiple events
   - Missing fields handling

3. **Stack Trace Extraction Tests** (4 tests)
   - Complete event with stack trace
   - Event without stack trace
   - Missing entries field
   - Stack trace without code context

4. **Breadcrumb Extraction Tests** (5 tests)
   - Complete event with breadcrumbs
   - Event without breadcrumbs
   - Missing entries field
   - Breadcrumb with data only (no message)
   - Data field limiting (max 3 fields)

5. **Truncation Tests** (2 tests)
   - Long stack traces (shows first 5 frames + count)
   - Many breadcrumbs (shows last 5)

All tests passing ✅

## Output Format Example

```
Event 1:
- Time: 2025-01-19T14:30:15Z
- Error: PaymentTokenExpiredError
- Message: "Token expired after 10 minutes of inactivity"
- Stack Trace:
  payment_service.py:42 in process_payment() -> raise PaymentTokenExpiredError('Token expired')
  checkout_handler.py:128 in handle_checkout() -> payment.process_payment(user_token)
- Breadcrumbs (user actions leading to error):
  [info] navigation: User navigated to /checkout
  [info] ui.click: Clicked 'Complete Purchase' button
  [info] http: url=/api/payment, method=POST, status_code=400
- Context: environment=production, release=v1.2.3, browser=Chrome 120, os=Windows 10
- Link: https://sentry.io/organizations/test-org/issues/?project=test-project&query=event-complete-456

Event 2:
...
```

## Progress Update

- Overall progress: 10/28 → 11/28 tasks completed
- Phase 3 (Sentry Integration): 1/3 → 2/3 tasks completed
- Next task: Task 3.3 - Wire Sentry Client to Analyze Endpoint

## Notes

- Format is concise but informative, optimized for LLM consumption
- Handles Sentry's nested and variable event structure gracefully
- Limits output length (5 stack frames, 5 breadcrumbs) to avoid overwhelming the LLM
- All code follows existing patterns in the codebase
- Tests use mock config to avoid dependency on actual environment variables
