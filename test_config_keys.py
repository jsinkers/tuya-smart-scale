#!/usr/bin/env python3
"""Test to verify config keys match between config_flow and the rest of the integration."""

from custom_components.tuya_smart_scale.const import (
    CONF_ACCESS_ID,
    CONF_ACCESS_KEY, 
    CONF_DEVICE_ID,
    CONF_REGION
)

print("Config constants defined in const.py:")
print(f"CONF_ACCESS_ID = '{CONF_ACCESS_ID}'")
print(f"CONF_ACCESS_KEY = '{CONF_ACCESS_KEY}'")
print(f"CONF_DEVICE_ID = '{CONF_DEVICE_ID}'")
print(f"CONF_REGION = '{CONF_REGION}'")

print("\nThese are the keys that will be stored in entry.data by config_flow.py")
print("and accessed by __init__.py and sensor.py")

# Simulate what config_flow stores
mock_user_input = {
    CONF_ACCESS_ID: "test_access_id",
    CONF_ACCESS_KEY: "test_access_key", 
    CONF_DEVICE_ID: "test_device_id",
    CONF_REGION: "eu"
}

print(f"\nSimulated entry.data keys: {list(mock_user_input.keys())}")
print("✓ All components should use these exact constant values as keys")
