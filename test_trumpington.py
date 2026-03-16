#!/usr/bin/env python3
"""
Tests for Trumpington Sport scraper.

- Scraper is configured to scrape multiple days (7–14).
- App uses the agent (LLM) scraper for Trumpington, not the base scraper.
- Integration test: full scrape succeeds and updates facility (fails until scraper is fixed).
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Use a temp DB so we don't touch the main database
TEST_DB = tempfile.NamedTemporaryFile(suffix=".db", delete=False).name

# Trumpington scrapes 14 days
EXPECTED_SCRAPE_DAYS_MIN = 7
EXPECTED_SCRAPE_DAYS_MAX = 14

FACILITY_NAME = "Trumpington Sport"


def test_scraper_configured_for_multiple_days():
    """Trumpington scraper must be set to scrape 7–14 days, not 2."""
    from scrapers.trumpington_sport import SCRAPE_DAYS

    assert EXPECTED_SCRAPE_DAYS_MIN <= SCRAPE_DAYS <= EXPECTED_SCRAPE_DAYS_MAX, (
        f"SCRAPE_DAYS should be between {EXPECTED_SCRAPE_DAYS_MIN} and {EXPECTED_SCRAPE_DAYS_MAX}; got {SCRAPE_DAYS}"
    )
    assert SCRAPE_DAYS > 2, "SCRAPE_DAYS must be more than 2."


def test_app_uses_agent_scraper():
    """Production must use TrumpingtonAgentScraper (LLM extraction), not base TrumpingtonSportScraper."""
    from scraper_manager import ScraperManager
    from scrapers.trumpington_agent_scraper import TrumpingtonAgentScraper
    from scrapers.trumpington_sport import TrumpingtonSportScraper

    sm = ScraperManager()
    try:
        scraper_class = sm.scrapers.get(FACILITY_NAME)
        assert scraper_class is not None, f"No scraper registered for {FACILITY_NAME}"
        assert scraper_class is TrumpingtonAgentScraper, (
            f"Trumpington must use TrumpingtonAgentScraper (LLM), not {scraper_class.__name__}"
        )
        assert issubclass(scraper_class, TrumpingtonSportScraper), (
            "Agent scraper must subclass TrumpingtonSportScraper"
        )
    finally:
        sm.close()


def test_trumpington_scraper_integration():
    """Trumpington Sport scrape completes successfully and updates facility.
    Fails while the scraper is broken; passes once the scraper is fixed.
    Skipped when OPENAI_API_KEY (and login env) are not set.
    """
    if not os.getenv("OPENAI_API_KEY"):
        from unittest import SkipTest
        raise SkipTest("OPENAI_API_KEY not set; skip integration test")

    from database import init_db, get_session, Facility, CourtAvailability
    from scraper_manager import ScraperManager

    saved_db = os.environ.get("DATABASE_URL")
    saved_path = os.environ.get("DB_PATH")
    try:
        os.environ.pop("DATABASE_URL", None)
        os.environ["DB_PATH"] = TEST_DB

        engine = init_db(db_path=TEST_DB)
        sm = ScraperManager(engine=engine)
        try:
            # Ensure facility exists and circuit breaker is not blocking
            facility = sm.session.query(Facility).filter_by(name=FACILITY_NAME).first()
            if not facility:
                facility = Facility(name=FACILITY_NAME)
                sm.session.add(facility)
                sm.session.commit()
            sm.reset_circuit_breaker(FACILITY_NAME)

            result = sm.scrape_facility(FACILITY_NAME)

            assert result.get("success") is True, (
                f"Expected scrape to succeed; got success={result.get('success')}, error={result.get('error')}"
            )
            facility = sm.session.query(Facility).filter_by(name=FACILITY_NAME).first()
            assert facility.last_scraped_at is not None, (
                "Expected last_scraped_at to be set after successful scrape"
            )
            # Optionally: at least one availability record (or at least one day was processed)
            cached = sm._get_cached_data(FACILITY_NAME)
            # We allow 0 slots if the site genuinely has no availability; success + last_scraped_at is enough
            assert "scraped_at" in result or facility.last_scraped_at, "Scrape time should be recorded"
        finally:
            sm.close()
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
    from unittest import SkipTest
    test_scraper_configured_for_multiple_days()
    print("PASS: test_scraper_configured_for_multiple_days")
    test_app_uses_agent_scraper()
    print("PASS: test_app_uses_agent_scraper")
    try:
        test_trumpington_scraper_integration()
        print("PASS: test_trumpington_scraper_integration")
        print("All Trumpington tests passed.")
    except SkipTest as e:
        print("SKIP: test_trumpington_scraper_integration (missing OPENAI_API_KEY or credentials)")
        print("Unit tests passed; run with OPENAI_API_KEY set to run integration test.")
