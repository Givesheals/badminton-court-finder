# Investigation: "Last updated: never" and no availability

**Date:** 5 February 2026

## What we found

### Your local machine
- **Database has data.** Running `check_db.py` showed:
  - Linton Village College: 206 available slots (last 14 days)
  - Hill Roads Sport and Tennis Centre: 4,736 available slots
  - One Leisure St Ives: 18 available slots
- So your code and scrapers work. Data was not “deleted” by a bug.

### Production (Render)
- **The database on Render is empty.** We called the live API and got:
  - `GET /api/facilities` → `last_updated` is `null` for all three facilities (so the frontend correctly shows “last updated: never”).
  - `GET /api/availability?facility=...&date=...` → `count: 0`, `data: []` (no slots).
  - `GET /api/facility/.../stats` → “Facility not found” (no facility rows in the DB at all).
- So **data is not flowing to the frontend because there is no data on the server.** The frontend is showing exactly what the API returns.

### Root cause
Render’s **free tier uses ephemeral storage**: when the app restarts or sleeps, the disk is wiped. The SQLite file `court_availability.db` is recreated empty each time. So:
- After every deploy or restart, production starts with an empty DB.
- “Last updated: never” and “no availability” are expected until scrapes run again **and** you add a way to keep data across restarts.

Your `DEPLOYMENT.md` already notes this: *“Lost on container restart (acceptable for cache)”* — but if you want the live site to show availability without re-scraping after every restart, you need persistent storage.

---

## What you can do

### Option A: Quick fix (temporary – data lost again on next restart)

**Goal:** See availability on the live site right now, knowing it will disappear after the next Render restart or sleep.

1. **Trigger scrapes on production**  
   From your project folder, in Terminal run:
   ```bash
   ./run_render_scrapes.sh
   ```
   This calls Render’s API to scrape Hill Roads and One Leisure St Ives. Each scrape can take a few minutes.  
   To also scrape Linton Village College, run (replace with your Render URL if different):
   ```bash
   curl -X POST "https://badminton-court-finder.onrender.com/api/scrape" \
     -H "Content-Type: application/json" \
     -d '{"facility":"Linton Village College"}'
   ```

2. **Wait for scrapes to finish**, then refresh the live site. You should see “last updated” times and availability until the next time Render restarts or the app sleeps.

---

### Option B: Proper fix (data survives restarts) — use Render’s free PostgreSQL

**Goal:** Production keeps data across restarts. No disks needed (disks aren’t available on free instances).

The app is **already updated** to use PostgreSQL when you set `DATABASE_URL`. You add a **free PostgreSQL database** in the same Render account and connect your web service to it. Same dashboard, free tier, data persists.

**Step-by-step:** see **[RENDER_POSTGRES_SETUP.md](RENDER_POSTGRES_SETUP.md)**. In short:

1. In Render dashboard: **New +** → **PostgreSQL** → create a **Free** database (same region as your app).
2. Copy the **Internal Database URL** from the new database’s **Connections** section.
3. In your **Web Service** → **Environment** → add `DATABASE_URL` = (paste that URL). Save (app will redeploy).
4. After deploy, run `./run_render_scrapes.sh` once to populate the DB; then data will persist across restarts.

---

## Summary

| Question | Answer |
|----------|--------|
| Was data deleted by a bug? | No. Local DB has data. |
| Is the frontend broken? | No. It shows what the API returns. |
| Why does production show “never” and no courts? | Production DB is empty because Render’s disk is wiped on restart. |
| Quick fix? | Run `./run_render_scrapes.sh` (and optionally the Linton scrape curl). Data will appear until the next restart. |
| Long-term fix? | Add Render’s free PostgreSQL and set `DATABASE_URL` (see RENDER_POSTGRES_SETUP.md). |
