"""Sensor platform for Tuya Smart Scale integration."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
import datetime

from .const import DOMAIN, SENSOR_TYPES, CONF_DEVICE_ID, SENSOR_DISPLAY_NAMES
from .utils import calculate_age_from_birthdate, calculate_age_from_birthdate

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
        
        # Use display name if available, otherwise use title case conversion
        display_name = SENSOR_DISPLAY_NAMES.get(entity_type, entity_type.replace('_', ' ').title())
        self._attr_name = f"{display_name} ({nickname or user_id})"
        
        # Find the canonical sensor type for this entity type
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
        
        # Handle special calculated sensors
        if self.entity_type == "physical_age":
            # Get birthdate from coordinator's config
            birthdate_str = getattr(self.coordinator, 'birthdate', None)
            if birthdate_str:
                return calculate_age_from_birthdate(birthdate_str)
            return None
        
        # Get the sensor config for this entity type
        config = SENSOR_TYPES.get(self.entity_type, {})
        
        # Check for value under the canonical name first
        value = user_data.get(self.entity_type)
        
        # If not found, check aliases
        if value is None:
            for alias in config.get("aliases", []):
                value = user_data.get(alias)
                if value is not None:
                    break
        
        # If still not found, check in analysis_report
        if value is None and "analysis_report" in user_data:
            value = user_data["analysis_report"].get(self.entity_type)
            # Also check aliases in analysis_report
            if value is None:
                for alias in config.get("aliases", []):
                    value = user_data["analysis_report"].get(alias)
                    if value is not None:
                        break
        
        # Handle special value conversions
        if value is not None:
            # Convert body_type integer to readable text
            if self.entity_type == "body_type":
                body_type_map = {
                    0: "Underweight",
                    1: "Normal", 
                    2: "Overweight",
                    3: "Obese",
                    4: "Severely Obese"
                }
                try:
                    return body_type_map.get(int(value), f"Unknown ({value})")
                except (ValueError, TypeError):
                    return value
            
            # Convert timestamp to datetime for timestamp sensors
            elif self.entity_type == "create_time":
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
        # Only create sensors for the canonical sensor types, not aliases
        for sensor_type in SENSOR_TYPES.keys():
            entities.append(TuyaSmartScaleSensor(
                coordinator,
                entry.data[CONF_DEVICE_ID],
                user_id,
                nickname,
                sensor_type
            ))
    async_add_entities(entities)