"""
Agent-based scraper for One Leisure St Ives.
Uses the same Playwright navigation as OneLeisureStIvesScraper but extracts
availability via LLM (OpenAI) instead of fixed selectors.
Requires OPENAI_API_KEY in the environment.
"""
from scrapers.one_leisure_st_ives import OneLeisureStIvesScraper
from scrapers.llm_extract import extract_availability_from_page


class OneLeisureAgentScraper(OneLeisureStIvesScraper):
    """
    One Leisure St Ives scraper that uses LLM to parse the timetable page.
    Same navigation as OneLeisureStIvesScraper; only extraction is agentic.
    """

    def _extract_availability_from_timetable(self, page):
        """Extract availability using LLM from the current timetable page."""
        return extract_availability_from_page(
            page,
            facility_name=self.facility.name if self.facility else "One Leisure St Ives",
        )
