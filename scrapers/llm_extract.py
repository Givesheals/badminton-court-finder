"""
LLM-based extraction of court availability from page content.
Used by the agent scraper when selectors break or for resilience to layout changes.
Requires OPENAI_API_KEY in the environment.
"""
import json
import os
import re
import logging
from datetime import date as date_type
from typing import Any, List, Optional

logger = logging.getLogger(__name__)

EXTRACTION_SYSTEM = """You are a parser for sports facility booking pages. Extract badminton court availability from the page content.

Return ONLY a valid JSON array of objects. Each object must have exactly these keys (use null for missing values):
- date: string YYYY-MM-DD
- court_number: string (e.g. "Court 1" or null if single court)
- start_time: string HH:MM (24-hour)
- end_time: string HH:MM (24-hour)
- is_available: boolean (true only if the slot can be booked)

Include only slots that are available (is_available true). If the page shows a grid: columns are often days, rows are times. Infer dates from day names and the current context. Return [] if no availability or content is unclear."""


def extract_availability_with_llm(
    page_content: str,
    facility_name: str = "facility",
    model: str = "gpt-4o-mini",
    expected_date: Optional[date_type] = None,
) -> List[dict]:
    """
    Send page content to OpenAI and parse returned JSON into slot records.
    page_content: inner text or HTML snippet of the availability area.
    expected_date: if set, all slots are for this date (YYYY-MM-DD). Use for every slot in the response.
    Returns list of dicts with date, court_number, start_time, end_time, is_available.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Set it in .env to use agent/LLM extraction."
        )

    try:
        from openai import OpenAI
    except ImportError:
        raise RuntimeError(
            "Install the openai package: pip install openai"
        )

    client = OpenAI(api_key=api_key)
    date_instruction = ""
    if expected_date is not None:
        date_str = expected_date.strftime("%Y-%m-%d")
        date_instruction = (
            f"The slots on this page are for date {date_str}. "
            "Use this date for every slot in your response.\n\n"
        )
    user_content = (
        f"Facility: {facility_name}\n\n"
        f"{date_instruction}"
        "Extract all bookable badminton court slots from this page content.\n\n"
        "Page content:\n"
        "---\n"
        f"{page_content[:120000]}\n"
        "---\n\n"
        "Reply with ONLY the JSON array, no other text."
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": EXTRACTION_SYSTEM},
            {"role": "user", "content": user_content},
        ],
        temperature=0.1,
    )
    text = (response.choices[0].message.content or "").strip()

    # Try to find a JSON array in the response (in case model added markdown or extra text)
    array_match = re.search(r"\[\s*\{.*\}\s*\]", text, re.DOTALL)
    if array_match:
        text = array_match.group(0)
    try:
        slots = json.loads(text)
    except json.JSONDecodeError as e:
        logger.warning("LLM extraction returned invalid JSON: %s", e)
        return []

    if not isinstance(slots, list):
        return []

    # Normalize to our schema; when expected_date is set, use it for every slot
    date_str_override = expected_date.strftime("%Y-%m-%d") if expected_date is not None else None
    result = []
    for s in slots:
        if not isinstance(s, dict):
            continue
        date = date_str_override or s.get("date")
        start = s.get("start_time")
        end = s.get("end_time")
        if not date or not start:
            continue
        result.append({
            "date": str(date),
            "court_number": s.get("court_number") if s.get("court_number") else None,
            "day_name": None,
            "start_time": str(start),
            "end_time": str(end) if end else start,
            "is_available": s.get("is_available", True),
        })
    return result


def extract_availability_from_page(
    page: Any,
    facility_name: str = "facility",
    expected_date: Optional[date_type] = None,
) -> List[dict]:
    """
    Get availability from a Playwright page using LLM extraction.
    page: Playwright page object (sync_api) after navigating to the slots view.
    expected_date: if set, the page is showing slots for this date; use it for every slot.
    Tries #slotsGrid first, then body.
    """
    try:
        # Prefer the slots grid if it exists
        grid = page.locator("#slotsGrid")
        if grid.count() > 0:
            content = grid.inner_text(timeout=5000)
        else:
            content = page.locator("body").inner_text(timeout=5000)
    except Exception as e:
        logger.warning("Could not get page content for LLM: %s", e)
        content = page.locator("body").inner_text(timeout=10000)
    return extract_availability_with_llm(
        content, facility_name=facility_name, expected_date=expected_date
    )
