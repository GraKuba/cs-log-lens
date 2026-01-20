# End-to-End Integration Testing Guide

**Last Updated:** 2026-01-20
**Status:** Complete
**Purpose:** Comprehensive guide for testing the entire LogLens MVP system

---

## Overview

This guide covers end-to-end (E2E) integration testing for LogLens MVP, verifying the complete flow from frontend/Slack through backend to Sentry and LLM services.

### Test Coverage

| Test ID | Test Case | Status |
|---------|-----------|--------|
| 0 | Health endpoint accessibility | ✅ Automated |
| 1 | Valid analysis request → Returns causes + response | ✅ Automated |
| 2 | Invalid customer ID → Returns "no events found" | ✅ Automated |
| 3 | Wrong password → Returns 401 | ✅ Automated |
| 4 | Slack command with valid inputs → Posts formatted response | ✅ Automated |
| 5 | Slack command with missing params → Posts usage instructions | ✅ Automated |
| 6 | Concurrent requests handling | ✅ Automated |
| 7 | Response time < 5 seconds | ✅ Automated |

---

## Automated Testing

### Prerequisites

1. **Python environment** with required packages:
   ```bash
   cd backend
   uv pip install httpx
   ```

2. **Environment variables** (for real data testing):
   ```bash
   export E2E_BACKEND_URL="https://your-app.railway.app"
   export E2E_AUTH_TOKEN="your-app-password"
   export E2E_SLACK_SECRET="your-slack-signing-secret"
   ```

### Running Tests

#### Test Local Development Server

```bash
cd backend
python test_e2e_integration.py
```

#### Test Deployed Railway Backend

```bash
cd backend
python test_e2e_integration.py \
  --url https://your-app.railway.app \
  --auth-token your-app-password
```

#### Test with Real Sentry Data

```bash
cd backend
python test_e2e_integration.py \
  --url https://your-app.railway.app \
  --auth-token your-app-password \
  --real-data
```

#### Run Specific Tests Only

```bash
cd backend
# Run only tests 1, 2, and 3
python test_e2e_integration.py --tests 1,2,3
```

#### Test Slack Integration

```bash
cd backend
python test_e2e_integration.py \
  --url https://your-app.railway.app \
  --auth-token your-app-password \
  --slack-secret your-slack-signing-secret \
  --tests 4,5
```

### Test Output

The test script will:
1. Print progress for each test as it runs
2. Show pass/fail status with timing
3. Print a summary at the end
4. Save results to `e2e_test_results.json`

Example output:
```
============================================================
Running 8 E2E Integration Tests
Backend URL: http://localhost:8000
============================================================

Running Test 0... ✅ PASS (0.15s)
  Health check passed. Version: 0.1.0

Running Test 1... ✅ PASS (4.23s)
  Analysis completed. Found 3 causes. Events: 2

Running Test 2... ✅ PASS (3.87s)
  Correctly handled invalid customer ID (no events found)

...

============================================================
Test Summary
============================================================
Total Tests:  8
Passed:       8 ✅
Failed:       0 ❌
Pass Rate:    100.0%
============================================================
```

---

## Manual Testing

### Web Form Testing

#### Test 1: Valid Analysis Request

1. Open frontend in browser: `https://your-frontend.pages.dev`
2. Enter password when prompted
3. Fill in form:
   - **Description:** "User says checkout button does nothing when clicked"
   - **Timestamp:** Current time minus 5 minutes
   - **Customer ID:** Use a valid customer ID from your Sentry project
4. Click "Analyze Logs"
5. **Expected:** Results display with:
   - 3 probable causes with confidence levels
   - Suggested customer response
   - Sentry links
   - Logs summary

#### Test 2: Invalid Customer ID

1. Fill in form with non-existent customer ID: `usr_nonexistent_12345`
2. Click "Analyze Logs"
3. **Expected:** Message indicating no events found

#### Test 3: Wrong Password

