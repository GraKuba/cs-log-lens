# LogLens Frontend

This directory contains the static frontend for LogLens - a simple, vanilla JavaScript web application for CS teams to analyze customer logs.

## Structure

```
frontend/
├── index.html           # Main HTML file
├── app.js              # Application logic
├── style.css           # Styles
├── config.example.js   # Configuration template
├── test_deployment.html # Deployment testing tool
└── test_*.html/js      # Unit tests
```

## Local Development

### Prerequisites

- A web browser
- A simple HTTP server (Python, Node.js, or any other)

### Setup

1. **Start the backend** (from `/backend` directory):
   ```bash
   cd backend
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   uvicorn main:app --reload --port 8000
   ```

2. **Start the frontend** (from `/frontend` directory):
   ```bash
   # Using Python
   python -m http.server 3000

   # Or using Node.js
   npx http-server -p 3000
   ```

3. **Open in browser**:
   ```
   http://localhost:3000
   ```

### Testing Locally

The `app.js` automatically detects localhost and uses `http://localhost:8000` as the API URL.

## Deployment

### Cloudflare Pages

The frontend is designed to deploy to Cloudflare Pages with zero build steps.

**Quick Deploy:**

1. Push code to GitHub
2. Connect repository to Cloudflare Pages
3. Configure:
   - Root directory: `frontend`
   - Build command: (none)
   - Build output: `/`
4. Set environment variable: `API_URL` (Railway backend URL)
5. Deploy

**Detailed Instructions:** See `/FRONTEND_DEPLOYMENT.md`

**Checklist:** See `/CLOUDFLARE_CHECKLIST.md`

### Configuration

Update the API URL in `app.js` line 5-7:

```javascript
const API_URL = window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : 'https://your-railway-app.railway.app'; // Update this
```

Or use the config file approach (see `config.example.js`).

## Testing

### Unit Tests

Run the test files in your browser:

- `test_auth.html` - Authentication tests
- `test_analysis_form.html` - Form submission tests
- `test_results_display.html` - Results display tests
- `test_error_states.html` - Error handling tests
- `test_error_integration.html` - Integration tests

### Deployment Tests

Use `test_deployment.html` to verify your deployed frontend works correctly.

1. Open `test_deployment.html` in your browser
2. Enter your Cloudflare Pages URL
3. Enter your Railway backend URL
4. Enter your auth password
5. Run all tests

## Features

### Authentication
- Simple password-based authentication
- Password stored in localStorage
- Automatic re-authentication on 401

### Analysis Form
- Three fields: description, timestamp, customer ID
- Client-side validation
- Loading states
- Error handling

### Results Display
- Ranked probable causes with confidence levels
- Suggested customer response (with copy button)
- Sentry event links
- Logs summary

### Mobile Support
- Responsive design
- Works on all screen sizes
- Touch-friendly interface

## Security

- HTTPS enforced in production
- Password authentication required
- XSS prevention through HTML escaping
- Secure external links (`rel="noopener noreferrer"`)
- CORS configured on backend

## Browser Support

- Chrome/Edge (last 2 versions)
- Firefox (last 2 versions)
- Safari (last 2 versions)
- Mobile browsers (iOS Safari, Chrome Android)

## Dependencies

**None!** This is vanilla JavaScript with no build step or dependencies.

## Troubleshooting

### "Failed to fetch" errors

**Cause:** CORS not configured or backend not running

**Solution:**
1. Verify backend is running: `curl https://your-backend.railway.app/health`
2. Check `ALLOWED_ORIGINS` in Railway includes your frontend URL
3. Hard refresh browser: Ctrl+Shift+R (or Cmd+Shift+R on Mac)

### Authentication fails

**Cause:** Wrong password or backend issue

**Solution:**
1. Verify password matches `APP_PASSWORD` in Railway
2. Check browser console for error details
3. Try clearing localStorage: `localStorage.clear()` in console

### Old version showing after deploy

**Cause:** Browser cache or Cloudflare cache

**Solution:**
1. Hard refresh: Ctrl+Shift+R (or Cmd+Shift+R on Mac)
2. Open in incognito/private mode
3. Wait 2-3 minutes for cache to clear

### Mobile layout broken

**Cause:** CSS not loading or syntax error

**Solution:**
1. Check browser console for errors
2. Verify `style.css` is accessible
3. Test in Chrome DevTools mobile view

## Contributing

When making changes:

1. Test locally first
2. Run all test files in browser
3. Test on mobile (or DevTools mobile view)
4. Update tests if adding new features
5. Push to GitHub (triggers auto-deploy on Cloudflare)

## License

Internal tool - not for public distribution.

## Support

For issues or questions:
- Check `/FRONTEND_DEPLOYMENT.md` for deployment help
- Check backend logs in Railway
- Check browser console for client-side errors
- Contact the development team
