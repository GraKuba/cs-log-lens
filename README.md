# LogLens 🔍

> AI-powered log analysis tool for customer support teams

LogLens helps customer support teams quickly analyze error logs and diagnose customer issues using AI. It integrates with Sentry for log collection and uses GPT-4 to provide probable causes and suggested responses.

## Features

- 🤖 **AI-Powered Analysis**: Uses GPT-4 to analyze logs and provide probable causes
- 🔍 **Sentry Integration**: Automatically fetches relevant error events from Sentry
- 💬 **Slack Bot**: Analyze logs directly from Slack with `/loglens` command
- 🌐 **Web Interface**: Simple, password-protected web form for log analysis
- ⚡ **Fast Response**: Get analysis results in under 5 seconds
- 📊 **Ranked Causes**: See top 3 probable causes with confidence levels
- 💡 **Suggested Responses**: Get AI-generated customer responses

## Quick Start

### Prerequisites

- Python 3.11+
- Sentry account with API access
- OpenAI API key
- (Optional) Slack workspace for bot integration

### Local Development

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/cs-log-lens.git
   cd cs-log-lens
   ```

2. **Set up the backend:**
   ```bash
   cd backend
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and credentials
   ```

4. **Run the backend:**
   ```bash
   uvicorn main:app --reload
   ```

5. **Open the frontend:**
   ```bash
   cd ../frontend
   # Open index.html in your browser or use a local server:
   python -m http.server 8000
   ```

6. **Run tests:**
   ```bash
   cd ../backend
   pytest
   ```

## Deployment

### Deploy to Production

LogLens deploys in three parts:

1. **Backend (Railway)** - FastAPI application
2. **Frontend (Cloudflare Pages)** - Static web interface
3. **Slack App (Optional)** - Bot integration

**Deployment Documentation:**

| Guide | Purpose |
|-------|---------|
| [DEPLOYMENT.md](DEPLOYMENT.md) | Backend (Railway) deployment guide |
| [FRONTEND_DEPLOYMENT.md](FRONTEND_DEPLOYMENT.md) | Frontend (Cloudflare Pages) deployment guide |
| [SLACK_SETUP.md](SLACK_SETUP.md) | Slack app configuration guide |
| [DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md) | Quick reference for all deployments |
| [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) | Backend deployment checklist |
| [CLOUDFLARE_CHECKLIST.md](CLOUDFLARE_CHECKLIST.md) | Frontend deployment checklist |
| [SLACK_CHECKLIST.md](SLACK_CHECKLIST.md) | Slack setup checklist |

**Quick Deploy Steps:**

1. **Backend (Railway):**
   ```bash
   # See DEPLOYMENT.md for details
   - Connect GitHub repo to Railway
   - Set root directory to `/backend`
   - Configure environment variables (8 required)
   - Deploy automatically on push
   ```

2. **Frontend (Cloudflare Pages):**
   ```bash
   # See FRONTEND_DEPLOYMENT.md for details
   - Connect GitHub repo to Cloudflare Pages
   - Set root directory to `/frontend`
   - Set API_URL environment variable
   - Deploy automatically on push
   ```

3. **Slack App (Optional):**
   ```bash
   # See SLACK_SETUP.md for details
   - Create app at api.slack.com/apps
   - Add /loglens slash command
   - Configure bot scopes and install to workspace
   - Add credentials to Railway environment variables
   ```

### Verify Deployment

**Automated verification:**
```bash
# Test backend deployment
cd backend
python test_deployment.py https://your-app.railway.app your-password

# Test full deployment (backend + frontend)
./verify_deployment.sh https://your-app.railway.app https://loglens-frontend.pages.dev

# Test Slack integration
python test_slack_integration.py https://your-app.railway.app your-signing-secret
```

**Manual verification:**
```bash
# Test backend health
curl https://your-app.railway.app/health

# Test frontend loads
curl https://loglens-frontend.pages.dev

