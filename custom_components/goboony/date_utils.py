"""Shared date parsing utilities for Goboony."""
from __future__ import annotations

import re
from datetime import date, datetime, timezone

MONTH_MAP_SHORT = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

MONTH_MAP_FULL = {
    **MONTH_MAP_SHORT,
    "january": 1, "february": 2, "march": 3, "april": 4,
    "june": 6, "july": 7, "august": 8, "september": 9,
    "october": 10, "november": 11, "december": 12,
}

_CHECK_DATE_RE = re.compile(
    r"(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*(\d{4})?",
    re.IGNORECASE,
)

_CHECK_DATETIME_RE = re.compile(
    r"(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*(\d{4})?\s*.*?(\d{1,2}):(\d{2})\s*(AM|PM)?",
    re.IGNORECASE,
)

_DATES_RANGE_RE = re.compile(
    r"(\w+)\s+(\d{1,2}).*?(\w+)\s+(\d{1,2}),?\s*(\d{4})",
)


def parse_date_from_check(text: str) -> date | None:
    """Parse a date from check-in/out text like 'Mon 27 Apr – 2:00 PM'."""
    if not text:
        return None
    m = _CHECK_DATE_RE.search(text)
    if m:
        day = int(m.group(1))
        month = MONTH_MAP_SHORT[m.group(2).lower()]
        year = int(m.group(3)) if m.group(3) else datetime.now().year
        return date(year, month, day)
    return None


def parse_check_datetime(text: str) -> datetime | None:
    """Parse datetime from check-in/out text like 'Mon 27 Apr – 2:00 PM'."""
    if not text:
        return None

    m = _CHECK_DATETIME_RE.search(text)
    if m:
        day = int(m.group(1))
        month = MONTH_MAP_SHORT[m.group(2).lower()]
        year = int(m.group(3)) if m.group(3) else datetime.now().year
        hour = int(m.group(4))
        minute = int(m.group(5))
        if m.group(6):
            ampm = m.group(6).upper()
            if ampm == "PM" and hour != 12:
                hour += 12
            elif ampm == "AM" and hour == 12:
                hour = 0
        return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)

    # Fallback: date only
    m = _CHECK_DATE_RE.search(text)
    if m:
        day = int(m.group(1))
        month = MONTH_MAP_SHORT[m.group(2).lower()]
        year = int(m.group(3)) if m.group(3) else datetime.now().year
        return datetime(year, month, day, tzinfo=timezone.utc)

    return None


def parse_check_in_date(booking: dict) -> datetime | None:
    """Parse the check-in date from booking data as a UTC datetime."""
    check_in = booking.get("check_in", "")
    if check_in:
        result = parse_check_datetime(check_in)
        if result:
            return result

    # Try dates field: "April 27 – May 1, 2026"
    dates = booking.get("dates", "")
    if dates:
        dates_clean = " ".join(dates.split())
        m = _DATES_RANGE_RE.search(dates_clean)
        if m:
            start_month = MONTH_MAP_FULL.get(m.group(1).lower())
            if start_month:
                year = int(m.group(5))
                return datetime(year, start_month, int(m.group(2)), tzinfo=timezone.utc)

    return None
