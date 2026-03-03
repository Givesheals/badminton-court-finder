# Deployment Guide

This project uses a split deployment architecture:
- **Backend API**: Hosted on Render
- **Frontend (primary)**: Streamlit app on [Streamlit Community Cloud](https://share.streamlit.io), live at **[https://court-finder.streamlit.app](https://court-finder.streamlit.app)**. See **[STREAMLIT_DEPLOY.md](STREAMLIT_DEPLOY.md)** to deploy or redeploy.
- **Frontend (fallback)**: Static `index.html` on GitHub Pages: `https://givesheals.github.io/badminton-court-finder/`

The Streamlit app is the intended main UI; the static site was deployed first and remains the fallback until Streamlit is deployed.

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
   DATABASE_URL=<Neon or Postgres connection URL>
   LVC_USERNAME=...
   LVC_PASSWORD=...
   PORT=5000
   ```
   Use Neon for a free, persistent DB; see [FREE_DB_ALTERNATIVES.md](FREE_DB_ALTERNATIVES.md). Add `OPENAI_API_KEY` (required for scraping). Optional: `EXCLUDE_SCRAPE_FACILITIES` (comma-separated; default: Linton Village College, due to bot protection).

4. **Deploy**: Render will auto-build from your Dockerfile

5. **Get URL**: Save your Render URL (e.g., `https://badminton-court-finder.onrender.com`)

### Frontend – Option A: Streamlit (primary UI)

Deploy the Streamlit app so the main UI is live. **See [STREAMLIT_DEPLOY.md](STREAMLIT_DEPLOY.md)** for full steps. In short: use [Streamlit Community Cloud](https://share.streamlit.io), connect the repo, set `API_BASE_URL` to your Render URL. Users then use the `*.streamlit.app` URL.

### Frontend – Option B: GitHub Pages (static fallback)

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

## Architecture

```
┌─────────────────────────────────────────────┐
│  User's Browser                             │
│  Streamlit: court-finder.streamlit.app     │
│  Fallback: givesheals.github.io/...        │
│  (Static HTML from GitHub Pages)            │
└────────────┬────────────────────────────────┘
             │ HTTPS API Calls
             ▼
┌─────────────────────────────────────────────┐
│  Backend API (Render)                       │
│  https://your-app.onrender.com              │
│  Flask + Playwright                         │
└────────────┬────────────────────────────────┘
             │
             │ DATABASE_URL
             ▼
┌─────────────────────────────────────────────┐
│  Database (Neon Postgres or Render Postgres)│
│  Persistent; data survives restarts          │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  cron-job.org (every 6h)                    │
│  POST /api/scrape-all → starts all scrapes  │
└────────────┬────────────────────────────────┘
             │
             ▼
       Backend API (same as above)
```

- **Database**: Set `DATABASE_URL` on Render (e.g. Neon connection URL). See [FREE_DB_ALTERNATIVES.md](FREE_DB_ALTERNATIVES.md).
- **Scheduled scrapes**: [SCHEDULED_SCRAPES.md](SCHEDULED_SCRAPES.md) (cron-job.org setup and overview).

## Cost Breakdown

| Service | Tier | Cost | Notes |
|---------|------|------|-------|
| Streamlit Community Cloud | Free | $0 | Primary frontend (court-finder.streamlit.app) |
| GitHub Pages | Free | $0 | Static fallback |
| Render Free | Free | $0 | Sleeps after 15min inactivity |
| Render Basic | Paid | $7/mo | Always-on, faster |

**Recommended**: Start with free tier, upgrade to Basic if cold starts are annoying.

## Environment Variables

### Required
- `DATABASE_URL`: PostgreSQL connection URL (e.g. Neon). Without this, the app uses SQLite (ephemeral on Render).
- `LVC_USERNAME`: Linton Village College username (for Linton scraper when enabled)
- `LVC_PASSWORD`: Linton Village College password
- `PORT`: 5000 (Render requires this)

### Required for scraping
- `OPENAI_API_KEY`: Your OpenAI API key. All scrapers use LLM extraction; add it in Render → Environment (see “Render: setting up scraping” below).

### Optional (with defaults)
- `EXCLUDE_SCRAPE_FACILITIES`: Comma-separated facility names to skip in scrape-all (default: Linton Village College, due to bot protection).
- `SCRAPE_DELAY_BETWEEN_FACILITIES_SECONDS`: Seconds to wait between facilities in scrape-all (default: 120). Reduces risk of being blocked by sites.
- `FLASK_DEBUG`: False
- `MAX_SCRAPES_PER_DAY`: 3
- `MAX_SCRAPES_PER_HOUR`: 1
- `MIN_CACHE_AGE_SECONDS`: 3600

## Testing Locally

Before deploying, test locally:

```bash
# Install dependencies
pip install -r requirements-backend.txt
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

## Render: setting up scraping

All scrapers use LLM extraction; you must set `OPENAI_API_KEY` on Render:

1. **Dashboard** → open your **Web Service** (the badminton court finder backend).
2. **Environment** (left sidebar or tab).
3. **Add environment variable** (or “Add Variable”):
   - **Key:** `OPENAI_API_KEY`
   - **Value:** your OpenAI API key (starts with `sk-...`). Use the same key you put in `.env` locally. Do not share it or commit it.
4. **Save Changes**. Render will redeploy; the new variables apply after the deploy finishes.

After deploy, scheduled scrape-all (and manual POST to `/api/scrape-all`) will scrape all four facilities using the agent (LLM) scrapers. To exclude a facility (e.g. temporarily), add its name to `EXCLUDE_SCRAPE_FACILITIES`.

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

### Dockerfile
The included Dockerfile is set up for Render:
- Multi-stage build for smaller image
- Playwright browsers pre-installed
- Use `DATABASE_URL` (Neon/Postgres) for persistent data; without it, SQLite is used (ephemeral on Render)
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

- **Production:** Set `DATABASE_URL` to a PostgreSQL URL (e.g. Neon — see [FREE_DB_ALTERNATIVES.md](FREE_DB_ALTERNATIVES.md)). Data then persists across restarts and deploys.
- **Local / no DATABASE_URL:** The app uses SQLite (`court_availability.db`). On Render without `DATABASE_URL`, the SQLite file is ephemeral and is lost on restart.

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
3. Update `FACILITY_BOOKING_URLS` in `streamlit_app.py` and `index.html`
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

