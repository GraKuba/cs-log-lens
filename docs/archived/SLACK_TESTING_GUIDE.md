# Slack Integration - Manual Testing Guide

This guide will walk you through testing the CS Log Lens Slack integration.

## Prerequisites

✅ **Before you start, verify:**
1. Backend is running: `cd backend && uvicorn main:app --reload`
2. Backend is accessible via public URL (Railway deployment)
3. Slack app is configured with your slash command
4. Environment variables are set in `.env`:
   - `SLACK_BOT_TOKEN`
   - `SLACK_SIGNING_SECRET`

## Step 1: Verify Slack App Configuration

### Check Your Slack App Settings
1. Go to https://api.slack.com/apps
2. Select your app (CS Log Lens)
3. Navigate to **"Slash Commands"**
4. Verify `/loglens` command exists with:
   - **Request URL**: `https://your-railway-url.railway.app/slack/commands`
   - **Description**: "Analyze Sentry logs for customer issues"
   - **Usage Hint**: `[description] | [timestamp] | [customer_id]`

### Verify OAuth Scopes
1. In Slack App settings, go to **"OAuth & Permissions"**
2. Check that these scopes are present:
   - `commands` - Required for slash commands
   - `chat:write` - For posting messages (if needed)

## Step 2: Test Backend Endpoint Directly

Before testing in Slack, verify the endpoint works:

```bash
# Test the analyze endpoint (without Slack auth)
curl -X POST https://your-railway-url.railway.app/analyze \
  -H "Content-Type: application/json" \
  -H "X-App-Password: Orbital2026" \
  -d '{
    "description": "User experiencing template error on dashboard",
    "timestamp": "2026-01-16T19:22:11.883Z",
    "customer_id": "test_customer"
  }'
```

**Expected result**: JSON response with causes, suggested_response, and sentry_links.

## Step 3: Test in Slack (Manual)

### 3.1 Open Slack Workspace
1. Open your Slack workspace where the app is installed
2. Go to any channel where you have the app installed

### 3.2 Test with Real Data

**Test Command:**
```
/loglens User experiencing template error on dashboard | 2026-01-16T19:22:11.883Z | test_customer
```

**Expected Response:**
The bot should respond with a formatted message containing:
- ✅ Success indicator
- 📊 **Top Causes** (ranked 1-3 with confidence levels)
- 💬 **Suggested Customer Response**
- 🔗 **Sentry Links** (clickable links to events)
- 📝 **Logs Summary**
- ⚡ Event count

### 3.3 Test Command Format Variations

**Test 1: Valid command with different data**
```
/loglens Payment processing failed | 2026-01-19T10:30:00Z | usr_12345
```

**Test 2: Missing parameters (should show error)**
```
/loglens User can't login | 2026-01-19T10:30:00Z
```
Expected: Error message about invalid format

**Test 3: Empty description (should show error)**
```
/loglens  | 2026-01-19T10:30:00Z | usr_12345
```
Expected: Error message about empty description

**Test 4: Invalid timestamp format (should show error)**
```
/loglens Login issue | not-a-timestamp | usr_12345
```
Expected: Error message about invalid timestamp

## Step 4: Check Logs

### Backend Logs
Watch the backend logs while testing:
```bash
cd backend
tail -f $(ls -t *.log | head -1)
```

**What to look for:**
- `Received Slack command: ...` - Command received
- `Slack signature verified successfully` - Authentication passed
- `Analyzing logs for customer ...` - Processing started
- `Successfully analyzed logs` - Analysis complete

### Sentry Dashboard
1. Go to https://de.sentry.io
2. Check if events are being fetched correctly
3. Verify the event links in Slack response match actual events

## Step 5: Test Error Scenarios

### 5.1 No Events Found
```
/loglens Testing with no events | 2020-01-01T00:00:00Z | nonexistent_user
```
**Expected**: Should still return a response, but with "No Sentry events found" in summary

### 5.2 Invalid Timestamp
```
/loglens Test | invalid-timestamp | usr_123
```
**Expected**: Error message about invalid timestamp format

### 5.3 Server Error Simulation
1. Stop the backend server
2. Try a command in Slack
3. **Expected**: Timeout or error message

## Step 6: Verify Response Formatting

A successful response should look like this in Slack:

```
✅ Analysis complete

📊 Top Causes:

1. Application code error: Invalid Django template filter 'list' (high confidence)
The Sentry logs show a 'TemplateSyntaxError' with the message "Invalid filter: 'list'"...

2. Deployment issue: Missing or misconfigured custom template filter (high confidence)
Since 'list' is not a standard Django template filter...

3. Server configuration issue: Disallowed HTTP host (low confidence)
While not directly causing the 'TemplateSyntaxError'...

💬 Suggested Customer Response:
Hi there,
Thank you for reaching out! We've investigated the logs...

🔗 Sentry Links:
• Event 1
• Event 2
...

📝 Logs Summary:
The Sentry logs show two critical 'TemplateSyntaxError' events...

⚡ Found 6 events
```

## Troubleshooting

### Issue: "Invalid signature" error
**Solution**:
- Verify `SLACK_SIGNING_SECRET` in `.env` matches Slack app settings
- Check that timestamp isn't too old (requests must be within 5 minutes)

### Issue: "Missing signature headers"
**Solution**:
- Verify Slack app Request URL is correct
- Make sure you're testing from actual Slack, not curl/Postman

### Issue: Command not responding
**Solution**:
- Check backend logs for errors
- Verify Railway deployment is running
- Check that Request URL in Slack app settings is accessible

### Issue: "Slack integration not configured"
**Solution**:
- Verify `.env` file has both `SLACK_BOT_TOKEN` and `SLACK_SIGNING_SECRET`
- Restart the backend server after updating `.env`

## Testing Checklist

- [ ] Backend server is running and accessible
- [ ] Slack app is configured with correct Request URL
- [ ] Environment variables are set correctly
- [ ] Test command works with valid data
- [ ] Error messages show for invalid formats
- [ ] Response formatting looks good in Slack
- [ ] Sentry links are clickable and correct
- [ ] Backend logs show successful processing
- [ ] Test with no events found scenario
- [ ] Test with invalid timestamp format

## Next Steps

After successful manual testing:
1. Document any issues found
2. Test with different timestamp ranges
3. Test with different customer IDs
4. Share with team members for feedback
5. Monitor production usage

## Quick Reference

**Command Format:**
```
/loglens [description] | [timestamp] | [customer_id]
```

**Example:**
```
/loglens User can't checkout | 2026-01-16T19:22:11.883Z | usr_abc123
```

**Timestamp Format:** ISO 8601 (YYYY-MM-DDTHH:MM:SSZ)

**Backend URL:** Check Railway dashboard for your deployment URL
