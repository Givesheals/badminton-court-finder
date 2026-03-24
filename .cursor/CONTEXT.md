# Cursor Context – Badminton Court Finder

## What We're Building
A web app that aggregates badminton court availability across Cambridge facilities so users can search one interface (e.g. "What courts are free Wednesday evening?") instead of checking many different booking sites.

## Tech Stack
- **Frontend**: Streamlit – main UI, live at [court-finder.streamlit.app](https://court-finder.streamlit.app) (Streamlit Community Cloud).
- **Backend**: Flask API (`app.py`) on Render (Docker). Same API serves both UIs.
- **Database**: Neon PostgreSQL (production); SQLite (local). SQLAlchemy in `database.py`.
- **Scraping**: Playwright per-venue scrapers in `scrapers/`; all use **LLM extraction** via OpenAI (`scrapers/llm_extract.py`, `*_agent_scraper.py`).
- **Deployment**: Render (backend, **~512 MB RAM** on free tier). GitHub Actions triggers **sequential** `/api/scrape-all` three times daily (00:00, 12:00, 18:00 UTC). Do not schedule concurrent scrape-all—OOM risk. See [DEPLOYMENT.md](../DEPLOYMENT.md#render-memory-512-mb).

## For New Developers (e.g. Martin)
**Start here:** [GETTING_STARTED.md](../GETTING_STARTED.md) – clone, `.env` (copy from `.env.example`), `pip install -r requirements-backend.txt`, `playwright install chromium`, run `app.py` then `streamlit run streamlit_app.py`. Optional: [DEPLOYMENT.md](../DEPLOYMENT.md) for Render and agent (OpenAI) setup.

## Current State
- **Facilities**: Cherry Hinton, Hill Roads, multiple One Leisure sites, Trumpington, Linton, etc. Agent (LLM) scrapers; `OPENAI_API_KEY` required.
- **Scrape-all**: Scheduled runs are **sequential** (one browser at a time). Optional `?concurrent=1` is **capped** (`SCRAPE_CONCURRENT_MAX_WORKERS`, default 2). Linton often excluded (`EXCLUDE_SCRAPE_FACILITIES`). Rate limits + circuit breaker in `scraper_manager.py`.

## Key Files
- `GETTING_STARTED.md` – setup for new devs (use `requirements-backend.txt` for local/API)
- `streamlit_app.py` – Streamlit UI
- `requirements.txt` – minimal (streamlit + requests) for Streamlit Cloud; `requirements-backend.txt` – full deps for Render and local
- `app.py` – Flask API; `scraper_manager.py` – scrape orchestration
- `scrapers/llm_extract.py` – OpenAI-based slot extraction; `*_agent_scraper.py` – agent scrapers
- `.env.example` – copy to `.env` and add keys (never commit `.env`)

## Constraints
- Web-only; no native app. No formal partnerships with facilities. Data must be fresh; past slots purged. Side project; using AI tools to move fast.
- **Memory**: Treat Render as **~512 MB** for the API process. Never add unbounded parallel Playwright/Chromium per facility in the same worker; prefer sequential scrapes or a small fixed pool (see `app.py`, `SCRAPE_CONCURRENT_MAX_WORKERS`).
