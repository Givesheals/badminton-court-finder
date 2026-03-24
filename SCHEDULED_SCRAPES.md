# Scheduled scrapes (three times daily)

Scrapers run automatically **three times per day** (00:00, 12:00, 18:00 UTC). **Each run scrapes every configured facility except** those listed in `EXCLUDE_SCRAPE_FACILITIES` (default skips **Linton Village College** due to bot protection). Runs are **sequential** (one facility at a time) so the Render host does not run out of memory—see [Render memory (~512 MB)](DEPLOYMENT.md#render-memory-512-mb).

**Deploy first:** Push this code and let Render redeploy so the `/api/scrape-all` endpoint is live. Then set up scheduled scrapes using GitHub Actions (see below).

## How it works

- **Endpoint:** `POST /api/scrape-all` on your Render web service (no query params for the scheduled job).
- **Behaviour:** Starts a background thread that scrapes each facility **except** those in `EXCLUDE_SCRAPE_FACILITIES`, **one after another**, with a delay between facilities (`SCRAPE_DELAY_BETWEEN_FACILITIES_SECONDS`, default 1s locally; set higher on Render if sites rate-limit). Returns `202 Accepted` immediately so the caller does not time out.
- **Why sequential:** The API runs on a **single Gunicorn worker** with **~512 MB RAM** on Render’s free tier. Each scrape launches **Chromium (Playwright)**. Running many scrapers **at once** exhausts RAM (OOM → process killed → stale data). Scheduled runs therefore **must not** use `?concurrent=1`.
- **Manual concurrent scrape-all:** `POST /api/scrape-all?concurrent=1` (or JSON `{"concurrent": true}`) uses a **small thread pool** capped by `SCRAPE_CONCURRENT_MAX_WORKERS` (default **2**), not one thread per facility. Only raise the cap on a larger instance.
- **Excluded by default:** Linton Village College. Set `EXCLUDE_SCRAPE_FACILITIES` to empty to include it, or add names to skip more venues.

## Schedule (three times daily)

- **00:00 UTC** (midnight)
- **12:00 UTC** (noon)
- **18:00 UTC**

So 3 runs per day. Times are UTC; adjust in the scheduler if you want a different timezone.

---

## GitHub Actions (recommended)

The repo uses a workflow that **wakes Render** (GET `/health`), **waits 90 seconds** for cold start, then **POSTs `/api/scrape-all`**. No keep-awake job; Render can spin down between runs.

### One-time setup

1. **Add repo secret:** In the repo go to **Settings → Secrets and variables → Actions**. New repository secret: **Name** `RENDER_APP_URL`, **Value** `https://badminton-court-finder.onrender.com` (no trailing slash).

2. **Confirm workflow:** The workflow is in [.github/workflows/scheduled-scrape.yml](.github/workflows/scheduled-scrape.yml). It runs on the schedule above; you can also trigger it manually from the **Actions** tab (**Scheduled scrape** → **Run workflow**).

3. **Avoid duplicate runs:** Ensure no other scheduler (e.g. another CI or external cron) is also calling `/api/scrape-all`, or scrapes may run twice.

### Flow

1. Workflow runs at 00:00, 12:00, 18:00 UTC.
2. **Wake:** GET `RENDER_APP_URL/health` (wakes Render if it was sleeping).
3. **Wait:** 90 seconds so the next request hits a warm instance.
4. **Trigger:** POST `RENDER_APP_URL/api/scrape-all` (sequential) with `Content-Type: application/json`; expect `202 Accepted`. The job fails if the response is not 202 (e.g. 503 if Render did not wake in time).

Scrapes then run **in series** in the background (may take a long wall-clock time); the workflow only checks that the trigger was accepted.

**Testing Linton from Render (if your IP is blocked):** Run a one-off scrape on Render: `curl --max-time 900 -X POST https://badminton-court-finder.onrender.com/api/scrape -H "Content-Type: application/json" -d '{"facility":"Linton Village College"}'`. Ensure `LVC_USERNAME` and `LVC_PASSWORD` are set in Render → Environment. Check Render Logs for scraper output.

---

## Option: Render Cron Job

Render Cron Jobs can run a command on a schedule. There is a **minimum $1/month** per cron job.

1. In the Render Dashboard: **New +** → **Cron Job**.
2. Connect the same repo (or use a **Docker image** that includes `curl`, e.g. `curlimages/curl`).
3. **Schedule:** `0 0,12,18 * * *` (three times daily at 00:00, 12:00, 18:00 UTC).
4. **Command:**  
   `curl -s -X POST https://badminton-court-finder.onrender.com/api/scrape-all -H "Content-Type: application/json"`
5. If using a Docker image, set the image to e.g. `curlimages/curl` and use the same command. If using the repo, add a minimal Dockerfile that installs `curl` and set the cron job’s start command to the `curl` line above.

---

## Environment variables (Render / API)

| Variable | Default | Description |
|----------|---------|-------------|
| `EXCLUDE_SCRAPE_FACILITIES` | `Linton Village College` | Comma-separated facility names to skip in scrape-all. |
| `SCRAPE_DELAY_BETWEEN_FACILITIES_SECONDS` | `1` (raise on Render if needed) | Pause between facilities in **sequential** scrape-all. |
| `SCRAPE_CONCURRENT_MAX_WORKERS` | `2` | Only for `?concurrent=1`: max parallel browser scrapes. Keep low on ~512 MB hosts. |

---

## Manual test

Trigger a run without waiting for the schedule:

```bash
curl -X POST https://badminton-court-finder.onrender.com/api/scrape-all \
  -H "Content-Type: application/json"
```

You should get `202 Accepted` and a JSON body with `"status": "accepted"` and the list of facilities. Check Render **Logs** for sequential lines like `Scheduled scrape started for: …`, per-facility results, and finally `Scheduled scrape run finished.`
