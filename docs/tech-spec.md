# LogLens MVP - Technical Specification

## Overview

**Product:** LogLens  
**Version:** MVP  
**Date:** January 2025  
**Estimated Build Time:** 2-3 days

---

## Architecture

```
┌─────────────────┐     ┌─────────────────┐
│   Cloudflare    │     │      Slack      │
│     Pages       │     │    Workspace    │
│   (Frontend)    │     │      (Bot)      │
└────────┬────────┘     └────────┬────────┘
         │                       │
         │    HTTPS              │    HTTPS
         │                       │
         └───────────┬───────────┘
                     ▼
            ┌─────────────────┐
            │     FastAPI     │
            │    (Railway)    │
            └────────┬────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   ┌─────────┐  ┌─────────┐  ┌─────────┐
   │ Sentry  │  │ OpenAI  │  │Markdown │
   │   API   │  │   API   │  │  Files  │
   └─────────┘  └─────────┘  └─────────┘
```

---

## Tech Stack

| Layer | Technology | Justification |
|-------|------------|---------------|
| Frontend | HTML/CSS/JS (vanilla) | Minimal, no build step |
| Hosting (FE) | Cloudflare Pages | Free, fast, simple deploy |
| Backend | FastAPI (Python 3.11) | Fast to build, async support |
| Hosting (BE) | Railway | Easy Python deploy, env vars |
| LLM | OpenAI GPT-4o | Best balance of speed/quality |
| Logs | Sentry API | Already in use |
| Slack | Slack Bolt SDK | Official, handles verification |

---

## Project Structure

```
/loglens
├── /backend
│   ├── main.py              # FastAPI app, routes, middleware
│   ├── sentry_client.py     # Sentry API integration
│   ├── analyzer.py          # LLM analysis logic
│   ├── slack_bot.py         # Slack command handler
│   ├── config.py            # Environment configuration
│   ├── requirements.txt     # Python dependencies
│   └── /docs
│       ├── workflow.md      # Expected user flows
│       └── known_errors.md  # Error pattern catalog
│
├── /frontend
│   ├── index.html           # Single page app
│   ├── style.css            # Minimal styling
│   └── app.js               # Form handling, API calls
│
└── README.md
```

---

## Backend Specification

### Dependencies

```txt
fastapi==0.109.0
uvicorn==0.27.0
httpx==0.26.0
openai==1.12.0
slack-bolt==1.18.0
python-dotenv==1.0.0
```

### Environment Variables

```bash
# Sentry
SENTRY_AUTH_TOKEN=sntrys_xxx
SENTRY_ORG=your-org-slug
SENTRY_PROJECT=your-project-slug

# OpenAI
OPENAI_API_KEY=sk-xxx

# Slack
SLACK_BOT_TOKEN=xoxb-xxx
SLACK_SIGNING_SECRET=xxx

# App
APP_PASSWORD=your-shared-password
ALLOWED_ORIGINS=https://your-frontend.pages.dev
```

### API Endpoints

#### POST /analyze

Analyzes logs and returns probable causes.

**Request:**
```json
{
  "description": "User couldn't complete checkout",
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
      "explanation": "User session timed out after 15 minutes of inactivity",
      "confidence": "high"
    },
    {
      "rank": 2,
      "cause": "Cart session timeout",
      "explanation": "Cart was cleared due to session expiry",
      "confidence": "medium"
    },
    {
      "rank": 3,
      "cause": "Inventory conflict",
      "explanation": "Item may have gone out of stock during checkout",
      "confidence": "low"
    }
  ],
  "suggested_response": "Hi [Customer], it looks like your payment session timed out...",
  "sentry_links": [
    "https://sentry.io/organizations/org/issues/123/"
  ],
  "logs_summary": "Found 3 error events between 14:25:00 and 14:35:00",
  "events_found": 3
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "No Sentry events found in time range",
  "suggestion": "Try expanding the time range or verify customer ID"
}
```

#### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

#### POST /slack/commands

Slack slash command webhook (handled by Slack Bolt).

---

### Authentication Middleware

