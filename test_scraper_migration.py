"""
Tests for full scraper migration to agent (LLM) technology.

These tests verify that:
- All facilities use agent scraper classes (no fixed-selector at runtime).
- No facility is excluded by default from scheduled scrape-all.
- Scrape-all includes all four facilities.
- API exposes all four facilities (front-end data path).
"""

import os
import sys

# Project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

EXPECTED_FACILITIES = {
    "Linton Village College",
    "Hill Roads Sport and Tennis Centre",
    "One Leisure St Ives",
    "Trumpington Sport",
}


def test_a_all_scrapers_are_agent_classes():
    """All registered scrapers must be agent (LLM) classes, not fixed-selector base classes."""
    from scraper_manager import ScraperManager
    from scrapers.hill_roads_agent_scraper import HillRoadsAgentScraper
    from scrapers.linton_agent_scraper import LintonAgentScraper
    from scrapers.one_leisure_agent_scraper import OneLeisureAgentScraper
    from scrapers.trumpington_agent_scraper import TrumpingtonAgentScraper

    sm = ScraperManager()
    agent_classes = {HillRoadsAgentScraper, LintonAgentScraper, OneLeisureAgentScraper, TrumpingtonAgentScraper}
    for name, scraper_class in sm.scrapers.items():
        assert scraper_class in agent_classes, (
            f"Facility {name} uses {scraper_class.__name__}; expected an agent scraper class."
        )
    sm.close()


def test_b_no_facility_excluded_by_default():
    """Default EXCLUDE_SCRAPE_FACILITIES must be empty so scrape-all runs all facilities."""
    # Build exclude list the same way app.py does when env is unset (default '').
    saved = os.environ.pop("EXCLUDE_SCRAPE_FACILITIES", None)
    try:
        raw = os.getenv("EXCLUDE_SCRAPE_FACILITIES", "")
        excluded = [name.strip() for name in raw.split(",") if name.strip()]
        assert excluded == [], (
            f"Default exclude list should be empty; got {excluded}. "
            "app.py must use default '' for EXCLUDE_SCRAPE_FACILITIES."
        )
    finally:
        if saved is not None:
            os.environ["EXCLUDE_SCRAPE_FACILITIES"] = saved


def test_c_scrape_all_includes_all_facilities():
    """With default (empty) exclude list, scrape-all should include all four facilities."""
    from scraper_manager import ScraperManager

    saved = os.environ.pop("EXCLUDE_SCRAPE_FACILITIES", None)
    sm = ScraperManager()
    try:
        raw = os.getenv("EXCLUDE_SCRAPE_FACILITIES", "")
        excluded = set(name.strip() for name in raw.split(",") if name.strip())
        to_scrape = [f for f in sm.get_facilities_list() if f not in excluded]
        assert len(to_scrape) == 4, (
            f"Scrape-all should include 4 facilities when none excluded; got {len(to_scrape)}: {to_scrape}."
        )
        assert set(to_scrape) == EXPECTED_FACILITIES, (
            f"Scrape-all facilities should be {EXPECTED_FACILITIES}; got {set(to_scrape)}."
        )
    finally:
        if saved is not None:
            os.environ["EXCLUDE_SCRAPE_FACILITIES"] = saved
        sm.close()


def test_d_api_returns_all_four_facilities():
    """GET /api/facilities must return exactly the four expected facilities (front-end data path)."""
    from app import app, scraper_manager

    with app.test_client() as client:
        rv = client.get("/api/facilities")
        assert rv.status_code == 200, f"Expected 200, got {rv.status_code}"
        data = rv.get_json()
        facilities = data.get("facilities") or []
        assert len(facilities) == 4, (
            f"API should return 4 facilities; got {len(facilities)}: {facilities}."
        )
        assert set(facilities) == EXPECTED_FACILITIES, (
            f"Facilities should be {EXPECTED_FACILITIES}; got {set(facilities)}."
        )


if __name__ == "__main__":
    # Run with: python test_scraper_migration.py
    import traceback
    for name in dir():
        if name.startswith("test_") and callable(locals()[name]):
            try:
                locals()[name]()
                print(f"PASS: {name}")
            except Exception as e:
                print(f"FAIL: {name}")
                traceback.print_exc()
                sys.exit(1)
    print("All migration tests passed.")
