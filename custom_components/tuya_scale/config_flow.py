from homeassistant import config_entries
import voluptuous as vol
from .const import DOMAIN, CONF_ACCESS_ID, CONF_ACCESS_KEY, CONF_REGION, REGIONS, DEFAULT_REGION, CONF_DEVICE_ID

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            # Validate credentials here if needed
            return self.async_create_entry(title="Tuya Smart Scale", data=user_input)

        region_options = {code: data["name"] for code, data in REGIONS.items()}
        data_schema = vol.Schema({
            vol.Required(CONF_ACCESS_ID): str,  # Access ID
            vol.Required(CONF_ACCESS_KEY): str,  # Access Key
            vol.Required(CONF_REGION, default=DEFAULT_REGION): vol.In(region_options),
            vol.Required(CONF_DEVICE_ID): str,  # Device ID
        })
        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    async def async_step_import(self, import_info):
        return await self.async_step_user(import_info)