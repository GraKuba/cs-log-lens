# Deployment Checklist

Use this checklist to track your deployment progress.

## Pre-Deployment

- [ ] All Phase 1-6 tasks completed (backend and frontend working locally)
- [ ] All tests passing (`pytest` in backend directory)
- [ ] Git repository pushed to GitHub
- [ ] Environment variables documented in `.env.example`
- [ ] API keys ready:
  - [ ] Sentry auth token, org, and project slug
  - [ ] OpenAI API key
  - [ ] App password chosen
  - [ ] (Optional) Slack bot token and signing secret

## Part 1: Backend Deployment (Railway)

### Setup
- [ ] Created Railway account at railway.app
- [ ] Connected GitHub repository to Railway
- [ ] Created new project in Railway
- [ ] Selected the correct repository

### Configuration
- [ ] Set root directory to `backend`
- [ ] Verified build command: `pip install -r requirements.txt`
- [ ] Verified start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Environment Variables
- [ ] `SENTRY_AUTH_TOKEN` set
- [ ] `SENTRY_ORG` set
- [ ] `SENTRY_PROJECT` set
- [ ] `OPENAI_API_KEY` set
- [ ] `APP_PASSWORD` set (use a strong password)
- [ ] `ALLOWED_ORIGINS` set to `*` initially (will update after frontend deploy)
- [ ] `SLACK_BOT_TOKEN` set (if using Slack)
- [ ] `SLACK_SIGNING_SECRET` set (if using Slack)
- [ ] `LOG_LEVEL` set to `INFO` (optional)

### Verification
- [ ] Deployment completed successfully
- [ ] Noted the Railway URL: `___________________________________`
- [ ] SSL/HTTPS enabled (URL starts with https://)
- [ ] Health endpoint accessible: `curl https://YOUR-URL/health`
- [ ] Health endpoint returns `{"status": "healthy", "version": "0.1.0"}`

## Part 2: Frontend Deployment (Cloudflare Pages)

### Setup
- [ ] Created Cloudflare account at cloudflare.com
- [ ] Navigated to Workers & Pages
- [ ] Created new Pages project
- [ ] Connected GitHub repository
- [ ] Selected the correct repository

### Configuration
- [ ] Set project name
- [ ] Set production branch to `main`
- [ ] Set framework preset to `None`
- [ ] Left build command empty
- [ ] Set build output directory to `/`
- [ ] Set root directory to `frontend`

### Environment Variables
- [ ] `API_URL` set to Railway backend URL

### Verification
- [ ] Deployment completed successfully
- [ ] Noted the Cloudflare Pages URL: `___________________________________`
- [ ] Frontend loads in browser
- [ ] No console errors in browser developer tools

### Update Backend CORS
- [ ] Updated `ALLOWED_ORIGINS` in Railway to Cloudflare Pages URL
- [ ] Railway automatically redeployed
- [ ] Frontend can now communicate with backend

## Part 3: Integration Testing

### Basic Tests
- [ ] Frontend password authentication works
- [ ] Can submit analysis request from web form
- [ ] Receives analysis results
- [ ] Results display correctly (causes, response, Sentry links)
- [ ] Copy-to-clipboard works for suggested response

### Deployment Verification Script
- [ ] Ran `python backend/test_deployment.py <RAILWAY_URL> <PASSWORD>`
- [ ] All tests passed:
  - [ ] SSL Enabled
  - [ ] Health Endpoint
  - [ ] CORS Headers
  - [ ] Auth Middleware (Reject)
  - [ ] Auth Middleware (Accept)

### Error Handling
- [ ] Test with invalid customer ID (should show "no events found")
- [ ] Test with wrong password (should show 401 error)
- [ ] Test with missing fields (should show validation errors)

## Part 4: Slack Integration (Optional)

### Slack App Setup
- [ ] Created Slack app at api.slack.com/apps
- [ ] Named app "LogLens"
- [ ] Selected workspace

### Slash Command
- [ ] Added `/loglens` slash command
- [ ] Set Request URL to `https://YOUR-RAILWAY-URL/slack/commands`
- [ ] Set description and usage hint
- [ ] Saved command

### Bot Scopes
- [ ] Added `commands` scope
- [ ] Added `chat:write` scope
- [ ] Saved scopes

### Installation
- [ ] Installed app to workspace
- [ ] Copied Bot User OAuth Token (starts with `xoxb-`)
- [ ] Copied Signing Secret from Basic Information

### Railway Update
- [ ] Updated `SLACK_BOT_TOKEN` in Railway
- [ ] Updated `SLACK_SIGNING_SECRET` in Railway
- [ ] Railway automatically redeployed

### Slack Testing
- [ ] Ran `/loglens` command in Slack
- [ ] Command responds correctly
- [ ] Tested with valid input: `/loglens User issue | 2025-01-19T14:30:00Z | usr_test`
- [ ] Tested with invalid input (shows usage instructions)
- [ ] Response formatting looks correct (emojis, links, etc.)

## Part 5: Security & Production Readiness

### Security
- [ ] `APP_PASSWORD` is strong and secure
- [ ] `ALLOWED_ORIGINS` set to specific domain (not `*`)
- [ ] All API keys are valid and not exposed in code
- [ ] `.env` file is in `.gitignore` and not committed to Git
- [ ] HTTPS enabled on both frontend and backend
- [ ] Slack signing secret validation working

### Documentation
- [ ] Shared frontend URL with CS team
- [ ] Shared `APP_PASSWORD` with CS team (securely)
- [ ] Documented how to use web interface
- [ ] Documented Slack command format (if applicable)
- [ ] Created internal runbook for troubleshooting

### Monitoring
- [ ] Railway logs are accessible and readable
- [ ] Set up Railway alerts for downtime (optional)
- [ ] Tested log format (JSON in production)

## Part 6: Post-Deployment

### Documentation Updates
- [ ] Updated `docs/tasks.md` - marked Task 7.1 as complete
- [ ] Added deployment date to task
- [ ] Updated overall progress counter
- [ ] Created history log in `docs/2-history/`

### Next Steps
- [ ] Proceed to Task 7.2 (already done if Cloudflare deployed)
- [ ] Proceed to Task 7.3 (already done if Slack configured)
- [ ] Move to Phase 8: Testing & Polish

## Deployment URLs (Fill In)

**Backend (Railway):**
```
https://___________________________________
```

**Frontend (Cloudflare Pages):**
```
https://___________________________________
```

**Credentials:**
- App Password: `___________________________________` (keep secure!)
- Slack Bot Token: `xoxb-___________________________________`
- Slack Signing Secret: `___________________________________`

## Rollback Plan

If something goes wrong:

**Railway:**
1. Go to Deployments tab in Railway
2. Find previous working deployment
3. Click "Redeploy"

**Cloudflare Pages:**
1. Go to Deployments tab in Cloudflare
2. Find previous deployment
3. Click "Rollback to this deployment"

## Support Contacts

**Railway Support:**
- Docs: https://docs.railway.app
- Discord: https://discord.gg/railway

**Cloudflare Support:**
- Docs: https://developers.cloudflare.com/pages
- Community: https://community.cloudflare.com

**Slack Support:**
- Docs: https://api.slack.com/docs
- Support: https://api.slack.com/support

---

**Deployment Started:** ___________________
**Deployment Completed:** ___________________
**Deployed By:** ___________________
