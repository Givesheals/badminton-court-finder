# Scheduled scrapes (every 6 hours)

Scrapers run automatically every 6 hours (00:00, 06:00, 12:00, 18:00 UTC). Three facilities are scraped by default (Linton Village College excluded due to bot protection). Set `EXCLUDE_SCRAPE_FACILITIES` to change which are skipped.

**Deploy first:** Push this code and let Render redeploy so the `/api/scrape-all` endpoint is live. Then set up scheduled scrapes (cron-job.org below, or Render Cron Job).

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

So 4 runs per day. Times are UTC; adjust in the cron tool if you want a different timezone.

---

## cron-job.org (recommended, free)

Use cron-job.org to call your API every 6 hours. No extra Render service or billing. **Full step-by-step:** [CRONJOB_ORG_SETUP.md](CRONJOB_ORG_SETUP.md).

### Quick setup summary

1. **Deploy first** so `/api/scrape-all` is live (push to GitHub, wait for Render to finish redeploying). Optional quick test: open `https://badminton-court-finder.onrender.com/health` (may take 30–60 s if app was sleeping).

2. **Sign up** at [cron-job.org](https://cron-job.org) (Sign up → email/password → confirm → log in).

3. **Create scrape-all cron job** (Create cron job or Cron jobs → Create):
   - **Common:** Title e.g. `Badminton court scrape-all`, **Address (URL):** `https://badminton-court-finder.onrender.com/api/scrape-all`, **Schedule:** Every 6 hours or Custom: Minute `0`, Hour `0,6,12,18`, Day `*`, Month `*`, Weekday `*`
   - **Headers:** Add **Key** `Content-Type`, **Value** `application/json`
   - **Advanced:** **Request method** = **POST** (not GET), Request body empty, Timeout 30 s
   - Click **CREATE** / **Save**.

4. **Create keep-awake cron job** (Create cron job again): Title e.g. `Badminton court keep-awake`, **URL:** `https://badminton-court-finder.onrender.com/health`, **Schedule:** Every 2 minutes (or every 5 minutes), **Request method:** GET. This keeps the Render service warm so the scrape-all job doesn't get 503 (cron-job.org has a 30 s max timeout).

5. **Confirm:** Both jobs are Enabled. Test with `curl -X POST https://badminton-court-finder.onrender.com/api/scrape-all -H "Content-Type: application/json"` — expect `202 Accepted`. Check Render → Logs for “Scheduled scrape started for: …”.

**Checklist:** Signed up at cron-job.org → Created scrape-all job (URL, every 6h, POST, Content-Type header) → Created keep-awake job (URL `/health`, every 2 min, GET) → Both enabled → Saw “Scheduled scrape started for: …” in Render logs.

**Testing Linton from Render (if your IP is blocked):** Run a one-off scrape on Render: `curl --max-time 900 -X POST https://badminton-court-finder.onrender.com/api/scrape -H "Content-Type: application/json" -d '{"facility":"Linton Village College"}'`. Ensure `LVC_USERNAME` and `LVC_PASSWORD` are set in Render → Environment. Check Render Logs for scraper output.

### Other options

- **Uptime Robot** – monitor + “custom interval” if supported.
- **EasyCron** – free tier can hit a URL on a schedule.

Your web service must be reachable (Render free tier may sleep; the first request after sleep can be slow). cron-job.org has a **30 second max timeout**, so you need a **keep-awake** job: a second cron job that GETs `/health` every 2 (or 5) minutes. See [CRONJOB_ORG_SETUP.md](CRONJOB_ORG_SETUP.md) for the full step-by-step (including the keep-awake job).

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
| `EXCLUDE_SCRAPE_FACILITIES` | `Linton Village College` | Comma-separated facility names to skip in scrape-all (Linton excluded due to bot protection). Set to empty to scrape all four. |

---

## Manual test

Trigger a run without waiting for the schedule:

```bash
curl -X POST https://badminton-court-finder.onrender.com/api/scrape-all \
  -H "Content-Type: application/json"
```

You should get `202 Accepted` and a JSON body with `"status": "accepted"` and the list of facilities being scraped. Check your Render **Logs** for “Scheduled scrape started for: …” and “Scheduled scrape … success=…”.
