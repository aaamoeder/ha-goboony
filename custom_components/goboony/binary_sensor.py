"""Binary sensor platform for Goboony."""
from __future__ import annotations

from datetime import date
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GoboonyCoordinator
from .date_utils import parse_date_from_check

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Goboony binary sensors from a config entry."""
    coordinator: GoboonyCoordinator = hass.data[DOMAIN][entry.entry_id]
    listing_id = entry.data.get("listing_id", "")

    async_add_entities([
        GoboonyCurrentlyRentedSensor(coordinator, entry, listing_id),
        GoboonyHasPendingRequestsSensor(coordinator, entry, listing_id),
        GoboonyHasUpcomingBookingSensor(coordinator, entry, listing_id),
        GoboonyTurnaroundSensor(coordinator, entry, listing_id),
    ])


class GoboonyBinaryBaseSensor(CoordinatorEntity, BinarySensorEntity):
    """Base class for Goboony binary sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: GoboonyCoordinator,
        entry: ConfigEntry,
        listing_id: str,
    ) -> None:
        super().__init__(coordinator)
        self._listing_id = listing_id
        self._entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._listing_id)},
            name=f"Goboony {self._listing_id}",
            manufacturer="Goboony",
            model="Camper Listing",
        )

    def _get_bookings(self) -> list[dict]:
        if not self.coordinator.data:
            return []
        return self.coordinator.data.get("bookings", [])

    def _get_confirmed_bookings(self) -> list[dict]:
        return [
            b for b in self._get_bookings()
            if b.get("status") in ("confirmed", "accepted", "request_accepted")
        ]


class GoboonyCurrentlyRentedSensor(GoboonyBinaryBaseSensor):
    """Binary sensor: ON when the camper is currently rented out."""

    _attr_icon = "mdi:caravan"
    _attr_device_class = BinarySensorDeviceClass.OCCUPANCY
    _attr_translation_key = "currently_rented"

    @property
    def unique_id(self) -> str:
        return f"{self._listing_id}_currently_rented"

    @property
    def is_on(self) -> bool:
        today = date.today()
        for b in self._get_confirmed_bookings():
            start = parse_date_from_check(b.get("check_in", ""))
            end = parse_date_from_check(b.get("check_out", ""))
            if start and end and start <= today <= end:
                return True
        return False

    @property
    def extra_state_attributes(self) -> dict:
        today = date.today()
        for b in self._get_confirmed_bookings():
            start = parse_date_from_check(b.get("check_in", ""))
            end = parse_date_from_check(b.get("check_out", ""))
            if start and end and start <= today <= end:
                return {
                    "renter": b.get("renter", ""),
                    "check_in": b.get("check_in", ""),
                    "check_out": b.get("check_out", ""),
                    "remaining_days": (end - today).days,
                }
        return {}


class GoboonyHasPendingRequestsSensor(GoboonyBinaryBaseSensor):
    """Binary sensor: ON when there are pending booking requests."""

    _attr_icon = "mdi:bell-ring"
    _attr_translation_key = "has_pending_requests"

    @property
    def unique_id(self) -> str:
        return f"{self._listing_id}_has_pending_requests"

    @property
    def is_on(self) -> bool:
        pending = [
            b for b in self._get_bookings()
            if b.get("status") in ("request", "inquiry")
        ]
        return len(pending) > 0

    @property
    def extra_state_attributes(self) -> dict:
        pending = [
            b for b in self._get_bookings()
            if b.get("status") in ("request", "inquiry")
        ]
        return {
            "count": len(pending),
            "requests": [
                {"renter": b.get("renter", ""), "status": b.get("status", ""), "dates": b.get("dates", "")}
                for b in pending
            ],
        }


class GoboonyHasUpcomingBookingSensor(GoboonyBinaryBaseSensor):
    """Binary sensor: ON when there's a confirmed booking in the future."""

    _attr_icon = "mdi:calendar-check"
    _attr_translation_key = "has_upcoming_booking"

    @property
    def unique_id(self) -> str:
        return f"{self._listing_id}_has_upcoming_booking"

    @property
    def is_on(self) -> bool:
        today = date.today()
        for b in self._get_confirmed_bookings():
            start = parse_date_from_check(b.get("check_in", ""))
            if start and start > today:
                return True
        return False


class GoboonyTurnaroundSensor(GoboonyBinaryBaseSensor):
    """Binary sensor: ON between a check-out and the next check-in (turnaround window)."""

    _attr_icon = "mdi:swap-horizontal"
    _attr_translation_key = "turnaround"

    @property
    def unique_id(self) -> str:
        return f"{self._listing_id}_turnaround"

    @property
    def is_on(self) -> bool:
        today = date.today()
        bookings = self._get_confirmed_bookings()

        # Collect all date ranges
        ranges = []
        for b in bookings:
            start = parse_date_from_check(b.get("check_in", ""))
            end = parse_date_from_check(b.get("check_out", ""))
            if start and end:
                ranges.append((start, end))

        ranges.sort(key=lambda r: r[0])

        # Check if today falls between consecutive bookings
        for i in range(len(ranges) - 1):
            prev_end = ranges[i][1]
            next_start = ranges[i + 1][0]
            if prev_end <= today < next_start:
                return True
        return False

    @property
    def extra_state_attributes(self) -> dict:
        today = date.today()
        bookings = self._get_confirmed_bookings()

        ranges = []
        for b in bookings:
            start = parse_date_from_check(b.get("check_in", ""))
            end = parse_date_from_check(b.get("check_out", ""))
            if start and end:
                ranges.append((start, end, b))

        ranges.sort(key=lambda r: r[0])

        for i in range(len(ranges) - 1):
            prev_end = ranges[i][1]
            next_start = ranges[i + 1][0]
            if prev_end <= today < next_start:
                return {
                    "previous_checkout": ranges[i][2].get("check_out", ""),
                    "next_checkin": ranges[i + 1][2].get("check_in", ""),
                    "days_until_next": (next_start - today).days,
                }
        return {}
