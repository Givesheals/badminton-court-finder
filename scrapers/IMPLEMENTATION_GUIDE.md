# Scraper implementation guide

This document summarises what we've learned building facility scrapers—especially from adding **Cherry Hinton Leisure Centre (Better.org)**—so the next scraper can reuse the same patterns and avoid the same pitfalls.

## Booking platforms: same products, different URLs

**Observation:** Facility booking URLs and branding differ, but the underlying tech often comes from a **small set of booking products**. If you recognise the platform, you can reuse patterns from an existing scraper for the same product.

| Platform / product | Venues in this project | Notes |
|--------------------|------------------------|--------|
| **Legend** (Legend Online Services) | Hill Roads, Trumpington Sport (Abbeycroft) | Same UI: login → Drop ins → club → Court bookings → Badminton → timetable. Red X = booked, green arrow / "N Slots" = bookable. |
| **GladstoneGo** (Gladstone Go) | One Leisure St Ives, One Leisure St Neots, One Leisure Huntingdon, One Leisure Ramsey, One Leisure Sawtry | SPA: /book, filters (Where / What / date / Starting from), "See available spaces" → timetable. "Book now" = available. All One Leisure venues share this platform and use a shared base scraper. |
| **Better.org** | Cherry Hinton Leisure Centre | No login. Location URL → activity list (e.g. "Badminton 60min") → day tabs → availability at bottom. Cookie consent on first load. |
| **Anglian Leisure** (gs-signature) | Linton Village College | Strong bot protection (403). Use sparingly; exclude from frequent scheduled scrapes. |

When adding a **new** facility, check whether its booking site is one of these (or another known product). If so, clone and adapt the corresponding scraper and doc below rather than starting from scratch.

---

## Architecture every scraper follows

1. **Base scraper** (`scrapers/<name>.py`): Playwright navigation only—goto URL, login if needed, open the right activity and date range, call `_extract_availability(page, expected_date=...)` per day, then `_store_availability(all_slots)` once. For GladstoneGo / One Leisure facilities, use `OneLeisureBaseScraper` in `scrapers/one_leisure_base.py` and provide a small `OneLeisureConfig` instead of duplicating navigation logic.
2. **Agent scraper** (`scrapers/<name>_agent_scraper.py`): Subclasses the base and overrides `_extract_availability` (or mixes in `OneLeisureAgentMixin` for GladstoneGo) to use `extract_availability_from_page(..., expected_date=expected_date)` from `llm_extract.py` (OpenAI). The app always uses the agent scraper.
3. **Registration**: Add the agent class to `scraper_manager.py` in `self.scrapers` with the exact facility name string (used by API and DB).
4. **Database**: No schema change. `_get_or_create_facility()` and `_store_availability()` (delete existing rows for that facility, then insert) are the same for all.

---

## Lessons from Cherry Hinton (Better.org)

### 1. Cookie / consent popups block navigation

The "Our cookies" (or similar) banner can sit over the page and **intercept clicks or prevent navigation**. If the scraper “clicks” an activity but stays on the same page, dismiss consent first.

- **Do:** Add a step early (e.g. after page load, before the main action) to accept or reject cookies.
- **Pattern:** Look for buttons by role and label, e.g. "Accept All Cookies", "Reject All", or a close control. Click once, short sleep, then continue.
- **Code:** See `_dismiss_cookie_consent()` in `cherry_hinton.py` and call it before clicking the activity link.

### 2. Match the exact label on the page

Sites often abbreviate (e.g. **"Badminton 60min"** not "Badminton 60 minutes"). If the scraper looks for the wrong string, the selector fails.

- **Do:** Use the **exact wording** you see in the UI (e.g. "Badminton 60min"). Prefer a small set of variants (regex) that include the real label.
- **Do:** Add a **JS fallback**: find an element whose text matches the intent (e.g. "Badminton" + "60" and not "40") and click it or its clickable parent. That survives minor copy changes.
- **Code:** See `_click_badminton_60()` in `cherry_hinton.py`: multiple selectors (role, text, regex) then `page.evaluate(...)` to find and click by text.

### 3. Wait for JS-rendered content

Activity lists and timetables are often loaded or updated by JavaScript. Selectors can run before the element exists.

- **Do:** After navigation (and after dismissing cookies), wait for a **stable element** that indicates the right view (e.g. text "Badminton" or "SPORTS HALL ACTIVITIES") before clicking.
- **Do:** After opening the timetable, add a short wait (e.g. 2–3 s) before looking for day tabs so the day view can render.
- **Code:** `page.get_by_text("Badminton", exact=False).first.wait_for(state="visible", timeout=15000)` then `_dismiss_cookie_consent()` then click; before the first day tab, `time.sleep(2)`.

### 4. Day tabs: structure varies

Sites use different markup for “choose a day” (tabs, buttons, list items, divs). A single selector (e.g. `role="tab"`) often isn’t enough.

- **Do:** Try several strategies: `get_by_role("tab")`, then locators for `button, a, [role='tab'], li` filtered by text matching a day pattern (e.g. `Mon 11`, `Tue 12`).
- **Do:** Add a **JS fallback**: walk the DOM for elements whose text looks like a day (e.g. day name + number), find the clickable container (`a`, `button`, `[role="tab"]`, `li`, or a class with "tab"/"day"),
  click the one at the desired index. See `_click_day_tab()` in `cherry_hinton.py`.
- **Do:** If the first day tab isn’t found, save a **screenshot** (e.g. `debug_<facility>_day_view.png`) so you can see the real layout and adjust selectors.

