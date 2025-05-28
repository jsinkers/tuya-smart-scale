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
        self._device_info = None
    
    @property
    def device_ids(self):
        """Get available device IDs (user IDs in this case)."""
        if not self.data:
            return []
        return list(self.data.keys())

    @property
    def device_info(self):
        """Get cached device information."""
        return self._device_info

    async def get_device_info(self):
        """Get device identification information."""
        if self._device_info is None:
            try:
                self._device_info = await self.hass.async_add_executor_job(
                    self.api_client.get_device_identification
                )
                _LOGGER.debug(f"Fetched device info: {self._device_info}")
            except Exception as err:
                _LOGGER.warning(f"Failed to fetch device info: {err}")
                # Use fallback device info
                self._device_info = {
                    "name": "Tuya Smart Scale",
                    "model": "Unknown",
                    "product_name": "Smart Scale",
                    "custom_name": "Smart Scale"
                }
        return self._device_info

    async def _async_update_data(self):
        """Fetch data from Tuya API."""
        try:
            return await self.hass.async_add_executor_job(
                self.api_client.get_latest_data
            )
        except Exception as err:
            raise UpdateFailed(f"Error communicating with Tuya API: {err}")