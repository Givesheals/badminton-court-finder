# Deployment Guide

This project uses a split deployment architecture:
- **Backend API**: Hosted on Render
- **Frontend**: Streamlit app on [Streamlit Community Cloud](https://share.streamlit.io), live at **[https://court-finder.streamlit.app](https://court-finder.streamlit.app)**. See **[STREAMLIT_DEPLOY.md](STREAMLIT_DEPLOY.md)** to deploy or redeploy.

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

### Frontend (Streamlit)

Deploy the Streamlit app so the main UI is live. **See [STREAMLIT_DEPLOY.md](STREAMLIT_DEPLOY.md)** for full steps. In short: use [Streamlit Community Cloud](https://share.streamlit.io), connect the repo, set `API_BASE_URL` to your Render URL. Users then use the `*.streamlit.app` URL.

## Architecture

```
┌─────────────────────────────────────────────┐
│  User's Browser                             │
│  Streamlit: court-finder.streamlit.app     │
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
│  GitHub Actions (every 6h)                  │
│  Wake Render → POST /api/scrape-all (sequential) │
└────────────┬────────────────────────────────┘
             │
             ▼
       Backend API (same as above)
```

- **Database**: Set `DATABASE_URL` on Render (e.g. Neon connection URL). See [FREE_DB_ALTERNATIVES.md](FREE_DB_ALTERNATIVES.md).
- **Scheduled scrapes**: [SCHEDULED_SCRAPES.md](SCHEDULED_SCRAPES.md) (GitHub Actions workflow; set `RENDER_APP_URL` secret).

## Cost Breakdown

| Service | Tier | Cost | Notes |
|---------|------|------|-------|
| Streamlit Community Cloud | Free | $0 | Frontend (court-finder.streamlit.app) |
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
- `SCRAPE_CONCURRENT_MAX_WORKERS`: For **concurrent** scrape-all only (`?concurrent=1`): max parallel Playwright scrapes (default: **2**). Avoid raising on small Render instances (OOM risk).
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

# Run Streamlit: streamlit run streamlit_app.py (set API URL in Settings if needed)
```

## Render: setting up scraping

All scrapers use LLM extraction; you must set `OPENAI_API_KEY` on Render:

1. **Dashboard** → open your **Web Service** (the badminton court finder backend).
2. **Environment** (left sidebar or tab).
3. **Add environment variable** (or “Add Variable”):
   - **Key:** `OPENAI_API_KEY`
   - **Value:** your OpenAI API key (starts with `sk-...`). Use the same key you put in `.env` locally. Do not share it or commit it.
4. **Save Changes**. Render will redeploy; the new variables apply after the deploy finishes.

After deploy, scheduled scrape-all scrapes **all configured facilities** (except those in `EXCLUDE_SCRAPE_FACILITIES`) using the agent (LLM) scrapers, **one at a time**. To exclude a venue temporarily, add its name to `EXCLUDE_SCRAPE_FACILITIES`.

## Render memory (~512 MB)

The **free** Render web tier gives the API process on the order of **~512 MB RAM** (single instance; our Dockerfile uses **one Gunicorn worker**). **Playwright + Chromium is heavy**: each active scrape holds a full browser in that same process.

**Code and ops should assume:**

- **Do not** run “one browser per facility” in parallel on this stack— the OS will **SIGKILL** the worker (OOM), the service restarts, and scrapes fail mid-run (stale or missing “last updated” in the UI).
- **Scheduled** scrape-all (GitHub Actions) calls `POST /api/scrape-all` **without** `concurrent=1`, so scrapes run **sequentially**. Wall-clock time is longer; memory stays safe.
- **Manual** `POST /api/scrape-all?concurrent=1` uses a **bounded pool** (`SCRAPE_CONCURRENT_MAX_WORKERS`, default **2**). Increase only on a **larger Render plan** (or a dedicated scrape worker) after verifying headroom in metrics.
- When adding facilities or heavier scrapers, prefer **sequential** orchestration or **few parallel browsers**, not unbounded concurrency.

## Render-Specific Notes

### Free Tier Limitations
- Sleeps after 15 minutes of inactivity
- Cold start takes 30-60 seconds on first request
- 750 hours/month included (plenty for hobby projects)
- Shared CPU/RAM (**~512 MB** on the web service—see [Render memory (~512 MB)](#render-memory-512-mb) above)
- Slower than Basic; upgrade if you need more RAM or always-on

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
5. **OOM / “SIGKILL” / “Perhaps out of memory?”** — Usually too many **concurrent** Playwright scrapes. Ensure scheduled job does **not** use `?concurrent=1`; keep `SCRAPE_CONCURRENT_MAX_WORKERS` low (default 2). See [Render memory (~512 MB)](#render-memory-512-mb).

### Frontend Can't Connect to Backend
1. Check CORS is enabled (already in app.py)
2. In Streamlit, open Settings and verify Backend API URL points to your Render URL
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
Redeploy via Streamlit Community Cloud (see [STREAMLIT_DEPLOY.md](STREAMLIT_DEPLOY.md)); it rebuilds from your repo on push.

## Adding New Facilities

1. Create scraper in `scrapers/` directory
2. Add to `scraper_manager.py`
3. Update `FACILITY_BOOKING_URLS` in `streamlit_app.py`
4. Push to GitHub
5. Backend and Streamlit will auto-deploy

## Security Notes

- Never commit credentials to Git
- Use environment variables in Render
- HTTPS everywhere (Streamlit and Render both use HTTPS)
- Credentials stored as encrypted env vars in Render

## Next Steps

- [ ] Add more facility scrapers
- [ ] Set up uptime monitoring (e.g., UptimeRobot)
- [ ] Add Google Analytics (optional)
- [ ] Consider custom domain (optional)
- [ ] Add email notifications for new availability (future)

