"""
Agent-based scraper for One Leisure St Ives.
Uses the same Playwright navigation as OneLeisureStIvesScraper but extracts
availability via LLM (OpenAI) instead of fixed selectors.
Requires OPENAI_API_KEY in the environment.
"""
import time
from datetime import datetime, timedelta

from scrapers.one_leisure_st_ives import OneLeisureStIvesScraper, BOOKING_WINDOW_DAYS
from scrapers.llm_extract import extract_availability_from_page


class OneLeisureAgentScraper(OneLeisureStIvesScraper):
    """
    One Leisure St Ives scraper that uses LLM to parse the timetable page.
    Same navigation as OneLeisureStIvesScraper; only extraction is agentic.
    Loops over the 14-day booking window (like the base) and aggregates all days.
    """

    def _extract_availability_from_timetable(self, page):
        """Extract availability using LLM for each day in the 14-day booking window."""
        today = datetime.now().date()
        dates_to_scrape = [today + timedelta(days=i) for i in range(BOOKING_WINDOW_DAYS)]
        all_slots = []
        facility_name = self.facility.name if self.facility else "One Leisure St Ives"

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
            print(f"  {date_str}: {len(day_slots)} slots ({sum(1 for s in day_slots if s.get('is_available'))} available)")

        return all_slots
