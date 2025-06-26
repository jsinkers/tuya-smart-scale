"""Constants for the Tuya Smart Scale integration."""

from homeassistant.components.sensor import SensorDeviceClass

API_ENDPOINT = "https://openapi.tuya.com/v1.0"
SMART_SCALE_DEVICE_TYPE = "smart_scale"
DEFAULT_UNIT_OF_MEASUREMENT = "kg"
CONF_ACCESS_ID = "Access ID"
CONF_ACCESS_KEY = "Access Key"
CONF_DEVICE_ID = "Device ID"
CONF_REGION = "Region"
CONF_AGE = "Age"
CONF_BIRTHDATE = "Date of Birth (YYYY-MM-DD)"
CONF_SEX = "Sex"

DOMAIN = "tuya_smart_scale"
UPDATE_INTERVAL = 60  # Update every 60 seconds

# Region definitions
REGIONS = {
    "us": {"name": "United States", "endpoint": "https://openapi.tuyaus.com"},
    "eu": {"name": "Europe", "endpoint": "https://openapi.tuyaeu.com"},
    "cn": {"name": "China", "endpoint": "https://openapi.tuyacn.com"},
    "in": {"name": "India", "endpoint": "https://openapi.tuyain.com"}
}

# Default region
DEFAULT_REGION = "eu"

# Default user profile values
DEFAULT_AGE = 34
DEFAULT_SEX = 1  # 1 = male, 2 = female (as expected by Tuya API)
DEFAULT_BIRTHDATE = "1990-01-01"  # Default birthdate as string in YYYY-MM-DD format

# Sex options for UI (maps display names to API values)
SEX_OPTIONS = {
    1: "Male",
    2: "Female"
}

# Display names for sensors (overrides default title case conversion)
SENSOR_DISPLAY_NAMES = {
    "ffm": "Fat-free Mass",
    "bmi": "BMI",
    "body_r": "Body Resistance",
    "user_id": "User ID",
    "device_id": "Device ID",
    "body_fat": "Body Fat",
    "body_age": "Body Age",
    "body_score": "Body Score",
    "body_type": "Body Type",
    "visceral_fat": "Visceral Fat"
}

# Sensor type definitions
SENSOR_TYPES = {
    "weight": {
        "unit": "kg",
        "device_class": SensorDeviceClass.WEIGHT,
        "icon": "mdi:weight-kilogram",
        "aliases": ["wegith"]  # Handle Tuya API typo
    },
    "body_fat": {
        "unit": "%",
        "device_class": None,
        "icon": "mdi:water-percent",
        "aliases": ["fat"]
    },
    "body_r": {
        "unit": "Ω",
        "device_class": None,
        "icon": "mdi:resistor",
        "aliases": []
    },
    "create_time": {
        "unit": None,
        "device_class": SensorDeviceClass.TIMESTAMP,
        "icon": "mdi:clock",
        "aliases": []
    },
    "height": {
        "unit": "cm",
        "device_class": None,
        "icon": "mdi:human-male-height",
        "aliases": []
    },
    "id": {
        "unit": None,
        "device_class": None,
        "icon": "mdi:identifier",
        "aliases": []
    },
    "device_id": {
        "unit": None,
        "device_class": None,
        "icon": "mdi:identifier",
        "aliases": []
    },
    "user_id": {
        "unit": None,
        "device_class": None,
        "icon": "mdi:identifier",
        "aliases": []
    },
    "nickname": {
        "unit": None,
        "device_class": None,
        "icon": "mdi:identifier",
        "aliases": []
    },
    "bmi": {
        "unit": None,
        "device_class": None,
        "icon": "mdi:human",
        "aliases": []
    },
    "body_age": {
        "unit": "years",
        "device_class": None,
        "icon": "mdi:calendar-account",
        "aliases": []
    },
    "body_score": {
        "unit": None,
        "device_class": None,
        "icon": "mdi:medal",
        "aliases": []
    },
    "body_type": {
        "unit": None,
        "device_class": None,
        "icon": "mdi:identifier",
        "aliases": []
    },
    "bones": {
        "unit": "kg",
        "device_class": None,
        "icon": "mdi:weight-lifter",
        "aliases": []
    },
    "ffm": {
        "unit": "kg",
        "device_class": None,
        "icon": "mdi:weight-lifter",
        "aliases": []
    },
    "muscle": {
        "unit": "kg",
        "device_class": None,
        "icon": "mdi:weight-lifter",
        "aliases": []
    },
    "protein": {
        "unit": "kg",
        "device_class": None,
        "icon": "mdi:weight-lifter",
        "aliases": []
    },
    "metabolism": {
        "unit": None,
        "device_class": None,
        "icon": "mdi:fire",
        "aliases": []
    },
    "visceral_fat": {
        "unit": "kg",
        "device_class": None,
        "icon": "mdi:stomach",
        "aliases": []
    },
    "water": {
        "unit": "%",
        "device_class": None,
        "icon": "mdi:water-percent",
        "aliases": []
    },
}

# Create a list of all sensor types including aliases for easy iteration
ALL_SENSOR_TYPES = []
for sensor_type, config in SENSOR_TYPES.items():
    ALL_SENSOR_TYPES.append(sensor_type)
    ALL_SENSOR_TYPES.extend(config["aliases"])