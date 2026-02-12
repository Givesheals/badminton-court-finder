# Badminton Court Finder

A web app to find available badminton courts in Cambridge by aggregating availability from multiple sports facilities.

**Live Demo**: [https://givesheals.github.io/badminton-court-finder/](https://givesheals.github.io/badminton-court-finder/)

## Current setup

- **Frontend**: Static HTML/CSS/JS on GitHub Pages
- **Backend**: Flask API on Render (Docker)
- **Database**: Neon PostgreSQL (production); SQLite (local dev). Data persists across deploys.
- **Scheduled scrapes**: cron-job.org POSTs to `/api/scrape-all` every 6 hours (00:00, 06:00, 12:00, 18:00 UTC). Hill Roads and One Leisure St Ives are scraped automatically; Linton Village College is excluded while that scraper is broken. See [SCHEDULED_SCRAPES.md](SCHEDULED_SCRAPES.md).

## Features

- **Scheduled scraping**: All facilities (except excluded) scraped every 6 hours via cron
- **Hybrid caching**: Uses DB cache; scrapes triggered by schedule or manual POST
- **Budget-safe**: Rate limiting and daily scrape limits prevent runaway costs
- **Circuit breaker**: Stops scraping after 3 consecutive errors per facility
- **REST API**: Query court availability and trigger scrapes

## Setup

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
playwright install chromium
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your credentials
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
- `EXCLUDE_SCRAPE_FACILITIES`: Comma-separated facility names to skip in scrape-all (default: `Linton Village College`).
- `MAX_SCRAPES_PER_DAY`: Maximum scrapes per facility per day (default: 3)
- `MAX_SCRAPES_PER_HOUR`: Maximum scrapes per facility per hour (default: 1)
- `MIN_CACHE_AGE_SECONDS`: Minimum cache age before re-scraping (default: 3600 = 1 hour)
- `PORT`: Server port (default: 5000)
- `FLASK_DEBUG`: Enable debug mode (default: False)

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

Use cron-job.org (free) to POST to `https://your-app.onrender.com/api/scrape-all` every 6 hours. See [SCHEDULED_SCRAPES.md](SCHEDULED_SCRAPES.md) for setup and overview.

### Frontend (GitHub Pages)

1. Update API URL in `index.html` with your Render URL
2. Push to GitHub
3. Enable GitHub Pages in repository Settings → Pages
4. Select main branch, root folder

Your site will be live at: `https://[username].github.io/badminton-court-finder/`

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
├── index.html              # Frontend UI (GitHub Pages)
├── app.py                  # Flask API (Render); /api/scrape-all for scheduled runs
├── scraper_manager.py      # Scraper orchestration, rate limiting, purge past slots
├── database.py             # SQLAlchemy models; Postgres (DATABASE_URL) or SQLite
├── scrapers/               # Facility-specific scrapers
│   ├── hill_roads.py
│   ├── linton_village_college.py   # Currently excluded (broken on Render)
│   ├── one_leisure_st_ives.py
│   ├── trumpington_sport.py
│   └── README.md           # Scraping policy and how to run
├── Dockerfile
├── requirements.txt
├── DEPLOYMENT.md            # Deployment architecture and env vars
├── SCHEDULED_SCRAPES.md     # Every-6h scrape setup (cron-job.org) and overview
├── FREE_DB_ALTERNATIVES.md # Neon / Supabase (persistent free DB)
└── RENDER_TEST.md          # Curl commands to test production API
```

## Adding New Facilities

1. Create a new scraper in `scrapers/` (e.g. follow `hill_roads.py` or `one_leisure_st_ives.py`).
2. Register it in `scraper_manager.py` in the `scrapers` dict.
3. Add the facility’s booking URL to `FACILITY_BOOKING_URLS` in `index.html`.
4. Deploy. The new facility is included in the next scheduled scrape-all (every 6 hours); no cron changes needed. To exclude it (e.g. if broken), add its name to `EXCLUDE_SCRAPE_FACILITIES` (env var, comma-separated).