1. Clear localStorage: `localStorage.clear()`
2. Refresh page
3. Enter wrong password
4. Try to analyze logs
5. **Expected:** 401 error, prompted to re-enter password

#### Test 4: Mobile Responsiveness

1. Open frontend on mobile device or use browser dev tools mobile emulation
2. Verify:
   - Form is readable and usable
   - Results are properly formatted
   - Buttons are easily tappable
   - No horizontal scrolling

### Slack Bot Testing

#### Test 5: Valid Slack Command

1. In Slack workspace, type:
   ```
   /loglens User can't checkout | 2025-01-19T14:30:00Z | usr_test123
   ```
2. **Expected:** Formatted response with:
   - 🔍 header
   - Numbered causes (1️⃣ 2️⃣ 3️⃣)
   - Confidence levels
   - Suggested response
   - Sentry links

#### Test 6: Invalid Slack Command

1. In Slack workspace, type:
   ```
   /loglens incomplete command
   ```
2. **Expected:** Usage instructions explaining correct format

---

## Edge Cases and Error Scenarios

### Test Cases

| Scenario | Input | Expected Result |
|----------|-------|-----------------|
| Empty description | `""` | Validation error |
| Invalid timestamp | `"not-a-date"` | Validation error |
| Future timestamp | `"2030-01-01T00:00:00Z"` | Works (may find no events) |
| Very old timestamp | `"2020-01-01T00:00:00Z"` | Works (may find no events) |
| Extremely long description | 10,000+ characters | Should handle gracefully |
| Special characters in customer ID | `usr_test@#$%` | Should work if valid in Sentry |
| Concurrent requests | Send 10 simultaneous requests | All should complete |
| Network timeout | Slow connection | Should timeout gracefully after 30s |
| Sentry API down | Disable Sentry | Should return error with suggestion |
| OpenAI API down | Invalid API key | Should return error message |
| Rate limiting | Many rapid requests | Should handle with retry logic |

### Testing These Scenarios

Use the automated test script with modifications:

```python
# Example: Test with empty description
request_data = {
    "description": "",
    "timestamp": "2025-01-19T14:30:00Z",
    "customer_id": "usr_test123"
}
```

Or test manually via frontend/Slack.

---

## Performance Testing

### Response Time Requirements

- **Target:** < 5 seconds for typical request
- **Maximum:** < 30 seconds (timeout)

### Load Testing

Test with multiple concurrent requests:

```bash
# Send 10 concurrent requests
for i in {1..10}; do
  curl -X POST https://your-app.railway.app/analyze \
    -H "Content-Type: application/json" \
    -H "X-Auth-Token: your-password" \
    -d '{"description":"Test","timestamp":"2025-01-19T14:30:00Z","customer_id":"usr_test123"}' &
done
wait
```

### Monitoring

During testing, monitor:
1. **Railway metrics:** CPU, memory, request count
2. **Response times:** Check logs for slow requests
3. **Error rates:** Any 500 errors or timeouts
4. **Sentry API usage:** Check for rate limiting

---

## Test Data

### Sample Valid Input

```json
{
  "description": "User says checkout button does nothing when clicked",
  "timestamp": "2025-01-19T14:30:00Z",
  "customer_id": "usr_test123"
}
```

### Sample Invalid Inputs

```json
// Missing required field
{
  "description": "Test",
  "timestamp": "2025-01-19T14:30:00Z"
}

// Invalid timestamp format
{
  "description": "Test",
  "timestamp": "not-a-date",
  "customer_id": "usr_test123"
}

// Empty customer ID
{
  "description": "Test",
  "timestamp": "2025-01-19T14:30:00Z",
  "customer_id": ""
}
```

---

## Troubleshooting

### Common Issues

#### Issue: Connection Refused

**Symptom:** `ConnectionError: Connection refused`
**Solution:**
- Verify backend is running: `curl http://localhost:8000/health`
- Check Railway deployment status
- Verify URL is correct

