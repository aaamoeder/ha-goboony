"""Diagnostics support for Goboony."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

REDACT_KEYS = {"email", "password"}


def _redact(data: dict, keys: set[str]) -> dict:
    """Redact sensitive keys from a dict."""
    result = {}
    for k, v in data.items():
        if k in keys:
            result[k] = "**REDACTED**"
        elif isinstance(v, dict):
            result[k] = _redact(v, keys)
        else:
            result[k] = v
    return result


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = hass.data[DOMAIN].get(entry.entry_id)
    if not coordinator:
        return {"error": "Coordinator not found"}

    data = coordinator.data or {}

    return {
        "config_entry": {
            "data": _redact(dict(entry.data), REDACT_KEYS),
            "options": dict(entry.options),
        },
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "update_interval": str(coordinator.update_interval),
        },
        "data": {
            "bookings_count": len(data.get("bookings", [])),
            "bookings": [
                {
                    "booking_id": b.get("booking_id"),
                    "status": b.get("status"),
                    "dates": b.get("dates"),
                    "check_in": b.get("check_in"),
                    "check_out": b.get("check_out"),
                    "num_days": b.get("num_days"),
                    "earnings": b.get("earnings"),
                }
                for b in data.get("bookings", [])
            ],
            "availability": {
                "booked_days": len(data.get("availability", {}).get("booked_dates", [])),
                "blocked_days": len(data.get("availability", {}).get("blocked_dates", [])),
                "available_days": len(data.get("availability", {}).get("available_dates", [])),
                "blocked_periods": data.get("availability", {}).get("blocked_periods", []),
            },
            "rates": data.get("rates", {}),
            "listing": {
                "title": data.get("listing", {}).get("title"),
                "rating": data.get("listing", {}).get("rating"),
                "review_count": data.get("listing", {}).get("review_count"),
                "photo_url": data.get("listing", {}).get("photo_url"),
            },
        },
    }
