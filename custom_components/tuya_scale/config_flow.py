from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_DEVICE_ID
from .tuya_connector import TuyaOpenAPI

from .const import (
    DOMAIN,
    CONF_API_ENDPOINT,
    CONF_ACCESS_ID,
    CONF_ACCESS_KEY,
)

class TuyaScaleConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            try:
                # Test the connection
                api = TuyaOpenAPI(
                    user_input[CONF_API_ENDPOINT],
                    user_input[CONF_ACCESS_ID],
                    user_input[CONF_ACCESS_KEY]
                )
                api.connect()

                return self.async_create_entry(
                    title=f"Tuya Scale {user_input[CONF_DEVICE_ID]}",
                    data=user_input,
                )
            except Exception as e:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_API_ENDPOINT): str,
                vol.Required(CONF_ACCESS_ID): str,
                vol.Required(CONF_ACCESS_KEY): str,
                vol.Required(CONF_DEVICE_ID): str,
            }),
            errors=errors,
        ) 