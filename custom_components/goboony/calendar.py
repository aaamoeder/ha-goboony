"""Calendar platform for Goboony."""
from __future__ import annotations

from datetime import date, datetime, timedelta
import logging

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN, STATUS_CONFIRMED
from .coordinator import GoboonyCoordinator
from .date_utils import check_in_datetime, check_out_datetime

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


def _all_day(start: str, end: str) -> tuple[date, date] | None:
    """Return all-day event bounds for an inclusive ISO date range (end is exclusive)."""
    try:
        return date.fromisoformat(start), date.fromisoformat(end) + timedelta(days=1)
    except (TypeError, ValueError):
        return None


def _as_datetime(value: date | datetime) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.combine(value, datetime.min.time(), tzinfo=dt_util.get_default_time_zone())


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
        events: list[CalendarEvent] = []
        if not self.coordinator.data:
            return events

        for booking in self.coordinator.data.get("bookings", []):
            if booking.get("status") != STATUS_CONFIRMED:
                continue
            start = check_in_datetime(booking)
            end = check_out_datetime(booking)
            if not start or not end:
                continue

            renter = booking.get("renter") or "Unknown"
            description_parts = [
                f"Booking: {booking.get('booking_number', '')}",
                f"Renter: {renter}",
            ]
            earnings = booking.get("earnings")
            if earnings:
                description_parts.append(f"Earnings: EUR {earnings:.2f}")
            if booking.get("num_days"):
                description_parts.append(f"Days: {booking['num_days']}")
            if booking.get("url"):
                description_parts.append(booking["url"])

            events.append(CalendarEvent(
                start=start,
                end=end,
                summary=f"Booking: {renter}",
                description="\n".join(description_parts),
                uid=f"goboony-booking-{booking.get('booking_id')}",
            ))

        availability = self.coordinator.data.get("availability", {})

        for item in availability.get("external_bookings", []):
            bounds = _all_day(item.get("start"), item.get("end"))
            if bounds:
                events.append(CalendarEvent(
                    start=bounds[0],
                    end=bounds[1],
                    summary="Booking",
                    description="Booking on the Goboony calendar without booking details",
                ))

        for period in availability.get("blocked_periods", []):
            bounds = _all_day(period.get("start"), period.get("end"))
            if bounds:
                name = period.get("name") or "Blocked"
                events.append(CalendarEvent(
                    start=bounds[0],
                    end=bounds[1],
                    summary="Blocked" if name == "Blocked" else f"Blocked: {name}",
                    description=f"Blocked period: {name}",
                ))

        events.sort(key=lambda ev: _as_datetime(ev.start))
        return events

    @property
    def event(self) -> CalendarEvent | None:
        """Return the current or next upcoming event."""
        now = dt_util.now()
        for ev in self._build_events():
            if _as_datetime(ev.end) > now:
                return ev
        return None

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return events within a date range."""
        return [
            ev for ev in self._build_events()
            if _as_datetime(ev.end) > start_date and _as_datetime(ev.start) < end_date
        ]
