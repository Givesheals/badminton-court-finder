# Deploy Streamlit as the Live Frontend

The **main UI** for Badminton Court Finder is the Streamlit app (`streamlit_app.py`). It is **live** at **[https://court-finder.streamlit.app](https://court-finder.streamlit.app)**. This guide describes how it was deployed and how to redeploy or replicate (Streamlit Community Cloud).

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

### Step 5: Set the backend URL (optional)

The app **defaults** to the production API (`https://badminton-court-finder.onrender.com`), so the deployed app works without any env var. If your Render backend has a **different** URL, in **Advanced settings** add an **Environment variable** (or **Secrets**): **Key** `API_BASE_URL`, **Value** your Render URL. If you use the Secrets panel, put the value in quotes for valid TOML (e.g. `API_BASE_URL = "https://your-app.onrender.com"`). If secrets are missing or invalid, the app falls back to the default URL and still runs.

Deploy. The first run may take a few minutes.

### Step 6: Get your live URL

After deployment you’ll get a URL like `https://[your-app-name].streamlit.app`. The current app is **https://court-finder.streamlit.app**. Share this with testers; they get the full UI (day picker, time range, “Find Available Courts”, “Scrape all facilities”, Settings).

### Step 7: (Optional) Update docs

- In **README.md** and **DEPLOYMENT.md**, list the Streamlit URL as the frontend.

---

## Limits and notes (Streamlit Community Cloud)

- **Free tier**: Apps may sleep after inactivity; first load after sleep can be slow.
- **First search / after idle**: "Find Available Courts" may take around 30 seconds when the Render backend is cold (free tier). Once the backend is awake, later searches in the same session are faster until the backend sleeps again (~15 min inactivity).
- **Secrets**: Use Streamlit Cloud’s “Secrets” for any sensitive env vars (e.g. if you ever need an API key in the frontend; currently the app only needs `API_BASE_URL` pointing at Render). Use quoted values in TOML to avoid parse errors.
- **Backend**: Your Render backend is unchanged. Streamlit Cloud only runs the UI; all data and scraping stay on Render.

---

## Summary


Once deployed, Streamlit is the frontend; share the `*.streamlit.app` URL with users.
