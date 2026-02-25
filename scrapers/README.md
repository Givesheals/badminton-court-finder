# Scrapers

This directory contains scrapers for different sports facilities. Each venue has a **fixed-selector** scraper (e.g. `hill_roads.py`, `linton_village_college.py`). Some also have an **agent (LLM) scraper** (e.g. `hill_roads_agent_scraper.py`, `linton_agent_scraper.py`) that uses the same navigation but extracts availability via OpenAI (`llm_extract.py`) for resilience to layout changes. Enable agent scrapers with env var `AGENT_SCRAPE_FACILITIES` and `OPENAI_API_KEY`; see project [README](../README.md) and [GETTING_STARTED.md](../GETTING_STARTED.md).

## Scraping policy (avoid getting blocked)

- **Minimise manual scrapes** while building. Sites use bot protection (WAF) and can block IPs that hit them too often.
- **Scheduled scrapes** (e.g. every 6 hours via cron) are preferred; the app uses rate limits and a delay between facilities.
- **Linton Village College** uses Anglian Leisure’s booking system (`anglianleisure.gs-signature.cloud`). That domain returns **403 Access Forbidden** when it detects automation or too many requests. If you see that in the browser, your IP may be temporarily blocked—avoid re-running the Linton scraper from that machine for 24h and rely on Render/cron if you need Linton data.
- The Linton scraper now detects 403 / block pages and raises a clear error instead of “no input fields found”.

## Linton Village College

The `linton_village_college.py` scraper handles:
- Navigation to the booking page
- Login with credentials
- Navigation to badminton court booking (New Gym)
- Extraction of court availability data
- Storage in SQLite database

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
playwright install chromium
```

2. Create `.env` from `.env.example` and add credentials (see [GETTING_STARTED.md](../GETTING_STARTED.md)):
```bash
cp .env.example .env
# Edit .env with LVC_USERNAME, LVC_PASSWORD, and optionally OPENAI_API_KEY
```

3. Run the scraper:
```bash
python scrapers/linton_village_college.py
```

### Debugging

The scraper saves debug files when it encounters issues:
- `debug_book_now.png` - Screenshot when looking for "Book now" button
- `debug_login.png` - Screenshot during login
- `debug_badminton_search.png` - Screenshot when looking for badminton interface
- `debug_availability_page.png` - Screenshot of the availability page
- `debug_*.html` – full HTML when saved (gitignored)

Use these to understand the page structure and update selectors as needed. Debug files are in `.gitignore`.
