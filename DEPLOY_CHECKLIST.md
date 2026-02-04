# Render Deployment Checklist

## Pre-Deployment ✅
- [x] Code committed to GitHub
- [x] All files staged and pushed
- [x] Dockerfile created
- [x] Environment variables documented
- [x] Frontend created (index.html)

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
- `LVC_USERNAME` = `theparker1337@gmail.com`
- `LVC_PASSWORD` = `CourtFinder123!`
- `PORT` = `5000`

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

## Frontend Deployment (GitHub Pages)

### Step 1: Update API URL
1. Open `index.html`
2. Find the API_URL constant (around line 316)
3. Replace with your Render URL
4. Save file

### Step 2: Commit Changes
```bash
git add index.html
git commit -m "Update API URL for production"
git push origin main
```

### Step 3: Enable GitHub Pages
1. Go to GitHub repo → **Settings** → **Pages**
2. Source: **main** branch, **/ (root)** folder
3. Click **Save**
4. Wait 1-2 minutes for deployment

### Step 4: Test Frontend
Visit: `https://givesheals.github.io/badminton-court-finder/`

## Post-Deployment Checklist

- [ ] Backend health check passes
- [ ] Backend facilities endpoint works
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
- GitHub Pages: Usually just works, check browser console if issues

### Cost Monitoring
- Render Free Tier: $0/month (with sleep)
- Render Basic: $7/month (always-on)
- GitHub Pages: FREE forever

## Troubleshooting

### Backend Issues
1. Check Render logs
2. Verify environment variables are set
3. Test health endpoint first
4. Check Playwright browser installation in logs

### Frontend Issues
1. Open browser console (F12)
2. Check for CORS errors
3. Verify API URL is correct in index.html
4. Test API directly with curl

### Connection Issues
1. Verify CORS is enabled (already in app.py)
2. Check API is live (visit health endpoint)
3. Check for mixed content (http vs https)

## URLs Reference

After deployment, save these:

- **Frontend**: `https://givesheals.github.io/badminton-court-finder/`
- **Backend**: `https://[your-app-name].onrender.com`

## Budget Safety

- GitHub Pages: Always free
- Render Free Tier: Free (with cold starts)
- Render Basic: $7/month fixed
- Total recommended cost: $0-7/month
