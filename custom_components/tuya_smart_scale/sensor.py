"""Sensor platform for Tuya Smart Scale integration."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
import datetime

from .const import DOMAIN, SENSOR_TYPES, CONF_DEVICE_ID

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
    def device_info(self):
        """Return device information for device registry."""
        device_identification = self.coordinator.device_info or {}
        
        return {
            "identifiers": {(DOMAIN, self.device_id)},
            "name": device_identification.get("custom_name") or device_identification.get("name") or "Tuya Smart Scale",
            "manufacturer": "Tuya",
            "model": device_identification.get("model") or "Smart Scale",
            "sw_version": None,
            "configuration_url": "https://iot.tuya.com/",
        }
    
    @property
    def native_value(self):
        """Return the state of the sensor."""
        user_data = self.coordinator.data.get(self.user_id)
        if not user_data:
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
        
        # Convert timestamp to datetime for timestamp sensors
        if self.entity_type == "create_time" and value is not None:
            try:
                # Convert milliseconds since epoch to datetime
                return datetime.datetime.fromtimestamp(int(value)/1000, datetime.timezone.utc)
            except (ValueError, TypeError):
                return None
        return value

    @property
    def extra_state_attributes(self):
        """Return additional state attributes."""
        attributes = {}
        
        # Add device identification info as attributes
        device_identification = self.coordinator.device_info or {}
        if device_identification.get("product_name"):
            attributes["product_name"] = device_identification["product_name"]
        if device_identification.get("model"):
            attributes["device_model"] = device_identification["model"]
        
        # Add user info
        user_data = self.coordinator.data.get(self.user_id)
        if user_data:
            if user_data.get("nickname"):
                attributes["user_nickname"] = user_data["nickname"]
            attributes["user_id"] = self.user_id
            attributes["device_id"] = self.device_id
            
        return attributes

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Tuya Smart Scale sensors for all users based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Ensure device info is fetched before creating sensors
    await coordinator.get_device_info()
    
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