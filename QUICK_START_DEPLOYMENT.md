# Quick Start: Deploying LogLens

This guide will get you from zero to deployed in ~30 minutes.

## Prerequisites Checklist

Have these ready before starting:

- [ ] GitHub account (with this repo pushed)
- [ ] Railway account (sign up at [railway.app](https://railway.app))
- [ ] Cloudflare account (sign up at [cloudflare.com](https://www.cloudflare.com/))
- [ ] Sentry auth token ([get it here](https://sentry.io/settings/account/api/auth-tokens/))
- [ ] Sentry org slug (find in your Sentry URL: `sentry.io/organizations/YOUR-ORG-SLUG/`)
- [ ] Sentry project slug (find in your Sentry URL: `sentry.io/organizations/ORG/projects/YOUR-PROJECT-SLUG/`)
- [ ] OpenAI API key ([get it here](https://platform.openai.com/api-keys))
- [ ] A strong password for the app (create a new one, don't reuse!)

## Step 1: Push to GitHub (1 minute)

If not already done:

```bash
git add -A
git commit -m "Ready for deployment"
git push origin main
```

## Step 2: Deploy Backend to Railway (10 minutes)

1. **Go to Railway:**
   - Visit [railway.app](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your `cs-log-lens` repository

2. **Configure:**
   - Click on the service settings (gear icon)
   - Set "Root Directory" to: `backend`
   - Verify "Build Command": `pip install -r requirements.txt`
   - Verify "Start Command": `uvicorn main:app --host 0.0.0.0 --port $PORT`

3. **Add Environment Variables:**
   - Go to "Variables" tab
   - Add these variables (click "Add Variable" for each):

   ```
   SENTRY_AUTH_TOKEN=<your-token>
   SENTRY_ORG=<your-org-slug>
   SENTRY_PROJECT=<your-project-slug>
   OPENAI_API_KEY=<your-openai-key>
   APP_PASSWORD=<create-a-strong-password>
   ALLOWED_ORIGINS=*
   LOG_LEVEL=INFO
   ```

   Note: We'll update `ALLOWED_ORIGINS` after deploying the frontend.

4. **Deploy:**
   - Railway will automatically deploy
   - Wait for "Success" message (takes 2-3 minutes)
   - Copy your Railway URL (looks like: `https://your-app.railway.app`)

5. **Test:**
   ```bash
   curl https://your-app.railway.app/health
   ```

   Should return: `{"status":"healthy","version":"0.1.0"}`

## Step 3: Deploy Frontend to Cloudflare Pages (10 minutes)

1. **Go to Cloudflare:**
   - Visit [dash.cloudflare.com](https://dash.cloudflare.com)
   - Navigate to "Workers & Pages"
   - Click "Create application" → "Pages" → "Connect to Git"

2. **Configure:**
   - Select your `cs-log-lens` repository
   - **Project name:** `cs-log-lens` (or your choice)
   - **Production branch:** `main`
   - **Framework preset:** `None`
   - **Build command:** Leave empty
   - **Build output directory:** `/`
   - **Root directory:** `frontend`

3. **Add Environment Variable:**
   - Click "Environment variables"
   - Add: `API_URL` = `<your-railway-url>` (the URL from Step 2)
   - Example: `https://your-app.railway.app`

4. **Deploy:**
   - Click "Save and Deploy"
   - Wait for "Success" (takes 1-2 minutes)
   - Copy your Cloudflare Pages URL (looks like: `https://cs-log-lens.pages.dev`)

5. **Update Backend CORS:**
   - Go back to Railway dashboard
   - Find `ALLOWED_ORIGINS` variable
   - Change from `*` to your Cloudflare Pages URL
   - Railway will automatically redeploy

## Step 4: Test Everything (5 minutes)

1. **Open your Cloudflare Pages URL in browser**
   - Enter the password you set in `APP_PASSWORD`
   - You should see the analysis form

2. **Run automated tests:**
   ```bash
   cd backend
   python test_deployment.py https://your-app.railway.app your-password
   ```

   All 5 tests should pass:
   - ✅ SSL Enabled
   - ✅ Health Endpoint
   - ✅ CORS Headers
   - ✅ Auth Middleware (Reject)
   - ✅ Auth Middleware (Accept)

3. **Try analyzing a log:**
   - Fill out the form with test data:
     - Description: "User can't complete checkout"
     - Timestamp: Use the date/time picker (any recent time)
     - Customer ID: A valid customer ID from your Sentry (e.g., `usr_test123`)
   - Click "Analyze Logs"
   - If you have events in Sentry, you should see results!

## Step 5: Share with Your Team (2 minutes)

Share these with your CS team:

**Frontend URL:** `https://your-app.pages.dev`
**Password:** `your-app-password` (share securely!)

**Usage Instructions:**
1. Open the URL in your browser
2. Enter the password (only needed once)
3. Fill in the form with customer issue details
4. Click "Analyze Logs"
5. Review the results and copy the suggested response

## Optional: Add Slack Integration

If you want to use `/loglens` command in Slack, follow the Slack setup guide in [DEPLOYMENT.md](DEPLOYMENT.md) Part 3.

## Troubleshooting

**"No events found" error:**
- Use a customer ID that has events in Sentry
- Make sure the timestamp is within ±5 minutes of actual errors
- Check your Sentry configuration

**CORS errors:**
- Verify `ALLOWED_ORIGINS` in Railway matches your Cloudflare URL exactly
- Make sure you include `https://` in the URL

**Authentication errors:**
- Make sure you're using the same password you set in Railway
- Clear browser cache and try again

**Frontend not loading:**
- Check Cloudflare Pages deployment logs
- Make sure `API_URL` is set correctly
- Try opening browser console to see errors

For more troubleshooting, see [DEPLOYMENT.md](DEPLOYMENT.md).

## What's Next?

- ✅ Backend deployed to Railway
- ✅ Frontend deployed to Cloudflare Pages
- ✅ Team has access to the tool

**Next steps:**
1. Monitor usage in Railway logs
2. Test with real customer issues
3. Update knowledge base files (`backend/docs/workflow.md` and `known_errors.md`) as you learn more
4. Optionally: Set up Slack integration

**Task status:**
- ✅ Task 7.1: Deploy Backend to Railway (complete)
- ✅ Task 7.2: Deploy Frontend to Cloudflare Pages (complete)
- Next: Task 8.1 - End-to-End Integration Testing

## Cost

**Monthly costs:**
- Railway: ~$5-10/month (or free with $5 credit)
- Cloudflare Pages: $0 (free tier)
- **Total: ~$0-10/month**

## Getting Help

- **Full deployment guide:** [DEPLOYMENT.md](DEPLOYMENT.md)
- **Deployment checklist:** [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)
- **Project documentation:** [README.md](README.md)
- **Railway docs:** [docs.railway.app](https://docs.railway.app)
- **Cloudflare docs:** [developers.cloudflare.com/pages](https://developers.cloudflare.com/pages)

---

**Total time:** ~30 minutes
**Difficulty:** Easy
**Result:** Production-ready log analysis tool! 🎉
