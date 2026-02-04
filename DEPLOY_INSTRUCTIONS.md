# Step-by-Step Deployment Instructions

## Part 1: Push Code to GitHub

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

### Step 4: Check Git Status
Type this command and press Enter:

```bash
git status
```

You should see "Your branch is ahead of 'origin/main' by 1 commit" or similar. This means you have code ready to push.

### Step 5: Push to GitHub
Type this command and press Enter:

```bash
git push origin main
```

**What might happen:**
- If it asks for your GitHub password, enter it (or use a personal access token)
- If it says "Permission denied", you may need to set up SSH keys (we can do this if needed)
- If it works, you'll see messages about uploading files

**If you get an error**, copy the entire error message and we'll fix it together.

---

## Part 2: Deploy to DigitalOcean

### Step 1: Create/Login to DigitalOcean Account
1. Open your web browser
2. Go to: https://www.digitalocean.com/
3. Click "Sign Up" (if new) or "Log In" (if you have an account)
4. Complete signup/login process

### Step 2: Create a New App
1. Once logged in, look for "Apps" in the left sidebar menu
2. Click on "Apps"
3. Click the big blue button that says "Create App"

### Step 3: Connect GitHub
1. You'll see options to connect a source - choose **"GitHub"**
2. If this is your first time, click "Authorize DigitalOcean" 
3. You'll be redirected to GitHub to authorize
4. Click "Authorize DigitalOcean" on GitHub
5. You'll be redirected back to DigitalOcean

### Step 4: Select Your Repository
1. You should now see a list of your GitHub repositories
2. Find and click on: **"badminton-court-finder"**
3. Make sure the branch says **"main"** (it should by default)
4. Click "Next" button at the bottom

### Step 5: Configure the App
DigitalOcean should automatically detect:
- **Type**: Docker
- **Dockerfile Path**: `Dockerfile`

**If it doesn't auto-detect:**
- Click "Edit" next to the service
- Change "Source Type" to "Docker"
- Make sure "Dockerfile Path" says `Dockerfile`
- Make sure "HTTP Port" says `5000`

Click "Next"

### Step 6: Choose Instance Size
1. You'll see "Instance Size" options
2. Select: **"basic-xxs"** (this is the smallest/cheapest option - $5/month)
3. Click "Next"

### Step 7: Add Environment Variables
This is IMPORTANT - you need to add your login credentials:

1. Scroll down to find "Environment Variables" section
2. Click "Edit" or "Add Variable"

**Add these variables one by one:**

**Variable 1:**
- **Key**: `LVC_USERNAME`
- **Value**: `theparker1337@gmail.com`
- **IMPORTANT**: Check the box that says "Encrypt" or "Secret" (this hides it)
- Click "Add" or "Save"

**Variable 2:**
- **Key**: `LVC_PASSWORD`
- **Value**: `CourtFinder123!`
- **IMPORTANT**: Check the box that says "Encrypt" or "Secret" (this hides it)
- Click "Add" or "Save"

**Optional variables (you can skip these, they have defaults):**
- `PORT` = `5000`
- `FLASK_DEBUG` = `False`
- `MAX_SCRAPES_PER_DAY` = `3`
- `MAX_SCRAPES_PER_HOUR` = `1`
- `MIN_CACHE_AGE_SECONDS` = `3600`

Click "Next"

### Step 8: Review and Deploy
1. Review all the settings you just configured
2. At the bottom, click the big button that says **"Create Resources"** or **"Deploy"**
3. You'll see a build progress screen
4. **This will take 5-10 minutes** - be patient!
5. You can watch the build logs to see what's happening

### Step 9: Wait for Deployment
- You'll see messages like "Building..." then "Deploying..."
- When it says "Live" or "Active", you're done!
- DigitalOcean will give you a URL like: `https://your-app-name-xyz123.ondigitalocean.app`
- **Copy this URL** - you'll need it!

---

## Part 3: Test Your Deployment

### Step 1: Test Health Check
Open a new terminal window and type:

```bash
curl https://YOUR-APP-URL-HERE/health
```

Replace `YOUR-APP-URL-HERE` with the actual URL DigitalOcean gave you.

**Example:**
```bash
curl https://badminton-court-finder-xyz123.ondigitalocean.app/health
```

You should see: `{"status":"healthy"}`

### Step 2: Test Facilities Endpoint
Type:

```bash
curl https://YOUR-APP-URL-HERE/api/facilities
```

You should see: `{"facilities":["Linton Village College"]}`

### Step 3: Test Availability
Type:

```bash
curl "https://YOUR-APP-URL-HERE/api/availability?facility=Linton%20Village%20College&date=2026-02-06"
```

You should see a list of available time slots.

---

## Part 4: Set Budget Alerts

### Step 1: Go to Billing
1. In DigitalOcean, click on your profile/account icon (top right)
2. Click "Billing" or "Settings" → "Billing"

### Step 2: Set Budget Alerts
1. Look for "Budget Alerts" or "Spending Alerts"
2. Click "Add Alert" or "Create Alert"
3. Set alerts at:
   - **$10/month** - Warning level
   - **$20/month** - Warning level  
   - **$50/month** - Critical level
4. Save each alert

### Step 3: (Optional) Set Spending Limit
1. Look for "Spending Limit" option
2. You can set a hard limit (e.g., $20/month) that stops services if exceeded
3. This is optional but recommended for safety

---

## Troubleshooting

### If GitHub Push Fails:
**Error: "Permission denied"**
- You may need to set up SSH keys or use HTTPS instead
- Try: `git remote set-url origin https://github.com/Givesheals/badminton-court-finder.git`
- Then try `git push origin main` again

### If DigitalOcean Build Fails:
1. Click on your app in DigitalOcean
2. Go to "Runtime Logs" tab
3. Look for error messages (usually in red)
4. Common issues:
   - Playwright browser installation failing
   - Missing environment variables
   - Port configuration wrong

### If App Doesn't Work After Deployment:
1. Check "Runtime Logs" in DigitalOcean dashboard
2. Verify environment variables are set correctly
3. Make sure the URL is correct (check for typos)

---

## Need Help?

If you get stuck at any step:
1. **Copy the exact error message** you see
2. **Tell me which step number** you're on
3. **Take a screenshot** if possible

I'll help you fix it!
