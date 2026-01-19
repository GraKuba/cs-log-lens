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

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment instructions.

**Quick Summary:**

1. **Backend (Railway):**
   - Connect GitHub repo to Railway
   - Set root directory to `/backend`
   - Configure environment variables
   - Deploy automatically

2. **Frontend (Cloudflare Pages):**
   - Connect GitHub repo to Cloudflare Pages
   - Set root directory to `/frontend`
   - Set `API_URL` environment variable
   - Deploy automatically

3. **Slack App (Optional):**
   - Create app at api.slack.com/apps
   - Add `/loglens` slash command
   - Configure bot scopes and install to workspace

### Verify Deployment

After deploying, run the deployment verification tests:

```bash
cd backend
python test_deployment.py https://your-app.railway.app your-password
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
├── DEPLOYMENT.md            # Deployment guide
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

### Run All Tests

```bash
cd backend
pytest
```

### Run Specific Test File

```bash
pytest test_analyzer.py
pytest test_sentry_client.py
```

### Test Coverage

```bash
pytest --cov=. --cov-report=html
```

### Frontend Tests

Open the test HTML files in a browser:
- `frontend/test_auth.html`
- `frontend/test_analysis_form.html`
- `frontend/test_results_display.html`

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

- [x] Phase 1: Project Setup
- [x] Phase 2: Backend Core
- [x] Phase 3: Sentry Integration
- [x] Phase 4: LLM Integration
- [x] Phase 5: Slack Bot
- [x] Phase 6: Frontend
- [ ] Phase 7: Deployment (in progress)
- [ ] Phase 8: Testing & Polish

See `docs/tasks.md` for detailed task breakdown.

---

Built with ❤️ for customer support teams
