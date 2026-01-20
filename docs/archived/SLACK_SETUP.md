# Slack App Setup Guide for LogLens

This guide walks you through setting up the LogLens Slack app so your CS team can analyze logs directly from Slack using the `/loglens` command.

## Prerequisites

Before you begin, ensure you have:

- ✅ Backend deployed to Railway (Task 7.1 complete)
- ✅ Railway backend URL (e.g., `https://your-app.railway.app`)
- ✅ Admin access to your Slack workspace
- ✅ Access to Railway environment variables

## Overview

The LogLens Slack integration allows CS agents to run log analysis without leaving Slack:

```
User types in Slack:
/loglens User can't checkout | 2025-01-19T14:30:00Z | usr_abc123

LogLens responds with:
🔍 LogLens Analysis
Probable Causes:
1️⃣ [HIGH] Payment token expired
   └ User session timed out after 15 minutes
...
```

## Setup Steps

### Step 1: Create Slack App

1. Go to https://api.slack.com/apps
2. Click **"Create New App"**
3. Choose **"From scratch"**
4. Enter app details:
   - **App Name:** `LogLens`
   - **Workspace:** Select your workspace
5. Click **"Create App"**

### Step 2: Configure Slash Command

1. In your app's settings, go to **"Slash Commands"** in the left sidebar
2. Click **"Create New Command"**
3. Fill in the command details:

   | Field | Value |
   |-------|-------|
   | **Command** | `/loglens` |
   | **Request URL** | `https://your-app.railway.app/slack/commands` |
   | **Short Description** | `Analyze customer logs and errors` |
   | **Usage Hint** | `[description] \| [timestamp] \| [customer_id]` |

4. Click **"Save"**

**⚠️ Important:** Replace `your-app.railway.app` with your actual Railway backend URL.

### Step 3: Add Bot Scopes

1. Go to **"OAuth & Permissions"** in the left sidebar
2. Scroll down to **"Scopes"** section
3. Under **"Bot Token Scopes"**, add these scopes:
   - `commands` - Allow slash commands
   - `chat:write` - Allow bot to post messages

4. Click **"Save Changes"**

### Step 4: Install App to Workspace

1. Go to **"Install App"** in the left sidebar
2. Click **"Install to Workspace"**
3. Review the permissions
4. Click **"Allow"**

### Step 5: Copy Credentials

After installation, you'll see two important credentials:

#### Bot Token
1. Go to **"OAuth & Permissions"**
2. Copy the **"Bot User OAuth Token"**
   - Format: `xoxb-...`
   - Keep this secure!

#### Signing Secret
1. Go to **"Basic Information"**
2. Scroll to **"App Credentials"**
3. Copy the **"Signing Secret"**
   - Keep this secure!

### Step 6: Add Credentials to Railway

1. Go to your Railway dashboard
2. Select your LogLens backend service
3. Go to **"Variables"** tab
4. Add/update these environment variables:

   | Variable | Value | Example |
   |----------|-------|---------|
   | `SLACK_BOT_TOKEN` | Bot User OAuth Token from Step 5 | `xoxb-1234567890...` |
   | `SLACK_SIGNING_SECRET` | Signing Secret from Step 5 | `a1b2c3d4e5f6...` |

5. Railway will automatically redeploy with the new variables

### Step 7: Verify Setup

Wait for Railway to finish deploying (1-2 minutes), then test:

1. Open your Slack workspace
2. In any channel, type: `/loglens`
3. You should see the command autocomplete appear
4. Try a test command:
   ```
   /loglens Test error | 2025-01-19T14:30:00Z | usr_test123
   ```

**Expected behavior:**
- If working: You'll get a formatted response (or "No events found")
- If error: Check Railway logs and verify credentials

## Command Usage

### Format
```
/loglens [description] | [timestamp] | [customer_id]
```

### Examples

**Basic usage:**
```
/loglens User can't complete checkout | 2025-01-19T14:30:00Z | usr_abc123
```

**Different issue types:**
```
/loglens Payment failed with error code 500 | 2025-01-19T09:15:00Z | usr_xyz789
/loglens Login button not responding | 2025-01-20T16:45:00Z | usr_def456
/loglens Dashboard shows blank page | 2025-01-20T11:00:00Z | usr_ghi321
```

### Timestamp Formats
The timestamp must be in ISO 8601 format: `YYYY-MM-DDTHH:MM:SSZ`

**Valid timestamps:**
- `2025-01-19T14:30:00Z` ✅
- `2025-01-19T09:15:00Z` ✅
- `2025-01-20T16:45:30Z` ✅

**Invalid timestamps:**
- `2025-01-19 14:30:00` ❌ (missing T and Z)
- `Jan 19, 2025 2:30 PM` ❌ (not ISO format)

**💡 Tip:** Use https://timestamp.online/ to convert timestamps

## Response Format

LogLens responds with formatted analysis:

```
🔍 LogLens Analysis

*Probable Causes:*
1️⃣ [HIGH] Payment token expired
   └ User session timed out after 15 minutes

2️⃣ [MEDIUM] Network timeout
   └ Payment gateway took longer than 30s to respond

3️⃣ [LOW] Browser compatibility issue
   └ Older Safari version may not support payment API

*Suggested Response:*
> Hi [Customer], it looks like your payment session expired.
> Please try checking out again. The issue has been logged for
> our engineering team to investigate recurring timeouts.

*Logs:* Found 3 events | <https://sentry.io/...|View in Sentry>
```

## Troubleshooting

### Command Not Showing
**Problem:** `/loglens` doesn't appear in autocomplete

**Solutions:**
1. Wait 5-10 minutes after installing app
2. Try typing `/loglens` fully and pressing Enter
3. Reinstall the app to your workspace

