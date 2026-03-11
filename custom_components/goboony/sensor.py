"""Sensor platform for Goboony."""
from __future__ import annotations

from datetime import datetime, timezone
import logging

from homeassistant.components.sensor import SensorEntity, SensorStateClass
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
    """Set up Goboony sensors from a config entry."""
    coordinator: GoboonyCoordinator = hass.data[DOMAIN][entry.entry_id]
    listing_id = entry.data.get("listing_id", "")

    entities: list[SensorEntity] = [
        GoboonyTotalBookingsSensor(coordinator, entry, listing_id),
        GoboonyConfirmedBookingsSensor(coordinator, entry, listing_id),
        GoboonyNextBookingSensor(coordinator, entry, listing_id),
        GoboonyNextBookingDaysSensor(coordinator, entry, listing_id),
        GoboonyTotalEarningsSensor(coordinator, entry, listing_id),
        GoboonyBaseRateSensor(coordinator, entry, listing_id),
        GoboonyPeakRateSensor(coordinator, entry, listing_id),
        GoboonyBookedDaysSensor(coordinator, entry, listing_id),
        GoboonyBlockedDaysSensor(coordinator, entry, listing_id),
        GoboonyAvailableDaysSensor(coordinator, entry, listing_id),
        GoboonyBlockedPeriodsSensor(coordinator, entry, listing_id),
        GoboonyOccupancyRateSensor(coordinator, entry, listing_id),
        GoboonyReviewsSensor(coordinator, entry, listing_id),
    ]

    async_add_entities(entities)


class GoboonyBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for Goboony sensors."""

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
        """Return device info."""
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
        return [b for b in self._get_bookings() if b.get("status") == "confirmed"]

    def _get_availability(self) -> dict:
        if not self.coordinator.data:
            return {}
        return self.coordinator.data.get("availability", {})

    def _get_rates(self) -> dict:
        if not self.coordinator.data:
            return {}
        return self.coordinator.data.get("rates", {})


class GoboonyTotalBookingsSensor(GoboonyBaseSensor):
    """Total number of bookings."""

    _attr_icon = "mdi:book-multiple"
    _attr_translation_key = "total_bookings"

    @property
    def unique_id(self) -> str:
        return f"{self._listing_id}_total_bookings"

    @property
    def native_value(self) -> int:
        return len(self._get_bookings())

    @property
    def extra_state_attributes(self) -> dict:
        bookings = self._get_bookings()
        booking_list = []
        for b in bookings:
            booking_list.append({
                "id": b.get("booking_number", b.get("booking_id", "")),
                "renter": b.get("renter", ""),
                "status": b.get("status", ""),
                "dates": b.get("dates", ""),
                "check_in": b.get("check_in", ""),
                "check_out": b.get("check_out", ""),
                "num_days": b.get("num_days"),
                "earnings": b.get("earnings"),
                "url": b.get("url", ""),
            })
        return {
            "confirmed": len([b for b in bookings if b.get("status") == "confirmed"]),
            "pending": len([b for b in bookings if b.get("status") in ("request", "request_accepted")]),
            "inquiries": len([b for b in bookings if b.get("status") in ("inquiry", "message")]),
            "bookings": booking_list,
        }


class GoboonyConfirmedBookingsSensor(GoboonyBaseSensor):
    """Number of confirmed bookings."""

    _attr_icon = "mdi:book-check"
    _attr_translation_key = "confirmed_bookings"

    @property
    def unique_id(self) -> str:
        return f"{self._listing_id}_confirmed_bookings"

    @property
    def native_value(self) -> int:
        return len(self._get_confirmed_bookings())

    @property
    def extra_state_attributes(self) -> dict:
        bookings = self._get_confirmed_bookings()
        attrs = {}
        for i, b in enumerate(bookings):
            prefix = f"booking_{i+1}"
            attrs[f"{prefix}_id"] = b.get("booking_number", b.get("booking_id", ""))
            attrs[f"{prefix}_renter"] = b.get("renter", "")
            attrs[f"{prefix}_dates"] = b.get("dates", "")
            attrs[f"{prefix}_earnings"] = b.get("earnings")
        return attrs


class GoboonyNextBookingSensor(GoboonyBaseSensor):
    """Next upcoming confirmed booking."""

    _attr_icon = "mdi:calendar-arrow-right"
    _attr_translation_key = "next_booking"

    @property
    def unique_id(self) -> str:
        return f"{self._listing_id}_next_booking"

    @property
    def native_value(self) -> str | None:
        bookings = self._get_confirmed_bookings()
        if bookings:
            b = bookings[0]
            return b.get("dates", "N/A")
        return None

    @property
    def extra_state_attributes(self) -> dict:
        bookings = self._get_confirmed_bookings()
        if bookings:
            b = bookings[0]
            return {
                "booking_id": b.get("booking_number", b.get("booking_id", "")),
                "renter": b.get("renter", ""),
                "earnings": b.get("earnings"),
                "num_days": b.get("num_days"),
                "check_in": b.get("check_in"),
                "check_out": b.get("check_out"),
            }
        return {}


class GoboonyNextBookingDaysSensor(GoboonyBaseSensor):
    """Days until next booking."""

    _attr_icon = "mdi:calendar-clock"
    _attr_native_unit_of_measurement = "d"
    _attr_translation_key = "next_booking_days"

    @property
    def unique_id(self) -> str:
        return f"{self._listing_id}_next_booking_days"

    @property
    def native_value(self) -> int | None:
        bookings = self._get_confirmed_bookings()
        now = datetime.now(timezone.utc)

        for b in bookings:
            dates = b.get("dates", "")
            check_in = b.get("check_in", "")
            if check_in:
                try:
                    dt = datetime.fromisoformat(check_in)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    delta = (dt - now).days
                    if delta >= 0:
                        return delta
                except (ValueError, TypeError):
                    pass
            if dates:
                try:
                    parts = dates.split(" - ")
                    if len(parts) == 2:
                        start_str = parts[0].strip()
                        end_str = parts[1].strip()
                        year = datetime.now().year
                        for fmt in ["%b %d, %Y", "%b %d %Y"]:
                            try:
                                end_dt = datetime.strptime(end_str, fmt)
                                year = end_dt.year
                                break
                            except ValueError:
                                continue
                        for fmt in ["%b %d", "%b %d, %Y"]:
                            try:
                                start_dt = datetime.strptime(start_str, fmt)
                                start_dt = start_dt.replace(year=year, tzinfo=timezone.utc)
                                delta = (start_dt - now).days
                                if delta >= 0:
                                    return delta
                                break
                            except ValueError:
                                continue
                except Exception:
                    pass

        return None


class GoboonyTotalEarningsSensor(GoboonyBaseSensor):
    """Total earnings from confirmed bookings."""

    _attr_icon = "mdi:cash-multiple"
    _attr_native_unit_of_measurement = "EUR"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_translation_key = "total_earnings"

    @property
    def unique_id(self) -> str:
        return f"{self._listing_id}_total_earnings"

    @property
    def native_value(self) -> float:
        bookings = self._get_confirmed_bookings()
        total = sum(b.get("earnings", 0) or 0 for b in bookings)
        return round(total, 2)

    @property
    def extra_state_attributes(self) -> dict:
        bookings = self._get_confirmed_bookings()
        return {
            "num_bookings": len(bookings),
            "bookings": [
                {
                    "id": b.get("booking_number", ""),
                    "renter": b.get("renter", ""),
                    "earnings": b.get("earnings"),
                }
                for b in bookings
            ],
        }


class GoboonyBaseRateSensor(GoboonyBaseSensor):
    """Base (low season) rate."""

    _attr_icon = "mdi:currency-eur"
    _attr_native_unit_of_measurement = "EUR"
    _attr_translation_key = "base_rate"

    @property
    def unique_id(self) -> str:
        return f"{self._listing_id}_base_rate"

    @property
    def native_value(self) -> float | None:
        rates = self._get_rates()
        return rates.get("base_rate")

    @property
    def extra_state_attributes(self) -> dict:
        rates = self._get_rates()
        return {
            "peak_rate": rates.get("peak_rate"),
            "shoulder_early_rate": rates.get("shoulder_early_rate"),
            "shoulder_late_rate": rates.get("shoulder_late_rate"),
            "cleaning_fee": rates.get("cleaning_fee"),
            "price_per_extra_km": rates.get("price_per_extra_km"),
            "max_km_per_week": rates.get("max_km_per_week"),
        }


class GoboonyPeakRateSensor(GoboonyBaseSensor):
    """Peak season rate."""

    _attr_icon = "mdi:cash-plus"
    _attr_native_unit_of_measurement = "EUR"
    _attr_translation_key = "peak_rate"

    @property
    def unique_id(self) -> str:
        return f"{self._listing_id}_peak_rate"

    @property
    def native_value(self) -> float | None:
        rates = self._get_rates()
        return rates.get("peak_rate")


class GoboonyBookedDaysSensor(GoboonyBaseSensor):
    """Number of booked days on calendar."""

    _attr_icon = "mdi:calendar-check"
    _attr_native_unit_of_measurement = "d"
    _attr_translation_key = "booked_days"

    @property
    def unique_id(self) -> str:
        return f"{self._listing_id}_booked_days"

    @property
    def native_value(self) -> int:
        avail = self._get_availability()
        return len(avail.get("booked_dates", []))


class GoboonyBlockedDaysSensor(GoboonyBaseSensor):
    """Number of blocked days on calendar."""

    _attr_icon = "mdi:calendar-remove"
    _attr_native_unit_of_measurement = "d"
    _attr_translation_key = "blocked_days"

    @property
    def unique_id(self) -> str:
        return f"{self._listing_id}_blocked_days"

    @property
    def native_value(self) -> int:
        avail = self._get_availability()
        return len(avail.get("blocked_dates", []))

    @property
    def extra_state_attributes(self) -> dict:
        avail = self._get_availability()
        periods = avail.get("blocked_periods", [])
        return {
            "periods": [{"name": p.get("name", ""), "id": p.get("id", "")} for p in periods],
        }


class GoboonyAvailableDaysSensor(GoboonyBaseSensor):
    """Number of available days on calendar."""

    _attr_icon = "mdi:calendar-blank"
    _attr_native_unit_of_measurement = "d"
    _attr_translation_key = "available_days"

    @property
    def unique_id(self) -> str:
        return f"{self._listing_id}_available_days"

    @property
    def native_value(self) -> int:
        avail = self._get_availability()
        return len(avail.get("available_dates", []))


class GoboonyBlockedPeriodsSensor(GoboonyBaseSensor):
    """Blocked periods info."""

    _attr_icon = "mdi:calendar-lock"
    _attr_translation_key = "blocked_periods"

    @property
    def unique_id(self) -> str:
        return f"{self._listing_id}_blocked_periods"

    @property
    def native_value(self) -> int:
        avail = self._get_availability()
        return len(avail.get("blocked_periods", []))

    @property
    def extra_state_attributes(self) -> dict:
        avail = self._get_availability()
        periods = avail.get("blocked_periods", [])
        return {
            f"period_{i+1}": p.get("name", "Unknown")
            for i, p in enumerate(periods)
        }


class GoboonyOccupancyRateSensor(GoboonyBaseSensor):
    """Occupancy rate as a percentage of booked vs available days."""

    _attr_icon = "mdi:percent-circle"
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_translation_key = "occupancy_rate"

    @property
    def unique_id(self) -> str:
        return f"{self._listing_id}_occupancy_rate"

    @property
    def native_value(self) -> float:
        avail = self._get_availability()
        booked = avail.get("booked_dates", [])
        available = avail.get("available_dates", [])
        total = len(booked) + len(available)
        if total == 0:
            return 0.0
        return round(len(booked) / total * 100, 1)


class GoboonyReviewsSensor(GoboonyBaseSensor):
    """Listing rating/reviews."""

    _attr_icon = "mdi:star"
    _attr_translation_key = "reviews"

    @property
    def unique_id(self) -> str:
        return f"{self._listing_id}_reviews"

    @property
    def native_value(self) -> float | None:
        if not self.coordinator.data:
            return None
        listing = self.coordinator.data.get("listing", {})
        return listing.get("rating")

    @property
    def extra_state_attributes(self) -> dict:
        if not self.coordinator.data:
            return {}
        listing = self.coordinator.data.get("listing", {})
        return {
            "review_count": listing.get("review_count"),
            "times_hired": listing.get("times_hired"),
        }
