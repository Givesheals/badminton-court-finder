# More permanent free database options

Render’s **free PostgreSQL** expires after **30 days** (then a 14-day grace period before deletion). The banner you see is correct: the instance will be removed unless you upgrade to a paid plan.

If you want a **free, long-term** database for this app, use an external Postgres provider and keep using Render only for the web app. The app already uses `DATABASE_URL` — you just point it at the new database.

---

## Option 1: Neon (recommended)

**Neon** offers free PostgreSQL with **no time limit** and no credit card required.

- **Free tier:** 0.5 GB storage per project, always free, no expiry  
- **Connection:** Standard Postgres URL; works with your app as-is  
- **Use case:** Small apps like this one

### Steps

1. Sign up at [neon.tech](https://neon.tech) (free).
2. Create a new project (e.g. “badminton-court-finder”).
3. In the Neon dashboard, open **Connection details** and copy the **connection string** (Postgres URL).
4. In **Render** → your **Web Service** → **Environment**, set:
   - **Key:** `DATABASE_URL`  
   - **Value:** paste the Neon connection string (replace Render’s Postgres URL).
5. Save so Render redeploys. The app will use Neon instead of Render Postgres.
6. Run `./run_render_scrapes.sh` once to fill the new DB.

No code changes are needed; the app already uses `DATABASE_URL` from the environment.

---

## Option 2: Supabase

**Supabase** provides free PostgreSQL (plus auth/storage) with a generous free tier.

- **Free tier:** 500 MB database, no expiry for normal use  
- **Connection:** Postgres URL from the Supabase project  
- **Use case:** Good if you might add auth or other Supabase features later

### Steps

1. Sign up at [supabase.com](https://supabase.com) (free).
2. Create a new project.
3. In the project: **Settings** → **Database** → **Connection string** (URI). Copy the URI; use the **Session mode** (direct) URL if you only have one app.
4. In **Render** → your **Web Service** → **Environment**, set `DATABASE_URL` to that URI. (Supabase uses `postgres://`; the app converts it to `postgresql://` automatically.)
5. Save, let Render redeploy, then run `./run_render_scrapes.sh` once.

Again, no code changes needed.

---

## Summary

| Provider   | Free tier        | Expires?     | Effort                          |
|-----------|------------------|-------------|----------------------------------|
| Render    | 30 days then gone| Yes (30 days)| Already using it                |
| **Neon**  | 0.5 GB, always free | No       | New project → copy URL → set env |
| **Supabase** | 500 MB, free   | No (normal use) | New project → copy URL → set env |

**Recommendation:** Use **Neon** for a simple, permanent free Postgres. Create a project, copy the connection string, set `DATABASE_URL` on your Render Web Service to that string, redeploy, and run the scrape script once. Your data will persist without the 30-day limit.