### Invalid Signature Error
**Problem:** Slack returns "Invalid signature" error

**Solutions:**
1. Verify `SLACK_SIGNING_SECRET` in Railway matches Slack dashboard
2. Check Railway logs for detailed error
3. Ensure no extra spaces in the signing secret

### Timeout Errors
**Problem:** Slack shows "Operation timed out"

**Solutions:**
1. Check Railway backend is running: `curl https://your-app.railway.app/health`
2. Verify Request URL in Slack matches Railway URL exactly
3. Check Railway logs for errors

### Command Works But No Response
**Problem:** Command executes but returns empty or error

**Solutions:**
1. Verify `SLACK_BOT_TOKEN` in Railway is correct
2. Check bot has `chat:write` scope
3. Check Railway logs for LLM or Sentry API errors

### "No events found" Every Time
**Problem:** Always returns no events even with valid customer ID

**Solutions:**
1. Verify `SENTRY_AUTH_TOKEN`, `SENTRY_ORG`, and `SENTRY_PROJECT` in Railway
2. Check customer ID format matches Sentry user IDs
3. Expand time window (try ±30 minutes from issue time)
4. Verify events exist in Sentry dashboard

## Testing

### Test 1: Valid Command
```
/loglens Test checkout error | 2025-01-19T14:30:00Z | usr_test123
```

**Expected:** Formatted response with causes and suggestions

### Test 2: Invalid Format (Missing Parts)
```
/loglens Test error | 2025-01-19T14:30:00Z
```

**Expected:** Usage instructions error message

### Test 3: Invalid Timestamp
```
/loglens Test error | not-a-timestamp | usr_test123
```

**Expected:** Error message about invalid timestamp format

### Test 4: Real Customer Issue
```
/loglens [actual-problem-description] | [actual-time] | [actual-customer-id]
```

**Expected:** Real analysis with Sentry events (or "no events found")

## Security Notes

### Keep These Secret! 🔒
- **Bot User OAuth Token** (`xoxb-...`)
- **Signing Secret**

Never commit these to your repository or share them publicly.

### Signature Verification
The backend automatically verifies every Slack request using the signing secret. This prevents:
- Unauthorized requests from non-Slack sources
- Replay attacks (5-minute timestamp window)
- Tampering with request data

### Best Practices
1. ✅ Rotate Slack tokens periodically
2. ✅ Use different workspaces for testing and production
3. ✅ Monitor Railway logs for suspicious activity
4. ✅ Limit Slack app to specific channels (optional)

## Advanced Configuration

### Custom Bot Name and Icon

1. Go to **"Basic Information"** in Slack app settings
2. Under **"Display Information"**:
   - **App Name:** Change if desired
   - **Short Description:** Customize
   - **App Icon:** Upload custom icon (512x512 PNG)
3. Click **"Save Changes"**

### Restrict to Specific Channels

1. Go to your Slack workspace settings
2. Navigate to **"Administration"** → **"Manage Apps"**
3. Find LogLens app
4. Click **"Configuration"**
5. Under **"Channel Restrictions"**, select channels

### Add App to Channels

By default, the app works in all channels. To explicitly add it:

1. In Slack, go to desired channel
2. Click channel name at top
3. Select **"Integrations"** tab
4. Click **"Add apps"**
5. Select **"LogLens"**

## Monitoring

### Check Usage
1. Go to https://api.slack.com/apps
2. Select LogLens app
3. Go to **"Event Subscriptions"** → **"View Logs"**

### Check Backend Logs
```bash
# Railway dashboard → Backend service → Logs
# Look for:
[INFO] Slack command received
[INFO] Sentry events fetched: 3
[INFO] LLM analysis complete
```

### Common Log Messages

**Success:**
```json
{
  "level": "INFO",
  "message": "Slack command processed successfully",
  "customer_id": "usr_abc123",
  "events_found": 3
}
```

**Error:**
```json
{
  "level": "ERROR",
  "message": "Sentry API error",
  "error": "Authentication failed"
}
```

## Rollback

If you need to revert Slack credentials:

1. Generate new tokens in Slack dashboard:
   - **"OAuth & Permissions"** → Reinstall app → Copy new bot token
   - **"Basic Information"** → Regenerate signing secret

2. Update Railway environment variables with new values

3. Railway will auto-redeploy

## Next Steps

After successful Slack setup:

1. ✅ Test command with real customer data
2. ⏭️ Train CS team on command usage
3. ⏭️ Proceed to Task 8.1: End-to-End Integration Testing
4. ⏭️ Create internal documentation for CS team
5. ⏭️ Set up monitoring and alerts

## Support

### Common Questions

**Q: Can multiple people use the command at once?**
A: Yes, the backend handles concurrent requests.

**Q: Is there a rate limit?**
A: Limited by Sentry and OpenAI API rate limits. For typical usage, no issues.

**Q: Can I use this in DMs?**
A: Yes, slash commands work in channels and DMs.

**Q: How long does analysis take?**
A: Typically 2-5 seconds depending on Sentry and LLM response times.

**Q: Can I customize the response format?**
A: Yes, modify `slack_bot.py` in the backend code.

### Getting Help

**Slack app issues:**
- Check https://api.slack.com/docs/slack-commands

**Backend issues:**
- Check Railway logs
- Review `backend/slack_bot.py` code
- Test `/slack/commands` endpoint directly

**Sentry integration issues:**
- Verify Sentry credentials
- Check Sentry API status
- Review `backend/sentry_client.py` code

---

**Last Updated:** 2026-01-20
**Task:** 7.3 - Configure Slack App
**Status:** Ready for manual configuration
