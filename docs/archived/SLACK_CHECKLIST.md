# Slack App Setup Checklist

Use this checklist to track your progress setting up the LogLens Slack integration.

**Date Started:** ___________
**Completed By:** ___________
**Railway URL:** https://_____________________________.railway.app

---

## Prerequisites ✓

- [ ] Backend deployed to Railway (Task 7.1)
- [ ] Railway backend URL noted above
- [ ] Admin access to Slack workspace
- [ ] Access to Railway dashboard and environment variables

---

## Step 1: Create Slack App

- [ ] Opened https://api.slack.com/apps
- [ ] Clicked "Create New App"
- [ ] Selected "From scratch"
- [ ] Entered app name: `LogLens`
- [ ] Selected workspace
- [ ] Clicked "Create App"

**Slack App URL:** https://api.slack.com/apps/___________

---

## Step 2: Configure Slash Command

- [ ] Navigated to "Slash Commands" in left sidebar
- [ ] Clicked "Create New Command"
- [ ] Filled in command details:
  - [ ] Command: `/loglens`
  - [ ] Request URL: `https://[your-railway-url]/slack/commands`
  - [ ] Short Description: `Analyze customer logs and errors`
  - [ ] Usage Hint: `[description] | [timestamp] | [customer_id]`
- [ ] Clicked "Save"

**Request URL Used:** https://_____________________________.railway.app/slack/commands

---

## Step 3: Add Bot Scopes

- [ ] Navigated to "OAuth & Permissions" in left sidebar
- [ ] Scrolled to "Scopes" section
- [ ] Added bot token scope: `commands`
- [ ] Added bot token scope: `chat:write`
- [ ] Clicked "Save Changes"

---

## Step 4: Install App to Workspace

- [ ] Navigated to "Install App" in left sidebar
- [ ] Clicked "Install to Workspace"
- [ ] Reviewed permissions
- [ ] Clicked "Allow"
- [ ] Installation completed successfully

---

## Step 5: Copy Credentials

### Bot Token
- [ ] Navigated to "OAuth & Permissions"
- [ ] Copied "Bot User OAuth Token" (starts with `xoxb-`)
- [ ] Stored securely (password manager or secure notes)

**Bot Token (first 10 chars):** xoxb-_____

### Signing Secret
- [ ] Navigated to "Basic Information"
- [ ] Scrolled to "App Credentials" section
- [ ] Copied "Signing Secret"
- [ ] Stored securely (password manager or secure notes)

**Signing Secret (first 8 chars):** ________

---

## Step 6: Add Credentials to Railway

- [ ] Opened Railway dashboard
- [ ] Selected LogLens backend service
- [ ] Clicked "Variables" tab
- [ ] Added/updated environment variable:
  - [ ] Variable name: `SLACK_BOT_TOKEN`
  - [ ] Value: Bot token from Step 5
- [ ] Added/updated environment variable:
  - [ ] Variable name: `SLACK_SIGNING_SECRET`
  - [ ] Value: Signing secret from Step 5
- [ ] Saved changes
- [ ] Waited for Railway to redeploy (1-2 minutes)
- [ ] Deployment completed successfully

**Deployment Status:** https://railway.app/project/[project-id]/service/[service-id]

---

## Step 7: Verify Setup

### Basic Command Test
- [ ] Opened Slack workspace
- [ ] In any channel, typed `/loglens`
- [ ] Command appeared in autocomplete
- [ ] Pressed Enter to see usage hint

### Test Command Execution
- [ ] Ran test command:
  ```
  /loglens Test error | 2025-01-19T14:30:00Z | usr_test123
  ```
- [ ] Received response (formatted or "no events found")
- [ ] No error messages

---

## Testing Checklist

### Test 1: Valid Command Format
- [ ] Command: `/loglens User can't checkout | 2025-01-19T14:30:00Z | usr_abc123`
- [ ] Result: ✓ Success / ✗ Error
- [ ] Notes: _______________________________________________

### Test 2: Invalid Format (Missing Parts)
- [ ] Command: `/loglens Test error | 2025-01-19T14:30:00Z`
- [ ] Result: ✓ Returned usage instructions / ✗ Error
- [ ] Notes: _______________________________________________

### Test 3: Invalid Timestamp
- [ ] Command: `/loglens Test | not-a-date | usr_test`
- [ ] Result: ✓ Returned error message / ✗ Wrong response
- [ ] Notes: _______________________________________________

### Test 4: Real Customer Data (if available)
- [ ] Command: `/loglens [real-issue] | [real-time] | [real-customer-id]`
- [ ] Result: ✓ Success / ✗ Error
- [ ] Events found: _______________________________________________
- [ ] Notes: _______________________________________________

---

## Troubleshooting Completed

If you encountered issues, check off what you tried:

- [ ] Command not showing: Waited 10 minutes after install
- [ ] Command not showing: Reinstalled app
- [ ] Invalid signature: Verified signing secret matches exactly
- [ ] Timeout: Checked Railway backend health endpoint
- [ ] Timeout: Verified Request URL matches Railway URL
- [ ] No response: Verified bot token is correct
- [ ] No response: Verified `chat:write` scope is added
- [ ] No events found: Checked Sentry credentials in Railway
- [ ] No events found: Verified customer ID format

**Issues Resolved:** _______________________________________________

---

## Security Verification

- [ ] Bot token stored securely (not in code/repository)
- [ ] Signing secret stored securely (not in code/repository)
- [ ] Railway environment variables contain correct credentials
- [ ] Tested in non-production workspace first (recommended)
- [ ] Signature verification working (no "invalid signature" errors)

---

## Optional Configuration

### Custom Branding
- [ ] Updated app name (if desired)
- [ ] Updated app description
- [ ] Uploaded custom app icon (512x512 PNG)

### Channel Restrictions
- [ ] Configured channel restrictions (if needed)
- [ ] Added app to specific channels

### Monitoring Setup
- [ ] Checked Slack app usage logs
- [ ] Reviewed Railway logs for Slack commands
- [ ] Set up alerts for Slack integration errors (optional)

---

## Documentation Completed

- [ ] Read `SLACK_SETUP.md` guide
- [ ] Bookmarked Slack app dashboard
- [ ] Noted credentials location for future reference
- [ ] Shared usage instructions with CS team (if ready)

---

## Final Verification

- [ ] `/loglens` command works in Slack
- [ ] Response formatting looks correct
- [ ] Sentry links are clickable
- [ ] Error handling works properly
- [ ] Team trained on command usage (if applicable)

---

## Completion Sign-off

**Setup Completed:** ☐ Yes / ☐ No
**Date Completed:** ___________
**Tested By:** ___________
**Issues Found:** _______________________________________________
**Ready for Production:** ☐ Yes / ☐ No / ☐ Needs Testing

---

## Next Steps

After completing this checklist:

1. ✅ Update `docs/tasks.md` - Mark Task 7.3 as complete
2. ⏭️ Proceed to Task 8.1: End-to-End Integration Testing
3. ⏭️ Create internal CS team documentation
4. ⏭️ Set up monitoring and alerts
5. ⏭️ Train CS team on Slack command usage

---

## Reference Links

- **Slack Setup Guide:** `SLACK_SETUP.md`
- **Slack App Dashboard:** https://api.slack.com/apps
- **Railway Dashboard:** https://railway.app
- **Backend Health Check:** https://[your-railway-url]/health
- **Deployment Summary:** `DEPLOYMENT_SUMMARY.md`

---

**Last Updated:** 2026-01-20
**Task:** 7.3 - Configure Slack App
**Document Version:** 1.0
