"""Image platform for Goboony."""
from __future__ import annotations

import logging
from datetime import datetime

from homeassistant.components.image import ImageEntity
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
    """Set up Goboony image from a config entry."""
    coordinator: GoboonyCoordinator = hass.data[DOMAIN][entry.entry_id]
    listing_id = entry.data.get("listing_id", "")

    async_add_entities([
        GoboonyListingImage(coordinator, entry, listing_id),
    ])


class GoboonyListingImage(CoordinatorEntity, ImageEntity):
    """Image entity showing the listing photo."""

    _attr_has_entity_name = True
    _attr_translation_key = "listing_photo"

    def __init__(
        self,
        coordinator: GoboonyCoordinator,
        entry: ConfigEntry,
        listing_id: str,
    ) -> None:
        CoordinatorEntity.__init__(self, coordinator)
        ImageEntity.__init__(self, coordinator.hass)
        self._listing_id = listing_id
        self._attr_unique_id = f"{listing_id}_listing_photo"
        self._current_url: str | None = None

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._listing_id)},
            name=f"Goboony {self._listing_id}",
            manufacturer="Goboony",
            model="Camper Listing",
        )

    @property
    def image_url(self) -> str | None:
        if not self.coordinator.data:
            return None
        listing = self.coordinator.data.get("listing", {})
        url = listing.get("photo_url")
        if url and url != self._current_url:
            self._current_url = url
            self._attr_image_last_updated = datetime.now()
        return url
