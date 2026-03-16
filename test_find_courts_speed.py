#!/usr/bin/env python3
"""
Speed test for "Find Available Courts" API path.

Simulates the exact API usage: one GET /api/facilities plus GET /api/availability
for each (facility, date). Asserts total time is under MAX_ELAPSED_SEC when the
backend is warm and only doing DB reads (no scrapes).

Run with: pytest test_find_courts_speed.py -v
Or: python test_find_courts_speed.py (requires app to be importable)
"""
import os
import sys
import time

# Project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Max allowed time for the full "find courts" API sequence (backend only, no network).
# Threshold is strict so that shared engine + batched queries are required (avoids per-request engine creation).
MAX_ELAPSED_SEC = 5.0

# Typical params from Streamlit UI
START_TIME = "18:00"
END_TIME = "22:00"


def test_find_courts_api_completes_within_time():
    """GET /api/facilities + GET /api/availability per (facility, date) must finish in < MAX_ELAPSED_SEC."""
    from datetime import datetime, timedelta
    from app import app

    today = datetime.now().date()
    # Two dates like the default Streamlit selection
    selected_dates = [today, today + timedelta(days=1)]
    selected_dates_str = [d.isoformat() for d in selected_dates]

    with app.test_client() as client:
        start = time.perf_counter()

        r_facilities = client.get("/api/facilities")
        assert r_facilities.status_code == 200, f"facilities returned {r_facilities.status_code}"
        data = r_facilities.get_json()
        facilities = data.get("facilities") or []
        assert facilities, "API must return at least one facility"

        for facility in facilities:
            for date_str in selected_dates_str:
                r_avail = client.get(
                    "/api/availability",
                    query_string={
                        "facility": facility,
                        "date": date_str,
                        "start_time": START_TIME,
                        "end_time": END_TIME,
                    },
                )
                assert r_avail.status_code in (200, 400), (
                    f"availability {facility} {date_str} returned {r_avail.status_code}"
                )

        elapsed = time.perf_counter() - start
        assert elapsed < MAX_ELAPSED_SEC, (
            f"Find courts API path took {elapsed:.2f}s (max {MAX_ELAPSED_SEC}s). "
            "Backend should only read from DB and respond quickly."
        )


if __name__ == "__main__":
    try:
        import pytest
        sys.exit(pytest.main([__file__, "-v"]))
    except ImportError:
        # Run without pytest
        try:
            test_find_courts_api_completes_within_time()
            print("PASS: Find courts API completed within time limit.")
        except AssertionError as e:
            print(f"FAIL: {e}")
            sys.exit(1)
