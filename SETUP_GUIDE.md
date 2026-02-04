# Quick Setup Guide

Follow these steps to get your badminton court finder live!

## Step 1: Get Your Render URL

If you've already deployed to Render:
1. Go to https://render.com/dashboard
2. Find your `badminton-court-finder` service
3. Copy the URL (looks like `https://badminton-court-finder-xyz.onrender.com`)

If you haven't deployed yet:
- See [DEPLOY_INSTRUCTIONS.md](DEPLOY_INSTRUCTIONS.md) for full walkthrough

## Step 2: Update Frontend with API URL

1. Open `index.html` in your code editor
2. Find line ~316:
   ```javascript
   const API_URL = window.location.hostname === 'localhost' 
       ? 'http://localhost:5000' 
       : 'https://your-app-name.onrender.com'; // TODO: Update with your Render URL
   ```
3. Replace `https://your-app-name.onrender.com` with your actual Render URL
4. Save the file

## Step 3: Commit and Push

```bash
cd /Users/simon.parker/Developer/badminton-court-finder
git add .
git commit -m "Add frontend and update for Render deployment"
git push origin main
```

## Step 4: Enable GitHub Pages

1. Go to https://github.com/Givesheals/badminton-court-finder/settings/pages
2. Under "Source":
   - Branch: **main**
   - Folder: **/ (root)**
3. Click **Save**
4. Wait 1-2 minutes

## Step 5: Test Everything

### Test Backend (Render)
```bash
# Replace with your actual Render URL
curl https://your-app-name.onrender.com/health
curl https://your-app-name.onrender.com/api/facilities
```

### Test Frontend (GitHub Pages)
Open in browser: `https://givesheals.github.io/badminton-court-finder/`

Try:
1. Select a few days
2. Set a time range
3. Click "Find Available Courts"
4. You should see results!

## Troubleshooting

### "Error searching for courts"
- Check browser console (F12) for details
- Verify API URL in index.html is correct
- Make sure Render backend is running (not sleeping)
- Try visiting the health endpoint directly

### Backend shows 404
- Wait a minute - Render free tier apps sleep after 15min
- First request takes 30-60 seconds to wake up
- Try again after waiting

### No results found
- This might be accurate! Try:
  - Selecting more days
  - Expanding time range
  - Different dates

## Next Steps

Once everything works:

1. **Bookmark your URLs**:
   - Frontend: `https://givesheals.github.io/badminton-court-finder/`
   - Backend: `https://your-app-name.onrender.com`

2. **Share with friends**: Send them the GitHub Pages URL

3. **Monitor usage**: Check Render dashboard occasionally

4. **Add more facilities**: See "Adding New Facilities" in README.md

## Cost Summary

- **GitHub Pages**: FREE forever ✅
- **Render Free Tier**: FREE (with cold starts) ✅
- **Render Basic**: $7/month (always-on) - upgrade if needed

Total cost: **$0-7/month** depending on your needs.

## Support

- Detailed deployment: [DEPLOY_INSTRUCTIONS.md](DEPLOY_INSTRUCTIONS.md)
- Technical details: [DEPLOYMENT.md](DEPLOYMENT.md)
- Quick reference: [DEPLOY_CHECKLIST.md](DEPLOY_CHECKLIST.md)
