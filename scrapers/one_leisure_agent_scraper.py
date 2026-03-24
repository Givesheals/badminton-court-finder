"""
Agent-based scrapers for One Leisure facilities.

These classes reuse the Playwright navigation from the OneLeisure*Scraper
base classes and override timetable extraction to use the LLM-based
`extract_availability_from_page` helper.

Requires OPENAI_API_KEY in the environment.
"""

import time
from datetime import datetime, timedelta

from scrapers.one_leisure_base import BOOKING_WINDOW_DAYS
from scrapers.one_leisure_st_ives import OneLeisureStIvesScraper
from scrapers.one_leisure_st_neots import OneLeisureStNeotsScraper
from scrapers.one_leisure_huntingdon import OneLeisureHuntingdonScraper
from scrapers.one_leisure_ramsey import OneLeisureRamseyScraper
from scrapers.llm_extract import extract_availability_from_page


class OneLeisureAgentMixin:
    """Mixin that implements LLM-based timetable extraction for One Leisure."""

    def _extract_availability_from_timetable(self, page):
        """Extract availability using LLM for each day in the 14-day booking window."""
        today = datetime.now().date()
        dates_to_scrape = [today + timedelta(days=i) for i in range(BOOKING_WINDOW_DAYS)]
        all_slots = []
        facility_name = getattr(self, "facility", None).name if getattr(self, "facility", None) else "One Leisure"

        for target_date in dates_to_scrape:
            date_str = target_date.strftime("%Y-%m-%d")
            day_num = target_date.day
            month_abbr = target_date.strftime("%b").lower()

            if not self._select_timetable_date(page, target_date, day_num, month_abbr):
                print(f"  Could not select date {date_str}, skipping.")
                continue
            time.sleep(1)
            page.wait_for_load_state("networkidle", timeout=10000)

            self._scroll_timetable_grid(page)
            time.sleep(0.5)

            day_slots = extract_availability_from_page(
                page,
                facility_name=facility_name,
                expected_date=target_date,
            )
            all_slots.extend(day_slots)
            print(
                f"  {date_str}: {len(day_slots)} slots "
                f"({sum(1 for s in day_slots if s.get('is_available'))} available)"
            )

        return all_slots


class OneLeisureStIvesAgentScraper(OneLeisureAgentMixin, OneLeisureStIvesScraper):
    """Agent-based scraper for One Leisure St Ives."""

    pass


class OneLeisureStNeotsAgentScraper(OneLeisureAgentMixin, OneLeisureStNeotsScraper):
    """Agent-based scraper for One Leisure St Neots."""

    pass


class OneLeisureHuntingdonAgentScraper(OneLeisureAgentMixin, OneLeisureHuntingdonScraper):
    """Agent-based scraper for One Leisure Huntingdon."""

    pass


class OneLeisureRamseyAgentScraper(OneLeisureAgentMixin, OneLeisureRamseyScraper):
    """Agent-based scraper for One Leisure Ramsey."""

    pass

