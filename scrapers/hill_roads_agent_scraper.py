"""
Agent-based scraper for Hill Roads Sport and Tennis Centre.
Uses the same Playwright navigation as HillRoadsScraper but extracts
availability via LLM (OpenAI) instead of fixed selectors.
Requires OPENAI_API_KEY in the environment.
"""
from scrapers.hill_roads import HillRoadsScraper
from scrapers.llm_extract import extract_availability_from_page


class HillRoadsAgentScraper(HillRoadsScraper):
    """
    Hill Roads scraper that uses LLM to parse the availability page(s).
    Same navigation and login as HillRoadsScraper; only extraction is agentic.
    """

    def _extract_availability(self, page):
        """Extract availability using LLM from the current page."""
        return extract_availability_from_page(
            page,
            facility_name=self.facility.name if self.facility else "Hill Roads Sport and Tennis Centre",
        )
