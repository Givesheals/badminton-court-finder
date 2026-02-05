#!/bin/bash
# Run Hill Roads then One Leisure scrapes on Render. Each can take several minutes.
set -e
BASE="https://badminton-court-finder.onrender.com"
echo "Triggering Hill Roads scrape..."
curl -s -X POST "$BASE/api/scrape" -H "Content-Type: application/json" -d '{"facility":"Hill Roads Sport and Tennis Centre"}'
echo ""
echo "Triggering One Leisure St Ives scrape..."
curl -s -X POST "$BASE/api/scrape" -H "Content-Type: application/json" -d '{"facility":"One Leisure St Ives"}'
echo ""
echo "Done."
