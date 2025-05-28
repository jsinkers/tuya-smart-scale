#!/usr/bin/env python3
"""Test the get_latest_data method to see if it reproduces the 501 error."""

import os
import sys
import logging

# Set up logging to see debug messages
logging.basicConfig(level=logging.DEBUG)

# Load credentials from .env file
try:
    from dotenv import load_dotenv
    load_dotenv(override=True, verbose=False)
except:
    pass

# Add the custom_components path to import the API
sys.path.insert(0, '/Users/james/development/tuya_smart_scale')
from custom_components.tuya_smart_scale.api import TuyaSmartScaleAPI

# Use .env credentials
ACCESS_ID = os.environ.get("ACCESS_ID")
ACCESS_KEY = os.environ.get("ACCESS_KEY") 
DEVICE_ID = os.environ.get("DEVICE_ID")
REGION = os.environ.get("TUYA_REGION", "eu")

if not ACCESS_ID or not ACCESS_KEY or not DEVICE_ID:
    print("ERROR: Missing credentials in .env file!")
    exit(1)

print(f"Testing get_latest_data with integration API for device {DEVICE_ID}")

# Create API client using the integration class
api = TuyaSmartScaleAPI(
    access_id=ACCESS_ID,
    access_key=ACCESS_KEY,
    device_id=DEVICE_ID,
    region=REGION
)

try:
    print("\n1. Testing access token...")
    token = api.get_access_token()
    print(f"✓ Got access token: {token[:20]}...")
    
    print("\n2. Testing get_scale_users...")
    users = api.get_scale_users()
    print(f"✓ Found {len(users)} users: {users}")
    
    print("\n3. Testing get_latest_data...")
    latest_data = api.get_latest_data()
    print(f"✓ Got latest data for {len(latest_data)} users")
    for user_id, data in latest_data.items():
        print(f"  User {user_id}: {list(data.keys())}")
        
except Exception as e:
    import traceback
    print(f"✗ Error: {e}")
    print(f"Traceback:\n{traceback.format_exc()}")
