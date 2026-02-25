"""
Agent-based scraper for Linton Village College.
Uses the same Playwright navigation as LintonVillageCollegeScraper but extracts
availability via LLM (OpenAI) instead of fixed selectors, for resilience to layout changes.
Requires OPENAI_API_KEY in the environment.
"""
from scrapers.linton_village_college import LintonVillageCollegeScraper
from scrapers.llm_extract import extract_availability_from_page


class LintonAgentScraper(LintonVillageCollegeScraper):
    """
    Linton scraper that uses LLM to parse the availability page.
    Same navigation and login as LintonVillageCollegeScraper; only extraction is agentic.
    """

    def _extract_availability(self, page):
        """Extract availability using LLM from the current page (after navigation)."""
        return extract_availability_from_page(
            page,
            facility_name=self.facility.name if self.facility else "Linton Village College",
        )
