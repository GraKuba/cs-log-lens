# Frontend Deployment Guide - Cloudflare Pages

This guide walks you through deploying the LogLens frontend to Cloudflare Pages.

## Prerequisites

- [x] Backend deployed to Railway (Task 7.1 completed)
- [x] GitHub repository with frontend code
- [x] Cloudflare account (free tier is sufficient)
- [x] Railway backend URL noted

## Step-by-Step Deployment

### 1. Get Your Backend URL

Before deploying the frontend, you need the Railway backend URL from Task 7.1.

```bash
# Your Railway backend URL should look like:
https://your-app-name.railway.app

# Or if you have a custom domain:
https://api.yourdomain.com
```

**Save this URL - you'll need it in step 4.**

### 2. Login to Cloudflare Pages

1. Go to https://dash.cloudflare.com/
2. Sign in (or create a free account)
3. Navigate to **Pages** in the left sidebar
4. Click **Create a project**

### 3. Connect Your GitHub Repository

1. Click **Connect to Git**
2. Authorize Cloudflare to access your GitHub account
3. Select your repository: `cs-log-lens`
4. Click **Begin setup**

### 4. Configure Build Settings

On the build configuration page, enter the following:

**Project Name:**
```
loglens-frontend
```
(or your preferred name - this will be part of your URL)

**Production Branch:**
```
main
```
(or your default branch name)

**Build Settings:**
- **Framework preset:** None (select from dropdown)
- **Build command:** (leave empty)
- **Build output directory:** `/`
- **Root directory:** `frontend`

**Environment Variables:**

Click **Add variable** and enter:

| Variable Name | Value |
|--------------|-------|
| `API_URL` | `https://your-railway-app.railway.app` |

**Replace `your-railway-app.railway.app` with your actual Railway backend URL from step 1.**

### 5. Deploy

1. Click **Save and Deploy**
2. Cloudflare will deploy your site (takes about 1-2 minutes)
3. Once complete, you'll see your site URL: `https://loglens-frontend.pages.dev`

### 6. Update Backend CORS Configuration

Now that you have your Cloudflare Pages URL, update your Railway backend to allow requests from it:

1. Go to your Railway project dashboard
2. Click on your backend service
3. Go to **Variables** tab
4. Find the `ALLOWED_ORIGINS` variable
5. Update it to include your Cloudflare Pages URL:

```bash
# If you had:
ALLOWED_ORIGINS=*

# Change to:
ALLOWED_ORIGINS=https://loglens-frontend.pages.dev

# Or if you have multiple origins:
ALLOWED_ORIGINS=https://loglens-frontend.pages.dev,https://custom-domain.com
```

6. Save the changes
7. Railway will automatically redeploy with the new CORS settings

### 7. Test Your Deployment

1. Visit your Cloudflare Pages URL: `https://loglens-frontend.pages.dev`
2. You should see the LogLens login screen
3. Enter your password (the one set in Railway's `APP_PASSWORD` variable)
4. Test the analysis form with sample data:
   - **Description:** "User can't checkout"
   - **Timestamp:** Current date/time
   - **Customer ID:** "usr_test123"

5. Verify:
   - ✅ Page loads correctly
   - ✅ Authentication works
   - ✅ API calls reach the backend
   - ✅ Results display correctly
   - ✅ HTTPS is enabled (lock icon in browser)
   - ✅ Mobile responsiveness (test on your phone)

### 8. Custom Domain (Optional)

If you want to use a custom domain instead of `.pages.dev`:

1. In Cloudflare Pages, go to your project
2. Click **Custom domains** tab
3. Click **Set up a custom domain**
4. Enter your domain (e.g., `loglens.yourdomain.com`)
5. Follow the DNS setup instructions
6. Once DNS propagates, update `ALLOWED_ORIGINS` in Railway to include your custom domain

## Environment Variable Configuration

The frontend uses the `API_URL` environment variable to determine which backend to call.

**How it works:**

The `app.js` file checks the environment at build time:

```javascript
const API_URL = window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : 'https://your-railway-app.railway.app';
```

However, since Cloudflare Pages doesn't do a build step for static sites, we need to update the code to use the environment variable at runtime.

**Update required:** See the next section for the code change.

## Code Updates for Deployment

### Update API_URL Configuration

We need to update `frontend/app.js` to use the Cloudflare Pages environment variable properly.

**Option 1: Replace hardcoded URL**

Simply update line 7 in `frontend/app.js`:

```javascript
// Before:
const API_URL = window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : 'https://your-railway-app.railway.app';

// After (replace with your actual Railway URL):
const API_URL = window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : 'https://your-actual-railway-url.railway.app';
```

**Option 2: Use a config file** (recommended for easier updates)

Create a `frontend/config.js` file (see Configuration Files section below).

## Automatic Deployments

Cloudflare Pages automatically redeploys when you push to your main branch:

1. Make changes to files in `/frontend` directory
2. Commit and push to GitHub
3. Cloudflare Pages automatically rebuilds and deploys
4. Changes live in 1-2 minutes

## Troubleshooting

### Issue: "Failed to fetch" or CORS errors

**Solution:** Check that `ALLOWED_ORIGINS` in Railway includes your Cloudflare Pages URL.

```bash
# In Railway, set:
ALLOWED_ORIGINS=https://your-site.pages.dev
```

### Issue: API calls go to wrong URL

**Solution:** Update the `API_URL` in `frontend/app.js` and push to GitHub.

### Issue: Page loads but shows old version

**Solution:** Cloudflare Pages caches aggressively. Try:
1. Hard refresh: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
2. Open in incognito/private mode
3. Wait a few minutes for cache to clear

### Issue: Authentication doesn't work

**Solution:** Check that the password you're entering matches the `APP_PASSWORD` set in Railway.

### Issue: Mobile view is broken

**Solution:** The CSS should be responsive. Check the browser console for errors and verify all CSS files loaded.

## Rollback

If you need to rollback to a previous version:

1. Go to Cloudflare Pages dashboard
2. Select your project
3. Click on **Deployments** tab
4. Find the previous successful deployment
5. Click the three dots menu → **Rollback to this deployment**

## Monitoring

### Check Deployment Status

- Cloudflare Pages dashboard shows all deployments
- Each deployment has logs you can view
- Failed deployments show error messages

### Check Site Health

Visit these endpoints to verify:

1. Frontend: `https://your-site.pages.dev`
2. Backend health: `https://your-railway-app.railway.app/health`

## Security Notes

### HTTPS

- Cloudflare Pages automatically provides HTTPS
- All traffic is encrypted with SSL/TLS
- Certificate is managed by Cloudflare (free)

### Authentication

- Frontend uses password authentication (stored in localStorage)
- Password is sent via `X-Auth-Token` header
- Backend validates password on each request

### Environment Variables

- Cloudflare Pages environment variables are **not** exposed to the client
- For client-side config, hardcode values or use a separate config file
- Never commit secrets to the repository

## Next Steps

After successful frontend deployment:

1. ✅ Mark Task 7.2 as completed in `docs/tasks.md`
2. ➡️ Proceed to Task 7.3: Configure Slack App
3. Document the deployment in `docs/2-history/`

## Configuration Files

See below for helper configuration files to add to your repository.

---

**Deployment Complete! 🎉**

Your LogLens frontend is now live and accessible to your CS team.
