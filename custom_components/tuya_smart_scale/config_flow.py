from homeassistant import config_entries
import voluptuous as vol
from datetime import datetime, date
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.core import HomeAssistant
import logging

from .const import (
    DOMAIN,
    CONF_ACCESS_ID,
    CONF_ACCESS_KEY, 
    CONF_DEVICE_ID,
    CONF_REGION,
    CONF_BIRTHDATE,
    CONF_SEX,
    DEFAULT_SEX,
    DEFAULT_BIRTHDATE,
    SEX_OPTIONS,
    REGIONS
)
from .api import TuyaSmartScaleAPI

_LOGGER = logging.getLogger(__name__)

class TuyaSmartScaleConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tuya Smart Scale."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            # Validate the user input
            errors = {}
            
            try:
                # Test the connection with the provided credentials
                api = TuyaSmartScaleAPI(
                    access_id=user_input[CONF_ACCESS_ID],
                    access_key=user_input[CONF_ACCESS_KEY],
                    device_id=user_input[CONF_DEVICE_ID],
                    region=user_input[CONF_REGION],
                    birthdate=user_input.get(CONF_BIRTHDATE, DEFAULT_BIRTHDATE),
                    sex=user_input.get(CONF_SEX, DEFAULT_SEX)
                )
                
                # Try to get device info to validate connection
                device_info = await self.hass.async_add_executor_job(api.get_device_info)
                
                if device_info:
                    return self.async_create_entry(title="Tuya Smart Scale", data=user_input)
                else:
                    errors["base"] = "cannot_connect"
                    
            except ValueError:
                errors[CONF_BIRTHDATE] = "invalid_date"
            except Exception as ex:
                _LOGGER.error("Failed to connect to Tuya API: %s", ex)
                errors["base"] = "cannot_connect"
        
        # Define region options
        region_options = {code: data["name"] for code, data in REGIONS.items()}
        
        data_schema = vol.Schema({
            vol.Required(CONF_ACCESS_ID): str,
            vol.Required(CONF_ACCESS_KEY): str,
            vol.Required(CONF_DEVICE_ID): str,
            vol.Optional(CONF_REGION, default="eu"): vol.In(region_options),
            vol.Optional(CONF_BIRTHDATE, default=DEFAULT_BIRTHDATE): str,
            vol.Optional(CONF_SEX, default=DEFAULT_SEX): vol.In(SEX_OPTIONS),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_import(self, import_info):
        return await self.async_step_user(import_info)