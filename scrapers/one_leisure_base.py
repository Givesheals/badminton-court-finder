"""Shared base scraper for One Leisure (GladstoneGo) facilities.

This module contains a configurable Playwright/DB base class that knows how to:
- Navigate to the GladstoneGo /book page
- Apply the standard filters: Where / What / date / Starting from
- Open the badminton timetable ("See available spaces")
- Loop over the 14-day booking window
- Store availability records in the database for a single Facility.

Facility-specific scrapers (St Ives, St Neots, Huntingdon, Ramsey, etc.)
should subclass `OneLeisureBaseScraper` and provide a small config describing:
- facility_name (DB/manager key)
- where_value (primary label for the Where dropdown)
- where_fallbacks (optional text variants)
- what_value (defaults to "Court Bookings" if not overridden)
- base_url (defaults to the common GladstoneGo book URL if not overridden)
"""

import os
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import init_db, get_session, Facility, CourtAvailability

load_dotenv()


BOOKING_WINDOW_DAYS = 14  # Can book today + 13 more days (14 days in advance)


@dataclass
class OneLeisureConfig:
    """Configuration for a single One Leisure facility on GladstoneGo."""

    facility_name: str
    where_value: str
    where_fallbacks: List[str] = field(default_factory=list)
    base_url: str = "https://oneleisure.gladstonego.cloud/book"
    what_value: str = "Court Bookings"
    starting_from_value: str = "Starting now"


