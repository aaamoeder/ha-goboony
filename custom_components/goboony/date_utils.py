"""Gedeelde datumhulpfuncties voor Goboony-boekingen."""
from __future__ import annotations

from datetime import date, datetime, time

from homeassistant.util import dt as dt_util


def today() -> date:
    """Geef de datum van vandaag in de tijdzone van Home Assistant."""
    return dt_util.now().date()


def booking_date_range(booking: dict) -> tuple[date, date] | None:
    """Geef de datums (start, einde) van een boeking, beide inbegrepen."""
    try:
        return date.fromisoformat(booking["start"]), date.fromisoformat(booking["end"])
    except (KeyError, TypeError, ValueError):
        return None


def _clock(text: str | None, default: time) -> time:
    """Lees een tijd als '14:00'."""
    try:
        hour, _, minute = str(text).partition(":")
        return time(int(hour), int(minute or 0))
    except (TypeError, ValueError):
        return default


def check_in_datetime(booking: dict) -> datetime | None:
    """Geef het moment van check-in in de tijdzone van Home Assistant."""
    rng = booking_date_range(booking)
    if not rng:
        return None
    return datetime.combine(
        rng[0],
        _clock(booking.get("check_in_time"), time(14, 0)),
        tzinfo=dt_util.get_default_time_zone(),
    )


def check_out_datetime(booking: dict) -> datetime | None:
    """Geef het moment van check-out in de tijdzone van Home Assistant."""
    rng = booking_date_range(booking)
    if not rng:
        return None
    return datetime.combine(
        rng[1],
        _clock(booking.get("check_out_time"), time(12, 0)),
        tzinfo=dt_util.get_default_time_zone(),
    )
