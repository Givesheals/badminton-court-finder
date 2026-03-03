# Scheduled scrapes with cron-job.org

Do these steps once. After that, scrapes run automatically every 6 hours (00:00, 06:00, 12:00, 18:00 UTC).

---

## Before you start

1. **Deploy the latest code** so `/api/scrape-all` is live:
   - Push your repo to GitHub (if you haven't already).
   - In Render, wait for the web service to finish redeploying.

2. **Quick test** (optional): In a browser or Terminal, run:
   ```text
   https://badminton-court-finder.onrender.com/health
   ```
   You should see `{"status":"healthy"}`. If the app is sleeping, the first load may take 30–60 seconds.

---

## Step 1: Sign up at cron-job.org

1. Open: **https://cron-job.org**
2. Click **Sign up** (or **Create free account**).
3. Enter your email and a password, then confirm.
4. Log in if you're not already.

---

## Step 2: Create the cron job

1. In the cron-job.org dashboard, click **Create cron job** (or **Cron jobs** → **Create**).

2. **Common** (or main) section:
   - **Title:** e.g. `Badminton court scrape-all`
   - **Address (URL):** `https://badminton-court-finder.onrender.com/api/scrape-all`
   - **Schedule:** Every 6 hours (preset if available), or **Custom**: **Minute** `0`, **Hour** `0,6,12,18`, **Day** `*`, **Month** `*`, **Weekday** `*`

3. **Headers** section:
   - Add a header: **Key** `Content-Type`, **Value** `application/json`  
   (You may already have this from the screenshot.)

4. **Advanced** section (this is where the request method lives):
   - **Request method:** set the dropdown to **POST** (do not leave as GET).
   - **Request body:** leave empty (our endpoint doesn't need a body).
   - **Timeout:** leave at 30 seconds (cron-job.org's maximum). To avoid 503 when the app is sleeping, use the keep-awake job in Step 3 below.
   - **Time zone:** leave as is (schedule runs in UTC unless you change it).

5. Leave **Notify on failure** or **Alerts** as you prefer (e.g. email if the request fails).

6. Click **CREATE** (or **Save**).

---

## Step 3: Create the keep-awake job

Render's free tier sleeps after inactivity. cron-job.org has a 30 second max timeout, so the scrape-all request can get **503** if the app is cold. Add a second job that pings your app so it stays warm.

1. In cron-job.org, click **Create cron job** again.
2. **Title:** e.g. `Badminton court keep-awake`
3. **Address (URL):** `https://badminton-court-finder.onrender.com/health`
4. **Schedule:** Every 2 minutes (or every 5 minutes if you prefer).
5. **Request method:** **GET** (default). No headers or body needed.
6. **Timeout:** 30 seconds is fine.
7. Click **CREATE** (or **Save**) and ensure the job is **Enabled**.

---

## Step 4: Confirm it's active

1. Check that **both** cron jobs are **Enabled** / **Active** (scrape-all and keep-awake).
2. **Trigger a test run** (cron-job.org sometimes has no "Run now" button):
   - From any terminal (or Postman), run:
     ```bash
     curl -X POST https://badminton-court-finder.onrender.com/api/scrape-all \
       -H "Content-Type: application/json"
     ```
   - You should get `202 Accepted` and "Scrapes started in background". That's the same request the timer will send.
3. Wait a few seconds, then check **Last run** or **History** on cron-job.org (when you do have it) – you should see a successful request (e.g. HTTP 202).
4. In **Render** → your **Web Service** → **Logs**, you should see lines like:
   - `Scheduled scrape started for: ['Hill Roads Sport and Tennis Centre', 'Linton Village College', 'One Leisure St Ives', 'Trumpington Sport']` (or three facilities if Linton is excluded by default)
   - `Scheduled scrape Hill Roads Sport and Tennis Centre: success=...`
   - (and similar for the other facilities)

---

## Troubleshooting: 503 Service Unavailable on test run

If a **test run** on cron-job.org returns **503 Service Unavailable**, the Render app was **sleeping** (cold start on the free tier). Render can take 30–60 seconds to wake, and **cron-job.org allows a maximum timeout of 30 seconds**, so you can't fix this by increasing the timeout.

**Fix: keep the service awake** so the scrape-all job always hits a warm instance.

### Option 1: Second cron job on cron-job.org (recommended)

Create a **second** cron job that only pings your app so it stays warm:

1. In cron-job.org, click **Create cron job** again.
2. **Title:** e.g. `Badminton court keep-awake`
3. **Address (URL):** `https://badminton-court-finder.onrender.com/health`
4. **Schedule:** Every 2 minutes (or every 5 minutes).
5. **Request method:** **GET** (default). No headers or body needed.
6. **Timeout:** 30 seconds is fine.
7. Create and enable the job.

This job only wakes the service; your main "Badminton Court Scrape All" job still runs every 6 hours and will then get 202 within 30 seconds.

### Option 2: UptimeRobot (or similar)

Use [UptimeRobot](https://uptimerobot.com) (free): add a monitor for `https://badminton-court-finder.onrender.com/health` with a 5‑minute check interval. The HTTP checks keep your Render service from sleeping.

### Quick checks

- **Verify the app:** Open `https://badminton-court-finder.onrender.com/health` in your browser and wait 30–60 seconds. If you see `{"status":"healthy"}`, the app is fine.
- **Test again:** After the keep-awake job has run once (e.g. wait 2–5 minutes), run "Test run" on the scrape-all job again; it should return 202.

---

## What happens from now on

- The **keep-awake** job GETs `/health` every 2 minutes so the Render service stays warm.
- The **scrape-all** job **POST**s to your API **every 6 hours** (00:00, 06:00, 12:00, 18:00 UTC).
- By default your app scrapes **three facilities** (Hill Roads Sport and Tennis Centre, One Leisure St Ives, Trumpington Sport); Linton Village College is excluded due to bot protection. To include Linton, set `EXCLUDE_SCRAPE_FACILITIES` to empty in Render.
- Any new facility you add to `scraper_manager.py` will be included automatically; only names in `EXCLUDE_SCRAPE_FACILITIES` are skipped.

---

## Copy-paste checklist

- [ ] Signed up at https://cron-job.org  
- [ ] Created **scrape-all** cron job:
  - **Common:** URL `https://badminton-court-finder.onrender.com/api/scrape-all`, schedule every 6 hours
  - **Headers:** Content-Type = application/json
  - **Advanced:** Request method = **POST**, Request body empty
- [ ] Created **keep-awake** cron job:
  - **Common:** URL `https://badminton-court-finder.onrender.com/health`, schedule every 2 minutes (or every 5 minutes)
  - **Advanced:** Request method = **GET**
- [ ] Both jobs are enabled and (optionally) scrape-all ran once successfully
- [ ] Saw "Scheduled scrape started for: …" in Render logs

That's it. You don't need to do anything else on your side for the 6-hour schedule.

---

## Testing the Linton scraper from Render (not your laptop)

If your laptop's IP is blocked by Anglian Leisure (403 on "Book now"), you can still test whether the Linton scraper would work on the timer by running it **on Render** (different IP).

1. **One-off Linton scrape on Render** (request runs on Render's servers; can take 5–15 minutes):
   ```bash
   curl --max-time 900 -X POST https://badminton-court-finder.onrender.com/api/scrape \
     -H "Content-Type: application/json" \
     -d '{"facility":"Linton Village College"}'
   ```
   - Replace the URL with your Render app URL if different.
   - Ensure `LVC_USERNAME` and `LVC_PASSWORD` are set in Render → Environment.
   - If the app was sleeping, the first request may take 30–60 s to wake, then the scrape runs.

2. **Check the result**: success returns JSON with `"success": true` and availability data; failure returns an error (e.g. 403 block message).

3. **Check Render logs**: Render → your Web Service → **Logs** to see scraper output (e.g. "Starting Linton Village College scraper…", "Booking page returned 403…", or "Scraping completed successfully!").

If Linton succeeds from Render, it should also work when the cron job runs every 6 hours (same endpoint, same server).
