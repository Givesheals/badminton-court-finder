# Scheduled scrapes (every 6 hours)

Scrapers run automatically every 6 hours (00:00, 06:00, 12:00, 18:00 UTC). Three facilities are scraped by default (Linton Village College excluded due to bot protection). Set `EXCLUDE_SCRAPE_FACILITIES` to change which are skipped.

**Deploy first:** Push this code and let Render redeploy so the `/api/scrape-all` endpoint is live. Then set up scheduled scrapes using GitHub Actions (see below).

## How it works

- **Endpoint:** `POST /api/scrape-all` on your Render web service.
- **Behaviour:** Starts a background thread that scrapes every facility **except** those in `EXCLUDE_SCRAPE_FACILITIES`. Returns `202 Accepted` immediately so the caller does not time out.
- **Excluded by default:** Linton Village College (bot protection returns 403). Set `EXCLUDE_SCRAPE_FACILITIES` to empty to include it, or add other names to skip.
- **Included by default:** Hill Roads Sport and Tennis Centre, One Leisure St Ives, Trumpington Sport.

## Schedule (every 6 hours)

- **00:00 UTC** (midnight)
- **06:00 UTC**
- **12:00 UTC** (noon)
- **18:00 UTC**

So 4 runs per day. Times are UTC; adjust in the scheduler if you want a different timezone.

---

## GitHub Actions (recommended)

The repo uses a workflow that **wakes Render** (GET `/health`), **waits 90 seconds** for cold start, then **POSTs `/api/scrape-all`**. No keep-awake job; Render can spin down between runs.

### One-time setup

1. **Add repo secret:** In the repo go to **Settings → Secrets and variables → Actions**. New repository secret: **Name** `RENDER_APP_URL`, **Value** `https://badminton-court-finder.onrender.com` (no trailing slash).

2. **Confirm workflow:** The workflow is in [.github/workflows/scheduled-scrape.yml](.github/workflows/scheduled-scrape.yml). It runs on the schedule above; you can also trigger it manually from the **Actions** tab (**Scheduled scrape** → **Run workflow**).

3. **Avoid duplicate runs:** Ensure no other scheduler (e.g. another CI or external cron) is also calling `/api/scrape-all`, or scrapes may run twice.

### Flow

1. Workflow runs at 00:00, 06:00, 12:00, 18:00 UTC.
2. **Wake:** GET `RENDER_APP_URL/health` (wakes Render if it was sleeping).
3. **Wait:** 90 seconds so the next request hits a warm instance.
4. **Trigger:** POST `RENDER_APP_URL/api/scrape-all` with `Content-Type: application/json`; expect `202 Accepted`. The job fails if the response is not 202 (e.g. 503 if Render did not wake in time).

Scrapes run in the background on Render after the 202; the workflow only ensures the trigger was accepted.

**Testing Linton from Render (if your IP is blocked):** Run a one-off scrape on Render: `curl --max-time 900 -X POST https://badminton-court-finder.onrender.com/api/scrape -H "Content-Type: application/json" -d '{"facility":"Linton Village College"}'`. Ensure `LVC_USERNAME` and `LVC_PASSWORD` are set in Render → Environment. Check Render Logs for scraper output.

---

## Option: Render Cron Job

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
| `EXCLUDE_SCRAPE_FACILITIES` | `Linton Village College` | Comma-separated facility names to skip in scrape-all (Linton excluded due to bot protection). Set to empty to scrape all four. |

---

## Manual test

Trigger a run without waiting for the schedule:

```bash
curl -X POST https://badminton-court-finder.onrender.com/api/scrape-all \
  -H "Content-Type: application/json"
```

You should get `202 Accepted` and a JSON body with `"status": "accepted"` and the list of facilities being scraped. Check your Render **Logs** for “Scheduled scrape started for: …” and “Scheduled scrape … success=…”.
