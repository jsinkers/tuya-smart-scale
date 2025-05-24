"""Data coordinator for Tuya Smart Scale integration."""
from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

class TuyaSmartScaleDataCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Tuya smart scale data."""

    def __init__(self, hass: HomeAssistant, api_client):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.api_client = api_client
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
                self.api_client.get_latest_data
            )
        except Exception as err:
            raise UpdateFailed(f"Error communicating with Tuya API: {err}")