### 5. One day written to all days (date bug)

When scraping **day by day**, the timetable DOM often doesn’t show the date next to each slot. If you don’t pass the date into extraction, the LLM (or parser) may assign a single date to every slot.

- **Do:** For each day, pass **`expected_date=target_date`** into `_extract_availability(page, expected_date=target_date)`. The LLM prompt and normalisation in `llm_extract.py` then attach that date to every slot for that page.
- **Do:** Compute `target_date` from your loop (e.g. `today + timedelta(days=day_index)`); don’t rely on the page text for the date when storing.
- **Code:** See `cherry_hinton.py` day loop and `llm_extract.py` (`expected_date`, `date_instruction`, `date_str_override`). Same pattern in Trumpington and One Leisure agent scrapers.

### 6. Debug screenshots

When something fails (e.g. “no day tab found”), save a screenshot so you can see the actual page.

- **Do:** On first failure in a key step (e.g. first day tab), save a screenshot to a known path (e.g. `debug_cherry_hinton_day_view.png`). Add the path to `.gitignore` if it shouldn’t be committed.
- **Code:** In `cherry_hinton.py`, when `_click_day_tab` returns False for day_index 0, we save `debug_cherry_hinton_day_view.png` and log it.

---

## Checklist for adding a new scraper

1. **Identify the platform**  
   Open the facility’s booking URL. Check the domain and UI: Legend, GladstoneGo, Better.org, Anglian/gs-signature, or something new. If it matches an existing platform, start by copying that scraper.

2. **Base scraper (`scrapers/<facility>.py`)**  
   - Same structure: `__init__(headless)`, `_get_or_create_facility()`, `scrape()`, `_store_availability(availability)`.
   - Navigation: goto URL; **dismiss cookie/consent if present**; wait for key content; select activity (and duration if applicable); for each day, select day tab, call `_extract_availability(page, expected_date=target_date)`, append to list; call `_store_availability(all_availability)` once.
   - Use multiple selectors + JS fallback for critical clicks (activity, day tab) if the platform is JS-heavy or the label varies.
   - Stub `_extract_availability` to return `[]` in the base; the agent overrides it.

3. **Agent scraper (`scrapers/<facility>_agent_scraper.py`)**  
   - Subclass base; override `_extract_availability(self, page, expected_date=None)` to call `extract_availability_from_page(page, facility_name=..., expected_date=expected_date)`.

4. **Register**  
   - In `scraper_manager.py`: import the agent class, add `'<Facility Name>': AgentScraperClass` to `self.scrapers`. Use the **exact** display name (API and DB use it).

5. **Tests**  
   - At least: (a) scraper configured for the expected number of days (e.g. 5–7); (b) storing slots for two (or more) different dates results in that many distinct dates in the DB (avoids “one day for all” bug); (c) slot structure has required keys. Update `test_scraper_migration.py` (expected facility set, scrape-all count, API facilities).

6. **Run locally**  
   - Run the agent scraper once (e.g. `python3 -c "from scrapers.<x>_agent_scraper import ...; ..."`). If day tabs or activity click fail, check screenshots and adjust selectors/waits/cookie dismiss.

---

## File reference

| File | Purpose |
|------|--------|
| `scrapers/cherry_hinton.py` | Better.org example: cookie dismiss, 60min selectors + JS fallback, day-tab selectors + JS fallback, expected_date loop, debug screenshot. |
| `scrapers/llm_extract.py` | `extract_availability_from_page(page, facility_name, expected_date)` and `expected_date` handling. |
| `scrapers/trumpington_sport.py` | Legend (Abbeycroft) example: login, date tabs, `expected_date` per day. |
| `scrapers/one_leisure_base.py` | Shared GladstoneGo / One Leisure base scraper with configurable facility metadata. |
| `scrapers/one_leisure_st_ives.py` | One Leisure St Ives scraper built on `OneLeisureBaseScraper` with timetable date/slot parsing. |
| `scrapers/one_leisure_st_neots.py` | One Leisure St Neots scraper built on `OneLeisureBaseScraper`. |
| `scrapers/one_leisure_huntingdon.py` | One Leisure Huntingdon scraper built on `OneLeisureBaseScraper`. |
| `scrapers/one_leisure_ramsey.py` | One Leisure Ramsey scraper built on `OneLeisureBaseScraper`. |
| `scrapers/one_leisure_sawtry.py` | One Leisure Sawtry scraper built on `OneLeisureBaseScraper`. |
| `scraper_manager.py` | Where to register new scrapers and facility names. |
| `test_cherry_hinton.py` | Example tests: SCRAPE_DAYS range, distinct dates stored, slot structure, integration with _store_availability. |

---

## Summary

- **Reuse by platform:** Many venues share the same booking product (Legend, GladstoneGo, Better.org, etc.). Reuse the right scraper and adapt URL/labels.
- **Cookie consent:** Dismiss before main clicks so navigation isn’t blocked.
- **Exact labels + JS fallback:** Match the real UI text and add a JS click fallback for critical buttons/links.
- **Waits:** Wait for key content after load and after opening the timetable before scraping day tabs.
- **Day tabs:** Multiple selectors + JS fallback; save a screenshot when they’re not found.
- **Dates:** Always pass `expected_date` when extracting per day so one day’s data isn’t written to all days.
- **Tests:** Cover day count, distinct dates in DB, and slot shape; keep migration tests in sync with the facility list.
