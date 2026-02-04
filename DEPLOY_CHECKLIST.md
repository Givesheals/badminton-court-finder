# DigitalOcean Deployment Checklist

## Pre-Deployment ✅
- [x] Code committed to GitHub
- [x] All files staged and pushed
- [x] Dockerfile created
- [x] app.yaml configured
- [x] Environment variables documented

## Step 1: Create DigitalOcean Account
1. Go to https://www.digitalocean.com/
2. Sign up or log in
3. Verify email if needed

## Step 2: Create App in DigitalOcean
1. Go to **Apps** → **Create App**
2. Choose **GitHub** as source
3. Authorize DigitalOcean to access GitHub
4. Select repository: `Givesheals/badminton-court-finder`
5. Select branch: `main`
6. Click **Next**

## Step 3: Configure App
DigitalOcean should auto-detect:
- **Type**: Docker
- **Dockerfile Path**: `Dockerfile`
- **Port**: 5000

If not auto-detected, configure manually:
- **Build Command**: (leave empty, Dockerfile handles it)
- **Run Command**: (leave empty, Dockerfile handles it)
- **HTTP Port**: 5000

## Step 4: Set Instance Size
- **Instance Size**: `basic-xxs` (smallest/cheapest - $5/month)
- This is sufficient for low traffic

## Step 5: Set Environment Variables
Go to **Environment Variables** section and add:

### Required Secrets (mark as SECRET):
- `LVC_USERNAME` = `theparker1337@gmail.com` (mark as SECRET)
- `LVC_PASSWORD` = `CourtFinder123!` (mark as SECRET)

### Optional (with defaults):
- `PORT` = `5000`
- `FLASK_DEBUG` = `False`
- `MAX_SCRAPES_PER_DAY` = `3`
- `MAX_SCRAPES_PER_HOUR` = `1`
- `MIN_CACHE_AGE_SECONDS` = `3600`

## Step 6: Review and Deploy
1. Review configuration
2. Click **Create Resources**
3. Wait for build (5-10 minutes)
4. Watch build logs for any errors

## Step 7: Set Budget Alerts
1. Go to **Billing** → **Budget Alerts**
2. Set alerts at:
   - $10/month (warning)
   - $20/month (warning)
   - $50/month (critical)
3. Optionally set hard spending limit

## Step 8: Test Deployment
Once deployed, test endpoints:

```bash
# Get your app URL from DigitalOcean dashboard
APP_URL="https://your-app-name.ondigitalocean.app"

# Health check
curl $APP_URL/health

# List facilities
curl $APP_URL/api/facilities

# Get availability
curl "$APP_URL/api/availability?facility=Linton%20Village%20College&date=2026-02-06"
```

## Troubleshooting

### Build Fails
- Check build logs in DigitalOcean dashboard
- Verify Dockerfile is correct
- Check that Playwright browsers install correctly

### App Crashes
- Check runtime logs
- Verify environment variables are set
- Check database migration ran (should auto-run)

### Playwright Issues
- Ensure `playwright install chromium` runs in Dockerfile
- Check system dependencies are installed

## Next Steps After Deployment
1. Test all API endpoints
2. Monitor logs for first few hours
3. Check facility stats endpoint to verify scraping works
4. Set up monitoring/alerting if desired
