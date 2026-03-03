# Getting started (for new developers)

This guide gets you from zero to running the Badminton Court Finder locally. Use it with Cursor or any editor.

**Live app:** The Streamlit UI is at [https://court-finder.streamlit.app](https://court-finder.streamlit.app); the static fallback is on [GitHub Pages](https://givesheals.github.io/badminton-court-finder/).

## What you need

- **Python 3.9+** (3.10 or 3.11 is fine)
- **Git**
- **OpenAI API key** – required for scraping (all scrapers use LLM extraction)

## Step 1: Clone the repo

```bash
git clone https://github.com/YOUR_ORG/badminton-court-finder.git
cd badminton-court-finder
```

(Replace `YOUR_ORG` with the actual GitHub org or username.)

## Step 2: Environment variables (`.env`)

The app reads secrets and options from a `.env` file in the project root. **Do not commit `.env`** (it’s in `.gitignore`).

1. **Create `.env`** from the example:
   ```bash
   cp .env.example .env
   ```
2. **Edit `.env`** and add your values:
   - **`OPENAI_API_KEY`** – Required for scraping. Get a key at [platform.openai.com/api-keys](https://platform.openai.com/api-keys). Replace the placeholder with your key (starts with `sk-...`).
   - **Venue credentials** (for scrapers that need login):
     - `LVC_USERNAME` / `LVC_PASSWORD` – Linton Village College
     - `LOGIN_USERNAME` / `LOGIN_PASSWORD` – Hill Roads (and some others)

If you skip `.env`, the API and Streamlit app will still run; scrapers will fail when triggered (they need `OPENAI_API_KEY` and any venue credentials).

## Step 3: Install dependencies

```bash
pip install -r requirements-backend.txt
playwright install chromium
```

(`playwright install chromium` downloads a browser used for scraping. You only need to run it once per machine.)

## Step 4: Run the backend API

```bash
python app.py
```

The API will be at **http://localhost:5000**. Leave this terminal open.

- Health: [http://localhost:5000/health](http://localhost:5000/health)
- Facilities: [http://localhost:5000/api/facilities](http://localhost:5000/api/facilities)

## Step 5: Run the frontend (Streamlit)

In a **second terminal**, from the same project folder:

```bash
streamlit run streamlit_app.py
```

Open the URL shown (default **http://localhost:8501**). You can:

- Select days, time range, and click **Find Available Courts** (uses the API).
- Click **Scrape all facilities** to refresh data (runs in the background).

The Streamlit app defaults to the production backend (Render). To use a **local** backend instead, set `API_BASE_URL=http://localhost:5000` in your `.env` or open **Settings** in the app and enter that URL in **Backend API URL**.

## Step 6: (Optional) Test scraping

With `OPENAI_API_KEY` in `.env`, trigger a scrape from the Streamlit UI (e.g. "Scrape all facilities") or run:

```bash
python -c "
from dotenv import load_dotenv
load_dotenv()
from scrapers.hill_roads_agent_scraper import HillRoadsAgentScraper
HillRoadsAgentScraper(headless=True).scrape()
"
```

Check that the facility gets slots in the UI or via the API.

---

## Next steps

- **Deploy backend to Render**: [DEPLOYMENT.md](DEPLOYMENT.md) and [DEPLOY_INSTRUCTIONS.md](DEPLOY_INSTRUCTIONS.md)
- **Set up a persistent database (Neon)**: [FREE_DB_ALTERNATIVES.md](FREE_DB_ALTERNATIVES.md) or [RENDER_POSTGRES_SETUP.md](RENDER_POSTGRES_SETUP.md)
- **Scheduled scrapes (cron)**: [SCHEDULED_SCRAPES.md](SCHEDULED_SCRAPES.md) and [CRONJOB_ORG_SETUP.md](CRONJOB_ORG_SETUP.md)
- **OpenAI key and agent scraping on Render**: [DEPLOYMENT.md](DEPLOYMENT.md) → “Render: setting up scraping”

## Troubleshooting

- **“OPENAI_API_KEY is not set”** – Add it to `.env` (and restart the app) it is required for scraping.
- **“Install the openai package”** – Run `pip install -r requirements-backend.txt`.
- **“Executable doesn't exist” (Playwright)** – Run `playwright install chromium`.
- **Port 5000 in use** – Start the API with `PORT=5001 python app.py` and set Backend API URL in Streamlit to `http://localhost:5001`.
