"""Config flow for Goboony."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .api import GoboonyApi, GoboonyAuthError
from .const import CONF_EMAIL, CONF_LISTING_ID, CONF_PASSWORD, DOMAIN

_LOGGER = logging.getLogger(__name__)


class GoboonyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Goboony."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Check if already configured
            await self.async_set_unique_id(user_input[CONF_LISTING_ID])
            self._abort_if_unique_id_configured()

            # Test credentials
            api = GoboonyApi(
                email=user_input[CONF_EMAIL],
                password=user_input[CONF_PASSWORD],
                listing_id=user_input[CONF_LISTING_ID],
            )
            try:
                await self.hass.async_add_executor_job(api.login)
            except GoboonyAuthError:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected error during login")
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=f"Goboony {user_input[CONF_LISTING_ID]}",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_EMAIL): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Required(CONF_LISTING_ID): str,
            }),
            errors=errors,
        )
