# Step-by-Step Deployment Instructions

**Local setup first:** If you haven’t run the app locally yet, follow [GETTING_STARTED.md](GETTING_STARTED.md) (clone, `.env`, `pip install -r requirements-backend.txt`, run API and Streamlit). This document covers **deploying the backend to Render** and **Streamlit frontend** via [STREAMLIT_DEPLOY.md](STREAMLIT_DEPLOY.md).

## Part 1: Deploy Backend API to Render

### Step 1: Open Terminal
1. On your Mac, press `Command + Space` to open Spotlight
2. Type "Terminal" and press Enter
3. A black window will open - this is your terminal

### Step 2: Navigate to Your Project Folder
In the terminal, type this EXACT command and press Enter:

```bash
cd /Users/simon.parker/Developer/badminton-court-finder
```

You should see the path change in your terminal prompt.

### Step 3: Verify You're in the Right Place
Type this command and press Enter:

```bash
pwd
```

You should see: `/Users/simon.parker/Developer/badminton-court-finder`

If you see something different, repeat Step 2.

### Step 4: Push Code to GitHub
First, check if you have uncommitted changes:

```bash
git status
```

If there are changes, commit and push them:

```bash
git add .
git commit -m "Add frontend and update deployment docs"
git push origin main
```

**What might happen:**
- If it asks for your GitHub password, enter it (or use a personal access token)
- If it says "Permission denied", you may need to set up SSH keys (we can do this if needed)
- If it works, you'll see messages about uploading files

**If you get an error**, copy the entire error message and we'll fix it together.

---

## Part 2: Deploy Backend to Render

### Step 1: Create/Login to Render Account
1. Open your web browser
2. Go to: https://render.com/
3. Click "Get Started" (if new) or "Log In" (if you have an account)
4. **Recommended**: Sign up with GitHub for easy integration

### Step 2: Create a New Web Service
1. Once logged in, click **"New +"** button (top right)
2. Select **"Web Service"**

### Step 3: Connect GitHub Repository
1. If first time, click **"Connect GitHub"**
2. Authorize Render to access your repositories
3. Find and select: **"badminton-court-finder"**
4. Click **"Connect"**

### Step 4: Configure the Web Service

Fill in these settings:

- **Name**: `badminton-court-finder` (or your preferred name)
- **Region**: Choose closest to you (e.g., Oregon USA, Frankfurt EU)
- **Branch**: `main`
- **Root Directory**: (leave blank)
- **Runtime**: `Docker`
- **Instance Type**: **Free** (or Basic if you need more reliability)

### Step 5: Add Environment Variables

Scroll down to **"Environment Variables"** section and add these:

**Required Variables:**
- **Key**: `LVC_USERNAME`
- **Value**: `theparker1337@gmail.com`

- **Key**: `LVC_PASSWORD`
- **Value**: `CourtFinder123!`

- **Key**: `PORT`
- **Value**: `5000`

**Important – persistent database:** Add `DATABASE_URL` with your Neon (or other Postgres) connection string so data survives restarts. See [FREE_DB_ALTERNATIVES.md](FREE_DB_ALTERNATIVES.md) or [RENDER_POSTGRES_SETUP.md](RENDER_POSTGRES_SETUP.md).

**Scraping (required):** All scrapers use LLM extraction. Add `OPENAI_API_KEY` (your OpenAI key) on Render. See [DEPLOYMENT.md](DEPLOYMENT.md) → "Render: setting up scraping".

**Optional Variables (have defaults):**
- `FLASK_DEBUG` = `False`
- `MAX_SCRAPES_PER_DAY` = `3`
- `MAX_SCRAPES_PER_HOUR` = `1`
- `MIN_CACHE_AGE_SECONDS` = `3600`
- `EXCLUDE_SCRAPE_FACILITIES` = (optional; comma-separated names to skip in scrape-all; default: Linton Village College, due to bot protection)

### Step 6: Deploy
1. Click **"Create Web Service"** at the bottom
2. Render will start building your app
3. **This takes 5-10 minutes** - be patient!
4. Watch the build logs to see progress

### Step 7: Get Your API URL
1. Once deployment is complete (status shows "Live")
2. You'll see a URL like: `https://badminton-court-finder.onrender.com`
3. **Copy this URL** - you'll need it for the frontend!

### Step 8: Test Your API
Open terminal and test:

```bash
curl https://YOUR-RENDER-URL/health
```

Example:
```bash
curl https://badminton-court-finder.onrender.com/health
```

You should see: `{"status":"healthy"}`

Test facilities:
```bash
curl https://YOUR-RENDER-URL/api/facilities
```

You should see: `{"facilities":["Linton Village College"]}`

---

## Part 3: Deploy Frontend

The app is live at [https://court-finder.streamlit.app](https://court-finder.streamlit.app). To deploy or redeploy, follow [STREAMLIT_DEPLOY.md](STREAMLIT_DEPLOY.md) (Streamlit Community Cloud, set `API_BASE_URL` to your Render URL).

---

## Part 4: Render Free Tier Notes

**Important things to know about Render's free tier:**

1. **Sleep after inactivity**: Free apps sleep after 15 minutes of no activity
2. **Cold starts**: First request after sleep takes 30-60 seconds to wake up
3. **750 hours/month free**: Enough for hobby projects
4. **Upgrade if needed**: Basic plan is $7/month for always-on service

**To avoid slow first loads:**
- Consider upgrading to Basic plan ($7/month)
- Or use an external health-check / uptime service to ping `/health` periodically (the repo's GitHub Actions workflow already wakes Render before each scheduled scrape)

---

## Troubleshooting

### If GitHub Push Fails:
**Error: "Permission denied"**
- You may need to set up SSH keys or use HTTPS instead
- Try: `git remote set-url origin https://github.com/Givesheals/badminton-court-finder.git`
- Then try `git push origin main` again

### If Render Build Fails:
1. Click on your web service in Render dashboard
2. Go to **"Logs"** tab
3. Look for error messages (usually in red)
4. Common issues:
   - Playwright browser installation failing
   - Missing environment variables
   - Docker build errors

### If API Doesn't Work After Deployment:
1. Check **"Logs"** in Render dashboard
2. Verify environment variables are set correctly
3. Make sure the URL is correct (check for typos)
4. Test health endpoint first: `curl https://your-url.onrender.com/health`

### If Frontend Can't Connect to API:
1. Check browser console for errors (F12 → Console)
2. In Streamlit, open Settings and verify Backend API URL points to your Render URL
3. Make sure CORS is enabled (already in app.py)
4. Check API is running: visit health endpoint in browser

---

## Need Help?

If you get stuck at any step:
1. **Copy the exact error message** you see
2. **Tell me which step number** you're on
3. **Take a screenshot** if possible

I'll help you fix it!

---

## Summary of Your URLs

After successful deployment:

- **Frontend (Streamlit)**: [https://court-finder.streamlit.app](https://court-finder.streamlit.app)
- **Backend API (Render)**: `https://YOUR-APP-NAME.onrender.com`

Save these somewhere safe!
