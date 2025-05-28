#!/usr/bin/env python3
"""Test the updated integration API."""

import sys
import os
sys.path.append('/Users/james/development/tuya_smart_scale')

# Load credentials
from dotenv import load_dotenv
load_dotenv()

ACCESS_ID = os.environ.get("ACCESS_ID")
ACCESS_KEY = os.environ.get("ACCESS_KEY") 
DEVICE_ID = os.environ.get("DEVICE_ID")
REGION = os.environ.get("TUYA_REGION", "eu")

# Import the updated API class
from custom_components.tuya_smart_scale.api import TuyaSmartScaleAPI

def test_updated_api():
    """Test the updated integration API."""
    print(f"Testing updated integration API with device {DEVICE_ID} in region {REGION}")
    
    # Create API client
    api = TuyaSmartScaleAPI(
        access_id=ACCESS_ID,
        access_key=ACCESS_KEY,
        device_id=DEVICE_ID,
        region=REGION
    )
    
    # Test getting access token
    print("\n1. Testing access token...")
    try:
        token = api.get_access_token()
        print(f"✓ Got access token: {token[:20]}...")
    except Exception as e:
        print(f"✗ Failed to get access token: {e}")
        return False
    
    # Test getting scale records
    print("\n2. Testing scale records...")
    try:
        records = api.get_scale_records(limit=3)
        print(f"✓ Got {len(records)} scale records")
        if records:
            print(f"  First record keys: {list(records[0].keys())}")
            print(f"  First record sample data:")
            for key, value in list(records[0].items())[:5]:  # Show first 5 fields
                print(f"    {key}: {value}")
    except Exception as e:
        print(f"✗ Failed to get scale records: {e}")
        return False
    
    # Test getting device info
    print("\n3. Testing device info...")
    try:
        device_info = api.get_device_info()
        print(f"✓ Got device info: {device_info.get('name', 'Unknown')} ({device_info.get('product_name', 'Unknown product')})")
    except Exception as e:
        print(f"✗ Failed to get device info: {e}")
        return False
    
    # Test analysis reports with real data
    print("\n4. Testing analysis reports with real resistance value...")
    try:
        # Use a real resistance value from the records
        if records and records[0].get("body_r") and records[0]["body_r"] != "0":
            real_resistance = records[0]["body_r"]
            real_height = float(records[0].get("height", 180))
            real_weight = float(records[0].get("wegith", 75))
            
            print(f"  Using real data: height={real_height}cm, weight={real_weight}kg, resistance={real_resistance}Ω")
            
            analysis = api.get_analysis_report(
                height=real_height,
                weight=real_weight,
                age=30,  # Default age
                sex=1,   # Default to male
                resistance=real_resistance
            )
            print(f"✓ Got analysis report with keys: {list(analysis.keys())}")
            if analysis:
                print("  Analysis results:")
                for key, value in analysis.items():
                    print(f"    {key}: {value}")
        else:
            print("  No records with resistance data found for testing")
    except Exception as e:
        print(f"✗ Failed to get analysis report: {e}")
    
    # Test get_latest_data (this should include analysis reports)
    print("\n5. Testing get_latest_data (should include analysis reports)...")
    try:
        latest_data = api.get_latest_data()
        print(f"✓ Got latest data for {len(latest_data)} users")
        for user_id, user_data in latest_data.items():
            print(f"  User {user_id}: {user_data.get('nickname', 'No nickname')}")
            if "analysis_report" in user_data:
                print(f"    ✓ Has analysis report with {len(user_data['analysis_report'])} metrics")
            else:
                print(f"    ✗ No analysis report (probably no resistance data)")
    except Exception as e:
        print(f"✗ Failed to get latest data: {e}")
        return False
    
    print("\n✅ All integration API tests completed successfully!")
    return True

if __name__ == "__main__":
    test_updated_api()
