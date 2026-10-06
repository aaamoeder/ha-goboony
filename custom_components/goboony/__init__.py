"""Goboony integration for Home Assistant."""
from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN
from .coordinator import GoboonyCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.BINARY_SENSOR, Platform.BUTTON, Platform.CALENDAR, Platform.IMAGE, Platform.SENSOR]

CARD_JS_URL = f"/{DOMAIN}/goboony-bookings-card.js"
CARD_JS_PATH = Path(__file__).parent / "goboony-bookings-card.js"
CARD_VERSION = "1.8.1"


async def _async_register_card(hass: HomeAssistant) -> None:
    """Make the Lovelace card available on dashboards.

    The card is registered as a Lovelace resource. An extra JS module runs before
    the frontend's custom element registry is ready, so on a direct page load the
    card stays undefined ("Custom element doesn't exist"). When Lovelace resources
    are managed in YAML they cannot be edited, so we fall back to the extra JS URL.
    """
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_JS_URL, str(CARD_JS_PATH), cache_headers=False)]
    )
    url = f"{CARD_JS_URL}?v={CARD_VERSION}"
    try:
        from homeassistant.components.lovelace.const import LOVELACE_DATA

        resources = hass.data[LOVELACE_DATA].resources
        if not hasattr(resources, "async_create_item"):
            raise RuntimeError("Lovelace resources are managed in YAML")
        if hasattr(resources, "loaded") and not resources.loaded:
            await resources.async_load()
            resources.loaded = True

        existing = [i for i in resources.async_items() if i["url"].split("?")[0] == CARD_JS_URL]
        if any(i["url"] == url for i in existing):
            return
        if existing:
            await resources.async_update_item(existing[0]["id"], {"res_type": "module", "url": url})
            for duplicate in existing[1:]:
                await resources.async_delete_item(duplicate["id"])
        else:
            await resources.async_create_item({"res_type": "module", "url": url})
        return
    except Exception as err:  # noqa: BLE001
        _LOGGER.debug("Could not register the card as a Lovelace resource (%s), using extra JS", err)
    add_extra_js_url(hass, url)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Goboony from a config entry."""
    # Register the custom card JS (only once)
    hass.data.setdefault(DOMAIN, {})
    if "frontend_loaded" not in hass.data[DOMAIN]:
        await _async_register_card(hass)
        hass.data[DOMAIN]["frontend_loaded"] = True

    coordinator = GoboonyCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update — reload integration to apply new scan interval."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator: GoboonyCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await hass.async_add_executor_job(coordinator.api.close)
    return unload_ok
