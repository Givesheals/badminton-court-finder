# Option A walkthrough: cron-job.org (free, every 6 hours)

Do these steps once. After that, scrapes run automatically every 6 hours (00:00, 06:00, 12:00, 18:00 UTC).

---

## Before you start

1. **Deploy the latest code** so `/api/scrape-all` is live:
   - Push your repo to GitHub (if you haven’t already).
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
4. Log in if you’re not already.

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
   - **Request body:** leave empty (our endpoint doesn’t need a body).
   - **Timeout:** 30 seconds is fine (the API returns 202 quickly; scrapes run in the background).
   - **Time zone:** leave as is (schedule runs in UTC unless you change it).

5. Leave **Notify on failure** or **Alerts** as you prefer (e.g. email if the request fails).

6. Click **CREATE** (or **Save**).

---

## Step 3: Confirm it’s active

1. On the cron job’s page, check that the job is **Enabled** / **Active**.
2. **Trigger a test run** (cron-job.org sometimes has no “Run now” button):
   - From any terminal (or Postman), run:
     ```bash
     curl -X POST https://badminton-court-finder.onrender.com/api/scrape-all \
       -H "Content-Type: application/json"
     ```
   - You should get `202 Accepted` and “Scrapes started in background”. That’s the same request the timer will send.
3. Wait a few seconds, then check **Last run** or **History** on cron-job.org (when you do have it) – you should see a successful request (e.g. HTTP 202).
4. In **Render** → your **Web Service** → **Logs**, you should see lines like:
   - `Scheduled scrape started for: ['Hill Roads Sport and Tennis Centre', 'One Leisure St Ives']`
   - `Scheduled scrape Hill Roads Sport and Tennis Centre: success=...`
   - `Scheduled scrape One Leisure St Ives: success=...`

---

## What happens from now on

- cron-job.org will **POST** to your API **every 6 hours** (00:00, 06:00, 12:00, 18:00 UTC).
- Your app will start scrapes for **Hill Roads** and **One Leisure St Ives** (Linton is excluded until you remove it from `EXCLUDE_SCRAPE_FACILITIES`).
- Any new facility you add to `scraper_manager.py` will be included automatically; only names in `EXCLUDE_SCRAPE_FACILITIES` are skipped.

---

## Copy-paste checklist

- [ ] Signed up at https://cron-job.org  
- [ ] Created cron job with:
  - **Common:** URL `https://badminton-court-finder.onrender.com/api/scrape-all`, schedule every 6 hours
  - **Headers:** Content-Type = application/json
  - **Advanced:** Request method = **POST**, Request body empty
- [ ] Job is enabled and (optionally) ran once successfully
- [ ] Saw “Scheduled scrape started for: …” in Render logs

That’s it. You don’t need to do anything else on your side for the 6-hour schedule.

---

## Testing the Linton scraper from Render (not your laptop)

If your laptop’s IP is blocked by Anglian Leisure (403 on “Book now”), you can still test whether the Linton scraper would work on the timer by running it **on Render** (different IP).

1. **One-off Linton scrape on Render** (request runs on Render’s servers; can take 5–15 minutes):
   ```bash
   curl --max-time 900 -X POST https://badminton-court-finder.onrender.com/api/scrape \
     -H "Content-Type: application/json" \
     -d '{"facility":"Linton Village College"}'
   ```
   - Replace the URL with your Render app URL if different.
   - Ensure `LVC_USERNAME` and `LVC_PASSWORD` are set in Render → Environment.
   - If the app was sleeping, the first request may take 30–60 s to wake, then the scrape runs.

2. **Check the result**: success returns JSON with `"success": true` and availability data; failure returns an error (e.g. 403 block message).

3. **Check Render logs**: Render → your Web Service → **Logs** to see scraper output (e.g. “Starting Linton Village College scraper…”, “Booking page returned 403…”, or “Scraping completed successfully!”).

If Linton succeeds from Render, it should also work when the cron job runs every 6 hours (same endpoint, same server).