```python
from fastapi import Request, HTTPException

async def verify_auth(request: Request):
    token = request.headers.get("X-Auth-Token")
    if token != config.APP_PASSWORD:
        raise HTTPException(status_code=401, detail="Unauthorized")
```

Applied to `/analyze` endpoint. Slack endpoint uses Slack's signing secret verification.

---

### Sentry Integration

**API Endpoint:**
```
GET https://sentry.io/api/0/projects/{org}/{project}/events/
```

**Query Parameters:**
| Param | Value |
|-------|-------|
| query | `user.id:{customer_id}` |
| start | `{timestamp} - 5 minutes` |
| end | `{timestamp} + 5 minutes` |
| full | `true` |

**Headers:**
```
Authorization: Bearer {SENTRY_AUTH_TOKEN}
```

**Response Processing:**
- Extract error message, stack trace, breadcrumbs
- Format for LLM consumption
- Generate direct links to Sentry UI

---

### LLM Integration

**Model:** `gpt-4o`

**System Prompt:**
```
You are LogLens, a log analysis assistant. Your job is to analyze application 
logs and help identify why a user experienced a problem.

Given:
1. Workflow documentation describing expected system behavior
2. Known error patterns and their resolutions
3. Sentry log events from the relevant time period
4. A problem description from customer support

You must return:
1. Top 3 most likely causes, ranked by probability
2. Confidence level for each (high/medium/low)
3. A suggested response that CS can send to the customer
4. Brief summary of relevant log findings

Be specific and actionable. Reference actual error messages from the logs.
If logs don't clearly indicate the cause, say so and suggest next steps.
```

**User Prompt Template:**
```
## Workflow Documentation
{workflow.md contents}

## Known Error Patterns
{known_errors.md contents}

## Sentry Events
{formatted_events}

## Problem Report
- Description: {description}
- Timestamp: {timestamp}
- Customer ID: {customer_id}

Analyze and respond in JSON format:
{
  "causes": [{"rank": 1, "cause": "", "explanation": "", "confidence": ""}],
  "suggested_response": "",
  "logs_summary": ""
}
```

**Response Parsing:**
- Parse JSON from LLM response
- Validate required fields
- Append Sentry links from fetched events

---

### Slack Bot

**Slash Command:** `/loglens`

**Usage:** `/loglens [description] | [timestamp] | [customer_id]`

**Example:** `/loglens User can't checkout | 2025-01-19T14:30:00Z | usr_abc123`

**Response Format:**
```
🔍 *LogLens Analysis*

*Probable Causes:*
1️⃣ [HIGH] Payment token expired
   └ User session timed out after 15 minutes

2️⃣ [MEDIUM] Cart session timeout
   └ Cart was cleared due to session expiry

3️⃣ [LOW] Inventory conflict
   └ Item may have gone out of stock

*Suggested Response:*
> Hi [Customer], it looks like your payment session timed out...

*Logs:* Found 3 events | <https://sentry.io/...|View in Sentry>
```

---

## Frontend Specification

### index.html

Single page with:
- Password gate (shown first if not authenticated)
- Analysis form (description, timestamp, customer ID)
- Results display area
- Loading state

### UI Components

```
┌─────────────────────────────────────────┐
│  🔍 LogLens                             │
├─────────────────────────────────────────┤
│                                         │
│  Problem Description                    │
│  ┌─────────────────────────────────┐   │
│  │                                 │   │
│  │                                 │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Timestamp            Customer ID       │
│  ┌──────────────┐    ┌──────────────┐  │
│  │              │    │              │  │
│  └──────────────┘    └──────────────┘  │
│                                         │
│  [ Analyze ]                            │
│                                         │
├─────────────────────────────────────────┤
│  Results                                │
│  ┌─────────────────────────────────┐   │
│  │ 1. [HIGH] Payment token expired │   │
│  │ 2. [MEDIUM] Cart timeout        │   │
│  │ 3. [LOW] Inventory conflict     │   │
│  │                                 │   │
│  │ Suggested Response:             │   │
│  │ "Hi [Customer]..."              │   │
│  │                                 │   │
│  │ [View in Sentry]                │   │
│  └─────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

### JavaScript Logic

```javascript
// Password check
const storedPassword = localStorage.getItem('loglens_auth');
if (!storedPassword) {
    showPasswordPrompt();
}

