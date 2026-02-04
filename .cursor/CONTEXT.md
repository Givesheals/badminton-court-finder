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

## Tech Stack
- **Frontend**: Next.js + React (simple, AI-friendly)
- **Backend**: Python + Flask (Martin's comfort zone, great for scraping)
- **Database**: SQLite for MVP
- **Deployment**: Vercel (frontend) + Railway/Render (backend)

## Team
- **You**: Building the frontend/UI, general product thinking
- **Martin**: Data engineer, building the scraping pipeline and backend
- Both of you will use AI coding tools (Cursor, ChatGPT, etc.) to write code.

## Current Phase
Data Research Phase - We're figuring out which Cambridge facilities we can scrape from and how to get their availability data.

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
