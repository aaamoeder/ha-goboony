"""DataUpdateCoordinator for Goboony."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import GoboonyApi, GoboonyApiError, GoboonyAuthError
from .const import CONF_EMAIL, CONF_LISTING_ID, CONF_PASSWORD, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class GoboonyCoordinator(DataUpdateCoordinator):
    """Goboony data update coordinator."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
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
            # Clear session to force re-login next time
            self.api.session.cookies.clear()
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except GoboonyApiError as err:
            raise UpdateFailed(f"API error: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err
