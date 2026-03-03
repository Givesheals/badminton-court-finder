"""
Streamlit frontend for Badminton Court Finder.
Calls the existing Flask API (app.py) for facilities and availability.
"""
import os
import time

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
from datetime import datetime, timedelta
from typing import Optional

import requests
import streamlit as st

# API base URL: Streamlit Cloud Secrets panel, then env (e.g. .env), then default production (Render)
_DEFAULT_API_BASE = "https://badminton-court-finder.onrender.com"
try:
    _from_secrets = st.secrets["API_BASE_URL"]
except Exception:
    # KeyError, TypeError, StreamlitSecretNotFoundError, TomlDecodeError (e.g. malformed secrets.toml)
    _from_secrets = None
API_BASE = (_from_secrets or os.getenv("API_BASE_URL") or _DEFAULT_API_BASE).strip() or _DEFAULT_API_BASE

# Booking URLs per facility (match index.html; add new facilities here)
FACILITY_BOOKING_URLS = {
    "Linton Village College": "https://clubspark.lta.org.uk/LintonVillageCampus/Booking/BookByDate",
    "One Leisure St Ives": "https://oneleisure.gladstonego.cloud/book",
    "Hill Roads Sport and Tennis Centre": "https://legendclub.co.uk/",
    "Trumpington Sport": "https://legendclub.co.uk/",
}

# Retries for cold start (e.g. Render free tier)
MAX_RETRIES = 12
RETRY_INTERVAL_SEC = 10


def get_facilities(api_base: Optional[str] = None):
    """Fetch facility list and last_updated from API. Retries on failure (e.g. Render cold start)."""
    base = (api_base or API_BASE).rstrip("/")
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = requests.get(f"{base}/api/facilities", timeout=15)
            if r.status_code != 200:
                raise RuntimeError(f"API returned {r.status_code}")
            ct = r.headers.get("Content-Type") or ""
            if "application/json" not in ct:
                raise RuntimeError("API returned non-JSON (may be starting up)")
            data = r.json()
            return (
                data.get("facilities") or [],
                data.get("last_updated") or {},
            )
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_INTERVAL_SEC)
    raise RuntimeError(
        f"Could not reach API after {MAX_RETRIES} tries. {last_error}"
    ) from last_error


def get_availability(
    facility: str, date: str, start_time: str, end_time: str, api_base: Optional[str] = None
):
    """Fetch availability for one facility and one date."""
    base = (api_base or API_BASE).rstrip("/")
    try:
        r = requests.get(
            f"{base}/api/availability",
            params={
                "facility": facility,
                "date": date,
                "start_time": start_time,
                "end_time": end_time,
            },
            timeout=15,
        )
        if r.status_code != 200:
            return []
        data = r.json()
        return data.get("data") or []
    except Exception:
        return []


def duration_hours(start_time: str, end_time: str) -> float:
    """Duration in hours between start_time and end_time (e.g. '18:00', '20:00')."""
    sh, sm = map(int, start_time.split(":")[:2])
    eh, em = map(int, end_time.split(":")[:2])
    return (eh * 60 + em - sh * 60 - sm) / 60.0


def find_continuous_blocks(slots, required_duration_hours: float, num_courts: int):
    """
    Group slots by court, find continuous blocks >= required_duration_hours.
    Returns list of dicts: court, start_time, end_time, duration.
    """
    from collections import defaultdict

    by_court = defaultdict(list)
    for slot in slots:
        court = slot.get("court_number") or "Unknown"
        by_court[court].append(slot)

    result = []
    for court, court_slots in by_court.items():
        court_slots.sort(key=lambda s: (s.get("start_time") or "", s.get("end_time") or ""))
        i = 0
        while i < len(court_slots):
            block = [court_slots[i]]
            start = block[0].get("start_time") or ""
            end = block[0].get("end_time") or ""
            total_dur = duration_hours(start, end)
            j = i + 1
            while j < len(court_slots):
                next_slot = court_slots[j]
                next_start = next_slot.get("start_time") or ""
                if next_start != end:
                    break
                block.append(next_slot)
                end = next_slot.get("end_time") or ""
                total_dur = duration_hours(block[0].get("start_time") or "", end)
                j += 1
            if total_dur >= required_duration_hours:
                result.append({
                    "court": court,
                    "start_time": block[0].get("start_time"),
                    "end_time": end,
                    "duration": round(total_dur, 1),
                })
            i = j
    return result


def format_last_updated(iso_string: Optional[str]) -> str:
    if not iso_string:
        return "never"
    try:
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        return dt.strftime("%d %b %Y, %H:%M")
    except Exception:
        return iso_string or "never"


def run_search(
    selected_dates, start_time, end_time, duration_h, num_courts, api_base: Optional[str] = None
):
    """Call API for each facility and each date; return results and last_updated."""
    base = (api_base or API_BASE).rstrip("/")
    facilities, last_updated = get_facilities(base)
    if not facilities:
        return {}, last_updated

    results = {}
    for facility in facilities:
        results[facility] = {}
        for date in selected_dates:
            slots = get_availability(facility, date, start_time, end_time, base)
            if not slots:
                continue
            blocks = find_continuous_blocks(slots, duration_h, num_courts)
            if blocks:
                results[facility][date] = blocks

    return results, last_updated


