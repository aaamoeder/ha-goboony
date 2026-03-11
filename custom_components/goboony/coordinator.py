"""DataUpdateCoordinator for Goboony."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import GoboonyApi, GoboonyApiError, GoboonyAuthError
from .const import CONF_EMAIL, CONF_LISTING_ID, CONF_PASSWORD, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class GoboonyCoordinator(DataUpdateCoordinator[dict]):
    """Goboony data update coordinator."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        scan_minutes = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL // 60)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=scan_minutes),
            config_entry=entry,
        )
        self.api = GoboonyApi(
            email=entry.data[CONF_EMAIL],
            password=entry.data[CONF_PASSWORD],
            listing_id=entry.data[CONF_LISTING_ID],
        )

    async def _async_update_data(self) -> dict:
        """Fetch data from Goboony."""
        try:
            return await self.hass.async_add_executor_job(self.api.get_all_data)
        except GoboonyAuthError as err:
            self.api.session.cookies.clear()
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN,
                translation_key="invalid_auth",
            ) from err
        except GoboonyApiError as err:
            raise UpdateFailed(f"API error: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err
