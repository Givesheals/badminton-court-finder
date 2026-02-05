"""Scraper for One Leisure St Ives badminton court availability.

Flow: land on /book → set Where/What/date/Starting from → Search → See available spaces
→ timetable page. We only scrape the 7-day booking window (today through today+6).
Slot states: "Book now" = available; "This slot is unavailable" or "available to be booked on" = not available.
"""
import os
import time
import re
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import sys

# Month name to number for parsing "Thu 5th Feb"
MONTH_NAMES = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}
BOOKING_WINDOW_DAYS = 7  # Can book today + 6 more days (7 days in advance)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import init_db, get_session, Facility, CourtAvailability

load_dotenv()


class OneLeisureStIvesScraper:
    """Scraper for One Leisure St Ives (GladstoneGo). Gets to timetable; timetable scraping TBD."""

    BASE_URL = "https://oneleisure.gladstonego.cloud/book"

    # Filter values for the booking page
    WHERE_VALUE = "One Leisure St Ives Indoo"
    WHAT_VALUE = "Court Bookings"
    STARTING_FROM_VALUE = "Starting now"

    def __init__(self, headless=True):
        self.headless = headless if headless is not None else True
        self.db_engine = init_db()
        self.session = get_session(self.db_engine)
        self.facility = self._get_or_create_facility()

    def _get_or_create_facility(self):
        """Get or create the One Leisure St Ives facility record."""
        facility = self.session.query(Facility).filter_by(name="One Leisure St Ives").first()
        if not facility:
            facility = Facility(name="One Leisure St Ives")
            self.session.add(facility)
            self.session.commit()
        return facility

    def _today_dd_mm_yyyy(self):
        return datetime.now().strftime("%d/%m/%Y")

    def scrape(self):
        """Navigate to book page, apply filters, open timetable via 'See available spaces'."""
        print("Starting One Leisure St Ives scraper...")

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
                # Step 1: Open book page
                print(f"Navigating to {self.BASE_URL}...")
                page.goto(self.BASE_URL, wait_until="networkidle")
                time.sleep(2)

                # Step 2: Set "Where" → One Leisure St Ives Indoo
                print("Setting 'Where' to One Leisure St Ives Indoo...")
                self._set_where(page)

                # Step 3: Set "What are you looking to do" → Court Bookings
                print("Setting 'What are you looking to do' to Court Bookings...")
                self._set_what(page)

                # Step 4: Set "What date" to today
                print("Setting date to today...")
                self._set_date(page)

                # Step 5: Set "Starting from" to Starting now
                print("Setting 'Starting from' to Starting now...")
                self._set_starting_from(page)

                # Step 6: Click Search (if present) or wait for results
                self._submit_search(page)

                # Step 7: Wait for results and click "See available spaces" (prefer Badminton)
                self._open_timetable(page)

                # Timetable page is now loaded; actual slot scraping will be added here
                time.sleep(2)
                print(f"Timetable URL: {page.url}")
                page.screenshot(path="debug_one_leisure_timetable.png")

                # Stub: extract and store availability from timetable (next phase)
                availability = self._extract_availability_from_timetable(page)
                if availability:
                    self._store_availability(availability)
                else:
                    print("No availability extracted yet (timetable scraping to be extended).")

                print("One Leisure St Ives scraper finished (reached timetable).")
            except Exception as e:
                print(f"Error during scraping: {e}")
                page.screenshot(path="debug_one_leisure_error.png")
                raise
            finally:
                browser.close()
                self.session.close()

    def _set_where(self, page):
        """Click the Where dropdown to open it, then select One Leisure St Ives Indoo."""
        # 1) Find and click the "Where" dropdown trigger (the box you click to open the list)
        where_clicked = False
        # Try combobox with "Where" in name (common for filter dropdowns)
        try:
            cb = page.get_by_role("combobox", name=re.compile(r"Where", re.I)).first
            if cb.is_visible(timeout=3000):
                cb.click()
                where_clicked = True
                print("Clicked Where combobox.")
        except Exception:
            pass
        if not where_clicked:
            # Try: clickable that contains the label "Where" (e.g. the filter row for Where)
            try:
                # Parent of "Where" text might be a label; the actual dropdown is often a sibling
                label = page.get_by_text("Where", exact=True).first
                if label.is_visible(timeout=3000):
                    # Click the next focusable/clickable: input, button, or div with role/listbox trigger
                    parent = label.locator("xpath=ancestor::*[.//input or .//button or .//*[@role='combobox']][1]")
                    if parent.count() > 0 and parent.first.is_visible(timeout=2000):
                        parent.first.click()
                        where_clicked = True
                        print("Clicked Where (parent of label).")
            except Exception:
                pass
        if not where_clicked:
            # Try: any clickable that shows "Where" and looks like a dropdown (placeholder "Select" or similar)
            try:
                # First input or button in the page that is in the same section as "Where"
                section = page.locator("label, [class*='filter'], [class*='where']").filter(has_text=re.compile(r"^\s*Where\s*$", re.I)).first
                if section.is_visible(timeout=3000):
                    # Next sibling or parent's next child that is clickable
                    trigger = section.locator("xpath=following-sibling::*[1] | ancestor::*[1]//*[@role='combobox'] | ancestor::*[2]//input | ancestor::*[2]//button").first
                    if trigger.count() > 0 and trigger.first.is_visible(timeout=2000):
                        trigger.first.click()
                        where_clicked = True
                        print("Clicked Where (section trigger).")
            except Exception:
                pass
        if not where_clicked:
            # Fallback: click the first visible combobox or the first input in a form (Where is often first)
            try:
                first_combobox = page.get_by_role("combobox").first
                if first_combobox.is_visible(timeout=3000):
                    first_combobox.click()
                    where_clicked = True
                    print("Clicked first combobox (Where).")
            except Exception:
                pass
        if not where_clicked:
            # Last resort: click near "Where" - the clickable area is often the whole filter block
            try:
                block = page.get_by_text("Where", exact=True).locator("xpath=ancestor::*[contains(@class, 'filter') or contains(@class, 'field') or contains(@class, 'select')][1]")
                if block.count() > 0 and block.first.is_visible(timeout=3000):
                    block.first.click()
                    where_clicked = True
                    print("Clicked Where block.")
            except Exception:
                pass
        if not where_clicked:
            raise Exception("Could not find or click the 'Where' dropdown")

        time.sleep(1)
        # 2) Wait for dropdown options and click "One Leisure St Ives Indoo" (or partial match)
        option_clicked = False
        for option_text in [self.WHERE_VALUE, "One Leisure St Ives", "St Ives Indoo", "St Ives"]:
            try:
                opt = page.get_by_role("option").filter(has_text=re.compile(re.escape(option_text.split(" Indoo")[0]), re.I)).first
                if opt.is_visible(timeout=2000):
                    opt.click()
                    option_clicked = True
                    print(f"Selected option: {option_text}")
                    break
            except Exception:
                try:
                    # Non-role option: any clickable text
                    opt = page.get_by_text(option_text, exact=False).first
                    if opt.is_visible(timeout=1500):
                        opt.click()
                        option_clicked = True
                        print(f"Selected option (text): {option_text}")
                        break
                except Exception:
                    continue
        if not option_clicked:
            raise Exception("Could not select 'One Leisure St Ives Indoo' from Where dropdown")
        time.sleep(0.5)

    def _set_what(self, page):
        """Fill or select 'What are you looking to do' with Court Bookings."""
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
                    el.fill(self.WHAT_VALUE)
                    time.sleep(1)
                    opt = page.get_by_text(self.WHAT_VALUE, exact=False).first
                    if opt.is_visible(timeout=2000):
                        opt.click()
                    print("Set What successfully.")
                    return
            except Exception as e:
                continue
        raise Exception("Could not set 'What are you looking to do' field")

    def _set_date(self, page):
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

    def _set_starting_from(self, page):
        """Open the 'Starting from' dropdown and select the first (earliest) option. Non-fatal if it fails."""
        # 1) Click the "Starting from" dropdown to open it (same pattern as Where)
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
                    parent = label.locator("xpath=ancestor::*[.//input or .//button or .//*[@role='combobox']][1]")
                    if parent.count() > 0 and parent.first.is_visible(timeout=2000):
                        parent.first.click()
                        opened = True
                        print("Clicked Starting from (parent of label).")
            except Exception:
                pass
        if not opened:
            try:
                first_cb = page.get_by_role("combobox").all()
                # "Starting from" is often the last or a later combobox; try the one that contains "Starting" in its accessible name
                for cb in first_cb:
                    if cb.is_visible(timeout=1000) and "starting" in (cb.get_attribute("aria-label") or cb.get_attribute("aria-labelledby") or "").lower():
                        cb.click()
                        opened = True
                        print("Clicked Starting from (combobox by aria).")
                        break
            except Exception:
                pass
        if not opened:
            try:
                block = page.get_by_text("Starting from", exact=True).locator("xpath=ancestor::*[contains(@class, 'filter') or contains(@class, 'field') or contains(@class, 'select')][1]")
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
        # 2) Select the first (earliest) option in the list instead of relying on "Starting now"
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
                # Fallback: first clickable that looks like a list item (e.g. div with time text)
                first_li = page.locator("[role='listbox'] >> [role='option'], [role='menu'] >> li, [class*='option']").first
                if first_li.is_visible(timeout=2000):
                    first_li.click()
                    option_clicked = True
                    print("Selected first option (listbox/menu).")
            except Exception:
                pass
        if not option_clicked:
            print("Warning: Could not select an option in 'Starting from'; continuing to Search.")
        time.sleep(0.5)

    def _submit_search(self, page):
        """Click the Search button (not 'Clear filters') to load results on the right, then wait for results."""
        search_clicked = False
        # Target only the actual Search button: exact text "Search", and explicitly exclude "Clear filters"
        candidates = [
            page.get_by_role("button", name="Search"),  # exact accessible name
            page.locator('button').filter(has_text=re.compile(r"^Search$", re.I)),
            page.get_by_text("Search", exact=True),
            page.locator('input[type="submit"][value="Search"]'),
            page.locator('button:has-text("Search")').filter(has_not=page.get_by_text("Clear", exact=False)),
        ]
        for candidate in candidates:
            try:
                el = candidate.first
                # Must not be the Clear filters button (ensure visible text is just "Search")
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
        # Wait for results panel: "See available spaces" or "Badminton" should appear on the right
        try:
            page.get_by_text("See available spaces", exact=False).first.wait_for(state="visible", timeout=15000)
            print("Results loaded (See available spaces visible).")
        except Exception:
            try:
                page.get_by_text("Badminton", exact=False).first.wait_for(state="visible", timeout=5000)
                print("Results loaded (Badminton card visible).")
            except Exception:
                if not search_clicked:
                    raise Exception("Search button was not clicked and results did not appear. Cannot proceed to timetable.")
        time.sleep(1)

    def _open_timetable(self, page):
        """Click 'See available spaces' — prefer Badminton Court card."""
        # Prefer: card containing "Badminton" then "See available spaces" inside it
        try:
            badminton_card = page.locator('[class*="card"], [class*="result"], article, section').filter(
                has_text=re.compile(r"Badminton", re.I)
            ).first
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

        # Fallback: first "See available spaces" on page
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

    def _extract_availability_from_timetable(self, page):
        """Extract slots from the timetable grid for the 7-day booking window only."""
        today = datetime.now().date()
        dates_to_scrape = [today + timedelta(days=i) for i in range(BOOKING_WINDOW_DAYS)]
        all_slots = []

        for target_date in dates_to_scrape:
            date_str = target_date.strftime("%Y-%m-%d")
            day_name = target_date.strftime("%A")
            day_num = target_date.day
            month_abbr = target_date.strftime("%b").lower()  # e.g. "feb"

            # Select this date in the calendar (click the day cell, e.g. "THU 5" or "5")
            if not self._select_timetable_date(page, target_date, day_num, month_abbr):
                print(f"  Could not select date {date_str}, skipping.")
                continue
            time.sleep(1)
            page.wait_for_load_state("networkidle", timeout=10000)

            # Scroll to load all time slots (down) and all courts (right, for Court 6)
            self._scroll_timetable_grid(page)
            time.sleep(0.5)

            # Find all slot cards for this date and parse them
            day_slots = self._parse_timetable_cards_for_date(page, date_str, day_name)
            all_slots.extend(day_slots)
            print(f"  {date_str}: {len(day_slots)} slots ({sum(1 for s in day_slots if s['is_available'])} available)")

        return all_slots

    def _select_timetable_date(self, page, target_date, day_num, month_abbr):
        """Click the calendar day cell for the given date (e.g. THU 5 in February)."""
        # Calendar shows "THU 5", "FRI 6", etc. Match day number as whole word so we don't match 5 in 15.
        day_pattern = re.compile(rf"(?:MON|TUE|WED|THU|FRI|SAT|SUN)\s+{day_num}\b", re.I)
        try:
            # Prefer: cell that shows "THU 5" style (day name + day number)
            day_cell = page.locator("[class*='calendar'], [class*='date'], [class*='day'], button, a").filter(
                has_text=day_pattern
            ).first
            if day_cell.is_visible(timeout=3000):
                day_cell.click()
                return True
        except Exception:
            pass
        try:
            # Fallback: any element whose text is exactly the day number (e.g. "5") in a calendar area
            day_cell = page.get_by_text(re.compile(rf"^{day_num}$"), exact=False).first
            if day_cell.is_visible(timeout=2000):
                day_cell.click()
                return True
        except Exception:
            pass
        return False

    def _scroll_timetable_grid(self, page):
        """Scroll down to load all time slots and right to load Court 6."""
        try:
            # Scroll main content down (multiple steps to load all hours)
            for _ in range(4):
                page.mouse.wheel(0, 400)
                time.sleep(0.2)
            # Scroll back up so we can parse from top
            for _ in range(4):
                page.mouse.wheel(0, -400)
                time.sleep(0.2)
            # Scroll right to reveal Court 6
            page.mouse.wheel(300, 0)
            time.sleep(0.3)
            page.mouse.wheel(-300, 0)
            time.sleep(0.2)
        except Exception:
            pass

    def _parse_timetable_cards_for_date(self, page, date_str, day_name):
        """Find all slot cards in the grid and parse court, time, availability. Only 'Book now' = available."""
        slots = []
        # Cards contain: "Court N", "HH:MM - HH:MM", "Thu 5th Feb", and either "Book now" or "unavailable" or "available to be booked"
        card_selectors = [
            page.locator("[class*='card'], [class*='slot'], [class*='cell']").filter(
                has_text=re.compile(r"Court\s+\d+", re.I)
            ).filter(has_text=re.compile(r"\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}")),
            page.locator("[class*='slot']").filter(has_text=re.compile(r"Court\s+\d+", re.I)),
        ]
        cards = []
        for sel in card_selectors:
            try:
                for el in sel.all():
                    if el.is_visible(timeout=300):
                        cards.append(el)
                if cards:
                    break
            except Exception:
                continue
        if not cards:
            # Fallback: any element that has Court + time range + one of the status phrases
            try:
                candidates = page.locator("div, article, section").filter(
                    has_text=re.compile(r"Court\s+\d+.*\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}", re.S)
                ).all()
                for el in candidates:
                    try:
                        t = el.inner_text()
                        if len(t) > 500:
                            continue
                        if re.search(r"Court\s+\d+", t, re.I) and re.search(r"\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}", t):
                            cards.append(el)
                    except Exception:
                        continue
            except Exception:
                pass

        seen = set()
        for card in cards:
            try:
                text = card.inner_text()
                # Court: "Court 1" .. "Court 6"
                court_m = re.search(r"Court\s+(\d+)", text, re.I)
                if not court_m:
                    continue
                court_num = court_m.group(1)
                court_label = f"Court {court_num}"
                # Time: "15:00 - 16:00"
                time_m = re.search(r"(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})", text)
                if not time_m:
                    continue
                start_time = f"{int(time_m.group(1)):02d}:{time_m.group(2)}"
                end_time = f"{int(time_m.group(3)):02d}:{time_m.group(4)}"
                key = (date_str, court_label, start_time)
                if key in seen:
                    continue
                seen.add(key)
                # Availability: only "Book now" means bookable; "unavailable" or "available to be booked on" = not
                is_available = bool(re.search(r"Book\s+now", text, re.I))
                slots.append({
                    "date": date_str,
                    "day_name": day_name,
                    "start_time": start_time,
                    "end_time": end_time,
                    "court_number": court_label,
                    "is_available": is_available,
                })
            except Exception:
                continue
        return slots

    def _store_availability(self, availability):
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
        print(f"Stored {len(availability)} availability records.")


if __name__ == "__main__":
    scraper = OneLeisureStIvesScraper(headless=False)
    try:
        scraper.scrape()
        print("Done.")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
