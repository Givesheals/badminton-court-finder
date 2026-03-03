"""
Agent-based scraper for Trumpington Sport.
Uses the same Playwright navigation as TrumpingtonSportScraper but extracts
availability via LLM (OpenAI) instead of fixed selectors.
Requires OPENAI_API_KEY in the environment.
"""
from scrapers.trumpington_sport import TrumpingtonSportScraper
from scrapers.llm_extract import extract_availability_from_page


class TrumpingtonAgentScraper(TrumpingtonSportScraper):
    """
    Trumpington Sport scraper that uses LLM to parse the availability page(s).
    Same navigation and login as TrumpingtonSportScraper; only extraction is agentic.
    """

    def _extract_availability(self, page, expected_date=None):
        """Extract availability using LLM from the current page."""
        return extract_availability_from_page(
            page,
            facility_name=self.facility.name if self.facility else "Trumpington Sport",
        )
