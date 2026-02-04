# 🎉 Frontend Complete! Next Steps

## What We Just Did

✅ Created a beautiful, responsive frontend (`index.html`)
✅ Updated all documentation to reference Render (not DigitalOcean)
✅ Removed DigitalOcean-specific files
✅ Set up architecture for GitHub Pages hosting

## What You Need to Do Now

### Option 1: If You Already Have Backend on Render

1. **Get your Render URL**:
   - Go to https://render.com/dashboard
   - Find your service
   - Copy the URL (e.g., `https://badminton-court-finder-abc.onrender.com`)

2. **Update `index.html`**:
   - Open `index.html`
   - Line 316: Replace `https://your-app-name.onrender.com` with your actual URL
   - Save

3. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Add frontend with Render API URL"
   git push origin main
   ```

4. **Enable GitHub Pages**:
   - Go to: https://github.com/Givesheals/badminton-court-finder/settings/pages
   - Source: main branch, / (root)
   - Save

5. **Done!** Visit: `https://givesheals.github.io/badminton-court-finder/`

### Option 2: If You Need to Deploy Backend First

Follow the complete guide: [DEPLOY_INSTRUCTIONS.md](DEPLOY_INSTRUCTIONS.md)

Quick version:
1. Go to https://render.com/ and sign up with GitHub
2. Create new Web Service
3. Connect your `badminton-court-finder` repo
4. Set environment variables (see DEPLOY_INSTRUCTIONS.md)
5. Deploy
6. Then follow "Option 1" above

## Testing Locally First (Recommended)

You can test the frontend locally before deploying:

1. **Make sure your local API is running**:
   ```bash
   # In terminal 1
   cd /Users/simon.parker/Developer/badminton-court-finder
   python3 app.py
   ```
   Note: If port 5000 is in use, disable AirPlay Receiver in System Preferences

2. **Open the frontend**:
   - Simply double-click `index.html` in Finder
   - Or open in browser: `file:///Users/simon.parker/Developer/badminton-court-finder/index.html`

3. **Test the search**:
   - Select some days (try tomorrow and the next day)
   - Set time range (default 18:00-22:00 is good)
   - Click "Find Available Courts"
   - Should see results!

## Architecture Overview

```
┌──────────────────────────────────────┐
│  GitHub Pages                        │
│  Frontend (HTML/CSS/JS)              │
│  FREE ✅                             │
│  https://givesheals.github.io/...    │
└─────────────┬────────────────────────┘
              │
              │ API Calls
              ▼
┌──────────────────────────────────────┐
│  Render                              │
│  Backend API (Flask + Playwright)    │
│  FREE or $7/mo ✅                    │
│  https://your-app.onrender.com       │
└──────────────────────────────────────┘
```

## Frontend Features

Your new frontend includes:

✅ **Multi-day selection** - Click multiple days you're available
✅ **Time range picker** - Set start and end times
✅ **Duration filtering** - Find continuous 2-hour blocks (customizable)
✅ **Multiple courts** - Search for 1-4 courts
✅ **Beautiful UI** - Modern gradient design, responsive
✅ **Loading states** - Shows spinner while searching
✅ **Results grouping** - Organized by facility and date
✅ **Direct booking links** - One click to book
✅ **Error handling** - Helpful messages when things go wrong
✅ **Mobile responsive** - Works great on phones

## Important Files

| File | Purpose | Action Needed |
|------|---------|---------------|
| `index.html` | Frontend UI | ✏️ Update API URL (line 316) |
| `app.py` | Backend API | ✅ Already has CORS enabled |
| `DEPLOY_INSTRUCTIONS.md` | Step-by-step guide | 📖 Read if deploying |
| `SETUP_GUIDE.md` | Quick setup | 📖 Quick reference |

## Troubleshooting

### Can't test locally (port 5000 in use)
Disable AirPlay Receiver:
- System Preferences → General → AirDrop & Handoff
- Turn off "AirPlay Receiver"

### Frontend can't connect to backend
- Check API_URL in `index.html` is correct
- Check backend is running (visit health endpoint)
- Check browser console (F12) for errors

### No results found
- Might be accurate! Try:
  - More days selected
  - Wider time range
  - Future dates (facilities may not have far-future availability yet)

## Cost Summary

- **Total cost: $0-7/month**
  - GitHub Pages: FREE forever
  - Render Free Tier: FREE (sleeps after 15min, cold start)
  - Render Basic: $7/month (always-on, instant)

Start with free, upgrade to Basic if cold starts annoy you.

## Questions?

Refer to:
- **Beginner guide**: [DEPLOY_INSTRUCTIONS.md](DEPLOY_INSTRUCTIONS.md)
- **Technical details**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **Quick checklist**: [DEPLOY_CHECKLIST.md](DEPLOY_CHECKLIST.md)
- **Quick setup**: [SETUP_GUIDE.md](SETUP_GUIDE.md)

You're all set! Just need to:
1. Get your Render URL (or deploy if you haven't)
2. Update line 316 in index.html
3. Push to GitHub
4. Enable GitHub Pages

Then share your app with friends! 🏸
