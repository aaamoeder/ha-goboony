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

RETRY_INTERVAL = timedelta(minutes=2)
MAX_CONSECUTIVE_FAILURES = 3


class GoboonyCoordinator(DataUpdateCoordinator[dict]):
    """Goboony data update coordinator."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self._normal_interval = timedelta(
            minutes=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL // 60)
        )
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=self._normal_interval,
            config_entry=entry,
        )
        self.api = GoboonyApi(
            email=entry.data[CONF_EMAIL],
            password=entry.data[CONF_PASSWORD],
            listing_id=entry.data[CONF_LISTING_ID],
        )
        self._consecutive_failures = 0

    async def _async_update_data(self) -> dict:
        """Fetch data from Goboony."""
        try:
            data = await self.hass.async_add_executor_job(self.api.get_all_data)
            self._consecutive_failures = 0
            # Restore normal interval after successful fetch
            if self.update_interval != self._normal_interval:
                _LOGGER.debug("Update succeeded, restoring normal interval (%s)", self._normal_interval)
                self.update_interval = self._normal_interval
            return data
        except GoboonyAuthError as err:
            self.api.session.cookies.clear()
            self._consecutive_failures = 0
            self.update_interval = self._normal_interval
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN,
                translation_key="invalid_auth",
            ) from err
        except (GoboonyApiError, Exception) as err:
            self._consecutive_failures += 1
            _LOGGER.warning(
                "Goboony update failed (%d/%d): %s — retrying in %s",
                self._consecutive_failures,
                MAX_CONSECUTIVE_FAILURES,
                err,
                RETRY_INTERVAL,
            )

            # Switch to fast retry interval
            self.update_interval = RETRY_INTERVAL

            # Keep previous data if we have it and haven't failed too many times
            if self.data and self._consecutive_failures < MAX_CONSECUTIVE_FAILURES:
                _LOGGER.debug("Keeping previous data, retry scheduled in %s", RETRY_INTERVAL)
                return self.data

            raise UpdateFailed(f"API error after {self._consecutive_failures} attempts: {err}") from err
