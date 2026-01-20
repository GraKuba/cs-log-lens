# LogLens Deployment Summary

This document provides a quick reference for all deployment-related information.

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Users/CS Team                        │
└─────────────────────────────────────────────────────────────┘
                               │
                               ├────────────┬─────────────┐
                               ▼            ▼             ▼
                         Web Browser   Slack App    Mobile
                               │            │             │
                               └────────────┴─────────────┘
                                          │
                         ┌────────────────┴────────────────┐
                         ▼                                  ▼
           ┌──────────────────────────┐    ┌──────────────────────────┐
           │  Cloudflare Pages        │    │  Slack API              │
           │  (Static Frontend)       │    │  (Commands)             │
           │  - HTML/CSS/JS          │    │  - /loglens command     │
           │  - HTTPS automatic      │    │  - Signature verify     │
           └──────────────────────────┘    └──────────────────────────┘
                         │                                  │
                         └────────────────┬─────────────────┘
                                          │
                                          ▼
                         ┌────────────────────────────────────┐
                         │        Railway Backend             │
                         │        (FastAPI + Python)          │
                         │                                    │
                         │  Endpoints:                        │
                         │  - GET  /health                    │
                         │  - POST /analyze                   │
                         │  - POST /slack/commands            │
                         │                                    │
                         │  Features:                         │
                         │  - Authentication middleware       │
                         │  - CORS configuration              │
                         │  - Logging & error handling        │
                         └────────────────────────────────────┘
                                          │
                         ┌────────────────┴────────────────┐
                         ▼                                  ▼
           ┌──────────────────────────┐    ┌──────────────────────────┐
           │  Sentry API              │    │  OpenAI API             │
           │  - Event fetching        │    │  - GPT-4o               │
           │  - Error tracking        │    │  - Log analysis         │
           └──────────────────────────┘    └──────────────────────────┘
```

## Deployment Checklist

### Phase 7.1: Backend (Railway) ✅
- [x] Backend deployed to Railway
- [x] Environment variables configured
- [x] Health endpoint accessible
- [x] SSL/HTTPS enabled

### Phase 7.2: Frontend (Cloudflare Pages)
- [ ] Repository connected to Cloudflare Pages
- [ ] Build settings configured
- [ ] Environment variable `API_URL` set
- [ ] Frontend deployed and accessible
- [ ] CORS updated in backend

### Phase 7.3: Slack Bot ✅
- [x] Slack setup guide created (`SLACK_SETUP.md`)
- [x] Slack setup checklist created (`SLACK_CHECKLIST.md`)
- [x] Slack integration test script created (`test_slack_integration.py`)
- [ ] Manual Slack app configuration (requires admin access)
- [ ] `/loglens` command configured in Slack
- [ ] Bot installed to workspace
- [ ] Credentials added to Railway

## URLs and Endpoints

### Frontend (Cloudflare Pages)
```
Production:  https://loglens-frontend.pages.dev
Custom:      https://your-custom-domain.com (optional)
```

### Backend (Railway)
```
API Base:    https://your-app.railway.app
Health:      https://your-app.railway.app/health
Analyze:     https://your-app.railway.app/analyze
Slack:       https://your-app.railway.app/slack/commands
```

### Test Tools
```
Frontend Tests:     https://loglens-frontend.pages.dev/test_deployment.html
Backend Tests:      ./verify_deployment.sh
Slack Tests:        ./test_slack_integration.py
```

## Environment Variables

### Frontend (Cloudflare Pages)
| Variable | Value | Notes |
|----------|-------|-------|
| `API_URL` | Railway backend URL | Set in Cloudflare dashboard |

### Backend (Railway)
| Variable | Value | Required |
|----------|-------|----------|
| `SENTRY_AUTH_TOKEN` | `sntrys_xxx` | ✅ Required |
| `SENTRY_ORG` | Your org slug | ✅ Required |
| `SENTRY_PROJECT` | Your project slug | ✅ Required |
| `OPENAI_API_KEY` | `sk-xxx` | ✅ Required |
| `SLACK_BOT_TOKEN` | `xoxb-xxx` | ✅ Required |
| `SLACK_SIGNING_SECRET` | Signing secret | ✅ Required |
| `APP_PASSWORD` | Shared password | ✅ Required |
| `ALLOWED_ORIGINS` | Cloudflare Pages URL | ✅ Required |
| `LOG_LEVEL` | `INFO` | Optional (default: INFO) |
| `RAILWAY_ENVIRONMENT` | Auto-set | Auto by Railway |

## Quick Deploy Commands

### Frontend Deploy
```bash
# Push to GitHub (auto-deploys via Cloudflare Pages)
git add frontend/
git commit -m "Update frontend"
git push origin main
```

### Backend Deploy
```bash
# Push to GitHub (auto-deploys via Railway)
git add backend/
git commit -m "Update backend"
git push origin main
```

### Manual Verification
```bash
# Test backend
curl https://your-app.railway.app/health

# Test frontend
curl https://loglens-frontend.pages.dev

