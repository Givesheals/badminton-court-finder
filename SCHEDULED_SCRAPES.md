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

### cron-job.org (free) — step-by-step

1. **Deploy first** so `/api/scrape-all` is live (push to GitHub, wait for Render to finish redeploying). Optional quick test: open `https://badminton-court-finder.onrender.com/health` (may take 30–60 s if app was sleeping).

2. **Sign up** at [cron-job.org](https://cron-job.org) (Sign up → email/password → confirm → log in).

3. **Create cron job** (Create cron job or Cron jobs → Create):
   - **Common:** Title e.g. `Badminton court scrape-all`, **Address (URL):** `https://badminton-court-finder.onrender.com/api/scrape-all`, **Schedule:** Every 6 hours or Custom: Minute `0`, Hour `0,6,12,18`, Day `*`, Month `*`, Weekday `*`
   - **Headers:** Add **Key** `Content-Type`, **Value** `application/json`
   - **Advanced:** **Request method** = **POST** (not GET), Request body empty, Timeout 30 s
   - Click **CREATE** / **Save**.

4. **Confirm:** Job is Enabled. Test with `curl -X POST https://badminton-court-finder.onrender.com/api/scrape-all -H "Content-Type: application/json"` — expect `202 Accepted`. Check Render → Logs for “Scheduled scrape started for: …”.

**Checklist:** Signed up at cron-job.org → Created job (URL, schedule every 6h, Content-Type header, method POST) → Job enabled → Saw “Scheduled scrape started for: …” in Render logs.

**Testing Linton from Render (if your IP is blocked):** Run a one-off scrape on Render: `curl --max-time 900 -X POST https://badminton-court-finder.onrender.com/api/scrape -H "Content-Type: application/json" -d '{"facility":"Linton Village College"}'`. Ensure `LVC_USERNAME` and `LVC_PASSWORD` are set in Render → Environment. Check Render Logs for scraper output.

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
