"""The Tuya Scale sensor platform."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
import pytz

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import (
    DOMAIN,
    SENSOR_WEIGHT,
    SENSOR_HEIGHT,
    SENSOR_BODY_FAT,
    SENSOR_BMI,
    SENSOR_BODY_WATER,
    SENSOR_SKELETAL_MUSCLE,
    SENSOR_MUSCLE_MASS,
    SENSOR_BMR,
    SENSOR_PROTEIN_RATE,
    SENSOR_SUBCUTANEOUS_FAT,
    SENSOR_VISCERAL_FAT,
    SENSOR_BODY_AGE,
    SENSOR_BODY_TYPE,
    SENSOR_BODY_SCORE,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Tuya Scale sensors."""
    coordinator = TuyaScaleCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    sensors = [
        TuyaScaleSensor(coordinator, SENSOR_WEIGHT, "Weight", "kg", SensorDeviceClass.WEIGHT),
        TuyaScaleSensor(coordinator, SENSOR_HEIGHT, "Height", "cm", SensorDeviceClass.DISTANCE),
        TuyaScaleSensor(coordinator, SENSOR_BODY_FAT, "Body Fat", "%"),
        TuyaScaleSensor(coordinator, SENSOR_BMI, "BMI", "kg/m²"),
        TuyaScaleSensor(coordinator, SENSOR_BODY_WATER, "Body Water", "%"),
        TuyaScaleSensor(coordinator, SENSOR_SKELETAL_MUSCLE, "Skeletal Muscle", "%"),
        TuyaScaleSensor(coordinator, SENSOR_MUSCLE_MASS, "Muscle Mass", "kg"),
        TuyaScaleSensor(coordinator, SENSOR_BMR, "BMR", "kcal"),
        TuyaScaleSensor(coordinator, SENSOR_PROTEIN_RATE, "Protein Rate", "%"),
        TuyaScaleSensor(coordinator, SENSOR_SUBCUTANEOUS_FAT, "Subcutaneous Fat", "%"),
        TuyaScaleSensor(coordinator, SENSOR_VISCERAL_FAT, "Visceral Fat", "%"),
        TuyaScaleSensor(coordinator, SENSOR_BODY_AGE, "Body Age", "years"),
        TuyaScaleSensor(coordinator, SENSOR_BODY_TYPE, "Body Type", None),
        TuyaScaleSensor(coordinator, SENSOR_BODY_SCORE, "Body Score", None),
    ]

    async_add_entities(sensors)

class TuyaScaleCoordinator(DataUpdateCoordinator):
    """Tuya Scale data coordinator."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Tuya Scale",
            update_interval=timedelta(minutes=5),
        )
        self.api = hass.data[DOMAIN][entry.entry_id]["api"]
        self.device_id = hass.data[DOMAIN][entry.entry_id]["device_id"]

    async def _async_update_data(self):
        """Fetch the latest data from the Tuya API."""
        try:
            # Get the latest record
            response = self.api.get(
                f"/v1.0/scales/{self.device_id}/datas/history",
                params={"page_no": 1, "page_size": 1}
            )
            
            if response.get("success") and response["result"]["records"]:
                return response["result"]["records"][0]
            return None
        except Exception as err:
            _LOGGER.error("Error fetching Tuya Scale data: %s", err)
            return None

class TuyaScaleSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Tuya Scale sensor."""

    def __init__(
        self,
        coordinator: TuyaScaleCoordinator,
        sensor_type: str,
        name: str,
        unit: str | None,
        device_class: SensorDeviceClass | None = None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._attr_name = f"Tuya Scale {name}"
        self._attr_unique_id = f"{coordinator.device_id}_{sensor_type}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        data = self.coordinator.data
        if self._sensor_type == SENSOR_WEIGHT:
            return data.get("weight")
        elif self._sensor_type == SENSOR_HEIGHT:
            return data.get("height")
        elif self._sensor_type == SENSOR_BODY_FAT:
            return data.get("body_fat")
        elif self._sensor_type == SENSOR_BMI:
            return data.get("bmi")
        elif self._sensor_type == SENSOR_BODY_WATER:
            return data.get("body_water")
        elif self._sensor_type == SENSOR_SKELETAL_MUSCLE:
            return data.get("skeletal_muscle")
        elif self._sensor_type == SENSOR_MUSCLE_MASS:
            return data.get("muscle_mass")
        elif self._sensor_type == SENSOR_BMR:
            return data.get("bmr")
        elif self._sensor_type == SENSOR_PROTEIN_RATE:
            return data.get("protein_rate")
        elif self._sensor_type == SENSOR_SUBCUTANEOUS_FAT:
            return data.get("subcutaneous_fat")
        elif self._sensor_type == SENSOR_VISCERAL_FAT:
            return data.get("visceral_fat")
        elif self._sensor_type == SENSOR_BODY_AGE:
            return data.get("body_age")
        elif self._sensor_type == SENSOR_BODY_TYPE:
            return data.get("body_type")
        elif self._sensor_type == SENSOR_BODY_SCORE:
            return data.get("body_score")
        return None 