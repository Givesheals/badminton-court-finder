# Scheduled scrapes (every 6 hours)

Scrapers run automatically every 6 hours (00:00, 06:00, 12:00, 18:00 UTC). Linton Village College is excluded while that scraper is broken; all other facilities (and any you add later) are included.

**Deploy first:** Push this code and let Render redeploy so the `/api/scrape-all` endpoint is live. Then set up the cron (Option A or B below).

## How it works

- **Endpoint:** `POST /api/scrape-all` on your Render web service.
- **Behaviour:** Starts a background thread that scrapes every facility **except** those in `EXCLUDE_SCRAPE_FACILITIES`. Returns `202 Accepted` immediately so the caller does not time out.
- **Excluded by default:** `Linton Village College` (env var `EXCLUDE_SCRAPE_FACILITIES`, comma-separated). Remove it when that scraper is fixed.
- **Included:** Hill Roads Sport and Tennis Centre, One Leisure St Ives, and any new facilities you add to `scraper_manager.py`.

## Schedule (every 6 hours)

- **00:00 UTC** (midnight)
- **06:00 UTC**
- **12:00 UTC** (noon)
- **18:00 UTC**

So 4 runs per day. Times are UTC; adjust in the cron tool if you want a different timezone.

---

## Option A: External cron (recommended, free)

Use a free external service to call your API every 6 hours. No extra Render service or billing.

### cron-job.org (free)

1. Sign up at [cron-job.org](https://cron-job.org).
2. Create a new cron job:
   - **Title:** e.g. Badminton scrape-all
   - **URL:** `https://badminton-court-finder.onrender.com/api/scrape-all`
   - **Method:** POST
   - **Schedule:** Every 6 hours (or custom: minute 0, hours 0,6,12,18, day * , month * , weekday *).
3. Save. The job will POST to your API every 6 hours.

### Other options

- **Uptime Robot** – monitor + “custom interval” if supported.
- **EasyCron** – free tier can hit a URL on a schedule.

Your web service must be reachable (Render free tier may sleep; the first request after sleep can be slow but will still trigger the scrapes).

---

## Option B: Render Cron Job

Render Cron Jobs can run a command on a schedule. There is a **minimum $1/month** per cron job.

1. In the Render Dashboard: **New +** → **Cron Job**.
2. Connect the same repo (or use a **Docker image** that includes `curl`, e.g. `curlimages/curl`).
3. **Schedule:** `0 0,6,12,18 * * *` (every 6 hours at 00:00, 06:00, 12:00, 18:00 UTC).
4. **Command:**  
   `curl -s -X POST https://badminton-court-finder.onrender.com/api/scrape-all -H "Content-Type: application/json"`
5. If using a Docker image, set the image to e.g. `curlimages/curl` and use the same command. If using the repo, add a minimal Dockerfile that installs `curl` and set the cron job’s start command to the `curl` line above.

---

## Environment variable

| Variable | Default | Description |
|----------|---------|-------------|
| `EXCLUDE_SCRAPE_FACILITIES` | `Linton Village College` | Comma-separated facility names to skip in scrape-all (e.g. broken scrapers). |

To include Linton again later, set `EXCLUDE_SCRAPE_FACILITIES` to empty (or remove Linton from the list) and redeploy.

---

## Manual test

Trigger a run without waiting for the schedule:

```bash
curl -X POST https://badminton-court-finder.onrender.com/api/scrape-all \
  -H "Content-Type: application/json"
```

You should get `202 Accepted` and a JSON body with `"status": "accepted"` and the list of facilities being scraped. Check your Render **Logs** for “Scheduled scrape started for: …” and “Scheduled scrape … success=…”.
