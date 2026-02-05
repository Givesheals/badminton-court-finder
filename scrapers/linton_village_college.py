"""Scraper for Linton Village College badminton court availability."""
import os
import time
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from dotenv import load_dotenv
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import init_db, get_session, Facility, CourtAvailability

load_dotenv()


class LintonVillageCollegeScraper:
    """Scraper for Linton Village College badminton courts."""
    
    BASE_URL = "https://lvc.org/sportscentre/badminton-hire/"
    LOGIN_URL = None  # Will be determined from the "Book now" link
    
    def __init__(self, headless=True):
        self.headless = headless if headless is not None else True
        self.username = os.getenv('LVC_USERNAME', 'theparker1337@gmail.com')
        self.password = os.getenv('LVC_PASSWORD', 'CourtFinder123!')
        self.db_engine = init_db()
        self.session = get_session(self.db_engine)
        
        # Ensure facility exists in database
        self.facility = self._get_or_create_facility()
    
    def _get_or_create_facility(self):
        """Get or create the Linton Village College facility record."""
        facility = self.session.query(Facility).filter_by(name='Linton Village College').first()
        if not facility:
            facility = Facility(name='Linton Village College')
            self.session.add(facility)
            self.session.commit()
        return facility
    
    def scrape(self):
        """Main scraping method."""
        print("Starting Linton Village College scraper...")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.headless,
                args=['--disable-blink-features=AutomationControlled']
            )
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                locale='en-GB',
                timezone_id='Europe/London'
            )
            # Hide webdriver flag
            page = context.new_page()
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            try:
                # Step 1: Navigate to badminton hire page
                print(f"Navigating to {self.BASE_URL}...")
                page.goto(self.BASE_URL, wait_until='networkidle')
                time.sleep(2)  # Give page time to load
                
                # Step 2: Find and click "Book now" button
                print("Looking for 'Book now' button...")
                try:
                    # Try to find the book now button/link
                    book_now = page.locator('text=Book now').first
                    if book_now.is_visible():
                        print("Clicking 'Book now' button...")
                        book_now.click()
                        print("Waiting for navigation to login page...")
                        page.wait_for_load_state('networkidle', timeout=30000)
                        time.sleep(2)
                        print(f"Current URL: {page.url}")
                    else:
                        # Try alternative selectors
                        book_now = page.locator('a:has-text("Book now")').first
                        if book_now.is_visible():
                            print("Clicking 'Book now' link...")
                            book_now.click()
                            print("Waiting for navigation to login page...")
                            page.wait_for_load_state('networkidle', timeout=30000)
                            time.sleep(2)
                            print(f"Current URL: {page.url}")
                        else:
                            raise Exception("Could not find 'Book now' button")
                except Exception as e:
                    print(f"Error finding book now button: {e}")
                    # Take screenshot for debugging
                    page.screenshot(path='debug_book_now.png')
                    raise
                
                # Step 3: Login
                print("Attempting to log in...")
                print(f"Current URL after Book now: {page.url}")
                try:
                    # Wait for page to fully load first
                    print("Waiting for page to fully load...")
                    page.wait_for_load_state('networkidle', timeout=30000)
                    time.sleep(2)  # Give JavaScript time to render
                    
                    # Wait for ANY input field (more lenient than specific placeholder)
                    print("Waiting for login form inputs...")
                    page.wait_for_selector('input[type="text"], input[type="email"], input[placeholder*="Email"]', timeout=30000)
                    print(f"Login form found! Current URL: {page.url}")
                    
                    # Find username/email field (try placeholder first for anglianleisure form)
                    email_selectors = [
                        'input[placeholder*="Email"]',
                        'input[type="email"]',
                        'input[name="email"]',
                        'input[id*="email"]',
                        'input[type="text"]:visible'
                    ]
                    
                    email_filled = False
                    for selector in email_selectors:
                        try:
                            email_field = page.locator(selector).first
                            if email_field.is_visible():
                                email_field.fill(self.username)
                                email_filled = True
                                print(f"Filled email using selector: {selector}")
                                break
                        except:
                            continue
                    
                    if not email_filled:
                        raise Exception("Could not find email input field")
                    
                    time.sleep(1)
                    
                    # Find password field
                    password_selectors = [
                        'input[type="password"]',
                        'input[name="password"]',
                        'input[id*="password"]'
                    ]
                    
                    password_filled = False
                    for selector in password_selectors:
                        try:
                            password_field = page.locator(selector).first
                            if password_field.is_visible():
                                password_field.fill(self.password)
                                password_filled = True
                                print(f"Filled password using selector: {selector}")
                                break
                        except:
                            continue
                    
                    if not password_filled:
                        raise Exception("Could not find password input field")
                    
                    time.sleep(1)
                    
                    # Submit login form
                    submit_selectors = [
                        'button[type="submit"]',
                        'input[type="submit"]',
                        'button:has-text("Login")',
                        'button:has-text("Sign in")',
                        'button:has-text("Log in")'
                    ]
                    
                    submitted = False
                    for selector in submit_selectors:
                        try:
                            submit_button = page.locator(selector).first
                            if submit_button.is_visible():
                                submit_button.click()
                                submitted = True
                                print(f"Clicked submit using selector: {selector}")
                                break
                        except:
                            continue
                    
                    if not submitted:
                        # Try pressing Enter
                        page.keyboard.press('Enter')
                        print("Pressed Enter to submit")
                    
                    time.sleep(5)  # Wait for login to complete
                    
                except Exception as e:
                    print(f"Error during login: {e}")
                    page.screenshot(path='debug_login.png')
                    raise
                
                # Step 4: Navigate to badminton booking (New Gym)
                print("Looking for badminton booking interface...")
                try:
                    time.sleep(2)  # Wait for page to fully load
                    
                    # First, check what activity is currently selected
                    # Look for the activity name in the page
                    activity_text = page.locator('h3').filter(has_text='Badminton').first
                    if activity_text.is_visible():
                        current_activity = activity_text.inner_text().strip()
                        print(f"Current activity shown: {current_activity}")
                    
                    # Look for activity selection buttons/links
                    # We need to find and click on "badminton" specifically
                    # The interface might show multiple activities, we need badminton
                    badminton_selectors = [
                        'a:has-text("badminton"):not(:has-text("basketball"))',
                        'button:has-text("badminton"):not(:has-text("basketball"))',
                        'a:has-text("Badminton"):not(:has-text("Basketball"))',
                        'button:has-text("Badminton"):not(:has-text("Basketball"))',
                        '[data-qa-id*="badminton"]',
                        'a[href*="badminton"]',
                    ]
                    
                    badminton_clicked = False
                    for selector in badminton_selectors:
                        try:
                            elements = page.locator(selector).all()
                            for element in elements:
                                if element.is_visible():
                                    text = element.inner_text().lower()
                                    # Make sure it's badminton, not basketball
                                    if 'badminton' in text and 'basketball' not in text:
                                        element.click()
                                        badminton_clicked = True
                                        print(f"Clicked badminton using selector: {selector}")
                                        time.sleep(3)  # Wait for page to update
                                        break
                            if badminton_clicked:
                                break
                        except Exception as e:
                            print(f"Tried selector {selector}: {e}")
                            continue
                    
                    # Verify we're on the right activity
                    time.sleep(2)
                    page.screenshot(path='debug_after_activity_selection.png')
                    activity_check = page.locator('h3').first
                    if activity_check.is_visible():
                        activity_name = activity_check.inner_text().strip()
                        print(f"Activity after selection: {activity_name}")
                        if 'basketball' in activity_name.lower():
                            print("WARNING: Still showing basketball! Trying to find badminton more specifically...")
                            # Try to find a list of activities and click badminton
                            all_links = page.locator('a').all()
                            for link in all_links:
                                try:
                                    text = link.inner_text().lower()
                                    if 'badminton' in text and 'basketball' not in text:
                                        link.click()
                                        print(f"Clicked badminton link: {text}")
                                        time.sleep(3)
                                        break
                                except:
                                    continue
                    
                    if not badminton_clicked:
                        print("Could not find badminton button. Screenshot saved to debug_badminton_search.png")
                        page.screenshot(path='debug_badminton_search.png')
                    
                except Exception as e:
                    print(f"Error finding badminton interface: {e}")
                    page.screenshot(path='debug_badminton_error.png')
                
                # Step 5: Verify we're on the right activity and extract availability data
                print("Verifying activity selection...")
                time.sleep(2)
                
                # Double-check we're viewing badminton, not basketball
                activity_heading = page.locator('h3').first
                if activity_heading.is_visible():
                    activity_name = activity_heading.inner_text().strip()
                    print(f"Current activity: {activity_name}")
                    if 'basketball' in activity_name.lower() and 'badminton' not in activity_name.lower():
                        raise Exception(f"Wrong activity selected! Currently showing: {activity_name}. Expected Badminton.")
                    elif 'badminton' in activity_name.lower():
                        print("✓ Confirmed: Badminton is selected")
                
                print("Extracting availability data...")
                time.sleep(2)  # Wait for calendar/availability to load
                
                availability_data = self._extract_availability(page)
                
                # Step 6: Store in database
                print(f"Storing {len(availability_data)} availability records...")
                self._store_availability(availability_data)
                
                # Update facility last_scraped_at
                from datetime import datetime
                self.facility.last_scraped_at = datetime.utcnow()
                self.session.commit()
                
                print("Scraping completed successfully!")
                
            except Exception as e:
                print(f"Error during scraping: {e}")
                page.screenshot(path='debug_error.png')
                raise
            finally:
                browser.close()
                self.session.close()
    
    def _extract_availability(self, page):
        """Extract court availability from the current page."""
        availability = []
        
        try:
            # Wait for the availability table to load
            page.wait_for_selector('#slotsGrid', timeout=60000)
            
            # Get the table
            table = page.locator('#slotsGrid')
            
            # Extract day headers (skip first column which is time)
            day_headers = []
            header_cells = table.locator('th.mastertableheader').all()
            for i, header in enumerate(header_cells):
                if i == 0:  # Skip first column (time header)
                    continue
                day_text = header.locator('.availabilityday').inner_text()
                day_headers.append(day_text.strip())
            
            print(f"Found {len(day_headers)} days: {day_headers}")
            
            # Extract time slots and availability
            rows = table.locator('tbody tr').all()
            
            for row in rows:
                # Get time from first cell
                time_cell = row.locator('td.masterTableLeftHeader').first
                if not time_cell.is_visible():
                    continue
                
                time_text = time_cell.inner_text().strip()
                if not time_text:
                    continue
                
                # Parse time (format: "HH:MM")
                start_time = time_text
                # Calculate end time (30 minutes later for 30-min slots)
                try:
                    hour, minute = map(int, start_time.split(':'))
                    end_hour = hour
                    end_minute = minute + 30
                    if end_minute >= 60:
                        end_hour += 1
                        end_minute -= 60
                    end_time = f"{end_hour:02d}:{end_minute:02d}"
                except:
                    end_time = start_time  # Fallback
                
                # Get availability cells (skip first column which is time)
                cells = row.locator('td').all()
                
                for i, cell in enumerate(cells[1:], start=0):  # Skip first cell (time)
                    if i >= len(day_headers):
                        break
                    
                    # Check if cell has availability button (including disabled ones)
                    button = cell.locator('input[type="submit"]').first
                    button_count = cell.locator('input[type="submit"]').count()
                    if button_count == 0:
                        continue
                    
                    # Get availability status based on button class (color)
                    # Green (btn-resource-success) = Available
                    # White (btn-resource-default) = Not Available
                    # Orange (btn-resource-warning) = My booking (not available to others)
                    button_class = button.get_attribute('class') or ''
                    cell_class = cell.get_attribute('class') or ''
                    
                    # Check button class first, then cell class
                    if 'btn-resource-success' in button_class:
                        # Green button = Available
                        is_available = True
                    elif 'btn-resource-warning' in button_class:
                        # Orange button = My booking (not available)
                        is_available = False
                    elif 'btn-resource-default' in button_class or 'itemnotavailable' in cell_class:
                        # White/default button = Not Available
                        is_available = False
                    elif 'itemavailable' in cell_class:
                        # Cell marked as available
                        is_available = True
                    else:
                        # Default to not available if unclear
                        is_available = False
                    
                    # Get date from data-qa-id attribute
                    data_qa_id = button.get_attribute('data-qa-id') or ''
                    date_str = None
                    if 'Date=' in data_qa_id:
                        # Extract date from format: "Date=04/02/2026 18:00:00"
                        date_part = data_qa_id.split('Date=')[1].split(' ')[0]
                        # Convert from DD/MM/YYYY to YYYY-MM-DD
                        try:
                            day, month, year = date_part.split('/')
                            date_str = f"{year}-{month}-{day}"
                        except:
                            pass
                    
                    # If no date from data attribute, try to parse from day header
                    if not date_str and i < len(day_headers):
                        day_header = day_headers[i]
                        # Format: "Wed 04 Feb" - need to get current year
                        try:
                            # Parse day header (e.g., "Wed 04 Feb")
                            parts = day_header.split()
                            if len(parts) >= 3:
                                day_num = parts[1]
                                month_name = parts[2]
                                current_year = datetime.now().year
                                # Convert month name to number
                                month_map = {
                                    'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                                    'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
                                    'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
                                }
                                month_num = month_map.get(month_name, '01')
                                date_str = f"{current_year}-{month_num}-{day_num.zfill(2)}"
                        except Exception as e:
                            print(f"Error parsing date from header: {e}")
                    
                    # Get day name
                    day_name = None
                    if i < len(day_headers):
                        day_header = day_headers[i]
                        day_name = day_header.split()[0]  # First word is day name
                    
                    if date_str:
                        availability.append({
                            'court_number': None,  # Single court for this facility
                            'date': date_str,
                            'day_name': day_name,
                            'start_time': start_time,
                            'end_time': end_time,
                            'is_available': is_available
                        })
            
            print(f"Extracted {len(availability)} time slots")
            
        except Exception as e:
            print(f"Error extracting availability: {e}")
            import traceback
            traceback.print_exc()
        
        return availability
    
    def _store_availability(self, availability_data):
        """Store availability data in the database."""
        # Clear old data for this facility (optional - you might want to keep history)
        # self.session.query(CourtAvailability).filter_by(facility_id=self.facility.id).delete()
        
        for record in availability_data:
            availability = CourtAvailability(
                facility_id=self.facility.id,
                court_number=record.get('court_number'),
                date=record.get('date'),
                day_name=record.get('day_name'),
                start_time=record.get('start_time'),
                end_time=record.get('end_time'),
                is_available=record.get('is_available', True),
                scraped_at=datetime.utcnow()
            )
            self.session.add(availability)
        
        self.session.commit()
        print(f"Stored {len(availability_data)} availability records")


def main():
    """Main entry point for the scraper."""
    scraper = LintonVillageCollegeScraper(headless=False)  # Set to False to see browser
    scraper.scrape()


if __name__ == '__main__':
    main()
