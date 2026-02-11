# Cursor Context - Badminton Court Finder

## What We're Building
A web application that solves the badminton court booking problem: instead of searching through 10+ different websites/apps with different UIs, logins, and booking systems, users can search one simple interface to find available courts across Cambridge.

## The Problem
- Badminton players have to search multiple websites to find available courts
- Each facility has a different UI, login system, and booking interface
- Most apps are built around 1-hour bookings (badminton needs 2 hours minimum)
- It's frustrating and time-consuming

## Our Solution
A website where users can ask: "What courts are free Wednesday evening?" and get back a list of all available courts across Cambridge facilities.

## MVP (What We're Building First)
Simple query interface:
- User enters: day + time window (e.g., "Wednesday 6-8pm")
- System returns: list of available courts across all facilities
- That's it. No booking, no accounts, no fancy features yet.

## How It Works (Technical)
- We scrape/access availability data from Cambridge sports centres
- We store it in a database
- User queries the database through a simple web interface
- We show them what's available
- **Display:** "Last updated: never" means no successful scrape has run yet for that facility on this database (e.g. new DB or a failure).

## Tech Stack
- **Frontend**: Static HTML/CSS/JS on GitHub Pages
- **Backend**: Python + Flask (Render, Docker)
- **Database**: Neon PostgreSQL (production, persistent); SQLite (local dev)
- **Deployment**: GitHub Pages (frontend) + Render (backend). Scheduled scrapes via cron-job.org (POST /api/scrape-all every 6 hours).

## Current state (as of last update)
- **Facilities**: Hill Roads Sport and Tennis Centre, One Leisure St Ives (auto-scraped every 6h); Linton Village College excluded (scraper broken on Render).
- **Scrape-all**: POST /api/scrape-all triggers all facilities except EXCLUDE_SCRAPE_FACILITIES (env var, default Linton). Cron runs at 00:00, 06:00, 12:00, 18:00 UTC.
- **Data flow**: Scrapers overwrite facility data on each run; past slots (more than 24h ago) are purged after each successful scrape. "Last updated: never" means no successful scrape has run yet for that facility on this DB.

## Team
- **You**: Building the frontend/UI, general product thinking
- **Martin**: Data engineer, building the scraping pipeline and backend
- Both of you will use AI coding tools (Cursor, ChatGPT, etc.) to write code.

## Current Phase
Live with 3 facilities (2 auto-scraped, 1 excluded). Adding more Cambridge facilities; fixing Linton scraper on Render when needed.

## Key Constraints
- Web-based only (no native app - that's the whole point!)
- Must work without partnerships/permissions from facilities
- Data must be fresh (can't show outdated availability)
- Must aggregate 10+ facilities in MVP

## Questions Cursor Might Help With
- "How do I scrape this website?"
- "How do I build a React component for searching?"
- "How do I structure this database?"
- "How do I deploy this?"

This is a side project - we're learning as we go and using AI tools to help us move fast.
