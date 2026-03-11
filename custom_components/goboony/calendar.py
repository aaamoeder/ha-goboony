"""Calendar platform for Goboony."""
from __future__ import annotations

from datetime import datetime, date, timedelta
import logging
import re

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GoboonyCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Goboony calendar from a config entry."""
    coordinator: GoboonyCoordinator = hass.data[DOMAIN][entry.entry_id]
    listing_id = entry.data.get("listing_id", "")

    async_add_entities([
        GoboonyBookingsCalendar(coordinator, entry, listing_id),
    ])


def _parse_booking_dates(dates_str: str) -> tuple[date | None, date | None]:
    """Parse dates from booking string like 'Apr 27 - May 1, 2026'."""
    if not dates_str:
        return None, None
    try:
        parts = dates_str.split(" - ")
        if len(parts) != 2:
            return None, None

        end_str = parts[1].strip()
        start_str = parts[0].strip()

        # Try to parse end date (usually has the year)
        end_dt = None
        for fmt in ["%b %d, %Y", "%d %b %Y", "%d %b, %Y"]:
            try:
                end_dt = datetime.strptime(end_str, fmt).date()
                break
            except ValueError:
                continue

        if not end_dt:
            return None, None

        year = end_dt.year

        # Parse start date (often without year)
        start_dt = None
        for fmt in ["%b %d", "%b %d, %Y", "%d %b", "%d %b %Y"]:
            try:
                start_dt = datetime.strptime(start_str, fmt).date()
                start_dt = start_dt.replace(year=year)
                # If start > end, it started in the previous year
                if start_dt > end_dt:
                    start_dt = start_dt.replace(year=year - 1)
                break
            except ValueError:
                continue

        return start_dt, end_dt
    except Exception:
        return None, None


def _parse_check_in_out(check_in: str, check_out: str) -> tuple[datetime | None, datetime | None]:
    """Parse check-in/out strings like 'Mon 27 Apr 2:00 PM'."""
    results = []
    for text in [check_in, check_out]:
        if not text:
            results.append(None)
            continue
        dt = None
        # Try formats with day name
        for fmt in [
            "%a %d %b %I:%M %p",
            "%a %d %b %Y %I:%M %p",
        ]:
            try:
                dt = datetime.strptime(text.strip(), fmt)
                if dt.year < 2000:
                    dt = dt.replace(year=datetime.now().year)
                break
            except ValueError:
                continue
        # Try extracting year from the string if present
        if dt and dt.year < 2000:
            year_match = re.search(r"20\d{2}", text)
            if year_match:
                dt = dt.replace(year=int(year_match.group()))
        results.append(dt)
    return results[0], results[1]


class GoboonyBookingsCalendar(CoordinatorEntity, CalendarEntity):
    """Calendar showing all Goboony bookings and blocked periods."""

    _attr_icon = "mdi:caravan"

    def __init__(
        self,
        coordinator: GoboonyCoordinator,
        entry: ConfigEntry,
        listing_id: str,
    ) -> None:
        super().__init__(coordinator)
        self._listing_id = listing_id
        self._entry = entry
        self._attr_unique_id = f"{listing_id}_calendar"
        self._attr_has_entity_name = True
        self._attr_translation_key = "bookings_calendar"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._listing_id)},
            name=f"Goboony {self._listing_id}",
            manufacturer="Goboony",
            model="Camper Listing",
        )

    def _build_events(self) -> list[CalendarEvent]:
        """Build calendar events from coordinator data."""
        events = []
        if not self.coordinator.data:
            return events

        # Add booking events
        bookings = self.coordinator.data.get("bookings", [])
        for booking in bookings:
            status = booking.get("status", "")
            if status not in ("confirmed", "accepted", "request_accepted"):
                continue

            renter = booking.get("renter", "Unknown")
            earnings = booking.get("earnings")
            booking_id = booking.get("booking_number", booking.get("booking_id", ""))

            # Try detailed check-in/out first
            check_in = booking.get("check_in", "")
            check_out = booking.get("check_out", "")
            start_dt, end_dt = _parse_check_in_out(check_in, check_out)

            # Fall back to dates string for date-only
            start_date = None
            end_date = None
            if not start_dt or not end_dt:
                start_date, end_date = _parse_booking_dates(booking.get("dates", ""))

            if not start_dt and not start_date:
                continue

            summary = f"Booking: {renter}"
            description_parts = [
                f"Booking: {booking_id}",
                f"Renter: {renter}",
                f"Status: {status}",
            ]
            if earnings:
                description_parts.append(f"Earnings: EUR {earnings:.2f}")
            num_days = booking.get("num_days")
            if num_days:
                description_parts.append(f"Days: {num_days}")

            description = "\n".join(description_parts)

            if start_dt and end_dt:
                events.append(CalendarEvent(
                    start=start_dt,
                    end=end_dt,
                    summary=summary,
                    description=description,
                ))
            elif start_date and end_date:
                events.append(CalendarEvent(
                    start=start_date,
                    end=end_date,
                    summary=summary,
                    description=description,
                ))

        # Add blocked period events
        availability = self.coordinator.data.get("availability", {})
        blocked_periods = availability.get("blocked_periods", [])
        blocked_dates = availability.get("blocked_dates", [])

        # Try to match blocked periods to their date ranges
        # Group consecutive blocked dates into ranges
        if blocked_dates:
            sorted_dates = sorted(blocked_dates)
            ranges = []
            range_start = sorted_dates[0]
            prev = sorted_dates[0]
            for d in sorted_dates[1:]:
                prev_date = date.fromisoformat(prev)
                curr_date = date.fromisoformat(d)
                if (curr_date - prev_date).days > 1:
                    ranges.append((range_start, prev))
                    range_start = d
                prev = d
            ranges.append((range_start, prev))

            for i, (start, end) in enumerate(ranges):
                # Try to find a matching named period
                name = "Blocked"
                if i < len(blocked_periods):
                    name = blocked_periods[i].get("name", "Blocked")

                events.append(CalendarEvent(
                    start=date.fromisoformat(start),
                    end=date.fromisoformat(end) + timedelta(days=1),  # end is exclusive
                    summary=f"Blocked: {name}",
                    description=f"Blocked period: {name}",
                ))

        return events

    @property
    def event(self) -> CalendarEvent | None:
        """Return the current or next upcoming event."""
        events = self._build_events()
        if not events:
            return None

        now = datetime.now()
        today = now.date()

        # Find active event (happening now)
        for ev in events:
            ev_start = ev.start if isinstance(ev.start, date) else ev.start.date()
            ev_end = ev.end if isinstance(ev.end, date) else ev.end.date()
            if ev_start <= today < ev_end:
                return ev

        # Find next upcoming event
        future = []
        for ev in events:
            ev_start = ev.start if isinstance(ev.start, date) else ev.start.date()
            if ev_start > today:
                future.append(ev)

        if future:
            future.sort(key=lambda e: e.start if isinstance(e.start, date) else e.start.date())
            return future[0]

        return None

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return events within a date range."""
        events = self._build_events()
        result = []

        for ev in events:
            ev_start = ev.start if isinstance(ev.start, datetime) else datetime.combine(ev.start, datetime.min.time())
            ev_end = ev.end if isinstance(ev.end, datetime) else datetime.combine(ev.end, datetime.min.time())

            if ev_end >= start_date and ev_start <= end_date:
                result.append(ev)

        return result
