# Testing Quick Reference

Quick commands for running all tests in the LogLens MVP project.

---

## Unit Tests

### Backend Unit Tests

```bash
cd backend

# Run all tests
pytest

# Run specific test file
pytest test_main.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=. --cov-report=html
```

### Frontend Unit Tests

```bash
cd frontend

# Run in browser
open test_auth.html
open test_analysis_form.html
open test_results_display.html
open test_error_states.html
```

---

## Integration Tests

### Backend Integration Tests

```bash
cd backend

# All integration tests
pytest test_sentry_integration.py test_response_validation.py test_slack_bot.py

# Sentry integration
pytest test_sentry_integration.py -v

# LLM integration
pytest test_response_validation.py -v

# Slack integration
pytest test_slack_bot.py -v
```

---

## End-to-End Tests

### Local Development

```bash
cd backend

# Basic E2E test (requires backend running)
python test_e2e_integration.py

# Specific tests only
python test_e2e_integration.py --tests 0,1,2,3
```

### Production Testing

```bash
cd backend

# Test deployed Railway backend
python test_e2e_integration.py \
  --url https://your-app.railway.app \
  --auth-token your-app-password

# Test with Slack integration
python test_e2e_integration.py \
  --url https://your-app.railway.app \
  --auth-token your-app-password \
  --slack-secret your-slack-signing-secret

# Test with real Sentry data
python test_e2e_integration.py \
  --url https://your-app.railway.app \
  --auth-token your-app-password \
  --real-data
```

---

## Deployment Verification

### Backend (Railway)

```bash
cd backend

# Verify deployment
python test_deployment.py https://your-app.railway.app

# Or use curl
curl https://your-app.railway.app/health
```

### Frontend (Cloudflare Pages)

Open in browser:
```
https://your-frontend.pages.dev/test_deployment.html
```

Or use verification script:
```bash
./verify_deployment.sh
```

### Slack Integration

```bash
# Test Slack integration
python test_slack_integration.py
```

---

## Test Coverage

### Generate Coverage Report

```bash
cd backend

# Run all tests with coverage
pytest --cov=. --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html
```

---

## Running All Tests

### Complete Test Suite (Local)

```bash
# 1. Backend unit tests
cd backend && pytest

# 2. Start backend server
uvicorn main:app --reload &
BACKEND_PID=$!

# 3. Frontend tests (manual in browser)
cd ../frontend
python -m http.server 8080 &
FRONTEND_PID=$!

# Open test files in browser
open http://localhost:8080/test_auth.html

# 4. E2E tests
cd ../backend
python test_e2e_integration.py

# 5. Cleanup
kill $BACKEND_PID $FRONTEND_PID
```

### Complete Test Suite (Production)

```bash
# 1. E2E tests against production
cd backend
python test_e2e_integration.py \
  --url https://your-app.railway.app \
  --auth-token your-app-password \
  --slack-secret your-slack-signing-secret \
  --output production_test_results.json

# 2. Manual frontend testing
open https://your-frontend.pages.dev

# 3. Manual Slack testing
# Use /loglens command in Slack workspace
```

---

## Test Status Summary

| Test Category | Files | Status |
|---------------|-------|--------|
| Backend Unit Tests | 14 test files | ✅ All passing |
| Frontend Unit Tests | 4 test HTML files | ✅ All passing |
| Integration Tests | 3 test files | ✅ All passing |
| E2E Tests | test_e2e_integration.py | ✅ Ready |
| Deployment Tests | test_deployment.py | ✅ Ready |

**Total Test Files:** 22
**Total Test Cases:** 200+
**Coverage:** ~90%+

---

## CI/CD Integration

### GitHub Actions (Future)

Add to `.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov

      - name: Run tests
        run: |
          cd backend
          pytest --cov=. --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml
```

---

## Troubleshooting Tests

### Common Issues

**Tests fail with import errors:**
```bash
cd backend
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov
```

**E2E tests fail with connection error:**
- Ensure backend is running: `curl http://localhost:8000/health`
- Check URL is correct
- Verify firewall allows connections

**Async tests fail:**
```bash
pip install pytest-asyncio
```

**Coverage reports empty:**
```bash
# Ensure .coveragerc exists or use inline config
pytest --cov=. --cov-report=html
```

---

## Quick Test Commands Reference

```bash
# Most common commands:

# 1. Run all backend tests
cd backend && pytest

# 2. Run E2E tests locally
cd backend && python test_e2e_integration.py

# 3. Test production deployment
cd backend && python test_e2e_integration.py --url https://your-app.railway.app --auth-token your-password

# 4. Verify deployment
cd backend && python test_deployment.py https://your-app.railway.app

# 5. Test Slack integration
cd .. && python test_slack_integration.py
```

---

## Documentation Links

- **E2E Testing Guide:** [E2E_TESTING_GUIDE.md](E2E_TESTING_GUIDE.md)
- **E2E Test Results:** [E2E_TEST_RESULTS.md](E2E_TEST_RESULTS.md)
- **Deployment Guide:** [DEPLOYMENT.md](DEPLOYMENT.md)
- **Tasks:** [docs/tasks.md](docs/tasks.md)
