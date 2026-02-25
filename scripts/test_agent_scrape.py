#!/usr/bin/env python3
"""
Run an agent scrape for Hill Roads (easier venue) to test the full pipeline:
1. Access – navigate, login, reach timetable
2. Collect – LLM extracts slots from page (requires OPENAI_API_KEY)
3. Store – write to DB

Usage:
  export OPENAI_API_KEY=sk-...
  export AGENT_SCRAPE_FACILITIES="Hill Roads Sport and Tennis Centre"
  python scripts/test_agent_scrape.py

Or with .env containing OPENAI_API_KEY and AGENT_SCRAPE_FACILITIES.
"""
import os
import sys

# Project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("Set OPENAI_API_KEY in .env or environment to test LLM extraction.")
        sys.exit(1)
    os.environ.setdefault("AGENT_SCRAPE_FACILITIES", "Hill Roads Sport and Tennis Centre")

    from scraper_manager import ScraperManager
    from database import get_session, init_db, Facility, CourtAvailability

    sm = ScraperManager()
    facility_name = "Hill Roads Sport and Tennis Centre"
    print(f"Scraping {facility_name} (agent/LLM)...")
    result = sm.scrape_facility(facility_name)
    sm.close()

    print("Success:", result.get("success"))
    if result.get("error"):
        print("Error:", result["error"])
    data = result.get("data", [])
    print("Slots returned:", len(data))
    if data:
        for slot in data[:5]:
            print(" ", slot.get("date"), slot.get("start_time"), slot.get("end_time"))

    # Verify DB
    engine = init_db()
    session = get_session(engine)
    f = session.query(Facility).filter_by(name=facility_name).first()
    if f:
        count = session.query(CourtAvailability).filter_by(facility_id=f.id).count()
        print("Stored in DB:", count, "records for", facility_name)
    session.close()

if __name__ == "__main__":
    main()
