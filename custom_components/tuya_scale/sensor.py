"""Sensor platform for Tuya Smart Scale integration."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
import datetime

from .const import DOMAIN, SENSOR_TYPES, ALL_SENSOR_TYPES

class TuyaSmartScaleSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Tuya Smart Scale sensor for a specific user."""
    
    def __init__(self, coordinator, device_id, user_id, nickname, entity_type):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.device_id = device_id
        self.user_id = user_id
        self.nickname = nickname
        self.entity_type = entity_type
        self._attr_unique_id = f"{device_id}_{user_id}_{entity_type}"
        self._attr_name = f"Tuya Scale {nickname or user_id} {entity_type.replace('_', ' ').title()}"
        
        # Find the canonical sensor type for this entity
        canonical_type = entity_type
        for sensor_type, config in SENSOR_TYPES.items():
            if entity_type == sensor_type or entity_type in config["aliases"]:
                canonical_type = sensor_type
                break
        
        # Configure sensor properties based on entity type
        if canonical_type in SENSOR_TYPES:
            config = SENSOR_TYPES[canonical_type]
            self._attr_native_unit_of_measurement = config["unit"]
            self._attr_device_class = config["device_class"]
            self._attr_icon = config["icon"]
    
    @property
    def native_value(self):
        """Return the state of the sensor."""
        user_data = self.coordinator.data.get(self.user_id)
        if not user_data:
            return None
        # Check if the entity_type is in the top-level user_data
        value = user_data.get(self.entity_type)
        # If not, check if it's in the analysis_report
        if value is None and "analysis_report" in user_data:
            value = user_data["analysis_report"].get(self.entity_type)
        # Convert timestamp to datetime for timestamp sensors
        if self.entity_type == "create_time" and value is not None:
            try:
                # Convert milliseconds since epoch to datetime
                return datetime.datetime.fromtimestamp(int(value)/1000, datetime.timezone.utc)
            except (ValueError, TypeError):
                return None
        return value

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Tuya Smart Scale sensors for all users based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    # coordinator.data is a dict: {user_id: {measurement data, 'nickname': ...}}
    for user_id, user_data in coordinator.data.items():
        nickname = user_data.get("nickname")
        for sensor_type in ALL_SENSOR_TYPES:
            entities.append(TuyaSmartScaleSensor(
                coordinator,
                entry.data["device_id"],
                user_id,
                nickname,
                sensor_type
            ))
    async_add_entities(entities)