def main():
    st.set_page_config(
        page_title="Badminton Court Finder",
        page_icon="🏸",
        layout="centered",
    )

    st.title("🏸 Badminton Court Finder")
    st.caption("Find available courts across Cambridge facilities")

    # API URL (optional override for dev/production)
    with st.expander("Settings", expanded=False):
        api_url = st.text_input(
            "Backend API URL",
            value=API_BASE,
            help="URL of the Flask backend (e.g. http://localhost:5000 or your Render URL)",
        )
    use_api_base = api_url.strip() or API_BASE

    # Day selector: next 14 days, multi-select
    st.subheader("Select days you're available")
    today = datetime.now().date()
    days_options = [(today + timedelta(days=i)) for i in range(14)]
    day_labels = {
        d: d.strftime("%a %d %b") for d in days_options
    }
    selected_dates = st.multiselect(
        "Days",
        options=days_options,
        format_func=lambda d: day_labels[d],
        default=[today, today + timedelta(days=1)] if len(days_options) >= 2 else days_options[:1],
        key="days",
    )
    selected_dates_str = [d.isoformat() for d in selected_dates]

    # Time range
    col1, col2 = st.columns(2)
    with col1:
        start_time = st.time_input("Start time", value=datetime.strptime("18:00", "%H:%M").time()).strftime("%H:%M")
    with col2:
        end_time = st.time_input("End time", value=datetime.strptime("22:00", "%H:%M").time()).strftime("%H:%M")

    # Duration and number of courts
    col3, col4 = st.columns(2)
    with col3:
        duration_h = st.selectbox(
            "Minimum block (hours)",
            options=[1.0, 1.5, 2.0, 2.5, 3.0],
            index=2,
            format_func=lambda x: f"{x} hour{'s' if x != 1 else ''}",
        )
    with col4:
        num_courts = st.selectbox("Number of courts", options=[1, 2, 3, 4], index=0)

    if st.button("Find Available Courts", type="primary"):
        if not selected_dates_str:
            st.warning("Please select at least one day.")
        else:
            with st.spinner("Searching for available courts…"):
                try:
                    results, last_updated = run_search(
                        selected_dates_str,
                        start_time,
                        end_time,
                        duration_h,
                        num_courts,
                        api_base=use_api_base,
                    )
                except Exception as e:
                    st.error(f"Could not reach the API. On the free tier it may be starting up — try again in a minute.\n\nError: {e}")
                    st.stop()

            facilities_with = [(f, d) for f, d in results.items() if d]
            facilities_without = [(f, d) for f, d in results.items() if not d]

            if not facilities_with and not facilities_without:
                st.info("No facilities returned from the API. Check that the backend is running and has scraped data.")

            if facilities_with:
                st.subheader(f"Available courts ({len(facilities_with)} {'facility' if len(facilities_with) == 1 else 'facilities'})")
                for facility, dates in facilities_with:
                    last_str = format_last_updated(last_updated.get(facility))
                    book_url = FACILITY_BOOKING_URLS.get(facility) or "#"
                    st.markdown(f"**{facility}** — last updated: {last_str}")
                    if book_url != "#":
                        st.markdown(f"[Book now →]({book_url})")
                    for date_str, blocks in sorted(dates.items()):
                        date_obj = datetime.fromisoformat(date_str).date()
                        st.markdown(f"_{date_obj.strftime('%A %d %B %Y')}_")
                        for b in blocks:
                            st.caption(f"  {b['court']} | {b['start_time']}–{b['end_time']} ({b['duration']}h)")
                    st.divider()

            if facilities_without:
                st.subheader("No availability for selected days")
                for facility, _ in facilities_without:
                    last_str = format_last_updated(last_updated.get(facility))
                    book_url = FACILITY_BOOKING_URLS.get(facility) or "#"
                    st.markdown(f"**{facility}** — last updated: {last_str}")
                    if book_url != "#":
                        st.markdown(f"[Book now →]({book_url})")
                    st.caption("No slots match your criteria. Run a scrape to refresh data or try other days.")
                    st.divider()

    # Scrape now (optional)
    st.divider()
    if st.button("Scrape all facilities (refresh data)"):
        try:
            # Longer timeout so a cold backend (e.g. Render) can wake up and respond
            r = requests.post(f"{use_api_base}/api/scrape-all", timeout=60)
            if r.status_code in (200, 202):
                data = r.json()
                if data.get("status") == "no_facilities":
                    st.warning("No facilities to scrape (all excluded or none configured).")
                else:
                    facilities = data.get("facilities", [])
                    excluded = data.get("excluded", [])
                    st.success(
                        data.get("message", "Scrapes started in background.") + " "
                        + (", ".join(facilities) if facilities else "No facilities to scrape.")
                    )
                    if excluded:
                        st.caption(f"Excluded (not scraped): {', '.join(excluded)}")
                    st.info(
                        "Scrapes run in the background and can take several minutes (each venue is scraped in turn). "
                        "Click **Find Available Courts** again in 5–10 minutes to see updated data."
                    )
            else:
                st.warning(f"API returned {r.status_code}. Check backend logs.")
        except requests.exceptions.Timeout:
            st.error("Request timed out. If the backend is on a free tier (e.g. Render), it may be starting up — try again in a minute.")
        except Exception as e:
            st.error(f"Could not trigger scrape: {e}")


if __name__ == "__main__":
    main()
