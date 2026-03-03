# Deploy Streamlit as the Live Frontend

The **main UI** for Badminton Court Finder is the Streamlit app (`streamlit_app.py`). It was built as the primary frontend, but only the static `index.html` was ever deployed to GitHub Pages. This guide gets the Streamlit app live so users can use it at a public URL.

## Option: Streamlit Community Cloud (recommended, free)

Streamlit offers free hosting at [share.streamlit.io](https://share.streamlit.io). Your app runs in the cloud and talks to your existing Render backend.

### Step 1: Push your code

Ensure your repo is up to date on GitHub (`main` branch). Streamlit Cloud deploys from GitHub.

### Step 2: Create a Streamlit Cloud account

1. Go to **https://share.streamlit.io**
2. Sign in with **GitHub**
3. Authorize Streamlit Cloud to access your repositories

### Step 3: Deploy the app

1. Click **"New app"**
2. **Repository**: `Givesheals/badminton-court-finder` (or your org/repo)
3. **Branch**: `main`
4. **Main file path**: `streamlit_app.py`
5. **App URL**: You can leave the default (e.g. `badminton-court-finder.streamlit.app`) or choose a name

### Step 4: Requirements (no change needed)

The repo’s root **`requirements.txt`** is minimal (streamlit + requests only) so Streamlit Cloud can install it without backend-only packages (e.g. `psycopg2-binary`). Use the default requirements file; no need to set a custom path.

### Step 5: Set the backend URL (required)

So the deployed Streamlit app talks to your Render API:

1. Still in **Advanced settings**, add an **Environment variable** (or **Secrets**):
   - **Key**: `API_BASE_URL`
   - **Value**: `https://badminton-court-finder.onrender.com` (your actual Render URL)

3. Deploy. The first run may take a few minutes.

### Step 6: Get your live URL

After deployment you’ll get a URL like:

**https://[your-app-name].streamlit.app**

That is your **live Streamlit frontend**. Share this with testers; they get the full UI (day picker, time range, “Find Available Courts”, “Scrape all facilities”, Settings).

### Step 7: (Optional) Set as primary in docs

- In **README.md** and **DEPLOYMENT.md**, list the Streamlit URL as the **main** frontend.
- Keep **https://givesheals.github.io/badminton-court-finder/** as the **static fallback** (no Streamlit dependency; works when Streamlit Cloud is down).

---

## Limits and notes (Streamlit Community Cloud)

- **Free tier**: Apps may sleep after inactivity; first load after sleep can be slow.
- **Secrets**: Use Streamlit Cloud’s “Secrets” for any sensitive env vars (e.g. if you ever need an API key in the frontend; currently the app only needs `API_BASE_URL` pointing at Render).
- **Backend**: Your Render backend is unchanged. Streamlit Cloud only runs the UI; all data and scraping stay on Render.

---

## Summary

| Before | After (migration complete) |
|--------|-----------------------------|
| Only static `index.html` on GitHub Pages was live | Streamlit app is live at `*.streamlit.app` |
| “Main UI” was only runnable locally | Main UI is public; share one link with users |
| GitHub Pages = only option for testers | Give testers the Streamlit URL (or keep both and document which is primary) |

Once deployed, your **intended** setup is in place: Streamlit as the primary frontend, static HTML as fallback.
