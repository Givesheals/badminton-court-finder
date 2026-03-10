"""
Agent-based scraper for Cherry Hinton Leisure Centre.
Uses the same Playwright navigation as CherryHintonScraper but extracts
availability via LLM (OpenAI) instead of fixed selectors.
Requires OPENAI_API_KEY in the environment.
"""
from scrapers.cherry_hinton import CherryHintonScraper, FACILITY_NAME
from scrapers.llm_extract import extract_availability_from_page


class CherryHintonAgentScraper(CherryHintonScraper):
    """
    Cherry Hinton Leisure Centre scraper that uses LLM to parse the availability.
    Same navigation as CherryHintonScraper; only extraction is agentic.
    Each day is extracted with expected_date to avoid one-day-written-to-all-days bug.
    """

    def _extract_availability(self, page, expected_date=None):
        """Extract availability using LLM from the current page."""
        return extract_availability_from_page(
            page,
            facility_name=self.facility.name if self.facility else FACILITY_NAME,
            expected_date=expected_date,
        )
