# Render Deployment Checklist

## Pre-Deployment ✅
- [x] Code committed to GitHub
- [x] All files staged and pushed
- [x] Dockerfile created
- [x] Environment variables documented
- [x] Frontend: Streamlit on Community Cloud ([court-finder.streamlit.app](https://court-finder.streamlit.app))

## Backend Deployment (Render)

### Step 1: Create Render Account
1. Go to https://render.com/
2. Sign up with GitHub (recommended)
3. Authorize Render to access repositories

### Step 2: Create Web Service
1. Click **New +** → **Web Service**
2. Connect GitHub repository: `badminton-court-finder`
3. Click **Connect**

### Step 3: Configure Service
- **Name**: `badminton-court-finder`
- **Region**: Choose closest to you
- **Branch**: `main`
- **Runtime**: `Docker`
- **Instance Type**: **Free** (or Basic for $7/month)

### Step 4: Set Environment Variables
Add these in the Environment section:

#### Required:
- `PORT` = `5000`
- `LVC_USERNAME` / `LVC_PASSWORD` (for Linton when enabled)
- `DATABASE_URL` = your Neon or Postgres URL (so data persists; see [FREE_DB_ALTERNATIVES.md](FREE_DB_ALTERNATIVES.md))

#### Required for scraping:
- `OPENAI_API_KEY` = your OpenAI key (all scrapers use LLM extraction)

#### Optional (with defaults):
- `FLASK_DEBUG` = `False`
- `MAX_SCRAPES_PER_DAY` = `3`
- `MAX_SCRAPES_PER_HOUR` = `1`
- `MIN_CACHE_AGE_SECONDS` = `3600`

### Step 5: Deploy
1. Click **Create Web Service**
2. Wait 5-10 minutes for build
3. Note your URL: `https://your-app-name.onrender.com`

### Step 6: Test Backend
```bash
# Replace with your actual URL
curl https://your-app-name.onrender.com/health
curl https://your-app-name.onrender.com/api/facilities
```

## Frontend Deployment

### Frontend (Streamlit)
Live at **[https://court-finder.streamlit.app](https://court-finder.streamlit.app)**. Deploy or redeploy via [STREAMLIT_DEPLOY.md](STREAMLIT_DEPLOY.md): connect repo to Streamlit Community Cloud, main file `streamlit_app.py`, set `API_BASE_URL` to your Render URL. Root `requirements.txt` is minimal (streamlit + requests) so no config needed.

### Test Frontend
- [https://court-finder.streamlit.app](https://court-finder.streamlit.app)

## After adding a new scraper (e.g. One Leisure St Ives)

1. Add the scraper module under `scrapers/` and register it in `scraper_manager.py` (`self.scrapers`).
2. Add the facility’s booking URL in `streamlit_app.py` (`FACILITY_BOOKING_URLS`).
3. **Redeploy on Render** so `/api/facilities` includes the new facility:
   - Push to `main` (if auto-deploy is on), or
   - Render Dashboard → your service → **Manual Deploy** → **Deploy latest commit**.
4. Verify: `curl -s "https://badminton-court-finder.onrender.com/api/facilities"` includes the new facility name.

## Post-Deployment Checklist

- [ ] Backend health check passes
- [ ] Backend facilities endpoint works (and lists all facilities, including One Leisure St Ives)
- [ ] Backend availability endpoint returns data
- [ ] Frontend loads successfully
- [ ] Frontend can connect to backend API
- [ ] Search functionality works end-to-end
- [ ] Booking links work correctly
- [ ] Mobile responsive design works

## Monitoring

### Render Free Tier Notes
- Apps sleep after 15 minutes of inactivity
- First request after sleep takes 30-60 seconds
- 750 hours/month free
- Consider Basic plan ($7/month) for always-on service

### Check Logs
- Render: Dashboard → Your Service → Logs

### Cost Monitoring
- Streamlit Community Cloud: FREE
- Render Free Tier: $0/month (with sleep)
- Render Basic: $7/month (always-on)

## Troubleshooting

### Backend Issues
1. Check Render logs
2. Verify environment variables are set
3. Test health endpoint first
4. Check Playwright browser installation in logs

### Frontend Issues
1. Open browser console (F12)
2. Check for CORS errors
3. In Streamlit Settings, verify Backend API URL points to your Render URL
4. Test API directly with curl

### Connection Issues
1. Verify CORS is enabled (already in app.py)
2. Check API is live (visit health endpoint)
3. Check for mixed content (http vs https)

## URLs Reference

After deployment, save these:

- **Frontend (Streamlit)**: [https://court-finder.streamlit.app](https://court-finder.streamlit.app)
- **Backend (Render)**: `https://[your-app-name].onrender.com`

## Budget Safety

- Render Free Tier: Free (with cold starts)
- Render Basic: $7/month fixed
- Total recommended cost: $0-7/month
