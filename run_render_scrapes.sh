#!/bin/bash
# Trigger all three facility scrapes on Render.
# Each scrape runs on the server and can take 5–15+ minutes; the request does not return until it finishes.
# So you may see no new output for 10–20 minutes — that is normal. Timeout is 20 min per scrape.
set -e
BASE="https://badminton-court-finder.onrender.com"
TIMEOUT=1200

echo "=== Badminton Court Finder: triggering scrapes on Render ==="
echo "Each request waits for the scrape to finish on the server (5–15+ min each). Don't close the terminal."
echo ""

echo "[1/3] Hill Roads Sport and Tennis Centre — triggering (timeout ${TIMEOUT}s)..."
curl -s --max-time "$TIMEOUT" -X POST "$BASE/api/scrape" \
  -H "Content-Type: application/json" \
  -d '{"facility":"Hill Roads Sport and Tennis Centre"}' | python3 -m json.tool 2>/dev/null || cat
echo ""

echo "[2/3] One Leisure St Ives — triggering (timeout ${TIMEOUT}s)..."
curl -s --max-time "$TIMEOUT" -X POST "$BASE/api/scrape" \
  -H "Content-Type: application/json" \
  -d '{"facility":"One Leisure St Ives"}' | python3 -m json.tool 2>/dev/null || cat
echo ""

echo "[3/3] Linton Village College — triggering (timeout ${TIMEOUT}s)..."
curl -s --max-time "$TIMEOUT" -X POST "$BASE/api/scrape" \
  -H "Content-Type: application/json" \
  -d '{"facility":"Linton Village College"}' | python3 -m json.tool 2>/dev/null || cat
echo ""

echo "Done. Refresh your live site to see last updated and availability."