class OneLeisureBaseScraper:
    """Base scraper for One Leisure (GladstoneGo) facilities.

    Subclasses should provide a `CONFIG` attribute of type `OneLeisureConfig`,
    and may override timetable-specific helpers if a facility deviates from
    the standard GladstoneGo layout.
    """

    CONFIG: OneLeisureConfig

    def __init__(self, headless: Optional[bool] = True) -> None:
        if not hasattr(self, "CONFIG"):
            raise ValueError("Subclasses of OneLeisureBaseScraper must define a CONFIG attribute")
        self.config: OneLeisureConfig = self.CONFIG
        self.headless = headless if headless is not None else True
        self.db_engine = init_db()
        self.session = get_session(self.db_engine)
        self.facility = self._get_or_create_facility()

    # ---------- DB helpers ----------

    def _get_or_create_facility(self) -> Facility:
        """Get or create the Facility record for this One Leisure config."""
        facility = self.session.query(Facility).filter_by(name=self.config.facility_name).first()
        if not facility:
            facility = Facility(name=self.config.facility_name)
            self.session.add(facility)
            self.session.commit()
        return facility

    # ---------- Date helpers ----------

    def _today_dd_mm_yyyy(self) -> str:
        return datetime.now().strftime("%d/%m/%Y")

    # ---------- Main entrypoint ----------

    def scrape(self) -> None:
        """Navigate to book page, apply filters, open timetable, and extract availability."""
        print(f"Starting One Leisure scraper for {self.config.facility_name}...")

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled"],
            )
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1920, "height": 1080},
                locale="en-GB",
                timezone_id="Europe/London",
                extra_http_headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-GB,en;q=0.9",
                },
            )
            page = context.new_page()
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            try:
                # Step 1: Open book page
                print(f"Navigating to {self.config.base_url}...")
                page.goto(self.config.base_url, wait_until="networkidle", timeout=60000)
                time.sleep(3)

                # Wait for the booking form to be visible (SPA may load slowly)
                try:
                    page.get_by_text("Where", exact=True).first.wait_for(state="visible", timeout=15000)
                except Exception:
                    try:
                        page.get_by_placeholder(re.compile(r"location|where", re.I)).first.wait_for(
                            state="visible", timeout=10000
                        )
                    except Exception:
                        pass
                time.sleep(1)

                # Step 2: Set "Where"
                print(f"Setting 'Where' to {self.config.where_value}...")
                self._set_where(page)

                # Step 3: Set "What are you looking to do"
                print(f"Setting 'What are you looking to do' to {self.config.what_value}...")
                self._set_what(page)

                # Step 4: Set "What date" to today
                print("Setting date to today...")
                self._set_date(page)

                # Step 5: Set "Starting from"
                print(f"Setting 'Starting from' to {self.config.starting_from_value}...")
                self._set_starting_from(page)

                # Step 6: Click Search (if present) or wait for results
                self._submit_search(page)

                # Step 7: Wait for results and click "See available spaces" (prefer Badminton)
                self._open_timetable(page)

                # Timetable page is now loaded; extraction implemented by subclasses/mixins
                time.sleep(2)
                print(f"Timetable URL: {page.url}")
                page.screenshot(path=f"debug_one_leisure_timetable_{self.facility.id}.png")

                availability = self._extract_availability_from_timetable(page)
                if availability:
                    self._store_availability(availability)
                else:
                    print("No availability extracted (empty list returned).")

                print(f"One Leisure scraper finished for {self.config.facility_name}.")
            except Exception as e:
                print(f"Error during scraping for {self.config.facility_name}: {e}")
                page.screenshot(path=f"debug_one_leisure_error_{self.facility.id}.png")
                raise
            finally:
                browser.close()
                self.session.close()

    # ---------- Filter helpers (Where / What / Date / Starting from) ----------

    def _set_where(self, page) -> None:
        """Click the Where dropdown to open it, then select the configured facility."""
        wait_short, wait_long = 5000, 10000
        where_clicked = False

        try:
            inp = page.get_by_placeholder(re.compile(r"Search for a location|location", re.I)).first
            if inp.is_visible(timeout=wait_long):
                inp.click()
                where_clicked = True
                print("Clicked Where (placeholder 'Search for a location').")
        except Exception:
            pass
        if not where_clicked:
            try:
                cb = page.get_by_role("combobox", name=re.compile(r"Where", re.I)).first
                if cb.is_visible(timeout=wait_long):
                    cb.click()
                    where_clicked = True
                    print("Clicked Where combobox.")
            except Exception:
                pass
        if not where_clicked:
            try:
                label = page.get_by_text("Where", exact=True).first
                if label.is_visible(timeout=wait_long):
                    parent = label.locator(
                        "xpath=ancestor::*[.//input or .//button or .//*[@role='combobox']][1]"
                    )
                    if parent.count() > 0 and parent.first.is_visible(timeout=wait_short):
                        parent.first.click()
                        where_clicked = True
                        print("Clicked Where (parent of label).")
            except Exception:
                pass
        if not where_clicked:
            try:
                first_combobox = page.get_by_role("combobox").first
                if first_combobox.is_visible(timeout=wait_long):
                    first_combobox.click()
                    where_clicked = True
                    print("Clicked first combobox (Where).")
            except Exception:
                pass
        if not where_clicked:
            try:
                block = page.get_by_text("Where", exact=True).locator(
                    "xpath=ancestor::*[contains(@class, 'filter') or "
                    "contains(@class, 'field') or contains(@class, 'select')][1]"
                )
                if block.count() > 0 and block.first.is_visible(timeout=wait_long):
                    block.first.click()
                    where_clicked = True
                    print("Clicked Where block.")
            except Exception:
                pass
        if not where_clicked:
            raise Exception("Could not find or click the 'Where' dropdown")

        time.sleep(1)

        option_clicked = False
        option_candidates = [self.config.where_value] + list(self.config.where_fallbacks)
        for option_text in option_candidates:
            try:
                base_text = option_text.split(" Indoo")[0]
                opt = page.get_by_role("option").filter(
                    has_text=re.compile(re.escape(base_text), re.I)
                ).first
                if opt.is_visible(timeout=2000):
                    opt.click()
                    option_clicked = True
                    print(f"Selected option: {option_text}")
                    break
            except Exception:
                try:
                    opt = page.get_by_text(option_text, exact=False).first
                    if opt.is_visible(timeout=1500):
                        opt.click()
                        option_clicked = True
                        print(f"Selected option (text): {option_text}")
                        break
                except Exception:
                    continue

        if not option_clicked:
            raise Exception(f"Could not select '{self.config.where_value}' from Where dropdown")
        time.sleep(0.5)

    def _set_what(self, page) -> None:
        """Fill or select 'What are you looking to do'."""
        what_label = "What are you looking to do"
        for attempt in [
            lambda: page.get_by_label(what_label, exact=False).first,
            lambda: page.get_by_placeholder(what_label).first,
            lambda: page.get_by_text(what_label, exact=False).locator("..").locator("input, [contenteditable]").first,
        ]:
            try:
                el = attempt()
                if el.is_visible(timeout=3000):
                    el.click()
                    time.sleep(0.5)
                    el.fill("")
                    el.fill(self.config.what_value)
                    time.sleep(1)
                    opt = page.get_by_text(self.config.what_value, exact=False).first
                    if opt.is_visible(timeout=2000):
                        opt.click()
                    print("Set What successfully.")
                    return
            except Exception:
                continue
        raise Exception("Could not set 'What are you looking to do' field")

    def _set_date(self, page) -> None:
        """Set 'What date' to today (DD/MM/YYYY)."""
        today_str = self._today_dd_mm_yyyy()
        for attempt in [
            lambda: page.get_by_label("What date", exact=False).first,
            lambda: page.get_by_placeholder("date", exact=False).first,
            lambda: page.locator('input[type="text"]').filter(has_text=re.compile(r"\d{2}/\d{2}/\d{4}")).first,
            lambda: page.get_by_text("What date", exact=False).locator("..").locator("input").first,
        ]:
            try:
                el = attempt()
                if el.is_visible(timeout=3000):
                    el.click()
                    time.sleep(0.3)
                    el.fill("")
                    el.fill(today_str)
                    time.sleep(0.5)
                    print("Set date successfully.")
                    return
            except Exception:
                continue
        raise Exception("Could not set 'What date' field")

    def _set_starting_from(self, page) -> None:
        """Open the 'Starting from' dropdown and select the first (earliest) option."""
        opened = False
        try:
            cb = page.get_by_role("combobox", name=re.compile(r"Starting from", re.I)).first
            if cb.is_visible(timeout=3000):
                cb.click()
                opened = True
                print("Clicked Starting from combobox.")
        except Exception:
            pass
        if not opened:
            try:
                label = page.get_by_text("Starting from", exact=True).first
                if label.is_visible(timeout=3000):
                    parent = label.locator(
                        "xpath=ancestor::*[.//input or .//button or .//*[@role='combobox']][1]"
                    )
                    if parent.count() > 0 and parent.first.is_visible(timeout=2000):
                        parent.first.click()
                        opened = True
                        print("Clicked Starting from (parent of label).")
            except Exception:
                pass
        if not opened:
            try:
                for cb in page.get_by_role("combobox").all():
                    aria = (cb.get_attribute("aria-label") or cb.get_attribute("aria-labelledby") or "").lower()
                    if cb.is_visible(timeout=1000) and "starting" in aria:
                        cb.click()
                        opened = True
                        print("Clicked Starting from (combobox by aria).")
                        break
            except Exception:
                pass
        if not opened:
            try:
                block = page.get_by_text("Starting from", exact=True).locator(
                    "xpath=ancestor::*[contains(@class, 'filter') or "
                    "contains(@class, 'field') or contains(@class, 'select')][1]"
                )
                if block.count() > 0 and block.first.is_visible(timeout=3000):
                    block.first.click()
                    opened = True
                    print("Clicked Starting from block.")
            except Exception:
                pass
        if not opened:
            print("Warning: Could not open 'Starting from' dropdown; continuing to Search.")
            return

        time.sleep(1)
        option_clicked = False
        try:
            first_opt = page.get_by_role("option").first
            if first_opt.is_visible(timeout=2000):
                first_opt.click()
                option_clicked = True
                print("Selected first (earliest) option in Starting from.")
        except Exception:
            pass
        if not option_clicked:
            try:
                first_li = page.locator(
                    "[role='listbox'] >> [role='option'], "
                    "[role='menu'] >> li, [class*='option']"
                ).first
                if first_li.is_visible(timeout=2000):
                    first_li.click()
                    option_clicked = True
                    print("Selected first option (listbox/menu).")
            except Exception:
                pass
        if not option_clicked:
            print("Warning: Could not select an option in 'Starting from'; continuing to Search.")
        time.sleep(0.5)

    def _submit_search(self, page) -> None:
        """Click the Search button (not 'Clear filters') to load results."""
        search_clicked = False
        candidates = [
            page.get_by_role("button", name="Search"),
            page.locator("button").filter(has_text=re.compile(r"^Search$", re.I)),
            page.get_by_text("Search", exact=True),
            page.locator('input[type="submit"][value="Search"]'),
            page.locator("button:has-text(\"Search\")").filter(
                has_not=page.get_by_text("Clear", exact=False)
            ),
        ]
        for candidate in candidates:
            try:
                el = candidate.first
                if not el.is_visible(timeout=1500):
                    continue
                text = el.inner_text().strip() if hasattr(el, "inner_text") else ""
                if "clear" in text.lower() or "filter" in text.lower():
                    continue
                el.click()
                search_clicked = True
                print("Clicked Search button.")
                break
            except Exception:
                continue
        if not search_clicked:
            print("Warning: Search button not found; waiting for results anyway.")
        time.sleep(2)
        page.wait_for_load_state("networkidle", timeout=15000)
        try:
            page.get_by_text("See available spaces", exact=False).first.wait_for(
                state="visible", timeout=15000
            )
            print("Results loaded (See available spaces visible).")
        except Exception:
            try:
                page.get_by_text("Badminton", exact=False).first.wait_for(
                    state="visible", timeout=5000
                )
                print("Results loaded (Badminton card visible).")
            except Exception:
                if not search_clicked:
                    raise Exception(
                        "Search button was not clicked and results did not appear. "
                        "Cannot proceed to timetable."
                    )
        time.sleep(1)

    def _open_timetable(self, page) -> None:
        """Click 'See available spaces' — prefer the Badminton card."""
        try:
            badminton_card = page.locator(
                "[class*='card'], [class*='result'], article, section"
            ).filter(has_text=re.compile(r"Badminton", re.I)).first
            if badminton_card.is_visible(timeout=3000):
                btn = badminton_card.get_by_role("button", name="See available spaces").or_(
                    badminton_card.get_by_text("See available spaces", exact=True)
                ).first
                if btn.is_visible(timeout=2000):
                    btn.click()
                    print("Clicked 'See available spaces' on Badminton card.")
                    page.wait_for_load_state("networkidle", timeout=15000)
                    time.sleep(2)
                    return
        except Exception as e:
            print(f"Badminton card not found: {e}")

        see_spaces = page.get_by_role("button", name="See available spaces").or_(
            page.get_by_text("See available spaces", exact=True)
        )
        first_btn = see_spaces.first
        if not first_btn.is_visible(timeout=5000):
            raise Exception("Could not find 'See available spaces' button")
        first_btn.click()
        print("Clicked first 'See available spaces'.")
        page.wait_for_load_state("networkidle", timeout=15000)
        time.sleep(2)

    # ---------- Timetable extraction (to be implemented/overridden) ----------

    def _extract_availability_from_timetable(self, page) -> List[Dict[str, Any]]:
        """Base implementation: no extraction. Agent or facility subclasses override."""
        return []

    # ---------- Storage ----------

    def _store_availability(self, availability: List[Dict[str, Any]]) -> None:
        """Store availability in DB (same shape as other scrapers)."""
        self.session.query(CourtAvailability).filter_by(facility_id=self.facility.id).delete()
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
        print(f"Stored {len(availability)} availability records for {self.config.facility_name}.")

