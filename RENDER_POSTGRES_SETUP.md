# Use Render’s free PostgreSQL (no disks needed)

Render’s **free PostgreSQL** database works with the free web service tier. You don’t need “Disks” — you add a separate **PostgreSQL** service in the same Render account and connect your app to it. Data survives restarts and sleeps.

The app is already set up to use PostgreSQL when you set `DATABASE_URL`. Follow these steps in the Render dashboard.

---

## If you already added the DB and ran the scrape script

- **Why it looked stuck:** The script calls Render’s API once per facility. Each call runs the full scrape on the server and only returns when it’s done. So you see “Triggering…” and then nothing for 5–20 minutes — that’s normal. The script is now updated to say so and to show the server’s JSON response when each scrape finishes (and to timeout after 20 min so it doesn’t hang forever).
- **What to do next:**
  1. **Rotate your DB password** (you shared the URL): Render dashboard → your **PostgreSQL** service → **Info** → **Reset database password**. Then in your **Web Service** → **Environment**, update `DATABASE_URL` with the new Internal Database URL and save (Render will redeploy).
  2. In Terminal, go to the project folder then run the script: `cd /Users/simon.parker/Developer/badminton-court-finder` then `./run_render_scrapes.sh`. Leave the terminal open; wait for each “[1/3]”, “[2/3]”, “[3/3]” to print a JSON block (can be 5–15+ min each).
  3. To see progress on the server: Render dashboard → your **Web Service** → **Logs**. You should see “Starting scrape for …” and “Successfully scraped …” (or errors) while the script runs.
  4. When the script finishes, refresh your live site; you should see “last updated” and availability.

---

## Step 1: Create a PostgreSQL database

1. Log in at [dashboard.render.com](https://dashboard.render.com).
2. Click **New +** → **PostgreSQL**.
3. Choose a name (e.g. `badminton-court-db`).
4. Pick the same **region** as your web service (e.g. Oregon) so the app and DB are in the same place.
5. Select the **Free** instance type.
6. Click **Create Database**.
7. Wait until the database status is **Available**.

---

## Step 2: Get the connection URL

1. Open your new PostgreSQL service.
2. In **Connections**, you’ll see **Internal Database URL** (for other Render services) and **External Database URL** (for outside Render).
3. Copy the **Internal Database URL** (it looks like `postgres://user:password@hostname/dbname`).  
   Use **Internal** so your web service talks to the DB inside Render (faster and free).

**Security:** The URL contains your database password. Don’t paste it into chat, docs, or public places. If you ever expose it, go to your PostgreSQL service → **Info** → **Reset database password** in Render, then update the `DATABASE_URL` value in your Web Service’s Environment.

---

## Step 3: Connect your web service to the database

1. Go to your **Web Service** (the badminton court finder app).
2. Open **Environment** (in the left sidebar).
3. Click **Add Environment Variable**.
4. **Key:** `DATABASE_URL`  
   **Value:** paste the Internal Database URL you copied.
5. Save.

Render will redeploy your app. When it’s live, the app will use PostgreSQL instead of the temporary SQLite file, and data will persist across restarts.

---

## Step 4: Populate the database (one time after deploy)

After the redeploy finishes:

1. Open **Terminal** and go to your project folder (the one that contains `run_render_scrapes.sh`), then run the script:
   ```bash
   cd /Users/simon.parker/Developer/badminton-court-finder
   ./run_render_scrapes.sh
   ```
   If you opened Terminal from Cursor or from the project in Finder, you may already be in that folder — then you only need `./run_render_scrapes.sh`. If you see “no such file or directory”, run the `cd` line first.
2. **Important:** Each scrape runs on Render and can take **5–15+ minutes**. The script sends one request per facility and waits for the server to finish that scrape before continuing. You may see no new output for 10–20 minutes — that is normal. Do not close the terminal. The script will print JSON when each scrape completes (or times out after 20 min).
3. When all three finish, refresh your live site. You should see “last updated” times and availability, and they will stay after restarts.

If you want to confirm the server is working, open your **Web Service** in Render → **Logs**, and watch for “Starting scrape for …” and “Successfully scraped …” while the script runs.

---

## Summary

| What | Where |
|------|--------|
| Create DB | Dashboard → New + → PostgreSQL → Free |
| Copy URL | PostgreSQL service → Connections → Internal Database URL |
| Connect app | Web Service → Environment → Add `DATABASE_URL` = (paste URL) |
| Fill data | In project folder: `cd …/badminton-court-finder` then `./run_render_scrapes.sh` |

No disks, no new platform — same Render account, free tier.
