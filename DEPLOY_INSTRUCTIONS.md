# Step-by-Step Deployment Instructions

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

**Optional Variables (have defaults):**
- `FLASK_DEBUG` = `False`
- `MAX_SCRAPES_PER_DAY` = `3`
- `MAX_SCRAPES_PER_HOUR` = `1`
- `MIN_CACHE_AGE_SECONDS` = `3600`

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

## Part 3: Deploy Frontend to GitHub Pages

### Step 1: Update Frontend with Your API URL
1. Open `index.html` in your code editor
2. Find line ~316 that says:
   ```javascript
   const API_URL = window.location.hostname === 'localhost' 
       ? 'http://localhost:5000' 
       : 'https://your-app-name.onrender.com';
   ```
3. Replace `https://your-app-name.onrender.com` with your actual Render URL
4. Save the file

### Step 2: Commit and Push Changes
In terminal:

```bash
git add index.html
git commit -m "Update API URL for production"
git push origin main
```

### Step 3: Enable GitHub Pages
1. Go to your repository on GitHub: https://github.com/Givesheals/badminton-court-finder
2. Click **"Settings"** tab
3. In the left sidebar, click **"Pages"**
4. Under "Source", select:
   - Branch: **main**
   - Folder: **/ (root)**
5. Click **"Save"**

### Step 4: Wait for Deployment
1. GitHub will show "Your site is ready to be published at..."
2. Wait 1-2 minutes
3. Your site will be live at: `https://givesheals.github.io/badminton-court-finder/`

### Step 5: Test Your Frontend
1. Open your browser
2. Go to: `https://givesheals.github.io/badminton-court-finder/`
3. Try selecting some days and searching for courts

---

## Part 4: Render Free Tier Notes

**Important things to know about Render's free tier:**

1. **Sleep after inactivity**: Free apps sleep after 15 minutes of no activity
2. **Cold starts**: First request after sleep takes 30-60 seconds to wake up
3. **750 hours/month free**: Enough for hobby projects
4. **Upgrade if needed**: Basic plan is $7/month for always-on service

**To avoid slow first loads:**
- Consider upgrading to Basic plan ($7/month)
- Or set up a health check ping service (like cron-job.org) to keep it awake

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
2. Verify API URL in index.html is correct
3. Make sure CORS is enabled (already in app.py)
4. Check API is running: visit health endpoint in browser

### If GitHub Pages Shows 404:
1. Wait 2-3 minutes (can take time to deploy)
2. Check Settings → Pages shows "Your site is published"
3. Make sure index.html is in root of repo
4. Try accessing with trailing slash: `https://givesheals.github.io/badminton-court-finder/`

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

- **Frontend (GitHub Pages)**: `https://givesheals.github.io/badminton-court-finder/`
- **Backend API (Render)**: `https://YOUR-APP-NAME.onrender.com`

Save these somewhere safe!
