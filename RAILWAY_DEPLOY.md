# Railway Deployment Instructions

Railway is better for low usage - you'll likely pay $0-2/month instead of $5/month.

## Step 1: Go to Railway

1. Open your web browser
2. Go to: **https://railway.app/**
3. You'll see the Railway homepage

## Step 2: Sign Up with GitHub

1. Click the **"Start a New Project"** button (or "Login" if you see that)
2. Click **"Login with GitHub"**
3. You'll be redirected to GitHub
4. Click **"Authorize Railway"** on the GitHub page
5. You'll be redirected back to Railway

## Step 3: Create New Project

1. You should now see a button that says **"New Project"** or **"Deploy from GitHub repo"**
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**

## Step 4: Select Your Repository

1. You'll see a list of your GitHub repositories
2. Find and click: **"badminton-court-finder"**
3. Railway will start analyzing your repository

## Step 5: Wait for Initial Setup

Railway will:
- Detect your Dockerfile automatically
- Start building your app
- This takes 2-3 minutes

You'll see a build progress screen with logs scrolling.

## Step 6: Add Environment Variables

This is IMPORTANT - Railway won't work without your credentials.

1. Look for your project in the Railway dashboard
2. Click on your service/app name
3. Click on the **"Variables"** tab (or look for a settings icon)
4. Click **"Add Variable"** or **"New Variable"**

Add these variables one by one:

### Variable 1:
- **Key**: `LVC_USERNAME`
- **Value**: `theparker1337@gmail.com`
- Click "Add" or press Enter

### Variable 2:
- **Key**: `LVC_PASSWORD`
- **Value**: `CourtFinder123!`
- Click "Add" or press Enter

### Variable 3:
- **Key**: `PORT`
- **Value**: `5000`
- Click "Add" or press Enter

### Optional Variables (skip if you want):
- `FLASK_DEBUG` = `False`
- `MAX_SCRAPES_PER_DAY` = `3`
- `MAX_SCRAPES_PER_HOUR` = `1`

## Step 7: Redeploy After Adding Variables

After adding variables:
1. Click on the **"Deployments"** tab
2. Click **"Redeploy"** or Railway might automatically redeploy
3. Wait 2-3 minutes for rebuild

## Step 8: Get Your URL

1. Once deployment is complete (status shows "Active" or "Success")
2. Look for **"Domains"** section or a **"Settings"** tab
3. Click **"Generate Domain"** or you'll see a URL like:
   - `your-app-name.up.railway.app`
4. **Copy this URL**

## Step 9: Test Your Deployment

Open Terminal (Command + Space, type "Terminal") and test:

### Test 1: Health Check
Type this (replace YOUR-URL with your Railway URL):

```
curl https://YOUR-URL/health
```

Example:
```
curl https://badminton-court-finder-production.up.railway.app/health
```

You should see: `{"status":"healthy"}`

### Test 2: Facilities
```
curl https://YOUR-URL/api/facilities
```

You should see: `{"facilities":["Linton Village College"]}`

### Test 3: Availability
```
curl "https://YOUR-URL/api/availability?facility=Linton%20Village%20College&date=2026-02-06"
```

You should see available time slots.

## Step 10: Check Usage and Costs

1. In Railway dashboard, click on your project
2. Look for **"Usage"** tab
3. You'll see:
   - Hours used
   - Cost estimate
   - Credits remaining

With Railway's free tier ($5 credit + 500 hours), you'll likely pay **$0/month** for 100 queries.

## Railway Pricing Notes

- **Free tier**: $5 credit per month + 500 hours
- Your app will likely use less than 50 hours/month with low traffic
- **Estimated cost**: $0-2/month for your usage
- Much better than DigitalOcean's fixed $5/month

## Troubleshooting

### Build Fails
1. Click on the failed deployment
2. Check the **"Build Logs"**
3. Look for errors (usually in red)
4. Common issues:
   - Dockerfile error
   - Missing dependencies

### App Not Responding
1. Check **"Deploy Logs"** tab
2. Look for error messages
3. Verify environment variables are set correctly

### Playwright Browser Issues
- Railway should handle Playwright installation automatically
- If it fails, check deploy logs for "chromium" errors

## Next Steps After Deployment

1. Test all endpoints (health, facilities, availability)
2. Save your Railway URL somewhere
3. Monitor usage for first few days
4. Check the Usage tab weekly to see costs

## Need Help?

If you get stuck:
1. Tell me which step you're on
2. Copy any error messages you see
3. Take a screenshot if helpful

I'll help you fix it!
