"""Scraper for Cherry Hinton Leisure Centre (Better.org) badminton court availability.

Flow: Navigate to sports-hall-activities → Click "Badminton 60 minutes" →
Click each day tab (up to 6 days), extract availability per day with expected_date,
then store all. No login required.
"""
import os
import re
import time
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import init_db, get_session, Facility, CourtAvailability

load_dotenv()

# Number of days to scrape (day tabs at top; site limits how far ahead)
SCRAPE_DAYS = 6

FACILITY_NAME = "Cherry Hinton Leisure Centre"
BASE_URL = "https://bookings.better.org.uk/location/cherry-hinton/sports-hall-activities"


class CherryHintonScraper:
    """Scraper for Cherry Hinton Leisure Centre (Better.org) badminton courts."""

    def __init__(self, headless=True):
        self.headless = headless if headless is not None else True
        self.db_engine = init_db()
        self.session = get_session(self.db_engine)
        self.facility = self._get_or_create_facility()

    def _get_or_create_facility(self):
        """Get or create the Cherry Hinton Leisure Centre facility record."""
        facility = self.session.query(Facility).filter_by(name=FACILITY_NAME).first()
        if not facility:
            facility = Facility(name=FACILITY_NAME)
            self.session.add(facility)
            self.session.commit()
        return facility

    def scrape(self):
        """Main scraping method."""
        print(f"Starting {FACILITY_NAME} scraper...")

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled"],
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="en-GB",
                timezone_id="Europe/London",
                extra_http_headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-GB,en;q=0.9",
                },
            )
            page = context.new_page()
            page.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

            try:
                # Step 1: Navigate to sports hall activities
                print(f"Navigating to {BASE_URL}...")
                page.goto(BASE_URL, wait_until="networkidle", timeout=60000)
                time.sleep(2)

                # Step 2: Click "Badminton 60 minutes" (avoid 40 minutes)
                print("Clicking Badminton 60 minutes...")
                self._click_badminton_60(page)
                time.sleep(2)
                page.wait_for_load_state("networkidle", timeout=15000)

                # Step 3: Scrape each day tab with expected_date to avoid one-day-written-to-all-days bug
                all_availability = []
                print(f"Scraping up to {SCRAPE_DAYS} days (each day extracted with expected_date)...")

                for day_index in range(SCRAPE_DAYS):
                    target_date = datetime.now().date() + timedelta(days=day_index)
                    clicked = self._click_day_tab(page, day_index)
                    if not clicked:
                        print(f"  Day {day_index + 1}: no tab found, stopping")
                        break
                    time.sleep(1)
                    page.wait_for_load_state("networkidle", timeout=10000)

                    try:
                        day_slots = self._extract_availability(page, expected_date=target_date)
                        all_availability.extend(day_slots)
                        print(f"  Day {day_index + 1} ({target_date.isoformat()}): {len(day_slots)} slots")
                    except Exception as e:
                        print(f"  Day {day_index + 1} extract failed: {e}")

                # Step 4: Store once with all days
                print(f"Storing {len(all_availability)} availability records...")
                self._store_availability(all_availability)

                print(f"{FACILITY_NAME} scraping completed successfully!")
            except Exception as e:
                print(f"Error during scraping: {e}")
                page.screenshot(path="debug_cherry_hinton_error.png")
                raise
            finally:
                browser.close()
                self.session.close()

    def _click_badminton_60(self, page):
        """Click the Badminton 60 minutes option (not 40 minutes)."""
        # Prefer link/button with "60" and "Badminton", avoid "40"
        selectors = [
            page.get_by_role("link", name=re.compile(r"Badminton.*60|60.*minute", re.I)),
            page.get_by_role("button", name=re.compile(r"Badminton.*60|60.*minute", re.I)),
            page.get_by_text(re.compile(r"Badminton\s+60|60\s*minute", re.I)),
        ]
        for loc in selectors:
            try:
                if loc.first.is_visible(timeout=3000):
                    loc.first.click()
                    return
            except Exception:
                continue
        # Fallback: any link containing "60" and "Badminton" but not "40"
        try:
            link = page.locator("a").filter(has_text=re.compile(r"Badminton", re.I)).filter(
                has_text=re.compile(r"60")
            ).filter(has_not_text=re.compile(r"40")).first
            if link.is_visible(timeout=3000):
                link.click()
                return
        except Exception:
            pass
        raise Exception("Could not find 'Badminton 60 minutes' link/button")

    def _click_day_tab(self, page, day_index):
        """Click the day tab at the given index (0 = first day, typically today). Returns True if clicked."""
        # Day tabs are often role=tab, or links/buttons with day names
        try:
            tabs = page.get_by_role("tab").all()
            if len(tabs) > day_index:
                tabs[day_index].click()
                return True
        except Exception:
            pass
        try:
            # Fallback: elements that look like day tabs (Mon 10, Tue 11, ...)
            day_tabs = page.locator(
                "button, a, [role='tab']"
            ).filter(has_text=re.compile(r"(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s*\d+", re.I))
            if day_tabs.count() > day_index:
                day_tabs.nth(day_index).click()
                return True
        except Exception:
            pass
        return False

    def _extract_availability(self, page, expected_date=None):
        """Extract slots from current page. Subclass overrides to use LLM; base returns []."""
        return []

    def _store_availability(self, availability):
        """Store availability in database (replace existing for this facility)."""
        self.session.query(CourtAvailability).filter_by(
            facility_id=self.facility.id
        ).delete()
        for slot in availability:
            record = CourtAvailability(
                facility_id=self.facility.id,
                date=slot["date"],
                day_name=slot.get("day_name"),
                start_time=slot["start_time"],
                end_time=slot["end_time"],
                court_number=slot.get("court_number", "Court 1"),
                is_available=slot["is_available"],
                scraped_at=datetime.utcnow(),
            )
            self.session.add(record)
        self.session.commit()
        print(f"Stored {len(availability)} availability records.")


if __name__ == "__main__":
    scraper = CherryHintonScraper(headless=False)
    try:
        scraper.scrape()
        print("Done.")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
