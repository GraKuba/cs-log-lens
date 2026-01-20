# Tests Directory

This directory contains all test files for the CS Log Lens project.

## Structure

```
tests/
├── backend/          # Backend Python unit and integration tests
├── frontend/         # Frontend HTML test files
└── integration/      # Cross-component integration tests
```

## Running Tests

### Backend Tests
```bash
cd backend
source .venv/bin/activate
pytest ../tests/backend/
```

### Quick Tests
```bash
cd backend
source .venv/bin/activate
pytest ../tests/backend/test_quick.py
```

### E2E Integration Tests
```bash
cd backend
source .venv/bin/activate
pytest ../tests/backend/test_e2e_integration.py
```

### Frontend Tests
Open the HTML files in `tests/frontend/` in a browser to run frontend tests.

## Test Organization

- **Unit tests**: Test individual functions and classes
- **Integration tests**: Test interactions between components
- **E2E tests**: Test complete user workflows
- **Performance tests**: Test system performance and load handling
