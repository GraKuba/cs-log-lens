# Slack Testing Quick Checklist

## Pre-Test Setup (5 minutes)

### 1. Start Backend Server
```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload
```
- [ ] Server starts without errors
- [ ] Logs show: "Application startup complete"

### 2. Verify Environment Variables
```bash
cd backend
grep -E "SLACK_BOT_TOKEN|SLACK_SIGNING_SECRET|GEMINI_API_KEY|SENTRY_AUTH_TOKEN" .env
```
- [ ] All 4 variables are present and not empty

### 3. Test Backend Locally
```bash
./test_slack_manual.sh
```
- [ ] Script shows "Backend Test Complete! ✓"

## Slack App Configuration (10 minutes)

### 4. Check Slack App Settings
Visit: https://api.slack.com/apps

- [ ] App exists and is installed in workspace
- [ ] Slash command `/loglens` is configured
- [ ] Request URL points to Railway deployment: `https://YOUR-APP.railway.app/slack/commands`
- [ ] OAuth scopes include `commands`

### 5. Get Your Railway URL
```bash
# Visit Railway dashboard or check deployment logs
# Your URL should look like: https://cs-log-lens-production.up.railway.app
```
- [ ] URL is accessible (visit in browser, should see FastAPI docs at /docs)

## Manual Testing in Slack (15 minutes)

### 6. Test Valid Command
In Slack, type:
```
/loglens User experiencing template error on dashboard | 2026-01-16T19:22:11.883Z | test_customer
```

**Expected result:**
- [ ] Bot responds within 30 seconds
- [ ] Response includes "✅ Analysis complete"
- [ ] Response shows 3 ranked causes
- [ ] Response includes Sentry links
- [ ] Links are clickable

### 7. Test Invalid Formats

**Missing parameter:**
```
/loglens Test issue | 2026-01-16T19:22:11.883Z
```
- [ ] Shows error about invalid format

**Empty description:**
```
/loglens  | 2026-01-16T19:22:11.883Z | usr_123
```
- [ ] Shows error about empty description

**Invalid timestamp:**
```
/loglens Test | invalid-time | usr_123
```
- [ ] Shows error about invalid timestamp

### 8. Check Backend Logs
While testing in Slack, watch backend logs:
```bash
cd backend
# Check the terminal where uvicorn is running
```

**Look for:**
- [ ] "Received Slack command: ..."
- [ ] "Slack signature verified successfully"
- [ ] "Analyzing logs for customer ..."
- [ ] No error messages

## Troubleshooting Quick Fixes

### If signature verification fails:
1. Copy `SLACK_SIGNING_SECRET` from Slack app "Basic Information" page
2. Update in `backend/.env`
3. Restart backend server

### If command doesn't respond:
1. Check Railway deployment is running
2. Verify Request URL in Slack app settings
3. Check backend logs for errors

### If "No events found":
- This is OK! The system is working, just no Sentry events in that time range
- Try with: `2026-01-16T19:22:11.883Z` (known to have events)

## Success Criteria

All these should be ✓:
- [ ] Backend starts and runs without errors
- [ ] Test script passes
- [ ] Valid Slack command returns formatted response
- [ ] Invalid commands show appropriate errors
- [ ] Sentry links work and point to correct events
- [ ] Backend logs show no errors during tests

## Quick Test Command

For fastest testing, use this proven command:
```
/loglens User experiencing template error on dashboard | 2026-01-16T19:22:11.883Z | test_customer
```

This uses real data from your Sentry and should return 6 events about Django template errors.

---

**Time estimate:** 30 minutes total
**Difficulty:** Easy (mostly configuration checks)