# Test frontend UI (in browser)
open https://loglens-frontend.pages.dev/test_deployment.html
```

## Usage

### Web Interface

1. Navigate to your deployed frontend URL
2. Enter the shared password
3. Fill in the analysis form:
   - **Problem Description**: What the customer reported
   - **Timestamp**: When the issue occurred
   - **Customer ID**: The customer's user ID
4. Click "Analyze Logs"
5. Review the results:
   - Top 3 probable causes with confidence levels
   - Suggested customer response
   - Links to Sentry events

### Slack Bot

Use the `/loglens` command in Slack:

```
/loglens User can't checkout | 2025-01-19T14:30:00Z | usr_abc123
```

Format: `[description] | [timestamp] | [customer_id]`

## Architecture

```
┌─────────────┐         ┌──────────────┐
│   CS Agent  │────────▶│   Frontend   │
│  (Web/Slack)│         │ (Cloudflare) │
└─────────────┘         └──────┬───────┘
                               │
                               ▼
                        ┌──────────────┐
                        │   Backend    │
                        │   (Railway)  │
                        └──────┬───────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
       ┌──────────┐     ┌──────────┐    ┌──────────┐
       │  Sentry  │     │  OpenAI  │    │   Slack  │
       │   API    │     │   GPT-4  │    │   API    │
       └──────────┘     └──────────┘    └──────────┘
```

### Tech Stack

- **Backend**: FastAPI, Python 3.11
- **Frontend**: Vanilla JavaScript, HTML, CSS
- **AI**: OpenAI GPT-4
- **Logs**: Sentry API
- **Hosting**: Railway (backend), Cloudflare Pages (frontend)
- **Chat**: Slack Bolt SDK

## Project Structure

```
cs-log-lens/
├── backend/
│   ├── main.py              # FastAPI app and endpoints
│   ├── config.py            # Environment configuration
│   ├── sentry_client.py     # Sentry API integration
│   ├── analyzer.py          # LLM analysis logic
│   ├── slack_bot.py         # Slack bot integration
│   ├── requirements.txt     # Python dependencies
│   ├── docs/
│   │   ├── workflow.md      # CS workflow documentation
│   │   └── known_errors.md  # Known error patterns
│   └── test_*.py            # Test files
├── frontend/
│   ├── index.html           # Main web interface
│   ├── app.js               # Frontend logic
│   └── style.css            # Styles
├── docs/
│   ├── prd.md               # Product requirements
│   ├── tech-spec.md         # Technical specification
│   ├── tasks.md             # Task breakdown
│   └── 2-history/           # Development logs
├── DEPLOYMENT.md            # Backend deployment guide
├── FRONTEND_DEPLOYMENT.md   # Frontend deployment guide
├── DEPLOYMENT_SUMMARY.md    # Deployment quick reference
├── DEPLOYMENT_CHECKLIST.md  # Backend deployment checklist
├── CLOUDFLARE_CHECKLIST.md  # Frontend deployment checklist
├── verify_deployment.sh     # Deployment verification script
├── CLAUDE.md                # Development guidelines
└── README.md                # This file
```

## API Endpoints

### `GET /health`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

### `POST /analyze`

Analyze customer logs.

**Headers:**
- `X-Auth-Token`: Shared password for authentication

**Request:**
```json
{
  "description": "User cannot complete checkout",
  "timestamp": "2025-01-19T14:30:00Z",
  "customer_id": "usr_abc123"
}
```

**Response:**
```json
{
  "success": true,
  "causes": [
    {
      "rank": 1,
      "cause": "Payment token expired",
      "explanation": "User session timed out after 15 minutes",
      "confidence": "high"
    },
    {
      "rank": 2,
      "cause": "Network timeout",
      "explanation": "Request to payment gateway timed out",
      "confidence": "medium"
    },
    {
      "rank": 3,
      "cause": "Invalid card details",
      "explanation": "Card validation failed",
      "confidence": "low"
    }
  ],
  "suggested_response": "Hi there, it looks like your session expired...",
  "sentry_links": ["https://sentry.io/..."],
  "logs_summary": "Found 3 error events in the last 10 minutes",
  "events_found": 3
}
```

### `POST /slack/commands`

Slack slash command handler.

**Note:** This endpoint is called by Slack and requires signature verification.

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SENTRY_AUTH_TOKEN` | Sentry API auth token | Yes |
| `SENTRY_ORG` | Sentry organization slug | Yes |
| `SENTRY_PROJECT` | Sentry project slug | Yes |
| `OPENAI_API_KEY` | OpenAI API key | Yes |
| `APP_PASSWORD` | Shared password for web access | Yes |
| `ALLOWED_ORIGINS` | CORS allowed origins (comma-separated) | Yes |
| `SLACK_BOT_TOKEN` | Slack bot token | No (for Slack) |
| `SLACK_SIGNING_SECRET` | Slack signing secret | No (for Slack) |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No |

### Knowledge Base

The AI uses two knowledge base files in `backend/docs/`:

