"""Scraper for One Leisure Ramsey badminton court availability."""

import re
import time
from datetime import datetime, timedelta

from scrapers.one_leisure_base import (
    OneLeisureBaseScraper,
    OneLeisureConfig,
    BOOKING_WINDOW_DAYS,
)

MONTH_NAMES = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


class OneLeisureRamseyScraper(OneLeisureBaseScraper):
    """Ramsey-specific GladstoneGo scraper using the shared OneLeisureBaseScraper."""

    CONFIG = OneLeisureConfig(
        facility_name="One Leisure Ramsey",
        where_value="One Leisure Ramsey",
        where_fallbacks=["Ramsey"],
    )

    def _extract_availability_from_timetable(self, page):
        """Extract slots from the timetable grid for the 14-day booking window only."""
        today = datetime.now().date()
        dates_to_scrape = [today + timedelta(days=i) for i in range(BOOKING_WINDOW_DAYS)]
        all_slots = []

        for target_date in dates_to_scrape:
            date_str = target_date.strftime("%Y-%m-%d")
            day_name = target_date.strftime("%A")
            day_num = target_date.day
            month_abbr = target_date.strftime("%b").lower()

            if not self._select_timetable_date(page, target_date, day_num, month_abbr):
                print(f"  Could not select date {date_str}, skipping.")
                continue
            time.sleep(1)
            page.wait_for_load_state("networkidle", timeout=10000)

            self._scroll_timetable_grid(page)
            time.sleep(0.5)

            day_slots = self._parse_timetable_cards_for_date(
                page, date_str, day_name, target_date=target_date
            )
            all_slots.extend(day_slots)
            print(
                f"  {date_str}: {len(day_slots)} slots "
                f"({sum(1 for s in day_slots if s['is_available'])} available)"
            )

        return all_slots

    def _select_timetable_date(self, page, target_date, day_num, month_abbr):
        """Click the calendar day cell for the given date."""
        day_pattern = re.compile(rf"(?:MON|TUE|WED|THU|FRI|SAT|SUN)\s+{day_num}\b", re.I)
        try:
            day_cell = page.locator(
                "[class*='calendar'], [class*='date'], [class*='day'], button, a"
            ).filter(has_text=day_pattern).first
            if day_cell.is_visible(timeout=3000):
                day_cell.click()
                time.sleep(1.5)
                return True
        except Exception:
            pass
        try:
            day_cell = page.get_by_text(re.compile(rf"^{day_num}$"), exact=False).first
            if day_cell.is_visible(timeout=2000):
                day_cell.click()
                time.sleep(1.5)
                return True
        except Exception:
            pass
        return False

    def _scroll_timetable_grid(self, page):
        """Scroll down to load all time slots and right to load all courts."""
        try:
            for _ in range(4):
                page.mouse.wheel(0, 400)
                time.sleep(0.2)
            for _ in range(4):
                page.mouse.wheel(0, -400)
                time.sleep(0.2)
            page.mouse.wheel(300, 0)
            time.sleep(0.3)
            page.mouse.wheel(-300, 0)
            time.sleep(0.2)
        except Exception:
            pass

    def _parse_date_from_card_text(self, text, target_date=None):
        """Parse 'Thu 5th Feb' or '5th Feb' from card text; return (date_str, day_name) or (None, None)."""
        year = target_date.year if target_date else datetime.now().year
        m = re.search(
            r"(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+(\d+)(?:st|nd|rd|th)?\s+"
            r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b",
            text,
            re.I,
        )
        if not m:
            m = re.search(
                r"\b(\d+)(?:st|nd|rd|th)?\s+"
                r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b",
                text,
                re.I,
            )
        if m:
            day_num = int(m.group(1))
            month_abbr = m.group(2).lower()[:3]
            month = MONTH_NAMES.get(month_abbr)
            if month:
                if month == 1 and target_date and target_date.month == 12:
                    year = target_date.year + 1
                try:
                    d = datetime(year, month, day_num).date()
                    return d.strftime("%Y-%m-%d"), d.strftime("%A")
                except ValueError:
                    pass
        return None, None

    def _parse_timetable_cards_for_date(self, page, date_str, day_name, target_date=None):
        """Find all slot cards in the grid and parse court, time, availability."""
        slots = []

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
            try:
                candidates = page.locator("div, article, section").filter(
                    has_text=re.compile(
                        r"Court\s+\d+.*\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}", re.S
                    )
                ).all()
                for el in candidates:
                    try:
                        t = el.inner_text()
                        if len(t) > 500:
                            continue
                        if re.search(r"Court\s+\d+", t, re.I) and re.search(
                            r"\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}", t
                        ):
                            cards.append(el)
                    except Exception:
                        continue
            except Exception:
                pass

        seen = set()
        for card in cards:
            try:
                text = card.inner_text()
                slot_date_str, slot_day_name = self._parse_date_from_card_text(
                    text, target_date=target_date
                )
                if slot_date_str is None:
                    slot_date_str, slot_day_name = date_str, day_name

                court_m = re.search(r"Court\s+(\d+)", text, re.I)
                if not court_m:
                    continue
                court_num = court_m.group(1)
                court_label = f"Court {court_num}"

                time_m = re.search(r"(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})", text)
                if not time_m:
                    continue
                start_time = f"{int(time_m.group(1)):02d}:{time_m.group(2)}"
                end_time = f"{int(time_m.group(3)):02d}:{time_m.group(4)}"

                key = (slot_date_str, court_label, start_time)
                if key in seen:
                    continue
                seen.add(key)

                has_bookable = bool(
                    re.search(r"Book\s+now|Book\b|Available", text, re.I)
                    and not re.search(r"available to be booked on", text, re.I)
                )
                has_unavailable = bool(
                    re.search(r"unavailable|available to be booked on|This slot is", text, re.I)
                )
                is_available = has_bookable or (not has_unavailable)
                slots.append(
                    {
                        "date": slot_date_str,
                        "day_name": slot_day_name,
                        "start_time": start_time,
                        "end_time": end_time,
                        "court_number": court_label,
                        "is_available": is_available,
                    }
                )
            except Exception:
                continue
        return slots

