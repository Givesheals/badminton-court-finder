"""Scraper for Hill Roads Sport and Tennis Centre badminton court availability."""
import os
import time
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from dotenv import load_dotenv
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import init_db, get_session, Facility, CourtAvailability

load_dotenv()


class HillRoadsScraper:
    """Scraper for Hill Roads Sport and Tennis Centre badminton courts."""
    
    BASE_URL = "https://hillsroad.legendonlineservices.co.uk/enterprise/account/login"
    
    def __init__(self, headless=True):
        self.headless = headless if headless is not None else True
        self.username = os.getenv('LOGIN_USERNAME', 'theparker1337@gmail.com')
        self.password = os.getenv('LOGIN_PASSWORD', 'CourtFinder123!')
        self.db_engine = init_db()
        self.session = get_session(self.db_engine)
        
        # Ensure facility exists in database
        self.facility = self._get_or_create_facility()
    
    def _get_or_create_facility(self):
        """Get or create the Hill Roads facility record."""
        facility = self.session.query(Facility).filter_by(name='Hill Roads Sport and Tennis Centre').first()
        if not facility:
            facility = Facility(name='Hill Roads Sport and Tennis Centre')
            self.session.add(facility)
            self.session.commit()
        return facility
    
    def scrape(self):
        """Main scraping method."""
        print("Starting Hill Roads Sport and Tennis Centre scraper...")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.headless,
                args=['--disable-blink-features=AutomationControlled']
            )
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                locale='en-GB',
                timezone_id='Europe/London',
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-GB,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
            )
            # Hide webdriver flag
            page = context.new_page()
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            try:
                # Step 1: Navigate to homepage/login
                print(f"Navigating to {self.BASE_URL}...")
                page.goto(self.BASE_URL, wait_until='networkidle')
                time.sleep(2)
                
                # Step 2: Login
                print("Attempting to log in...")
                self._login(page)
                
                # Step 3: Click "make a booking"
                print("Looking for 'make a booking' button...")
                print(f"Current URL before 'make a booking': {page.url}")
                print(f"Current page title: {page.title()}")
                
                # Take screenshot before looking for button
                page.screenshot(path='debug_before_make_booking.png')
                
                # Look for the "Make a Booking" link in the main content area (not sidebar)
                # Based on debug: it's a link (not a button) - Link 7 and Link 24 both say "Make a Booking"
                # We want the one in the main content, not the sidebar "Make Bookings"
                make_booking_selectors = [
                    'a:has-text("Make a Booking")',  # Main link in content area
                    'a:has-text("make a booking")',
                    'text="Make a Booking" i',  # Case-insensitive text match
                    'text="make a booking" i'
                ]
                make_booking = None
                clicked = False
                for selector in make_booking_selectors:
                    try:
                        # Get all matches (there might be 2 - sidebar and main content)
                        all_matches = page.locator(selector).all()
                        print(f"Found {len(all_matches)} matches for selector: {selector}")
                        
                        # Try the second match first (index 1) as it's likely the main content one
                        # If that doesn't work, try the first one
                        matches_to_try = [1, 0] if len(all_matches) > 1 else [0]
                        
                        for match_idx in matches_to_try:
                            if match_idx >= len(all_matches):
                                continue
                            try:
                                match = all_matches[match_idx]
                                if match.is_visible(timeout=2000):
                                    make_booking = match
                                    print(f"Found 'make a booking' element (match {match_idx}) using: {selector}")
                                    # Try to click and wait for navigation
                                    try:
                                        with page.expect_navigation(timeout=10000, wait_until='networkidle'):
                                            make_booking.click()
                                        clicked = True
                                        print(f"Clicked 'make a booking' using: {selector}")
                                        break
                                    except:
                                        # No navigation, just click
                                        make_booking.click()
                                        page.wait_for_load_state('networkidle', timeout=10000)
                                        clicked = True
                                        print(f"Clicked 'make a booking' using: {selector} (no navigation)")
                                        break
                            except:
                                continue
                        
                        if clicked:
                            break
                    except Exception as e:
                        print(f"Selector {selector} failed: {str(e)[:100]}")
                        continue
                
                if not clicked:
                    # Debug: show what buttons are on the page
                    print("DEBUG: Listing all BUTTONS on page...")
                    all_buttons = page.locator('button').all()
                    print(f"Found {len(all_buttons)} buttons on page:")
                    for i, btn in enumerate(all_buttons):
                        try:
                            text = btn.inner_text().strip()[:50] or btn.get_attribute('value') or 'no text'
                            print(f"  Button {i+1}: '{text}'")
                        except Exception as e:
                            print(f"  Button {i+1}: Error reading: {e}")
                    
                    # Also check links
                    print("\nDEBUG: Listing links with 'booking' in text...")
                    booking_links = page.locator('a').all()
                    for i, link in enumerate(booking_links):
                        try:
                            text = link.inner_text().strip().lower()
                            if 'booking' in text:
                                print(f"  Link {i+1}: '{link.inner_text().strip()}'")
                        except:
                            pass
                    
                    page.screenshot(path='debug_no_make_booking.png')
                    raise Exception("Could not find 'make a booking' button")
                
                time.sleep(3)
                print(f"Current URL after 'make a booking': {page.url}")
                print(f"Page title after 'make a booking': {page.title()}")
                
                # Step 4: Wait for booking page to load (AJAX content)
                print("Waiting for booking page content to load...")
                time.sleep(3)
                page.wait_for_load_state('networkidle', timeout=30000)
                
                # Wait for booking form elements to appear (radio buttons or form)
                print("Waiting for booking form to appear...")
                try:
                    # Wait for radio buttons or form to appear
                    page.wait_for_selector('input[type="radio"], form, [class*="booking"], [id*="booking"]', timeout=15000)
                    print("Booking form elements detected")
                except:
                    print("Warning: Booking form elements not detected, continuing anyway...")
                
                print(f"After 'Make Bookings', URL: {page.url}, Title: {page.title()}")
                page.screenshot(path='debug_after_make_bookings.png')
                
                # Step 5: Click "sports hall" radio button
                print("Clicking 'sports hall' radio button...")
                sports_hall_selectors = [
                    'input[type="radio"][value*="sports hall" i]',
                    'input[type="radio"][value*="Sports Hall" i]',
                    'label:has-text("sports hall") input[type="radio"]',
                    'label:has-text("Sports Hall") input[type="radio"]',
                    'input[type="radio"]:near(label:has-text("sports hall"))',
                    'input[type="radio"]:near(label:has-text("Sports Hall"))'
                ]
                sports_hall_radio = None
                for selector in sports_hall_selectors:
                    try:
                        sports_hall_radio = page.locator(selector).first
                        if sports_hall_radio.is_visible(timeout=10000):
                            sports_hall_radio.click()
                            print(f"Clicked 'sports hall' using: {selector}")
                            break
                    except Exception as e:
                        print(f"Selector {selector} failed: {e}")
                        continue
                if not sports_hall_radio:
                    # Debug: show all radio buttons
                    all_radios = page.locator('input[type="radio"]').all()
                    print(f"Found {len(all_radios)} radio buttons on page:")
                    for i, radio in enumerate(all_radios[:10]):
                        try:
                            value = radio.get_attribute('value') or 'no value'
                            label = page.locator(f'label[for="{radio.get_attribute("id")}"]').inner_text() if radio.get_attribute('id') else 'no label'
                            print(f"  {i+1}: value={value}, label={label}")
                        except:
                            pass
                    page.screenshot(path='debug_no_sports_hall.png')
                    raise Exception("Could not find 'sports hall' radio button")
                time.sleep(3)
                print("Sports hall radio clicked, waiting for activities to load...")
                
                # Step 6: Click badminton checkbox (click the LABEL so the checkbox toggles regardless of HTML structure)
                print("Clicking badminton checkbox...")
                badminton_clicked = False
                # Prefer clicking the label containing "Badminton" - works for both <label><input>Badminton and <input id><label for>Badminton
                for label_text in ["Badminton", "badminton"]:
                    try:
                        label_el = page.get_by_role("checkbox", name=label_text)
                        if label_el.is_visible(timeout=3000):
                            label_el.check()
                            badminton_clicked = True
                            print(f"Checked badminton via get_by_role(checkbox, name={label_text!r})")
                            break
                    except Exception as e:
                        print(f"get_by_role(checkbox, name={label_text!r}): {e}")
                if not badminton_clicked:
                    try:
                        label_el = page.locator('label:has-text("Badminton")').first
                        if label_el.is_visible(timeout=3000):
                            label_el.click()
                            badminton_clicked = True
                            print("Checked badminton by clicking label:has-text('Badminton')")
                    except Exception as e:
                        print(f"label click: {e}")
                if not badminton_clicked:
                    # Fallback: click checkbox by value or nearby label
                    for selector in [
                        'input[type="checkbox"][value*="badminton" i]',
                        'input[type="checkbox"][value*="Badminton"]',
                    ]:
                        try:
                            cb = page.locator(selector).first
                            if cb.is_visible(timeout=3000):
                                cb.check()
                                badminton_clicked = True
                                print(f"Checked badminton via selector: {selector}")
                                break
                        except Exception as e:
                            print(f"Selector {selector}: {e}")
                if not badminton_clicked:
                    raise Exception("Could not find or check badminton checkbox")
                time.sleep(2)
                page.wait_for_load_state('networkidle', timeout=15000)
                print("Badminton checkbox clicked, waiting for timetable to load...")
                
                # Verify badminton is actually selected (find checkbox again for verification)
                try:
                    cb = page.locator('input[type="checkbox"][value*="badminton" i], input[type="checkbox"][value*="Badminton"]').first
                    if cb.is_visible(timeout=2000):
                        print(f"Badminton checkbox is checked: {cb.is_checked()}")
                except Exception:
                    print("Could not verify if badminton is checked")
                
                print(f"Current URL after badminton: {page.url}")
                page.screenshot(path='debug_after_badminton.png')
                
                # Look for time slot elements - they might be in a different structure
                time_slots = page.locator('[class*="time"], [class*="hour"], [class*="slot"]').all()
                print(f"Found {len(time_slots)} time slot elements on page")
                for i, slot in enumerate(time_slots[:5]):
                    try:
                        text = slot.inner_text().strip()[:50]
                        print(f"  Time slot {i+1}: '{text}'")
                    except:
                        pass
                
                # Step 7: Click "View Timetable" button (bottom right)
                print("Clicking 'View Timetable'...")
                page.screenshot(path='debug_before_timetable.png')
                
                view_timetable_clicked = False
                # Prefer role-based and exact text so we hit the green button, not a menu item
                view_timetable_candidates = [
                    ('role', 'button', 'View Timetable'),
                    ('role', 'link', 'View Timetable'),
                    ('text', None, 'View Timetable'),
                ]
                for kind, role_or_none, name in view_timetable_candidates:
                    try:
                        if kind == 'role' and role_or_none:
                            btn = page.get_by_role(role_or_none, name=name)
                        else:
                            btn = page.get_by_text(name, exact=True)
                        if btn.is_visible(timeout=3000):
                            url_before = page.url
                            btn.click()
                            # Wait for either URL change or network idle (timetable may load in-page)
                            try:
                                page.wait_for_url(lambda u: u != url_before, timeout=8000)
                            except Exception:
                                page.wait_for_load_state('networkidle', timeout=8000)
                            view_timetable_clicked = True
                            print(f"Clicked 'View Timetable' (kind={kind}, name={name}), URL now: {page.url}")
                            break
                    except Exception as e:
                        print(f"View Timetable candidate {kind}={name}: {e}")
                        continue
                if not view_timetable_clicked:
                    timetable_selectors = [
                        'button:has-text("View Timetable")',
                        'a:has-text("View Timetable")',
                        'input[type="submit"][value*="View Timetable" i]',
                        '[class*="timetable"]:has-text("View Timetable")',
                    ]
                    for selector in timetable_selectors:
                        try:
                            view_timetable = page.locator(selector).first
                            if view_timetable.is_visible(timeout=3000):
                                url_before = page.url
                                view_timetable.click()
                                try:
                                    page.wait_for_url(lambda u: u != url_before, timeout=8000)
                                except Exception:
                                    page.wait_for_load_state('networkidle', timeout=8000)
                                view_timetable_clicked = True
                                print(f"Clicked 'View Timetable' using: {selector}")
                                break
                        except Exception as e:
                            print(f"Selector {selector}: {e}")
                            continue
                if not view_timetable_clicked:
                    # Debug: show what buttons/links are on the page
                    print("DEBUG: Listing all clickable elements on page...")
                    all_buttons = page.locator('button, a, input[type="submit"], input[type="button"], input[type="submit"]').all()
                    print(f"Found {len(all_buttons)} buttons/links on page:")
                    for i, btn in enumerate(all_buttons[:15]):
                        try:
                            text = btn.inner_text()[:50] or btn.get_attribute('value') or btn.get_attribute('href') or 'no text'
                            print(f"  {i+1}: {text}")
                        except Exception as e:
                            print(f"  {i+1}: Error reading button: {e}")
                    
                    # Also try to find anything with "timetable" or "view" in text
                    print("\nDEBUG: Looking for elements containing 'timetable' or 'view'...")
                    timetable_text = page.locator('text=/timetable/i, text=/view/i').all()
                    print(f"Found {len(timetable_text)} elements with 'timetable' or 'view' text")
                    for i, elem in enumerate(timetable_text[:5]):
                        try:
                            text = elem.inner_text()[:50]
                            print(f"  {i+1}: {text}")
                        except:
                            pass
                    
                    page.screenshot(path='debug_no_timetable_button.png')
                    print("Warning: 'view timetable' button not found - timetable may already be loaded")
                    # Don't raise - continue to try extracting timetable
                page.wait_for_load_state('networkidle', timeout=30000)
                time.sleep(3)
                print(f"Current URL after 'view timetable': {page.url}")
                page.screenshot(path='debug_after_timetable.png')
                
                # Step 8: Scrape all available days (same pattern as Linton - all days in one run)
                MAX_DAYS = 5
                all_availability = []
                date_tabs = self._get_date_tabs(page)
                print(f"Found {len(date_tabs)} date tabs, scraping up to {MAX_DAYS} days...")
                
                for day_index in range(min(len(date_tabs), MAX_DAYS)):
                    tab = date_tabs[day_index]
                    try:
                        tab.click()
                        time.sleep(2)
                        page.wait_for_load_state('networkidle', timeout=15000)
                        day_availability = self._extract_availability(page)
                        all_availability.extend(day_availability)
                        print(f"  Day {day_index + 1}: {len(day_availability)} slots")
                    except Exception as e:
                        print(f"  Day {day_index + 1} failed: {e}")
                        continue
                
                # Step 9: Store all days in database (once, like Linton)
                print(f"Storing {len(all_availability)} availability records...")
                self._store_availability(all_availability)
                
                print("Scraping completed successfully!")
                
            except Exception as e:
                print(f"Error during scraping: {e}")
                page.screenshot(path='debug_hill_roads_error.png')
                raise
            finally:
                browser.close()
                self.session.close()
    
    def _login(self, page):
        """Handle login process."""
        # Wait for login form
        page.wait_for_selector('input[type="email"], input[type="text"], input[type="password"]', timeout=30000)
        time.sleep(2)
        
        # Find and fill email
        email_selectors = [
            'input[type="email"]',
            'input[name*="email" i]',
            'input[id*="email" i]',
            'input[type="text"]'
        ]
        
        email_filled = False
        for selector in email_selectors:
            try:
                email_field = page.locator(selector).first
                email_field.fill(self.username, timeout=10000)
                email_filled = True
                print(f"Filled email using selector: {selector}")
                break
            except:
                continue
        
        if not email_filled:
            raise Exception("Could not find email input field")
        
        time.sleep(1)
        
        # Find and fill password
        password_field = page.locator('input[type="password"]').first
        password_field.fill(self.password)
        print("Filled password")
        
        time.sleep(1)
        
        # Submit
        submit_selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has-text("Login")',
            'button:has-text("Sign in")'
        ]
        
        submitted = False
        for selector in submit_selectors:
            try:
                submit_btn = page.locator(selector).first
                if submit_btn.is_visible():
                    submit_btn.click()
                    submitted = True
                    print(f"Clicked submit using selector: {selector}")
                    break
            except:
                continue
        
        if not submitted:
            page.keyboard.press('Enter')
            print("Pressed Enter to submit")
        
        time.sleep(5)  # Wait for login to complete
        
        # Verify we're logged in - check URL or page content
        print(f"After login, current URL: {page.url}")
        print(f"After login, page title: {page.title()}")
        
        # Wait for page to fully load after login
        page.wait_for_load_state('networkidle', timeout=30000)
        time.sleep(2)
    
    def _get_date_tabs(self, page):
        """Return a list of date tab locators (TODAY, TOMORROW, then date links) in display order."""
        tab_text_pattern = re.compile(
            r'^(TODAY|TOMORROW|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})$',
            re.I
        )
        tabs = []
        try:
            # Find tab container (often has role=tablist or class with tab/date)
            candidates = page.locator('[role="tab"], [class*="tab"], [class*="date"], a, button').filter(
                has_text=re.compile(r'TODAY|TOMORROW|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}', re.I)
            ).all()
            for el in candidates:
                if not el.is_visible(timeout=500):
                    continue
                text = el.inner_text().strip()
                if tab_text_pattern.match(text) or text.upper() in ('TODAY', 'TOMORROW'):
                    tabs.append(el)
            # Deduplicate by text (same tab might match multiple selectors) and keep order
            seen = set()
            unique = []
            for t in tabs:
                try:
                    key = t.inner_text().strip().upper()[:50]
                    if key not in seen:
                        seen.add(key)
                        unique.append(t)
                except Exception:
                    continue
            return unique[:10]  # cap at 10
        except Exception as e:
            print(f"Date tabs detection: {e}")
        return tabs

    def _get_viewing_date(self, page):
        """Parse the currently selected date from the timetable (TODAY / TOMORROW / date text)."""
        today = datetime.now().date()
        # Look for selected/highlighted date tab (TODAY, TOMORROW, or "07 FEB 2026")
        try:
            # Tab that is selected often has aria-selected or a class like "active"/"selected"
            selected = page.locator('[class*="active"]:has-text("TODAY"), [class*="active"]:has-text("TOMORROW"), [class*="selected"]:has-text("TODAY"), [class*="selected"]:has-text("TOMORROW")').first
            if selected.is_visible(timeout=2000):
                text = selected.inner_text().strip().upper()
                if 'TODAY' in text:
                    return today, today.strftime('%A')
                if 'TOMORROW' in text:
                    d = today + timedelta(days=1)
                    return d, d.strftime('%A')
            # Try to find a visible date like "07 FEB 2026" in the tab area (selected tab)
            date_links = page.locator('a, button, [role="tab"]').filter(has_text=re.compile(r'\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}', re.I)).all()
            for link in date_links[:5]:
                try:
                    t = link.inner_text().strip()
                    # Parse "07 FEB 2026" or "06 Feb 2026"
                    m = re.search(r'(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})', t, re.I)
                    if m:
                        day, mon_name, year = int(m.group(1)), m.group(2), int(m.group(3))
                        mon = {'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,'Jul':7,'Aug':8,'Sep':9,'Oct':10,'Nov':11,'Dec':12}[mon_name.capitalize()[:3]]
                        d = datetime(year, mon, day).date()
                        # Only use if this tab looks selected (e.g. has green/highlight) or is first date tab
                        if link.get_attribute('class') and ('active' in (link.get_attribute('class') or '') or 'selected' in (link.get_attribute('class') or '')):
                            return d, d.strftime('%A')
                except Exception:
                    continue
            # Fallback: check for text "TODAY" / "TOMORROW" in visible tabs
            for label in ['TODAY', 'TOMORROW']:
                el = page.get_by_text(label, exact=False).first
                if el.is_visible(timeout=1000):
                    # Check if it's in an active tab (parent has active class)
                    try:
                        parent = el.locator('xpath=ancestor::*[contains(@class, "active") or contains(@class, "selected")][1]')
                        if parent.count() > 0:
                            if 'TODAY' in label:
                                return today, today.strftime('%A')
                            if 'TOMORROW' in label:
                                d = today + timedelta(days=1)
                                return d, d.strftime('%A')
                    except Exception:
                        pass
        except Exception as e:
            print(f"Date detection warning: {e}")
        return today, today.strftime('%A')

    def _extract_availability(self, page):
        """Extract court availability from the div-based timetable (slot cards)."""
        availability = []
        today = datetime.now().date()

        print(f"Current page: {page.title()}, URL: {page.url}")

        # Resolve the date being viewed (TODAY / TOMORROW / specific date tab)
        viewing_date, day_name = self._get_viewing_date(page)
        date_str = viewing_date.strftime('%Y-%m-%d')
        print(f"Viewing date: {date_str} ({day_name})")

        # Find slot cards: div-based tiles that contain time (HH:MM) and either "Full" or "X Slots"
        card_selectors = [
            '[class*="slot"]',
            '[class*="Slot"]',
            '[class*="tile"]',
            '[class*="card"]',
            '[class*="booking"]',
            '[class*="time-slot"]',
        ]
        cards = []
        for selector in card_selectors:
            try:
                els = page.locator(selector).all()
                for el in els:
                    if not el.is_visible(timeout=500):
                        continue
                    text = el.inner_text()
                    # Must contain a time like 07:00 and either Full or N Slots
                    if re.search(r'\d{1,2}:\d{2}', text) and (re.search(r'\bFull\b', text, re.I) or re.search(r'\d+\s*Slots?', text, re.I)):
                        cards.append(el)
                if cards:
                    break
            except Exception as e:
                print(f"Selector {selector}: {e}")
                continue

        # Fallback: find any element that looks like a slot card (has time + Full or Slots)
        if not cards:
            try:
                # Get elements that contain both time and availability text; avoid huge containers
                candidates = page.locator('div').all()
                for el in candidates:
                    try:
                        if not el.is_visible(timeout=200):
                            continue
                        text = el.inner_text()
                        if len(text) > 500:  # Skip big containers
                            continue
                        if re.search(r'\d{1,2}:\d{2}', text) and (re.search(r'\bFull\b', text, re.I) or re.search(r'\d+\s*Slots?', text, re.I)):
                            if 'BADMINTON' in text.upper() or '60 MINUTES' in text:
                                cards.append(el)
                    except Exception:
                        continue
            except Exception as e:
                print(f"Fallback card search: {e}")

        # Deduplicate by time (same card might match multiple selectors)
        seen_times = set()
        unique_cards = []
        for card in cards:
            try:
                text = card.inner_text()
                m = re.search(r'(\d{1,2}):(\d{2})', text)
                if m:
                    t = f"{int(m.group(1)):02d}:{m.group(2)}"
                    if t not in seen_times:
                        seen_times.add(t)
                        unique_cards.append(card)
            except Exception:
                continue

        print(f"Found {len(unique_cards)} slot cards")

        for card in unique_cards:
            try:
                text = card.inner_text()
                # Time: first HH:MM
                time_m = re.search(r'(\d{1,2}):(\d{2})', text)
                if not time_m:
                    continue
                hour, minute = int(time_m.group(1)), int(time_m.group(2))
                start_time = f"{hour:02d}:{minute:02d}"
                if hour + 1 >= 24:
                    continue
                end_time = f"{hour + 1:02d}:{minute:02d}"

                # Availability: "Full" vs "N Slots"
                if re.search(r'\bFull\b', text, re.I):
                    is_available = False
                    num_slots = 0
                else:
                    slot_m = re.search(r'(\d+)\s*Slots?', text, re.I)
                    num_slots = int(slot_m.group(1)) if slot_m else 0
                    is_available = num_slots > 0

                if num_slots > 0:
                    for i in range(1, num_slots + 1):
                        availability.append({
                            'date': date_str,
                            'day_name': day_name,
                            'start_time': start_time,
                            'end_time': end_time,
                            'court_number': f'Court {i}',
                            'is_available': True,
                        })
                else:
                    availability.append({
                        'date': date_str,
                        'day_name': day_name,
                        'start_time': start_time,
                        'end_time': end_time,
                        'court_number': 'Court 1',
                        'is_available': False,
                    })
            except Exception as e:
                print(f"Error parsing card: {e}")
                continue

        print(f"Extracted {len(availability)} availability records")
        return availability
    
    def _store_availability(self, availability):
        """Store availability data in database."""
        # Clear old data for this facility
        self.session.query(CourtAvailability).filter_by(facility_id=self.facility.id).delete()
        
        for slot in availability:
            record = CourtAvailability(
                facility_id=self.facility.id,
                date=slot['date'],
                day_name=slot.get('day_name'),
                start_time=slot['start_time'],
                end_time=slot['end_time'],
                court_number=slot.get('court_number', 'Court 1'),
                is_available=slot['is_available'],
                scraped_at=datetime.utcnow()
            )
            self.session.add(record)
        
        self.session.commit()
        print(f"Stored {len(availability)} availability records")


if __name__ == "__main__":
    scraper = HillRoadsScraper(headless=False)
    try:
        scraper.scrape()
        print("Done.")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
