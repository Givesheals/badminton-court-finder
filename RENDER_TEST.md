# Deploy & Test on Render

## 1. Deploy

**After adding a new scraper (e.g. One Leisure St Ives), redeploy so the facility appears in the list.**

Push to `main` (auto-deploy if connected), or Render Dashboard → **Manual Deploy** → **Deploy latest commit**.

- **Check deploy status**: https://dashboard.render.com → your `badminton-court-finder` service → **Events** or **Logs**. Wait until the latest deploy shows **Live** (usually 2–5 minutes after push).

## 2. Test once deploy is live

Base URL: `https://badminton-court-finder.onrender.com`  
(Free tier may sleep; first request can take 30–60 seconds.)

### Health
```bash
curl -s "https://badminton-court-finder.onrender.com/health"
# Expect: {"status":"healthy"}
```

### List facilities (should include all three)
```bash
curl -s "https://badminton-court-finder.onrender.com/api/facilities"
# Expect: "facilities" includes "Hill Roads Sport and Tennis Centre", "Linton Village College", "One Leisure St Ives"
```
If One Leisure St Ives is missing, trigger a new deploy — the running code is old.

### Trigger Hills Road scrape
```bash
curl -s -X POST "https://badminton-court-finder.onrender.com/api/scrape" \
  -H "Content-Type: application/json" \
  -d '{"facility":"Hill Roads Sport and Tennis Centre"}'
```
- **Success**: `"success":true` and `"scraped_at":...`
- **Failure**: `"success":false`, `"error":...` — check Render **Logs** for the full trace (login blocked, timeout, etc.)

Scrape can take 1–3 minutes. Gunicorn timeout is 300s.

### Get availability (from cache; no scrape on request)
```bash
curl -s "https://badminton-court-finder.onrender.com/api/availability?facility=One%20Leisure%20St%20Ives&date=2026-02-05"
curl -s "https://badminton-court-finder.onrender.com/api/availability?facility=Hill%20Roads%20Sport%20and%20Tennis%20Centre"
```

### Facility stats
```bash
curl -s "https://badminton-court-finder.onrender.com/api/facility/One%20Leisure%20St%20Ives/stats"
curl -s "https://badminton-court-finder.onrender.com/api/facility/Hill%20Roads%20Sport%20and%20Tennis%20Centre/stats"
```

## 3. If scrapers fail on Render

Some booking sites block Render IPs or headless browsers. If you see 404 on login or “blocked” in logs:

- Keep the API on Render; run scrapers elsewhere (e.g. your machine, GitHub Actions, or another host) and either call `/api/scrape` after scraping or write to a shared DB.
- See DEPLOYMENT.md for options (Railway, cron, etc.).
