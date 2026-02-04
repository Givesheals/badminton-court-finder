# Deployment Guide

This project uses a split deployment architecture:
- **Backend API**: Hosted on Render
- **Frontend**: Hosted on GitHub Pages

## Quick Start

### Backend (Render)

1. **Sign up at Render**: https://render.com/ (use GitHub login)

2. **Create Web Service**:
   - Connect your GitHub repository
   - Select `badminton-court-finder`
   - Runtime: Docker
   - Instance Type: Free or Basic ($7/month)

3. **Set Environment Variables**:
   ```
   LVC_USERNAME=theparker1337@gmail.com
   LVC_PASSWORD=CourtFinder123!
   PORT=5000
   ```

4. **Deploy**: Render will auto-build from your Dockerfile

5. **Get URL**: Save your Render URL (e.g., `https://badminton-court-finder.onrender.com`)

### Frontend (GitHub Pages)

1. **Update API URL** in `index.html`:
   ```javascript
   const API_URL = 'https://your-app-name.onrender.com';
   ```

2. **Push to GitHub**:
   ```bash
   git add index.html
   git commit -m "Update API URL"
   git push origin main
   ```

3. **Enable GitHub Pages**:
   - Go to Settings → Pages
   - Source: main branch, / (root)
   - Save

4. **Access**: Your site will be at `https://[username].github.io/badminton-court-finder/`

## Detailed Instructions

See [DEPLOY_INSTRUCTIONS.md](DEPLOY_INSTRUCTIONS.md) for step-by-step guide.

## Architecture

```
┌─────────────────────────────────────────────┐
│  User's Browser                             │
│  https://givesheals.github.io/...           │
│  (Static HTML/CSS/JS from GitHub Pages)     │
└────────────┬────────────────────────────────┘
             │
             │ HTTPS API Calls
             ▼
┌─────────────────────────────────────────────┐
│  Backend API                                │
│  https://your-app.onrender.com              │
│  (Flask + Playwright + SQLite on Render)    │
└─────────────────────────────────────────────┘
```

## Cost Breakdown

| Service | Tier | Cost | Notes |
|---------|------|------|-------|
| GitHub Pages | Free | $0 | Unlimited static hosting |
| Render Free | Free | $0 | Sleeps after 15min inactivity |
| Render Basic | Paid | $7/mo | Always-on, faster |

**Recommended**: Start with free tier, upgrade to Basic if cold starts are annoying.

## Environment Variables

### Required
- `LVC_USERNAME`: Linton Village College username
- `LVC_PASSWORD`: Linton Village College password
- `PORT`: 5000 (Render requires this)

### Optional (with defaults)
- `FLASK_DEBUG`: False
- `MAX_SCRAPES_PER_DAY`: 3
- `MAX_SCRAPES_PER_HOUR`: 1
- `MIN_CACHE_AGE_SECONDS`: 3600

## Testing Locally

Before deploying, test locally:

```bash
# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Run migration
python migrate_db.py

# Start API
python app.py

# In another terminal, test:
curl http://localhost:5000/health
curl http://localhost:5000/api/facilities

# Open index.html in browser (set API_URL to localhost)
```

## Render-Specific Notes

### Free Tier Limitations
- Sleeps after 15 minutes of inactivity
- Cold start takes 30-60 seconds on first request
- 750 hours/month included (plenty for hobby projects)
- Shared CPU/RAM (slower than Basic)

### Basic Tier Benefits ($7/month)
- Always-on (no sleep)
- Instant responses
- More CPU/RAM
- Better for regular users

### Dockerfile Optimization
The included Dockerfile is optimized for Render:
- Multi-stage build for smaller image
- Playwright browsers pre-installed
- SQLite database persists in container
- Python dependencies cached

## Monitoring

### Check Backend Health
```bash
curl https://your-app-name.onrender.com/health
```

### Check Logs
- Render: Dashboard → Your Service → Logs tab
- GitHub Pages: Usually just works, check browser console for errors

### Check Facility Stats
```bash
curl https://your-app-name.onrender.com/api/facility/Linton%20Village%20College/stats
```

## Troubleshooting

### Render Build Fails
1. Check build logs in Render dashboard
2. Common issues:
   - Dockerfile syntax errors
   - Missing system dependencies
   - Playwright installation fails

### Render App Crashes
1. Check deploy logs
2. Verify environment variables are set
3. Check database initialization
4. Look for Python exceptions

### Frontend Can't Connect to Backend
1. Check CORS is enabled (already in app.py)
2. Verify API_URL in index.html is correct
3. Check Render app is running (not sleeping)
4. Check browser console for errors

### Playwright Issues
- Ensure Dockerfile installs Chromium
- Check system dependencies are installed
- Render's environment should work out of the box

## Database Persistence

The app uses SQLite with a file-based database:
- File: `court_availability.db`
- Persists in Render's ephemeral storage
- Lost on container restart (acceptable for cache)
- For permanent storage, upgrade to PostgreSQL

## Rate Limiting & Budget Safety

Built-in protections:
- Max 3 scrapes per facility per day
- Max 1 scrape per facility per hour
- Minimum 1-hour cache TTL
- Circuit breaker after 3 consecutive errors

These limits prevent runaway costs from scraping.

## Updating After Deployment

### Update Backend
```bash
git add .
git commit -m "Update backend"
git push origin main
```
Render auto-deploys on push.

### Update Frontend
```bash
git add index.html
git commit -m "Update frontend"
git push origin main
```
GitHub Pages auto-deploys in 1-2 minutes.

## Adding New Facilities

1. Create scraper in `scrapers/` directory
2. Add to `scraper_manager.py`
3. Update `FACILITY_BOOKING_URLS` in `index.html`
4. Push to GitHub
5. Both backend and frontend will auto-deploy

## Security Notes

- Never commit credentials to Git
- Use environment variables in Render
- HTTPS everywhere (GitHub Pages and Render both use HTTPS)
- Credentials stored as encrypted env vars in Render

## Next Steps

- [ ] Add more facility scrapers
- [ ] Set up uptime monitoring (e.g., UptimeRobot)
- [ ] Add Google Analytics (optional)
- [ ] Consider custom domain (optional)
- [ ] Add email notifications for new availability (future)

## Support

For detailed step-by-step instructions, see:
- [DEPLOY_INSTRUCTIONS.md](DEPLOY_INSTRUCTIONS.md) - Beginner-friendly guide
- [RAILWAY_DEPLOY.md](RAILWAY_DEPLOY.md) - Alternative to Render (also free tier)
