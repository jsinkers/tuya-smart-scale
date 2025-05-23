"""The Tuya Scale integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .tuya_connector import TuyaOpenAPI

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=5)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Tuya Scale from a config entry."""
    api = TuyaOpenAPI(
        endpoint=entry.data["endpoint"],
        access_id=entry.data["access_id"],
        access_secret=entry.data["access_secret"],
    )

    coordinator = TuyaScaleCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault("tuya_scale", {})
    hass.data["tuya_scale"][entry.entry_id] = coordinator

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )

    return True

class TuyaScaleCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(self, hass: HomeAssistant, api: TuyaOpenAPI) -> None:
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Tuya Scale",
            update_interval=SCAN_INTERVAL,
        )
        self.api = api

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        try:
            await self.api.connect()
            response = await self.api.get("/v1.0/devices/status", {"device_ids": "YOUR_DEVICE_ID"})
            if not response or not response.get("success"):
                raise UpdateFailed("Failed to fetch data from Tuya API")
            return response.get("result", [])
        except Exception as err:
            raise UpdateFailed(f"Error communicating with Tuya API: {err}")

class TuyaScaleSensor:
    """Representation of a Tuya Scale sensor."""

    def __init__(self, coordinator: TuyaScaleCoordinator, name: str, device_id: str) -> None:
        """Initialize the sensor."""
        self.coordinator = coordinator
        self._name = name
        self._device_id = device_id
        self._state = None

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        for device in self.coordinator.data:
            if device.get("id") == self._device_id:
                for status in device.get("status", []):
                    if status.get("code") == "weight":
                        return status.get("value")
        return None

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement."""
        return "kg"

    @property
    def device_class(self) -> str:
        """Return the device class."""
        return "weight" 