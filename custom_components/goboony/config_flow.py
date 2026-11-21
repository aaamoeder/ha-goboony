"""Configuratiestroom voor Goboony."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback

from .api import GoboonyApi, GoboonyAuthError, GoboonyListingNotFound
from .const import CONF_EMAIL, CONF_LISTING_ID, CONF_PASSWORD, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_LISTING_ID): str,
    }
)


class GoboonyConfigFlow(ConfigFlow, domain=DOMAIN):
    """Verwerk de configuratiestroom voor Goboony."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Geef de optiestroom."""
        return GoboonyOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Verwerk de eerste stap."""
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_LISTING_ID])
            self._abort_if_unique_id_configured()

            api = GoboonyApi(
                email=user_input[CONF_EMAIL],
                password=user_input[CONF_PASSWORD],
                listing_id=user_input[CONF_LISTING_ID],
            )
            try:
                await self.hass.async_add_executor_job(api.validate)
            except GoboonyAuthError:
                errors["base"] = "invalid_auth"
            except GoboonyListingNotFound:
                errors["base"] = "listing_not_found"
            except Exception:
                _LOGGER.exception("Unexpected error during login")
                errors["base"] = "cannot_connect"
            finally:
                await self.hass.async_add_executor_job(api.close)
            if not errors:
                return self.async_create_entry(
                    title=f"Goboony {user_input[CONF_LISTING_ID]}",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Verwerk opnieuw aanmelden als de gegevens niet meer werken."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Verwerk de bevestiging van het opnieuw aanmelden."""
        errors: dict[str, str] = {}

        if user_input is not None:
            entry = self.hass.config_entries.async_get_entry(
                self.context["entry_id"]
            )
            if entry is None:
                return self.async_abort(reason="reauth_failed")

            api = GoboonyApi(
                email=user_input[CONF_EMAIL],
                password=user_input[CONF_PASSWORD],
                listing_id=entry.data[CONF_LISTING_ID],
            )
            try:
                await self.hass.async_add_executor_job(api.login)
            except GoboonyAuthError:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected error during reauth")
                errors["base"] = "cannot_connect"
            finally:
                await self.hass.async_add_executor_job(api.close)
            if not errors:
                return self.async_update_reload_and_abort(
                    entry,
                    data={**entry.data, **user_input},
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EMAIL): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )


class GoboonyOptionsFlow(OptionsFlow):
    """Verwerk de opties voor Goboony."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Verwerk de stap met opties."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL // 60
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=current_interval,
                    ): vol.All(vol.Coerce(int), vol.Range(min=15, max=1440)),
                }
            ),
        )
