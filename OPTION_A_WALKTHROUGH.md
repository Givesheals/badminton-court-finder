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
2. Fill in the form with these **exact** values (copy-paste where possible):

| Field | Value |
|-------|--------|
| **Title** | `Badminton court scrape-all` (or any name you like) |
| **Address (URL)** | `https://badminton-court-finder.onrender.com/api/scrape-all` |
| **Request method** | **POST** (do not leave as GET) |
| **Schedule** | **Every 6 hours** (use the preset if available), or **Custom** and set: **Minute** `0`, **Hour** `0,6,12,18`, **Day** `*`, **Month** `*`, **Weekday** `*` |

3. **Optional but recommended:** Under advanced or request options, add a header:
   - **Header name:** `Content-Type`
   - **Header value:** `application/json`  
   (Some services expect this for POST.)

4. Leave **Notify on failure** or **Alerts** as you prefer (e.g. email if the request fails).

5. Click **Create** or **Save**.

---

## Step 3: Confirm it’s active

1. On the cron job’s page, check that the job is **Enabled** / **Active**.
2. If there’s a **Run now** or **Execute now** button, click it once to trigger a test run.
3. Wait a few seconds, then check **Last run** or **History** – you should see a successful request (e.g. HTTP 202).
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
  - URL: `https://badminton-court-finder.onrender.com/api/scrape-all`
  - Method: **POST**
  - Schedule: every 6 hours (or minute 0, hours 0,6,12,18)
- [ ] Job is enabled and (optionally) ran once successfully
- [ ] Saw “Scheduled scrape started for: …” in Render logs

That’s it. You don’t need to do anything else on your side for the 6-hour schedule.