// Form submission
async function analyze(e) {
    e.preventDefault();
    setLoading(true);
    
    const response = await fetch(`${API_URL}/analyze`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Auth-Token': localStorage.getItem('loglens_auth')
        },
        body: JSON.stringify({
            description: form.description.value,
            timestamp: form.timestamp.value,
            customer_id: form.customer_id.value
        })
    });
    
    const data = await response.json();
    renderResults(data);
    setLoading(false);
}
```

---

## Deployment

### Backend (Railway)

1. Connect GitHub repo
2. Set root directory to `/backend`
3. Add environment variables
4. Deploy (auto-detects Python)

**Railway Settings:**
- Build: `pip install -r requirements.txt`
- Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Frontend (Cloudflare Pages)

1. Connect GitHub repo
2. Set root directory to `/frontend`
3. Build command: (none, static files)
4. Set environment variable: `API_URL`

### Slack App Setup

1. Create app at https://api.slack.com/apps
2. Add slash command `/loglens`
3. Set request URL: `https://{railway-url}/slack/commands`
4. Add bot token scopes: `commands`, `chat:write`
5. Install to workspace
6. Copy bot token and signing secret to Railway env vars

---

## Build Order

| Step | Task | Time |
|------|------|------|
| 1 | Backend skeleton (FastAPI + health + auth) | 1 hour |
| 2 | Sentry client (fetch events) | 2 hours |
| 3 | Analyzer (LLM integration) | 2 hours |
| 4 | Wire up /analyze endpoint | 1 hour |
| 5 | Frontend (form + results) | 3 hours |
| 6 | Slack bot | 2 hours |
| 7 | Deploy + test | 2 hours |
| 8 | Documentation + polish | 1 hour |

**Total: ~14 hours / 2-3 days**

---

## Starter Files

### docs/workflow.md

```markdown
# Expected User Flows

## Checkout Flow
1. User adds items to cart
2. User clicks "Checkout"
3. User enters shipping information
4. User enters payment information
5. User clicks "Place Order"
6. Order confirmation displayed
7. Confirmation email sent

### Expected Behaviors
- Session timeout: 15 minutes of inactivity
- Cart persists for 24 hours
- Payment tokens valid for 10 minutes

## Login Flow
1. User enters email
2. User enters password
3. System validates credentials
4. Session created (24 hour expiry)
5. User redirected to dashboard

### Expected Behaviors
- Max 5 login attempts before lockout
- Lockout duration: 15 minutes
- Password reset link valid for 1 hour

## [Add more flows as needed]
```

### docs/known_errors.md

```markdown
# Known Error Patterns

<!-- Add entries as you encounter and resolve errors -->

## Template

### [Error Name]
- **Sentry Error:** `ErrorClassName` or error message pattern
- **Root Cause:** What actually happened
- **User Impact:** What the user experienced  
- **Resolution:** How to fix / what to tell customer
- **Customer Response:** Copy-paste response for CS

---

## Example Entry

### Payment Token Expired
- **Sentry Error:** `PaymentTokenExpiredError` or "token expired"
- **Root Cause:** User took longer than 10 minutes on payment page
- **User Impact:** "Payment failed" error on checkout
- **Resolution:** User needs to restart checkout
- **Customer Response:** "Hi! It looks like your payment session timed out - this happens if the checkout page is open for more than 10 minutes. Please try checking out again, and let me know if you run into any issues!"

---

<!-- Add new errors below as they're resolved -->
```

---

## Testing

### Manual Test Cases

| # | Test | Expected Result |
|---|------|-----------------|
| 1 | Submit with valid inputs | Returns causes + response |
| 2 | Submit with invalid customer ID | Returns "no events found" |
| 3 | Submit with wrong password | Returns 401 |
| 4 | Slack command with valid inputs | Posts formatted response |
| 5 | Slack command with missing params | Posts usage instructions |

### Sample Test Input

```json
{
  "description": "User says checkout button does nothing when clicked",
  "timestamp": "2025-01-19T14:30:00Z",
  "customer_id": "usr_test123"
}
```