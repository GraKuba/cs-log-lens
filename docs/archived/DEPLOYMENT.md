# LogLens Deployment Guide

This guide covers deploying the LogLens MVP to production.

## Prerequisites

Before deploying, ensure you have:

1. **GitHub Repository**: Code must be pushed to GitHub
2. **Railway Account**: Sign up at [railway.app](https://railway.app)
3. **Cloudflare Account**: Sign up at [cloudflare.com](https://www.cloudflare.com/)
4. **API Keys Ready**:
   - Sentry auth token, org slug, and project slug
   - OpenAI API key
   - Slack bot token and signing secret (for Slack integration)
   - A secure password for the web app

## Part 1: Deploy Backend to Railway

### Step 1: Create New Project

1. Go to [railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Authenticate with GitHub if needed
5. Select your `cs-log-lens` repository

### Step 2: Configure Service

1. Railway will auto-detect the project as Python
2. Click on the service settings (gear icon)
3. Configure the following:

**Root Directory:**
```
backend
```

**Build Command** (should auto-detect, but verify):
```
pip install -r requirements.txt
```

**Start Command** (should auto-detect, but verify):
```
uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Step 3: Set Environment Variables

In the Railway dashboard, go to the "Variables" tab and add the following:

| Variable | Description | Example |
|----------|-------------|---------|
| `SENTRY_AUTH_TOKEN` | Your Sentry auth token | `sntrys_xxxxx` |
| `SENTRY_ORG` | Your Sentry organization slug | `my-org` |
| `SENTRY_PROJECT` | Your Sentry project slug | `my-project` |
| `OPENAI_API_KEY` | Your OpenAI API key | `sk-xxxxx` |
| `SLACK_BOT_TOKEN` | Slack bot token (optional for now) | `xoxb-xxxxx` |
| `SLACK_SIGNING_SECRET` | Slack signing secret (optional for now) | `xxxxx` |
| `APP_PASSWORD` | Shared password for web access | Choose a secure password |
| `ALLOWED_ORIGINS` | Frontend URL (set after frontend deploy) | `https://your-app.pages.dev` |
| `LOG_LEVEL` | Logging level (optional) | `INFO` |
| `RAILWAY_ENVIRONMENT` | Auto-set by Railway | `production` |

**Important Notes:**
- For `ALLOWED_ORIGINS`, you can initially set it to `*` to allow all origins during testing
- You'll update `ALLOWED_ORIGINS` after deploying the frontend
- Keep `APP_PASSWORD` secure and share it only with your CS team

### Step 4: Deploy

1. Click "Deploy" or wait for automatic deployment
2. Railway will build and deploy your backend
3. Once deployed, click on the service to see the deployment URL
4. Copy the URL (e.g., `https://your-app.railway.app`)

### Step 5: Verify Deployment

Test the health endpoint:

```bash
curl https://your-app.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

Test the analyze endpoint with authentication:

```bash
curl -X POST https://your-app.railway.app/analyze \
  -H "Content-Type: application/json" \
  -H "X-Auth-Token: YOUR_APP_PASSWORD" \
  -d '{
    "description": "User cannot complete checkout",
    "timestamp": "2025-01-19T14:30:00Z",
    "customer_id": "usr_test123"
  }'
```

### Step 6: Enable SSL

Railway automatically enables SSL/HTTPS for all deployments. Verify by visiting your URL with `https://`.

## Part 2: Deploy Frontend to Cloudflare Pages

### Step 1: Create New Project

1. Go to [dash.cloudflare.com](https://dash.cloudflare.com)
2. Navigate to "Workers & Pages"
3. Click "Create application"
4. Select "Pages" tab
5. Click "Connect to Git"
6. Authenticate with GitHub and select your repository

### Step 2: Configure Build Settings

| Setting | Value |
|---------|-------|
| Project name | `cs-log-lens` (or your choice) |
| Production branch | `main` |
| Framework preset | `None` |
| Build command | Leave empty |
| Build output directory | `/` |
| Root directory | `frontend` |

### Step 3: Set Environment Variables

Add the following environment variable:

| Variable | Value |
|----------|-------|
| `API_URL` | Your Railway backend URL (e.g., `https://your-app.railway.app`) |

**Note:** The frontend code is configured to use this environment variable. If you need to hardcode it for now, you can edit `frontend/app.js` and replace `API_URL` with your Railway URL.

### Step 4: Deploy

1. Click "Save and Deploy"
2. Cloudflare will deploy your frontend
3. Once deployed, you'll get a URL like `https://cs-log-lens.pages.dev`

### Step 5: Update Backend CORS

Now that you have your frontend URL, update the Railway backend:

1. Go back to Railway dashboard
2. Update the `ALLOWED_ORIGINS` environment variable to your Cloudflare Pages URL
3. Example: `https://cs-log-lens.pages.dev`
4. Railway will automatically redeploy with the new configuration

### Step 6: Test Frontend

1. Visit your Cloudflare Pages URL
2. Enter your `APP_PASSWORD`
3. Try submitting an analysis request
4. Verify you get results back

## Part 3: Configure Slack App (Optional)

If you want to enable the Slack integration:

### Step 1: Create Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App"
3. Choose "From scratch"
4. Name it "LogLens" and select your workspace

### Step 2: Add Slash Command

1. In your app settings, go to "Slash Commands"
2. Click "Create New Command"
3. Configure:
   - **Command:** `/loglens`
   - **Request URL:** `https://your-app.railway.app/slack/commands`
   - **Short Description:** "Analyze customer logs"
   - **Usage Hint:** `[description] | [timestamp] | [customer_id]`
4. Save

### Step 3: Add Bot Scopes

1. Go to "OAuth & Permissions"
2. Under "Scopes" → "Bot Token Scopes", add:
   - `commands`
   - `chat:write`
3. Save

### Step 4: Install App

1. Go to "Install App"
2. Click "Install to Workspace"
3. Authorize the app
4. Copy the "Bot User OAuth Token" (starts with `xoxb-`)

### Step 5: Get Signing Secret

1. Go to "Basic Information"
2. Under "App Credentials", find "Signing Secret"
3. Click "Show" and copy it

### Step 6: Update Railway Environment Variables

Add these to your Railway backend:

| Variable | Value |
|----------|-------|
| `SLACK_BOT_TOKEN` | Your bot token (`xoxb-xxxxx`) |
| `SLACK_SIGNING_SECRET` | Your signing secret |

Railway will automatically redeploy.

### Step 7: Test Slack Command

In your Slack workspace, try:

```
/loglens User can't checkout | 2025-01-19T14:30:00Z | usr_test123
```

You should see a formatted response with analysis results.

## Monitoring and Logs

### Railway Logs

1. Go to your Railway project
2. Click on your service
3. View real-time logs in the "Deployments" tab
4. Logs are JSON-formatted for easy parsing

### Cloudflare Pages Logs

1. Go to your Pages project
2. Click "View build logs" to see deployment logs
3. Function logs (if any) are available in the "Functions" tab

## Troubleshooting

### Backend Issues

**Health endpoint returns 500 error:**
- Check Railway logs for errors
- Verify all environment variables are set correctly
- Check that `SENTRY_AUTH_TOKEN`, `OPENAI_API_KEY` are valid

**CORS errors in frontend:**
- Verify `ALLOWED_ORIGINS` in Railway matches your Cloudflare Pages URL
- Include the protocol (`https://`) in the URL
- Try setting to `*` temporarily to debug

**Authentication errors:**
- Verify `APP_PASSWORD` is set in Railway
- Ensure frontend is sending the password in `X-Auth-Token` header

### Frontend Issues

**Cannot connect to API:**
- Check that `API_URL` environment variable is set in Cloudflare Pages
- Verify the Railway backend is deployed and accessible
- Check browser console for CORS errors

**Blank screen:**
- Check browser console for JavaScript errors
- Verify all files deployed correctly to Cloudflare Pages

### Slack Integration Issues

**Command not responding:**
- Check that Request URL in Slack app settings is correct
- Verify `SLACK_SIGNING_SECRET` is set in Railway
- Check Railway logs for signature verification errors

**Bot cannot send messages:**
- Verify `SLACK_BOT_TOKEN` is set and starts with `xoxb-`
- Check that bot has `chat:write` scope
- Reinstall the app if scopes were added after installation

## Security Checklist

Before going live:

- [ ] `APP_PASSWORD` is strong and secure
- [ ] `ALLOWED_ORIGINS` is set to specific domain (not `*`)
- [ ] All API keys are valid and not exposed in code
- [ ] `.env` file is in `.gitignore` and not committed
- [ ] HTTPS is enabled on both frontend and backend
- [ ] Slack signing secret validation is working
- [ ] Railway environment variables are not logged

## Rollback

If you need to rollback:

**Railway:**
1. Go to "Deployments" tab
2. Find a previous successful deployment
3. Click "Redeploy"

**Cloudflare Pages:**
1. Go to "Deployments" tab
2. Find a previous deployment
3. Click "Rollback to this deployment"

## Cost Estimates

**Railway:**
- Free tier: 500 hours/month ($5 credit)
- Pay-as-you-go: ~$5-10/month for low traffic

**Cloudflare Pages:**
- Free tier: Unlimited requests, 500 builds/month
- More than sufficient for internal CS tool

**Total estimated cost:** $0-10/month for MVP

## Next Steps

After deployment:

1. Test the complete flow with real customer data
2. Share the frontend URL and password with your CS team
3. Monitor Railway logs for errors
4. Set up alerts in Railway for downtime
5. Proceed to Task 8.1: End-to-End Integration Testing

## Support

If you encounter issues:
- Check Railway logs first
- Review this guide's troubleshooting section
- Check GitHub issues for similar problems
- Railway docs: [docs.railway.app](https://docs.railway.app)
- Cloudflare Pages docs: [developers.cloudflare.com/pages](https://developers.cloudflare.com/pages)
