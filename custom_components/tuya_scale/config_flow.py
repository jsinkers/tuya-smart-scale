"""Config flow for Tuya Scale integration."""
from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .tuya_connector.tuya_connector.openapi import TuyaOpenAPI

_LOGGER = logging.getLogger(__name__)

DOMAIN = "tuya_scale"

class TuyaScaleConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tuya Scale."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                api = TuyaOpenAPI(
                    endpoint=user_input["endpoint"],
                    access_id=user_input["access_id"],
                    access_secret=user_input["access_secret"],
                )
                await api.connect()
                return self.async_create_entry(
                    title="Tuya Scale",
                    data=user_input,
                )
            except Exception as err:
                _LOGGER.error("Failed to connect to Tuya API: %s", err)
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("endpoint"): str,
                    vol.Required("access_id"): str,
                    vol.Required("access_secret"): str,
                }
            ),
            errors=errors,
        ) 