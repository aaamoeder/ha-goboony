"""Goboony integration for Home Assistant."""
from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import GoboonyCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.CALENDAR]

CARD_JS_URL = f"/{DOMAIN}/goboony-bookings-card.js"
CARD_JS_PATH = Path(__file__).parent / "goboony-bookings-card.js"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Goboony from a config entry."""
    # Register the custom card JS (only once)
    hass.data.setdefault(DOMAIN, {})
    if "frontend_loaded" not in hass.data[DOMAIN]:
        hass.http.register_static_path(CARD_JS_URL, str(CARD_JS_PATH), cache_headers=False)
        add_extra_js_url(hass, CARD_JS_URL)
        hass.data[DOMAIN]["frontend_loaded"] = True

    coordinator = GoboonyCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
