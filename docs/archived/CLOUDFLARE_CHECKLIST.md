# Cloudflare Pages Deployment Checklist

Use this checklist to track your frontend deployment progress.

## Pre-Deployment

- [ ] Backend deployed to Railway (Task 7.1 completed)
- [ ] Railway backend URL noted: `___________________________`
- [ ] Cloudflare account created/accessed
- [ ] GitHub repository accessible

## Cloudflare Pages Setup

- [ ] Logged into Cloudflare Dashboard (https://dash.cloudflare.com/)
- [ ] Navigated to Pages section
- [ ] Clicked "Create a project"
- [ ] Connected to Git provider (GitHub)
- [ ] Authorized Cloudflare to access GitHub
- [ ] Selected repository: `cs-log-lens`

## Build Configuration

- [ ] Project name set: `loglens-frontend` (or your choice)
- [ ] Production branch set: `main`
- [ ] Framework preset: `None`
- [ ] Build command: (left empty)
- [ ] Build output directory: `/`
- [ ] Root directory: `frontend`

## Environment Variables

- [ ] Added variable: `API_URL`
- [ ] Set value to Railway backend URL: `https://___________________________`

## Deployment

- [ ] Clicked "Save and Deploy"
- [ ] Deployment started successfully
- [ ] Deployment completed (1-2 minutes)
- [ ] Noted Cloudflare Pages URL: `https://___________________________`

## Backend CORS Update

- [ ] Opened Railway dashboard
- [ ] Selected backend service
- [ ] Opened Variables tab
- [ ] Updated `ALLOWED_ORIGINS` with Cloudflare Pages URL
- [ ] Saved changes
- [ ] Backend redeployed automatically

## Testing

### Basic Functionality
- [ ] Visited Cloudflare Pages URL
- [ ] Page loads correctly (no console errors)
- [ ] HTTPS enabled (lock icon in browser)
- [ ] Login screen appears

### Authentication
- [ ] Entered password (from Railway `APP_PASSWORD`)
- [ ] Successfully authenticated
- [ ] Redirected to analysis form

### API Integration
- [ ] Submitted test analysis:
  - Description: "User can't checkout"
  - Timestamp: (current date/time)
  - Customer ID: "usr_test123"
- [ ] Loading spinner appeared
- [ ] Results displayed correctly
- [ ] No CORS errors in console
- [ ] Sentry links clickable

### Error Handling
- [ ] Tested with wrong password (shows error)
- [ ] Tested with invalid customer ID (shows "no events" message)
- [ ] Error messages display correctly

### Mobile Testing
- [ ] Opened on mobile device (or DevTools mobile view)
- [ ] Page is responsive
- [ ] All buttons clickable
- [ ] Form inputs work correctly
- [ ] Results readable on small screen

## Security Verification

- [ ] HTTPS certificate valid (no warnings)
- [ ] Security headers present (check DevTools Network tab)
- [ ] No sensitive data in URL parameters
- [ ] localStorage used correctly for auth token

## Optional: Custom Domain

- [ ] Custom domain configured (if using)
- [ ] DNS records updated
- [ ] SSL certificate active for custom domain
- [ ] `ALLOWED_ORIGINS` updated to include custom domain

## Documentation

- [ ] Updated `docs/tasks.md` with completion status
- [ ] Created history log in `docs/2-history/`
- [ ] Documented deployment URLs in `README.md`

## Post-Deployment

- [ ] Shared URL with CS team
- [ ] Verified team can access and use the tool
- [ ] Set up monitoring/alerts (optional)
- [ ] Scheduled follow-up to gather feedback

---

## Troubleshooting

If you encounter issues, refer to the **Troubleshooting** section in `FRONTEND_DEPLOYMENT.md`.

Common issues:
- **CORS errors**: Update `ALLOWED_ORIGINS` in Railway
- **Old version showing**: Hard refresh or wait for cache to clear
- **API calls fail**: Check Railway backend is running via `/health` endpoint
- **Authentication fails**: Verify password matches `APP_PASSWORD` in Railway

---

**Status:**
- [ ] Not Started
- [ ] In Progress
- [ ] Blocked (reason: _________________)
- [ ] Complete ✅

**Deployed URL:** `___________________________`

**Deployment Date:** `___________________________`

**Deployed By:** `___________________________`