- **workflow.md**: Your CS team's workflow and processes
- **known_errors.md**: Common error patterns and resolutions

Edit these files to improve analysis accuracy for your specific use case.

## Testing

### Testing Documentation

| Guide | Purpose |
|-------|---------|
| [E2E_TESTING_GUIDE.md](E2E_TESTING_GUIDE.md) | Comprehensive E2E integration testing guide |
| [E2E_TEST_RESULTS.md](E2E_TEST_RESULTS.md) | Test results and tracking template |
| [TESTING_QUICK_REFERENCE.md](TESTING_QUICK_REFERENCE.md) | Quick reference for all test commands |

### Unit Tests

```bash
cd backend
# Run all tests
pytest

# Run specific test file
pytest test_analyzer.py
pytest test_sentry_client.py

# Run with coverage
pytest --cov=. --cov-report=html
```

### Integration Tests

```bash
cd backend
# Sentry integration
pytest test_sentry_integration.py -v

# LLM integration
pytest test_response_validation.py -v

# Slack integration
pytest test_slack_bot.py -v
```

### End-to-End Tests

```bash
cd backend
# Test local development
python test_e2e_integration.py

# Test production deployment
python test_e2e_integration.py \
  --url https://your-app.railway.app \
  --auth-token your-password

# Test with real Sentry data
python test_e2e_integration.py \
  --url https://your-app.railway.app \
  --auth-token your-password \
  --real-data

# Test Slack integration
python test_e2e_integration.py \
  --url https://your-app.railway.app \
  --auth-token your-password \
  --slack-secret your-signing-secret
```

### Frontend Tests

Open the test HTML files in a browser:
- `frontend/test_auth.html`
- `frontend/test_analysis_form.html`
- `frontend/test_results_display.html`
- `frontend/test_error_states.html`

### Test Coverage Summary

| Test Type | Files | Test Count | Status |
|-----------|-------|------------|--------|
| Backend Unit Tests | 14 files | 150+ tests | ✅ All passing |
| Frontend Unit Tests | 4 HTML files | 50+ tests | ✅ All passing |
| Integration Tests | 3 files | 40+ tests | ✅ All passing |
| E2E Tests | 1 file | 8 tests | ✅ Ready |

**Total: ~260+ test cases**

## Development

### Adding New Features

1. Check `docs/tasks.md` for planned features
2. Review `docs/prd.md` and `docs/tech-spec.md` for requirements
3. Create feature branch: `git checkout -b feature/your-feature`
4. Implement feature with tests
5. Update `docs/tasks.md` with progress
6. Log work in `docs/2-history/`
7. Submit pull request

### Code Style

- Python: Follow PEP 8
- JavaScript: Use ES6+ features
- Tests: Write comprehensive unit tests for all new code
- Documentation: Update README and DEPLOYMENT.md for user-facing changes

## Troubleshooting

### Common Issues

**"No events found":**
- Verify customer ID is correct
- Check timestamp is within ±5 minutes of actual error
- Ensure Sentry has events for this customer

**CORS errors:**
- Check `ALLOWED_ORIGINS` includes your frontend URL
- Verify frontend is using HTTPS (not HTTP)

**Authentication failed:**
- Verify `APP_PASSWORD` matches in backend and frontend
- Check password is sent in `X-Auth-Token` header

**Slack command not responding:**
- Verify Request URL in Slack app matches Railway URL
- Check `SLACK_SIGNING_SECRET` is correct
- Review Railway logs for errors

See [DEPLOYMENT.md](DEPLOYMENT.md) for more troubleshooting tips.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Write tests for new code
4. Ensure all tests pass
5. Update documentation
6. Submit a pull request

## License

[Add your license here]

## Support

For questions or issues:
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for deployment help
- Review `docs/tasks.md` for development roadmap
- Open a GitHub issue for bugs

## Roadmap

- [x] Phase 1: Project Setup (4/4 tasks)
- [x] Phase 2: Backend Core (5/5 tasks)
- [x] Phase 3: Sentry Integration (3/3 tasks)
- [x] Phase 4: LLM Integration (3/3 tasks)
- [x] Phase 5: Slack Bot (3/3 tasks)
- [x] Phase 6: Frontend (4/4 tasks)
- [x] Phase 7: Deployment (3/3 tasks)
- [ ] Phase 8: Testing & Polish (1/3 tasks)

**Overall Progress: 26/28 tasks completed (93%)**

See `docs/tasks.md` for detailed task breakdown.

---

Built with ❤️ for customer support teams
