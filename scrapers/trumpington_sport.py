"""Scraper for Trumpington Sport (Abbeycroft Leisure) badminton court availability.

Flow: Abbeycroft Legend login → Drop ins → Select club "Trumpington Sport" →
Court bookings → Badminton → View timetable. Scrapes today + 13 days.
Red X = booked, green arrow / N Slots = bookable (same Legend UI as Hill Roads).
"""
import os
import time
import re
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import init_db, get_session, Facility, CourtAvailability

load_dotenv()

# Number of days to scrape: today + 13 following = 14 days
SCRAPE_DAYS = 14


class TrumpingtonSportScraper:
    """Scraper for Trumpington Sport (Abbeycroft) badminton courts via Legend."""

    # Racquet sports timetable goes to Legend login
    LOGIN_URL = "https://abbeycroft.legendonlineservices.co.uk/enterprise/account/login"

    def __init__(self, headless=True):
        self.headless = headless if headless is not None else True
        self.username = os.getenv("LOGIN_USERNAME", "theparker1337@gmail.com")
        self.password = os.getenv("LOGIN_PASSWORD", "CourtFinder123!")
        self.db_engine = init_db()
        self.session = get_session(self.db_engine)
        self.facility = self._get_or_create_facility()

    def _get_or_create_facility(self):
        """Get or create the Trumpington Sport facility record."""
        name = "Trumpington Sport"
        facility = self.session.query(Facility).filter_by(name=name).first()
        if not facility:
            facility = Facility(name=name)
            self.session.add(facility)
            self.session.commit()
        return facility

    def scrape(self):
        """Main scraping method."""
        print("Starting Trumpington Sport (Abbeycroft) scraper...")

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
                # Step 1: Go to Legend login (Abbeycroft racquet sports)
                print(f"Navigating to {self.LOGIN_URL}...")
                page.goto(self.LOGIN_URL, wait_until="networkidle", timeout=60000)
                time.sleep(2)

                # Step 2: Login
                print("Logging in...")
                self._login(page)

                # Step 3: Click "Drop ins" in the Make a booking section (right side)
                print("Looking for 'Drop ins'...")
                self._click_drop_ins(page)

                # Step 4: Select club "Trumpington Sport"
                print("Selecting club Trumpington Sport...")
                self._select_club(page)
                time.sleep(3)  # Let category section load (radios appear after club selected)

                # Step 5: Select category "Court Bookings" radio
                print("Selecting Court bookings...")
                self._select_court_bookings(page)

                # Step 6: Select activity "Badminton" (if present; some Legend flows show View Timetable directly)
                print("Selecting Badminton...")
                self._select_badminton(page)

                # Step 7: Click "View timetable"
                print("Clicking View timetable...")
                self._click_view_timetable(page)

                time.sleep(3)
                page.wait_for_load_state("networkidle", timeout=30000)
                print(f"Timetable URL: {page.url}")

                # Step 8: Scrape today + 13 days (14 total). Date bar reveals one more day
                # each time you click (TODAY → TOMORROW → 13 FEB 2026 → …). Click through
                # to reveal and select each day.
                all_availability = []
                print(f"Scraping {SCRAPE_DAYS} days (click through date bar to reveal each)...")

                for day_index in range(SCRAPE_DAYS):
                    date_tabs = self._get_date_tabs(page)
                    # Click the rightmost tab repeatedly to reveal the next day until we have a tab for this index
                    while len(date_tabs) <= day_index:
                        if not date_tabs:
                            break
                        prev_count = len(date_tabs)
                        try:
                            date_tabs[-1].click()
                            time.sleep(2)
                            page.wait_for_load_state("networkidle", timeout=10000)
                            date_tabs = self._get_date_tabs(page)
                            if len(date_tabs) <= prev_count:
                                break  # No new tab appeared
                        except Exception:
                            break
                    if day_index < len(date_tabs):
                        tab = date_tabs[day_index]
                        try:
                            tab.click()
                            time.sleep(2)
                            page.wait_for_load_state("networkidle", timeout=15000)
                            day_availability = self._extract_availability(page)
                            all_availability.extend(day_availability)
                            print(f"  Day {day_index + 1}: {len(day_availability)} slots")
                        except Exception as e:
                            print(f"  Day {day_index + 1} failed: {e}")
                        continue
                    # Fallback: use date picker (far right of date bar) to select today + day_index
                    target_date = datetime.now().date() + timedelta(days=day_index)
                    if self._select_date_via_picker(page, target_date):
                        time.sleep(2)
                        page.wait_for_load_state("networkidle", timeout=15000)
                        try:
                            day_availability = self._extract_availability(page, expected_date=target_date)
                            all_availability.extend(day_availability)
                            print(f"  Day {day_index + 1} (picker): {len(day_availability)} slots")
                        except Exception as e:
                            print(f"  Day {day_index + 1} failed: {e}")
                    else:
                        print(f"  Day {day_index + 1}: no tab or picker, skipping")

                # Step 9: Store in database
                print(f"Storing {len(all_availability)} availability records...")
                self._store_availability(all_availability)

                print("Trumpington Sport scraping completed successfully!")
            except Exception as e:
                print(f"Error during scraping: {e}")
                page.screenshot(path="debug_trumpington_error.png")
                raise
            finally:
                browser.close()
                self.session.close()

    def _login(self, page):
        """Handle login (email + password + Login)."""
        page.wait_for_selector(
            "input[type='email'], input[type='text'], input[type='password']",
            timeout=30000,
        )
        time.sleep(2)

        # Email
        for selector in [
            "input[type='email']",
            "input[name*='email' i]",
            "input[id*='email' i]",
            "input[type='text']",
        ]:
            try:
                page.locator(selector).first.fill(self.username, timeout=10000)
                print("Filled email")
                break
            except Exception:
                continue
        else:
            raise Exception("Could not find email input")

        time.sleep(1)
        page.locator("input[type='password']").first.fill(self.password)
        print("Filled password")
        time.sleep(1)

        # Submit (Login button)
        for sel in [
            "button[type='submit']",
            "input[type='submit']",
            "button:has-text('Login')",
            "button:has-text('Sign in')",
        ]:
            try:
                btn = page.locator(sel).first
                if btn.is_visible():
                    btn.click()
                    break
            except Exception:
                continue
        else:
            page.keyboard.press("Enter")

        time.sleep(5)
        page.wait_for_load_state("networkidle", timeout=30000)
        time.sleep(2)
        print(f"After login: {page.url}")

    def _click_drop_ins(self, page):
        """Click 'Drop ins' in the Make a booking section."""
        for selector in [
            'a:has-text("Drop ins")',
            'button:has-text("Drop ins")',
            '[class*="drop"]:has-text("Drop ins")',
            'text="Drop ins"',
        ]:
            try:
                el = page.locator(selector).first
                if el.is_visible(timeout=5000):
                    el.click()
                    time.sleep(3)
                    page.wait_for_load_state("networkidle", timeout=15000)
                    print("Clicked Drop ins")
                    return
            except Exception:
                continue
        raise Exception("Could not find 'Drop ins'")

    def _select_club(self, page):
        """Select club 'Trumpington Sport' in the main content Clubs field (combobox)."""
        # Open the Clubs combobox in the main "Online Booking" area (placeholder "Please select a clubs")
        try:
            clubs_input = page.get_by_placeholder(re.compile(r"Please select a club", re.I)).first
            if clubs_input.is_visible(timeout=5000):
                clubs_input.click()
                time.sleep(1)
                # Click the option "Trumpington Sport" in the dropdown
                opt = page.get_by_role("option").filter(has_text="Trumpington Sport").first
                if opt.is_visible(timeout=5000):
                    opt.click()
                    time.sleep(2)
                    page.wait_for_load_state("networkidle", timeout=10000)
                    print("Selected club: Trumpington Sport (combobox)")
                    return
        except Exception as e:
            print(f"  Combobox path: {e}")
        try:
            # Fallback: click label "Clubs" then find and click option
            page.get_by_text("Clubs", exact=True).first.click()
            time.sleep(1)
            page.get_by_text("Trumpington Sport", exact=True).first.click()
            time.sleep(2)
            page.wait_for_load_state("networkidle", timeout=10000)
            print("Selected club: Trumpington Sport (label + text)")
            return
        except Exception:
            pass
        for name in ["Trumpington Sport", "Trumpington", "trumpington sport"]:
            try:
                sel = page.locator("select").first
                if sel.is_visible(timeout=2000):
                    sel.select_option(label=name)
                    time.sleep(2)
                    page.wait_for_load_state("networkidle", timeout=10000)
                    print(f"Selected club: {name}")
                    return
            except Exception:
                pass
            try:
                el = page.get_by_text(re.compile(re.escape(name), re.I)).first
                if el.is_visible(timeout=3000):
                    el.click()
                    time.sleep(2)
                    page.wait_for_load_state("networkidle", timeout=10000)
                    print(f"Selected club (text): {name}")
                    return
            except Exception:
                continue
        raise Exception("Could not select club Trumpington Sport")

    def _select_court_bookings(self, page):
        """Select the 'Court Bookings' radio in the Category section (not the left nav)."""
        # Wait for Category section to show radios (loads after club selected)
        try:
            page.get_by_text(re.compile(r"Court Bookings|Appointments and Inductions")).first.wait_for(
                state="visible", timeout=10000
            )
            time.sleep(1)
        except Exception:
            pass
        for label_text in ["Court Bookings", "Court bookings"]:
            try:
                radio = page.get_by_role("radio", name=label_text).first
                if radio.is_visible(timeout=3000):
                    radio.check()
                    time.sleep(2)
                    page.wait_for_load_state("networkidle", timeout=10000)
                    print("Selected Court Bookings (category radio)")
                    return
            except Exception:
                pass
            try:
                label = page.locator(f'label:has-text("{label_text}")').first
                if label.is_visible(timeout=3000):
                    label.click()
                    time.sleep(2)
                    page.wait_for_load_state("networkidle", timeout=10000)
                    print("Selected Court Bookings (label click)")
                    return
            except Exception:
                continue
        # Fallback: click element with exact text "Court Bookings" in main content (avoid left nav)
        try:
            # Prefer main content area so we don't click "Court hire and appointments" in the nav
            main = page.locator("main, [role='main'], #content, .content, .main-content").first
            if main.is_visible(timeout=2000):
                el = main.get_by_text("Court Bookings", exact=True).first
                if el.is_visible(timeout=3000):
                    el.click()
                    time.sleep(2)
                    page.wait_for_load_state("networkidle", timeout=10000)
                    print("Selected Court Bookings (main content text)")
                    return
            el = page.get_by_text("Court Bookings", exact=True).first
            if el.is_visible(timeout=3000):
                el.click()
                time.sleep(2)
                page.wait_for_load_state("networkidle", timeout=10000)
                print("Selected Court Bookings (text click)")
                return
        except Exception:
            pass
        page.screenshot(path="debug_trumpington_no_court_bookings.png")
        raise Exception("Could not select Court Bookings category radio")

    def _select_badminton(self, page):
        """Check the 'Badminton' checkbox in the Activities section (enables View Timetable)."""
        time.sleep(2)  # Let activities checkboxes load after Court Bookings is selected
        for name in ["Badminton", "badminton"]:
            try:
                cb = page.get_by_role("checkbox", name=name).first
                if cb.is_visible(timeout=5000):
                    cb.check()
                    time.sleep(2)
                    page.wait_for_load_state("networkidle", timeout=10000)
                    print("Selected Badminton (checkbox)")
                    return True
            except Exception:
                pass
            try:
                label = page.locator(f'label:has-text("{name}")').first
                if label.is_visible(timeout=3000):
                    label.click()
                    time.sleep(2)
                    page.wait_for_load_state("networkidle", timeout=10000)
                    print("Selected Badminton (label)")
                    return True
            except Exception:
                continue
        try:
            el = page.get_by_text("Badminton", exact=True).first
            if el.is_visible(timeout=2000):
                el.click()
                time.sleep(2)
                page.wait_for_load_state("networkidle", timeout=10000)
                print("Selected Badminton (text click)")
                return True
        except Exception:
            pass
        page.screenshot(path="debug_trumpington_no_badminton.png")
        raise Exception("Could not select Badminton checkbox in Activities")

    def _click_view_timetable(self, page):
        """Click 'View timetable' button (bottom right). Uses short timeouts to avoid hanging if button is disabled."""
        wait_after = 10000  # 10s max wait after click
        for candidate in [
            page.get_by_role("button", name="View Timetable"),
            page.get_by_role("link", name="View Timetable"),
            page.get_by_text("View Timetable", exact=True),
        ]:
            try:
                if candidate.first.is_visible(timeout=3000):
                    candidate.first.click()
                    try:
                        page.wait_for_load_state("networkidle", timeout=wait_after)
                    except Exception:
                        pass
                    print("Clicked View timetable")
                    return
            except Exception:
                continue
        for selector in [
            'button:has-text("View Timetable")',
            'a:has-text("View Timetable")',
            '[class*="timetable"]:has-text("View Timetable")',
        ]:
            try:
                el = page.locator(selector).first
                if el.is_visible(timeout=3000):
                    el.click()
                    try:
                        page.wait_for_load_state("networkidle", timeout=wait_after)
                    except Exception:
                        pass
                    print("Clicked View timetable (selector)")
                    return
            except Exception:
                continue
        raise Exception("Could not find or click 'View timetable' button (ensure Badminton is selected if required)")

    def _select_date_via_picker(self, page, target_date):
        """Use the date picker (calendar icon, far right of date bar) to select the given date. Returns True if done."""
        try:
            # Find date picker: input or button near the calendar icon / current date text
            picker = page.locator(
                "input[type='date'], input[type='text'][class*='date'], "
                "[class*='datepicker'], [class*='calendar'] button, button[aria-label*='date' i]"
            ).first
            if not picker.is_visible(timeout=3000):
                # Try clicking visible date text (e.g. "12 Feb 2026") next to calendar icon
                date_str = target_date.strftime("%d %b %Y")
                picker = page.get_by_text(re.compile(r"\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}")).first
            if picker.is_visible(timeout=2000):
                picker.click()
                time.sleep(1)
                # In the calendar popup, click the day number for target_date
                day_num = target_date.day
                day_el = page.get_by_text(re.compile(rf"^{day_num}$")).first
                if day_el.is_visible(timeout=3000):
                    day_el.click()
                    return True
                # Some pickers use aria or data attributes
                day_el = page.locator(f"[data-day='{day_num}'], [aria-label*='{day_num}']").first
                if day_el.is_visible(timeout=2000):
                    day_el.click()
                    return True
        except Exception:
            pass
        return False

    def _get_date_tabs(self, page):
        """Return list of date tab locators (TODAY, TOMORROW, then dates) in order."""
        tab_pattern = re.compile(
            r"^(TODAY|TOMORROW|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})$",
            re.I,
        )
        tabs = []
        try:
            candidates = page.locator(
                '[role="tab"], [class*="tab"], [class*="date"], a, button'
            ).filter(
                has_text=re.compile(
                    r"TODAY|TOMORROW|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}",
                    re.I,
                )
            ).all()
            seen = set()
            for el in candidates:
                if not el.is_visible(timeout=500):
                    continue
                text = el.inner_text().strip()
                if tab_pattern.match(text) or text.upper() in ("TODAY", "TOMORROW"):
                    key = text.upper()[:50]
                    if key not in seen:
                        seen.add(key)
                        tabs.append(el)
            return tabs[:15]
        except Exception as e:
            print(f"Date tabs: {e}")
        return tabs

    def _get_viewing_date(self, page):
        """Parse the currently selected date from the timetable tab."""
        today = datetime.now().date()
        try:
            selected = page.locator(
                '[class*="active"]:has-text("TODAY"), [class*="active"]:has-text("TOMORROW"), '
                '[class*="selected"]:has-text("TODAY"), [class*="selected"]:has-text("TOMORROW")'
            ).first
            if selected.is_visible(timeout=2000):
                text = selected.inner_text().strip().upper()
                if "TODAY" in text:
                    return today, today.strftime("%A")
                if "TOMORROW" in text:
                    d = today + timedelta(days=1)
                    return d, d.strftime("%A")
        except Exception:
            pass
        try:
            date_links = page.locator(
                'a, button, [role="tab"]'
            ).filter(
                has_text=re.compile(
                    r"\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}",
                    re.I,
                )
            ).all()
            months = {
                "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
                "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
            }
            for link in date_links[:5]:
                t = link.inner_text().strip()
                m = re.search(
                    r"(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})",
                    t,
                    re.I,
                )
                if m:
                    day, mon_name, year = int(m.group(1)), m.group(2), int(m.group(3))
                    mon = months.get(mon_name.capitalize()[:3])
                    if mon:
                        d = datetime(year, mon, day).date()
                        cls = link.get_attribute("class") or ""
                        if "active" in cls or "selected" in cls:
                            return d, d.strftime("%A")
        except Exception:
            pass
        return today, today.strftime("%A")

    def _extract_availability(self, page, expected_date=None):
        """Extract slots from timetable: red X = booked, green arrow / N Slots = bookable.
        If expected_date is set (e.g. from date picker), use it when the tab date can't be parsed."""
        availability = []
        today = datetime.now().date()
        viewing_date, day_name = self._get_viewing_date(page)
        if expected_date is not None:
            viewing_date = expected_date
            day_name = expected_date.strftime("%A")
        date_str = viewing_date.strftime("%Y-%m-%d")

        # Same pattern as Hill Roads: slot cards with time and "Full" or "N Slots"
        card_selectors = [
            "[class*='slot']",
            "[class*='Slot']",
            "[class*='tile']",
            "[class*='card']",
            "[class*='booking']",
            "[class*='time-slot']",
        ]
        cards = []
        for selector in card_selectors:
            try:
                for el in page.locator(selector).all():
                    if not el.is_visible(timeout=500):
                        continue
                    text = el.inner_text()
                    if re.search(r"\d{1,2}:\d{2}", text) and (
                        re.search(r"\bFull\b", text, re.I)
                        or re.search(r"\d+\s*Slots?", text, re.I)
                    ):
                        cards.append(el)
                if cards:
                    break
            except Exception:
                continue

        if not cards:
            try:
                for el in page.locator("div").all():
                    try:
                        if not el.is_visible(timeout=200):
                            continue
                        text = el.inner_text()
                        if len(text) > 500:
                            continue
                        if re.search(r"\d{1,2}:\d{2}", text) and (
                            re.search(r"\bFull\b", text, re.I)
                            or re.search(r"\d+\s*Slots?", text, re.I)
                        ):
                            cards.append(el)
                    except Exception:
                        continue
            except Exception:
                pass

        # Deduplicate by time
        seen_times = set()
        unique_cards = []
        for card in cards:
            try:
                text = card.inner_text()
                m = re.search(r"(\d{1,2}):(\d{2})", text)
                if m:
                    t = f"{int(m.group(1)):02d}:{m.group(2)}"
                    if t not in seen_times:
                        seen_times.add(t)
                        unique_cards.append(card)
            except Exception:
                continue

        for card in unique_cards:
            try:
                text = card.inner_text()
                time_m = re.search(r"(\d{1,2}):(\d{2})", text)
                if not time_m:
                    continue
                hour, minute = int(time_m.group(1)), int(time_m.group(2))
                start_time = f"{hour:02d}:{minute:02d}"
                if hour + 1 >= 24:
                    continue
                end_time = f"{hour + 1:02d}:{minute:02d}"

                if re.search(r"\bFull\b", text, re.I):
                    num_slots = 0
                    is_available = False
                else:
                    slot_m = re.search(r"(\d+)\s*Slots?", text, re.I)
                    num_slots = int(slot_m.group(1)) if slot_m else 0
                    is_available = num_slots > 0

                if num_slots > 0:
                    for i in range(1, num_slots + 1):
                        availability.append({
                            "date": date_str,
                            "day_name": day_name,
                            "start_time": start_time,
                            "end_time": end_time,
                            "court_number": f"Court {i}",
                            "is_available": True,
                        })
                else:
                    availability.append({
                        "date": date_str,
                        "day_name": day_name,
                        "start_time": start_time,
                        "end_time": end_time,
                        "court_number": "Court 1",
                        "is_available": False,
                    })
            except Exception as e:
                print(f"Parse slot: {e}")
                continue

        return availability

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
    scraper = TrumpingtonSportScraper(headless=False)
    try:
        scraper.scrape()
        print("Done.")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
