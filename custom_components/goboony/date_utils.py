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
    # Dutch
    "januari": 1, "februari": 2, "maart": 3, "mei": 5, "juni": 6, "juli": 7,
    "augustus": 8, "oktober": 10, "mrt": 3, "okt": 10,
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
    r"([^\W\d_]+)\s+(\d{1,2})(?:,?\s*(\d{4}))?\s*[\u2013\u2014-]\s*(?:([^\W\d_]+)\s+)?(\d{1,2}),?\s*(\d{4})",
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


def parse_dates_range(dates: str) -> tuple[date, date] | None:
    """Parse a dates field like 'October 03 - October 11, 2026' into (start, end).

    Also handles 'October 28 - 31, 2026' and ranges that cross a year boundary.
    """
    if not dates:
        return None
    m = _DATES_RANGE_RE.search(" ".join(dates.split()))
    if not m:
        return None
    start_month = MONTH_MAP_FULL.get(m.group(1).lower())
    end_month = MONTH_MAP_FULL.get(m.group(4).lower()) if m.group(4) else start_month
    if not start_month or not end_month:
        return None
    end_year = int(m.group(6))
    start_year = int(m.group(3)) if m.group(3) else end_year
    try:
        end = date(end_year, end_month, int(m.group(5)))
        start = date(start_year, start_month, int(m.group(2)))
    except ValueError:
        return None
    if start > end and not m.group(3):
        start = start.replace(year=start.year - 1)
    return start, end


def booking_date_range(booking: dict) -> tuple[date, date] | None:
    """Return the (start, end) dates of a booking.

    Prefers the detailed check-in/check-out text and falls back to the dates
    field of the bookings list, which is always present.
    """
    start = parse_date_from_check(booking.get("check_in", ""))
    end = parse_date_from_check(booking.get("check_out", ""))
    if start and end:
        return start, end
    return parse_dates_range(booking.get("dates", ""))


def parse_check_in_date(booking: dict) -> datetime | None:
    """Parse the check-in date from booking data as a UTC datetime."""
    check_in = booking.get("check_in", "")
    if check_in:
        result = parse_check_datetime(check_in)
        if result:
            return result

    rng = parse_dates_range(booking.get("dates", ""))
    if rng:
        return datetime(rng[0].year, rng[0].month, rng[0].day, tzinfo=timezone.utc)

    return None
