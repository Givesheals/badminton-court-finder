# Scrapers

This directory contains scrapers for different sports facilities.

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

2. Create `.env` file (copy from `.env.example`):
```bash
cp .env.example .env
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
- `debug_page.html` - Full HTML of the availability page

Use these to understand the page structure and update selectors as needed.