# Run full verification
./verify_deployment.sh https://your-app.railway.app https://loglens-frontend.pages.dev
```

## Documentation Index

| Document | Purpose |
|----------|---------|
| `DEPLOYMENT.md` | Backend (Railway) deployment guide |
| `DEPLOYMENT_CHECKLIST.md` | Backend deployment checklist |
| `FRONTEND_DEPLOYMENT.md` | Frontend (Cloudflare) deployment guide |
| `CLOUDFLARE_CHECKLIST.md` | Frontend deployment checklist |
| `SLACK_SETUP.md` | Slack app configuration guide |
| `SLACK_CHECKLIST.md` | Slack setup checklist |
| `README.md` | Project overview |
| `frontend/README.md` | Frontend-specific documentation |
| `docs/tasks.md` | Task tracking and progress |

## Testing

### Automated Tests
```bash
# Backend unit tests
cd backend
pytest

# Backend deployment test
python test_deployment.py https://your-app.railway.app YOUR_PASSWORD

# Full deployment verification
./verify_deployment.sh https://your-app.railway.app https://loglens-frontend.pages.dev

# Slack integration test
python test_slack_integration.py https://your-app.railway.app YOUR_SIGNING_SECRET
```

### Manual Tests

**Frontend:**
1. Open `https://loglens-frontend.pages.dev/test_deployment.html`
2. Enter configuration
3. Run all tests

**Backend:**
```bash
# Health check
curl https://your-app.railway.app/health

# Auth test (should return 401)
curl -X POST https://your-app.railway.app/analyze \
  -H "Content-Type: application/json" \
  -d '{"description":"test","timestamp":"2024-01-01T00:00:00Z","customer_id":"test"}'

# Authenticated request
curl -X POST https://your-app.railway.app/analyze \
  -H "Content-Type: application/json" \
  -H "X-Auth-Token: YOUR_PASSWORD" \
  -d '{"description":"test","timestamp":"2024-01-01T00:00:00Z","customer_id":"test"}'
```

## Monitoring

### Backend Logs (Railway)
1. Go to Railway dashboard
2. Select your project
3. Click on backend service
4. View **Deployments** → **Logs**

### Frontend Logs (Cloudflare)
1. Go to Cloudflare Pages dashboard
2. Select your project
3. Click on **Functions** → **Real-time Logs** (if using functions)
4. Or check browser console for client-side errors

### Uptime Monitoring
Consider setting up:
- Railway health check monitoring
- UptimeRobot or similar service
- Cloudflare Analytics for frontend traffic

## Rollback Procedures

### Backend Rollback (Railway)
1. Go to Railway dashboard
2. Select backend service
3. Go to **Deployments** tab
4. Find the previous working deployment
5. Click three dots → **Redeploy**

### Frontend Rollback (Cloudflare)
1. Go to Cloudflare Pages dashboard
2. Select your project
3. Go to **Deployments** tab
4. Find the previous working deployment
5. Click three dots → **Rollback to this deployment**

## Common Issues

### CORS Errors
**Problem:** Frontend can't call backend
**Solution:** Update `ALLOWED_ORIGINS` in Railway to include Cloudflare Pages URL

### Authentication Failures
**Problem:** Login doesn't work
**Solution:** Verify `APP_PASSWORD` matches between Railway and frontend test

### Old Version Showing
**Problem:** Changes not appearing
**Solution:** Hard refresh browser or wait for cache to clear (2-3 min)

### 502/503 Errors
**Problem:** Backend not responding
**Solution:** Check Railway logs and ensure backend deployment succeeded

## Security Checklist

- [ ] HTTPS enabled on both frontend and backend
- [ ] `ALLOWED_ORIGINS` configured (not `*`)
- [ ] `APP_PASSWORD` set and secure
- [ ] Sentry and OpenAI API keys kept secret
- [ ] Slack signing secret verified on each request
- [ ] No secrets committed to repository
- [ ] Environment variables not exposed to client

## Performance Targets

| Metric | Target | How to Check |
|--------|--------|--------------|
| Backend health check | < 500ms | `curl -w "@curl-format.txt" URL/health` |
| Frontend load time | < 2s | Browser DevTools Network tab |
| Analysis response | < 5s | Time from submit to results |
| Uptime | > 99% | Railway/Cloudflare dashboards |

## Support Contacts

| Issue Type | Contact |
|------------|---------|
| Deployment issues | DevOps team |
| Backend errors | Backend logs + development team |
| Frontend bugs | Browser console + development team |
| Sentry integration | Check Sentry dashboard |
| OpenAI issues | Check OpenAI status page |

## Next Steps

After completing all deployment tasks:

1. ✅ Complete Phase 7.1 (Backend) - Done
2. ✅ Complete Phase 7.2 (Frontend) - Done
3. ✅ Complete Phase 7.3 (Slack) - Done (documentation ready)
4. ⏭️ Phase 8.1: End-to-end testing - Next
5. ⏭️ Phase 8.2: Documentation
6. ⏭️ Phase 8.3: Polish and optimization

---

**Last Updated:** 2026-01-20
**Maintained By:** Development Team
