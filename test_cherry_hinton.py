#!/usr/bin/env python3
"""
Tests for Cherry Hinton Leisure Centre scraper.

- Scraper is configured to scrape ~6 days (5–7); tests assert we don't limit to 2.
- Ensures multi-day availability is stored with correct date per day (avoids
  "one day written to all days" bug).
- Ensures slot structure has required keys.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Use a temp DB so we don't touch the main database
TEST_DB = tempfile.NamedTemporaryFile(suffix=".db", delete=False).name

# Cherry Hinton should show around 6 days (might be 5 or 7), definitely more than 2
EXPECTED_SCRAPE_DAYS_MIN = 5
EXPECTED_SCRAPE_DAYS_MAX = 7


def _mock_slots_for_date(date_str, day_name, count=2):
    """Return list of slot dicts for one day (expected_date must be used when scraping)."""
    return [
        {
            "date": date_str,
            "day_name": day_name,
            "start_time": "09:00",
            "end_time": "10:00",
            "court_number": "Court 1",
            "is_available": True,
        },
        {
            "date": date_str,
            "day_name": day_name,
            "start_time": "10:00",
            "end_time": "11:00",
            "court_number": "Court 1",
            "is_available": True,
        },
    ][:count]


def test_scraper_configured_for_multiple_days():
    """Cherry Hinton scraper must be set to scrape ~6 days (5–7), not 2."""
    from scrapers.cherry_hinton import SCRAPE_DAYS

    assert EXPECTED_SCRAPE_DAYS_MIN <= SCRAPE_DAYS <= EXPECTED_SCRAPE_DAYS_MAX, (
        f"SCRAPE_DAYS should be between {EXPECTED_SCRAPE_DAYS_MIN} and {EXPECTED_SCRAPE_DAYS_MAX} "
        f"(~6 days); got {SCRAPE_DAYS}"
    )
    assert SCRAPE_DAYS > 2, "SCRAPE_DAYS must be more than 2."


def test_store_availability_preserves_distinct_dates():
    """Storing slots for multiple days must result in each date in DB (not one date for all).
    Uses 2 days here as minimal case; real scraper uses SCRAPE_DAYS (~6)."""
    from datetime import date, timedelta
    from database import init_db, get_session, Facility, CourtAvailability

    # Isolated DB for test
    engine = init_db(db_path=TEST_DB)
    session = get_session(engine)

    # Create facility
    facility = session.query(Facility).filter_by(name="Cherry Hinton Leisure Centre").first()
    if not facility:
        facility = Facility(name="Cherry Hinton Leisure Centre")
        session.add(facility)
        session.commit()

    date_a = date.today()
    date_b = date.today() + timedelta(days=1)
    slots_a = _mock_slots_for_date(date_a.isoformat(), date_a.strftime("%A"))
    slots_b = _mock_slots_for_date(date_b.isoformat(), date_b.strftime("%A"))

    # Store combined (as scraper does after looping days with expected_date)
    session.query(CourtAvailability).filter_by(facility_id=facility.id).delete()
    for slot in slots_a + slots_b:
        session.add(
            CourtAvailability(
                facility_id=facility.id,
                date=slot["date"],
                day_name=slot.get("day_name"),
                start_time=slot["start_time"],
                end_time=slot["end_time"],
                court_number=slot.get("court_number", "Court 1"),
                is_available=slot["is_available"],
            )
        )
    session.commit()

    # Assert both dates appear (avoids "one day to all days" bug)
    rows = session.query(CourtAvailability).filter_by(facility_id=facility.id).all()
    dates_in_db = {r.date for r in rows}
    assert date_a.isoformat() in dates_in_db, f"Expected date {date_a} in DB; got {dates_in_db}"
    assert date_b.isoformat() in dates_in_db, f"Expected date {date_b} in DB; got {dates_in_db}"
    assert len(dates_in_db) == 2, f"Expected exactly 2 distinct dates; got {dates_in_db}"

    session.close()
    try:
        os.unlink(TEST_DB)
    except Exception:
        pass


def test_slot_structure_has_required_keys():
    """Stored slots must have date, start_time, end_time, is_available (and optional court_number)."""
    from database import init_db, get_session, Facility, CourtAvailability

    engine = init_db(db_path=TEST_DB)
    session = get_session(engine)
    facility = session.query(Facility).filter_by(name="Cherry Hinton Leisure Centre").first()
    if not facility:
        facility = Facility(name="Cherry Hinton Leisure Centre")
        session.add(facility)
        session.commit()

    required_keys = {"date", "start_time", "end_time", "is_available"}
    slot = _mock_slots_for_date("2025-06-01", "Sunday", count=1)[0]
    for key in required_keys:
        assert key in slot, f"Slot must have key {key}"

    session.query(CourtAvailability).filter_by(facility_id=facility.id).delete()
    session.add(
        CourtAvailability(
            facility_id=facility.id,
            date=slot["date"],
            day_name=slot.get("day_name"),
            start_time=slot["start_time"],
            end_time=slot["end_time"],
            court_number=slot.get("court_number", "Court 1"),
            is_available=slot["is_available"],
        )
    )
    session.commit()
    row = session.query(CourtAvailability).filter_by(facility_id=facility.id).first()
    assert row.date == slot["date"]
    assert row.start_time == slot["start_time"]
    assert row.end_time == slot["end_time"]
    assert row.is_available is True

    session.close()
    try:
        os.unlink(TEST_DB)
    except Exception:
        pass


def test_cherry_hinton_scraper_store_availability_integration():
    """CherryHintonScraper._store_availability with ~6 days yields that many distinct dates in DB."""
    from datetime import date, timedelta
    from database import CourtAvailability

    from scrapers.cherry_hinton import CherryHintonScraper, SCRAPE_DAYS

    saved_db = os.environ.get("DATABASE_URL")
    saved_path = os.environ.get("DB_PATH")
    try:
        os.environ.pop("DATABASE_URL", None)
        os.environ["DB_PATH"] = TEST_DB

        scraper = CherryHintonScraper(headless=True)
        all_slots = []
        for i in range(SCRAPE_DAYS):
            d = date.today() + timedelta(days=i)
            all_slots.extend(
                _mock_slots_for_date(d.isoformat(), d.strftime("%A"))
            )

        scraper._store_availability(all_slots)

        rows = scraper.session.query(CourtAvailability).filter_by(
            facility_id=scraper.facility.id
        ).all()
        dates_in_db = {r.date for r in rows}
        assert len(dates_in_db) >= EXPECTED_SCRAPE_DAYS_MIN, (
            f"Expected at least {EXPECTED_SCRAPE_DAYS_MIN} distinct dates; got {len(dates_in_db)}: {dates_in_db}"
        )
        assert len(dates_in_db) == SCRAPE_DAYS, (
            f"Expected {SCRAPE_DAYS} distinct dates (one per scraped day); got {len(dates_in_db)}: {dates_in_db}"
        )

        scraper.session.close()
    finally:
        if saved_db is not None:
            os.environ["DATABASE_URL"] = saved_db
        if saved_path is not None:
            os.environ["DB_PATH"] = saved_path
        else:
            os.environ.pop("DB_PATH", None)
        try:
            os.unlink(TEST_DB)
        except Exception:
            pass


if __name__ == "__main__":
    test_scraper_configured_for_multiple_days()
    print("PASS: test_scraper_configured_for_multiple_days")
    test_store_availability_preserves_distinct_dates()
    print("PASS: test_store_availability_preserves_distinct_dates")
    test_slot_structure_has_required_keys()
    print("PASS: test_slot_structure_has_required_keys")
    test_cherry_hinton_scraper_store_availability_integration()
    print("PASS: test_cherry_hinton_scraper_store_availability_integration")
    print("All Cherry Hinton tests passed.")
