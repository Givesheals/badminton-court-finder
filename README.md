# Badminton Court Finder

A web app to find available badminton courts in Cambridge by aggregating availability from multiple sports facilities.

**Live app (primary)**: [https://court-finder.streamlit.app](https://court-finder.streamlit.app) — Streamlit UI. **Fallback**: [GitHub Pages](https://givesheals.github.io/badminton-court-finder/) — static HTML.

**New to the repo?** Follow **[GETTING_STARTED.md](GETTING_STARTED.md)** for full setup (clone, `.env`, run API and Streamlit).

## Current setup

- **Frontend (primary)**: Streamlit on [Streamlit Community Cloud](https://share.streamlit.io) at [court-finder.streamlit.app](https://court-finder.streamlit.app). Root `requirements.txt` is minimal (streamlit + requests) for Cloud; backend/local use `requirements-backend.txt`.
- **Frontend (fallback)**: Static `index.html` on GitHub Pages; both call the same Flask API.
- **Backend**: Flask API on Render (Docker)
- **Database**: Neon PostgreSQL (production); SQLite (local dev). Data persists across deploys.
- **Scheduled scrapes**: GitHub Actions triggers `/api/scrape-all` every 6 hours (00:00, 06:00, 12:00, 18:00 UTC) after waking Render. Three facilities are scraped by default (Linton excluded due to bot protection); see `EXCLUDE_SCRAPE_FACILITIES`. See [SCHEDULED_SCRAPES.md](SCHEDULED_SCRAPES.md).

## Documentation

| Doc | Purpose |
|-----|---------|
| [GETTING_STARTED.md](GETTING_STARTED.md) | Local setup (clone, `.env`, run API and Streamlit) |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Deployment overview, env vars, troubleshooting |
| [DEPLOY_CHECKLIST.md](DEPLOY_CHECKLIST.md) | Render + frontend deployment checklist |
| [DEPLOY_INSTRUCTIONS.md](DEPLOY_INSTRUCTIONS.md) | Detailed step-by-step deployment walkthrough |
| [STREAMLIT_DEPLOY.md](STREAMLIT_DEPLOY.md) | Deploy Streamlit app to Community Cloud |
| [SCHEDULED_SCRAPES.md](SCHEDULED_SCRAPES.md) | How 6-hour scrapes work; GitHub Actions (recommended) vs cron-job.org |
| [CRONJOB_ORG_SETUP.md](CRONJOB_ORG_SETUP.md) | Legacy: step-by-step cron-job.org (scrape-all + keep-awake) |

## Features

- **Scheduled scraping**: All facilities (except excluded) scraped every 6 hours via GitHub Actions
- **Hybrid caching**: Uses DB cache; scrapes triggered by schedule or manual POST
- **Budget-safe**: Rate limiting and daily scrape limits prevent runaway costs
- **Circuit breaker**: Stops scraping after 3 consecutive errors per facility
- **REST API**: Query court availability and trigger scrapes

## Setup

**New to the project?** Follow **[GETTING_STARTED.md](GETTING_STARTED.md)** for a full step-by-step (clone, `.env`, run API, run Streamlit). The steps below are a short version.

### Local Development

1. Install dependencies:
```bash
pip install -r requirements-backend.txt
playwright install chromium
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env: add OPENAI_API_KEY (required for scraping) and any venue credentials (see .env.example)
```

3. Run database migration (if needed):
```bash
python migrate_db.py
```

4. Run the API:
```bash
python app.py
```

The API will be available at `http://localhost:5000`

5. Run the Streamlit frontend (main UI):
```bash
streamlit run streamlit_app.py
```
Open the URL shown (default `http://localhost:8501`). To use a remote backend (e.g. Render), open **Settings** and set **Backend API URL** to your API URL.

## API Endpoints

### Health Check
```
GET /health
```

### Get Availability
```
GET /api/availability?facility=Linton Village College&date=2026-02-06&start_time=15:00&end_time=18:00
```

Parameters:
- `facility` (required): Name of the facility
- `date` (optional): Filter by date (YYYY-MM-DD)
- `start_time` (optional): Filter by start time (HH:MM)
- `end_time` (optional): Filter by end time (HH:MM)

### List Facilities
```
GET /api/facilities
```

### Trigger Scrape (single facility)
```
POST /api/scrape
Body: {"facility": "Hill Roads Sport and Tennis Centre"}
```

### Trigger scrape-all (scheduled run)
```
POST /api/scrape-all
```
Starts background scrapes for all facilities except those in `EXCLUDE_SCRAPE_FACILITIES`. Returns 202 Accepted. Used by cron every 6 hours.

### Facility stats
```
GET /api/facility/<facility_name>/stats
```

## Configuration

Environment variables:
- `DATABASE_URL`: PostgreSQL connection URL (e.g. Neon). If set, app uses Postgres; otherwise SQLite (local).
- `EXCLUDE_SCRAPE_FACILITIES`: Comma-separated facility names to skip in scrape-all (default: Linton Village College, due to bot protection).
- `MAX_SCRAPES_PER_DAY`: Maximum scrapes per facility per day (default: 3)
- `MAX_SCRAPES_PER_HOUR`: Maximum scrapes per facility per hour (default: 1)
- `MIN_CACHE_AGE_SECONDS`: Minimum cache age before re-scraping (default: 3600 = 1 hour)
- `PORT`: Server port (default: 5000)
- `FLASK_DEBUG`: Enable debug mode (default: False)

### Scraping (LLM extraction)

All scrapers use **Playwright for navigation** and **OpenAI (LLM) for extracting** court availability from the page content. This avoids brittle fixed selectors when sites change layout.

- `OPENAI_API_KEY`: Your OpenAI API key (required for scraping). Set it in `.env` or in Render environment.
- Install the extra dependency: `pip install openai`. The LLM uses `gpt-4o-mini` by default (configurable in `scrapers/llm_extract.py`).

## Deployment

### Backend (Render)

1. Push code to GitHub
2. Sign up at https://render.com/ (use GitHub login)
3. Create new Web Service from your repository
4. Select Docker runtime
5. Set environment variables in Render dashboard (including `DATABASE_URL` for Neon — see [FREE_DB_ALTERNATIVES.md](FREE_DB_ALTERNATIVES.md))
6. Deploy (auto-builds from Dockerfile)

See [DEPLOYMENT.md](DEPLOYMENT.md) for architecture and env vars.

### Database (production)

Use Neon (free, persistent) or another Postgres. Set `DATABASE_URL` on Render to the connection URL. See [FREE_DB_ALTERNATIVES.md](FREE_DB_ALTERNATIVES.md).

### Scheduled scrapes (every 6 hours)

Use the GitHub Actions workflow (see [SCHEDULED_SCRAPES.md](SCHEDULED_SCRAPES.md)) to trigger `POST /api/scrape-all` every 6 hours after waking Render. Set the `RENDER_APP_URL` repo secret to your Render URL.

### Frontend (Streamlit – primary)

Live at **[https://court-finder.streamlit.app](https://court-finder.streamlit.app)**. To deploy or redeploy: see **[STREAMLIT_DEPLOY.md](STREAMLIT_DEPLOY.md)** (Streamlit Community Cloud, set `API_BASE_URL` to your Render URL). Root `requirements.txt` is minimal so Cloud installs without backend deps.

### Frontend (GitHub Pages – fallback)

1. Update API URL in `index.html` with your Render URL
2. Push to GitHub
3. Enable GitHub Pages in repository Settings → Pages
4. Select main branch, root folder

Your site will be at: `https://[username].github.io/badminton-court-finder/`

### Docker (Local Testing)

```bash
docker build -t badminton-court-finder .
docker run -p 5000:5000 --env-file .env badminton-court-finder
```

## Budget Safety Features

- **Daily Limits**: Max 3 scrapes per facility per day
- **Hourly Limits**: Max 1 scrape per facility per hour
- **Cache TTL**: 1 hour minimum cache age
- **Circuit Breaker**: Stops scraping after 3 consecutive errors
- **Graceful Degradation**: Returns cached data if scraping fails

## Project Structure

```
.
├── GETTING_STARTED.md      # Start here – setup guide for new developers
├── index.html              # Static frontend (GitHub Pages fallback)
├── streamlit_app.py        # Streamlit frontend (main UI; calls Flask API)
├── app.py                  # Flask API (Render); /api/scrape-all for scheduled runs
├── scraper_manager.py      # Scraper orchestration, rate limiting, circuit breaker
├── database.py             # SQLAlchemy models; Postgres (DATABASE_URL) or SQLite
├── scrapers/               # Facility-specific scrapers (Playwright nav + LLM extraction)
│   ├── hill_roads.py       # Hill Roads base (navigation)
│   ├── hill_roads_agent_scraper.py   # Hill Roads + LLM
│   ├── linton_village_college.py
│   ├── linton_agent_scraper.py
│   ├── one_leisure_st_ives.py
│   ├── one_leisure_agent_scraper.py
│   ├── trumpington_sport.py
│   ├── trumpington_agent_scraper.py
│   ├── llm_extract.py      # OpenAI-based slot extraction
│   └── README.md
├── scripts/
│   └── test_agent_scrape.py   # Test agent scrape for Hill Roads
├── .env.example            # Copy to .env and add your keys (do not commit .env)
├── Dockerfile              # Uses requirements-backend.txt (full deps for Render)
├── requirements.txt        # Minimal (Streamlit Cloud): streamlit + requests
├── requirements-backend.txt   # Full deps for API + local dev (Render, playwright, etc.)
├── DEPLOYMENT.md           # Deployment overview, env vars, troubleshooting
├── DEPLOY_CHECKLIST.md     # Render + frontend deployment checklist
├── DEPLOY_INSTRUCTIONS.md  # Detailed step-by-step (Render + GitHub Pages)
├── STREAMLIT_DEPLOY.md     # Deploy Streamlit to Community Cloud
├── SCHEDULED_SCRAPES.md    # Every-6h scrapes: overview and options
├── CRONJOB_ORG_SETUP.md    # Legacy: cron-job.org setup (step-by-step)
├── FREE_DB_ALTERNATIVES.md # Neon / Supabase (persistent free DB)
└── RENDER_POSTGRES_SETUP.md # Render Postgres (time-limited free)
```

## Adding New Facilities

1. Create a new scraper in `scrapers/` (e.g. follow `hill_roads.py` or `one_leisure_st_ives.py`).
2. Register it in `scraper_manager.py` in the `scrapers` dict.
3. Add the facility’s booking URL to `FACILITY_BOOKING_URLS` in `streamlit_app.py` and in `index.html`.
4. Deploy. The new facility is included in the next scheduled scrape-all (every 6 hours); no cron changes needed. To exclude it (e.g. if broken), add its name to `EXCLUDE_SCRAPE_FACILITIES` (env var, comma-separated).
