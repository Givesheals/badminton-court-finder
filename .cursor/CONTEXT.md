# Cursor Context – Badminton Court Finder

## What We're Building
A web app that aggregates badminton court availability across Cambridge facilities so users can search one interface (e.g. "What courts are free Wednesday evening?") instead of checking many different booking sites.

## Tech Stack
- **Frontend**: Streamlit – main UI, live at [court-finder.streamlit.app](https://court-finder.streamlit.app) (Streamlit Community Cloud). Fallback: static `index.html` on GitHub Pages.
- **Backend**: Flask API (`app.py`) on Render (Docker). Same API serves both UIs.
- **Database**: Neon PostgreSQL (production); SQLite (local). SQLAlchemy in `database.py`.
- **Scraping**: Playwright per-venue scrapers in `scrapers/`; all use **LLM extraction** via OpenAI (`scrapers/llm_extract.py`, `*_agent_scraper.py`).
- **Deployment**: Render (backend), cron-job.org POST to `/api/scrape-all` every 6 hours.

## For New Developers (e.g. Martin)
**Start here:** [GETTING_STARTED.md](../GETTING_STARTED.md) – clone, `.env` (copy from `.env.example`), `pip install -r requirements-backend.txt`, `playwright install chromium`, run `app.py` then `streamlit run streamlit_app.py`. Optional: [DEPLOYMENT.md](../DEPLOYMENT.md) for Render and agent (OpenAI) setup.

## Current State
- **Facilities**: Hill Roads, One Leisure St Ives, Trumpington Sport, Linton Village College. All four use agent (LLM) scrapers; `OPENAI_API_KEY` is required for scraping.
- **Scrape-all**: Runs three facilities by default (Linton excluded via `EXCLUDE_SCRAPE_FACILITIES`, default: Linton Village College — bot protection). Rate limits and circuit breaker in `scraper_manager.py`.

## Key Files
- `GETTING_STARTED.md` – setup for new devs (use `requirements-backend.txt` for local/API)
- `streamlit_app.py` – Streamlit UI; `index.html` – static fallback
- `requirements.txt` – minimal (streamlit + requests) for Streamlit Cloud; `requirements-backend.txt` – full deps for Render and local
- `app.py` – Flask API; `scraper_manager.py` – scrape orchestration
- `scrapers/llm_extract.py` – OpenAI-based slot extraction; `*_agent_scraper.py` – agent scrapers
- `.env.example` – copy to `.env` and add keys (never commit `.env`)

## Constraints
- Web-only; no native app. No formal partnerships with facilities. Data must be fresh; past slots purged. Side project; using AI tools to move fast.