#### Issue: 401 Unauthorized

**Symptom:** All requests return 401
**Solution:**
- Check `APP_PASSWORD` matches between frontend and backend
- Verify `X-Auth-Token` header is being sent
- Check Railway environment variables

#### Issue: Timeout

**Symptom:** Requests timeout after 30 seconds
**Solution:**
- Check Sentry API is responding: `curl https://sentry.io/api/0/`
- Check OpenAI API key is valid
- Monitor Railway logs for errors
- Increase timeout: `--timeout 60`

#### Issue: No Events Found

**Symptom:** Always returns 0 events
**Solution:**
- Verify customer ID exists in Sentry
- Check timestamp is within range of actual events
- Verify `SENTRY_AUTH_TOKEN` has correct permissions
- Test Sentry API directly with curl

#### Issue: Slack Signature Verification Fails

**Symptom:** Slack commands return signature error
**Solution:**
- Verify `SLACK_SIGNING_SECRET` is correct
- Check timestamp is current (< 5 minutes old)
- Ensure body is properly formatted

---

## Continuous Integration

### GitHub Actions Integration

Add to `.github/workflows/e2e-tests.yml`:

```yaml
name: E2E Integration Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install httpx

      - name: Run E2E tests
        env:
          E2E_BACKEND_URL: ${{ secrets.RAILWAY_URL }}
          E2E_AUTH_TOKEN: ${{ secrets.APP_PASSWORD }}
        run: |
          cd backend
          python test_e2e_integration.py --url $E2E_BACKEND_URL --auth-token $E2E_AUTH_TOKEN

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: e2e-test-results
          path: backend/e2e_test_results.json
```

---

## Test Results Documentation

### Recording Results

After running tests, document results:

1. **Automated tests:** Results saved to `e2e_test_results.json`
2. **Manual tests:** Use the checklist below
3. **Issues found:** Create GitHub issues for bugs

### Manual Test Checklist

Copy this checklist for each test run:

```markdown
## E2E Test Run - [Date]

### Environment
- [ ] Backend URL: _______________
- [ ] Frontend URL: _______________
- [ ] Testing with real data: Yes / No

### Web Form Tests
- [ ] Test 1: Valid analysis request
- [ ] Test 2: Invalid customer ID
- [ ] Test 3: Wrong password
- [ ] Test 4: Mobile responsiveness

### Slack Bot Tests
- [ ] Test 5: Valid Slack command
- [ ] Test 6: Invalid Slack command

### Performance
- [ ] Response time < 5 seconds
- [ ] Concurrent requests handled

### Issues Found
1. _________________
2. _________________

### Notes
_________________
```

---

## Success Criteria

### All Tests Must Pass

✅ Health endpoint accessible
✅ Valid requests return structured analysis
✅ Invalid customer IDs handled gracefully
✅ Authentication enforced correctly
✅ Slack commands work as expected
✅ Concurrent requests handled
✅ Response time meets requirements

### Performance Targets

✅ Average response time < 5 seconds
✅ 95th percentile < 8 seconds
✅ 99th percentile < 10 seconds
✅ No timeouts under normal load

### Quality Targets

✅ Zero crashes or unhandled exceptions
✅ All errors have clear, actionable messages
✅ Mobile UI is fully functional
✅ No console errors in browser

---

## Next Steps

1. ✅ Create automated test script
2. ✅ Document manual testing procedures
3. ⏭️ Run tests against deployed environment
4. ⏭️ Document actual test results
5. ⏭️ Fix any issues found
6. ⏭️ Re-test until all pass
7. ⏭️ Sign off on integration testing

---

## References

- **PRD:** Lines 47-57 (Core User Flow)
- **Tech Spec:** Lines 514-534 (Testing)
- **Task:** Task 8.1 in docs/tasks.md
- **Test Script:** backend/test_e2e_integration.py
- **Deployment Guide:** DEPLOYMENT.md
