"""
Tests for full scraper migration to agent (LLM) technology.

These tests verify that:
- All facilities use agent scraper classes (no fixed-selector at runtime).
- Linton Village College is excluded by default from scheduled scrape-all (bot protection).
- Scrape-all includes the four non-excluded facilities when using default config.
- API exposes all five facilities (front-end data path).
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
    "Cherry Hinton Leisure Centre",
}


def test_a_all_scrapers_are_agent_classes():
    """All registered scrapers must be agent (LLM) classes, not fixed-selector base classes."""
    from scraper_manager import ScraperManager
    from scrapers.cherry_hinton_agent_scraper import CherryHintonAgentScraper
    from scrapers.hill_roads_agent_scraper import HillRoadsAgentScraper
    from scrapers.linton_agent_scraper import LintonAgentScraper
    from scrapers.one_leisure_agent_scraper import OneLeisureAgentScraper
    from scrapers.trumpington_agent_scraper import TrumpingtonAgentScraper

    sm = ScraperManager()
    agent_classes = {
        CherryHintonAgentScraper,
        HillRoadsAgentScraper,
        LintonAgentScraper,
        OneLeisureAgentScraper,
        TrumpingtonAgentScraper,
    }
    for name, scraper_class in sm.scrapers.items():
        assert scraper_class in agent_classes, (
            f"Facility {name} uses {scraper_class.__name__}; expected an agent scraper class."
        )
    sm.close()


def test_b_linton_excluded_by_default():
    """Default EXCLUDE_SCRAPE_FACILITIES must include Linton (bot protection) so cron does not hit it."""
    saved = os.environ.pop("EXCLUDE_SCRAPE_FACILITIES", None)
    try:
        raw = os.getenv("EXCLUDE_SCRAPE_FACILITIES", "Linton Village College")
        excluded = [name.strip() for name in raw.split(",") if name.strip()]
        assert "Linton Village College" in excluded, (
            f"Default exclude list should include Linton Village College; got {excluded}."
        )
    finally:
        if saved is not None:
            os.environ["EXCLUDE_SCRAPE_FACILITIES"] = saved


def test_c_scrape_all_excludes_linton_by_default():
    """With default config, scrape-all should include 4 facilities (Linton excluded)."""
    from scraper_manager import ScraperManager

    saved = os.environ.pop("EXCLUDE_SCRAPE_FACILITIES", None)
    sm = ScraperManager()
    try:
        raw = os.getenv("EXCLUDE_SCRAPE_FACILITIES", "Linton Village College")
        excluded = set(name.strip() for name in raw.split(",") if name.strip())
        to_scrape = [f for f in sm.get_facilities_list() if f not in excluded]
        assert len(to_scrape) == 4, (
            f"Scrape-all should include 4 facilities (Linton excluded); got {len(to_scrape)}: {to_scrape}."
        )
        assert "Cherry Hinton Leisure Centre" in to_scrape, (
            "Cherry Hinton Leisure Centre must be in the scrape list when using default exclude."
        )
        assert "Linton Village College" not in to_scrape, (
            "Linton Village College must not be in the scrape list when using default exclude."
        )
    finally:
        if saved is not None:
            os.environ["EXCLUDE_SCRAPE_FACILITIES"] = saved
        sm.close()


def test_d_api_returns_all_facilities():
    """GET /api/facilities must return exactly the five expected facilities (front-end data path)."""
    from app import app, scraper_manager

    with app.test_client() as client:
        rv = client.get("/api/facilities")
        assert rv.status_code == 200, f"Expected 200, got {rv.status_code}"
        data = rv.get_json()
        facilities = data.get("facilities") or []
        assert len(facilities) == 5, (
            f"API should return 5 facilities; got {len(facilities)}: {facilities}."
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
