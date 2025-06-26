"""Data coordinator for Tuya Smart Scale integration."""
from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, UPDATE_INTERVAL
from .api import TuyaSmartScaleAPI

_LOGGER = logging.getLogger(__name__)

class TuyaSmartScaleDataCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the Tuya Smart Scale API."""

    def __init__(self, hass: HomeAssistant, api_client: TuyaSmartScaleAPI):
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.api = api_client
        self.birthdate = api_client.birthdate  # Store birthdate for physical age calculation
        self.data = {}
    
    @property
    def device_ids(self):
        """Get available device IDs (user IDs in this case)."""
        if not self.data:
            return []
        return list(self.data.keys())

    async def _async_update_data(self):
        """Fetch data from Tuya API."""
        try:
            return await self.hass.async_add_executor_job(
                self.api.get_latest_data  # Fixed: should be self.api, not self.api_client
            )
        except Exception as err:
            raise UpdateFailed(f"Error communicating with Tuya API: {err}")