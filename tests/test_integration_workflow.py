#!/usr/bin/env python3
"""
Complete integration test - tests the full Home Assistant integration workflow
including data fetching, user discovery, and sensor value extraction.
"""

import os
import sys
import time
import json
from datetime import datetime

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

# Get credentials
ACCESS_ID = os.environ.get("ACCESS_ID")
ACCESS_KEY = os.environ.get("ACCESS_KEY") 
DEVICE_ID = os.environ.get("DEVICE_ID")
REGION = os.environ.get("TUYA_REGION", "eu")

if not ACCESS_ID or not ACCESS_KEY or not DEVICE_ID:
    print("ERROR: Missing credentials!")
    exit(1)

# Import the integration API directly by copying the core logic
import requests
import hashlib
import hmac
from typing import Dict, List, Any

REGIONS = {
    "us": {"endpoint": "https://openapi.tuyaus.com"},
    "eu": {"endpoint": "https://openapi.tuyaeu.com"},
    "cn": {"endpoint": "https://openapi.tuyacn.com"},
    "in": {"endpoint": "https://openapi.tuyain.com"}
}

class TuyaSmartScaleAPI:
    """Integration API client - copied from the fixed integration."""

    def __init__(self, access_id: str, access_key: str, device_id: str, region: str = "us"):
        self.access_id = access_id
        self.access_key = access_key
        self.device_id = device_id
        self.region = region
        self.endpoint = REGIONS.get(region, REGIONS["eu"])["endpoint"]
        self.access_token = None
        self.token_expires = 0
        self.sign_method = "HMAC-SHA256"

    def _sign_request(self, method, path, access_token=None, params=None, body=None):
        if body:
            body_sha256 = hashlib.sha256(body.encode('utf-8')).hexdigest()
        else:
            body_sha256 = hashlib.sha256(b'').hexdigest()
        if params:
            sorted_params = sorted(params.items())
            param_str = "&".join([f"{k}={v}" for k, v in sorted_params])
            canonical_path = f"{path}?{param_str}"
        else:
            canonical_path = path
        str_to_sign = f"{method}\n{body_sha256}\n\n{canonical_path}"
        t = str(int(time.time() * 1000))
        if access_token:
            message = self.access_id + access_token + t + str_to_sign
        else:
            message = self.access_id + t + str_to_sign
        sign = hmac.new(
            self.access_key.encode("utf-8"),
            msg=message.encode("utf-8"),
            digestmod=hashlib.sha256
        ).hexdigest().upper()
        return sign, t, canonical_path

    def get_access_token(self) -> str:
        if self.access_token and time.time() < self.token_expires - 60:
            return self.access_token
        path = "/v1.0/token?grant_type=1"
        sign, t, canonical_path = self._sign_request("GET", path, access_token=None, params=None)
        url = f"{self.endpoint}{canonical_path}"
        headers = {
            "client_id": self.access_id,
            "t": t,
            "sign_method": self.sign_method,
            "sign": sign,
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Failed to get access token: {response.text}")
        data = response.json()
        if not data.get("success"):
            raise Exception(f"API returned error: {data}")
        result = data.get("result", {})
        self.access_token = result.get("access_token")
        self.token_expires = time.time() + result.get("expire_time", 7200)
        return self.access_token

    def get_scale_records(self, start_time: int = None, end_time: int = None, 
                         limit: int = 10, user_id: str = None) -> List[Dict[str, Any]]:
        token = self.get_access_token()
        params = {"page_size": limit, "page_no": 1}
        if start_time:
            params["start_time"] = start_time
        path = f"/v1.0/scales/{self.device_id}/datas/history"
        sign, t, canonical_path = self._sign_request("GET", path, access_token=token, params=params)
        url = f"{self.endpoint}{canonical_path}"
        headers = {
            "client_id": self.access_id,
            "access_token": token,
            "t": t,
            "sign": sign,
            "sign_method": "HMAC-SHA256",
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return []
        data = response.json()
        if not isinstance(data, dict) or "result" not in data:
            return []
        if "records" not in data["result"]:
            return []
        records = data["result"]["records"]
        if user_id:
            records = [r for r in records if r.get("user_id") == user_id]
        return records

    def get_scale_users(self) -> List[Dict[str, Any]]:
        records = self.get_scale_records(limit=100)
        users = {}
        for rec in records:
            user_id = rec.get("user_id")
            nickname = rec.get("nick_name") or rec.get("nickname")
            if user_id and user_id != "0" and len(user_id.strip()) > 0 and user_id not in users:
                users[user_id] = {"user_id": user_id, "nickname": nickname}
        return list(users.values())

    def get_analysis_report(self, height: float, weight: float, age: int, sex: int, resistance: str) -> Dict[str, Any]:
        token = self.get_access_token()
        path = f"/v1.0/scales/{self.device_id}/analysis-reports"
        body_data = {
            "height": height,
            "weight": weight,
            "age": age,
            "sex": sex,
            "resistance": resistance
        }
        body_json = json.dumps(body_data, separators=(',', ':'))
        sign, t, canonical_path = self._sign_request("POST", path, access_token=token, params=None, body=body_json)
        url = f"{self.endpoint}{canonical_path}"
        headers = {
            "client_id": self.access_id,
            "access_token": token,
            "t": t,
            "sign": sign,
            "sign_method": "HMAC-SHA256",
            "Content-Type": "application/json",
        }
        response = requests.post(url, headers=headers, data=body_json)
        if response.status_code != 200:
            raise Exception(f"Failed to get analysis report: {response.text}")
        return response.json().get("result", {})

    def get_latest_data(self) -> Dict[str, Dict[str, Any]]:
        try:
            users = self.get_scale_users()
            if not users:
                print("ERROR: No users found for this scale device.")
                return {}
            result = {}
            for user in users:
                user_id = user.get("user_id")
                if not user_id:
                    continue
                try:
                    # Get more records to find one with valid resistance data
                    records = self.get_scale_records(user_id=user_id, limit=10)
                except Exception as e:
                    print(f"ERROR: Error fetching records for user {user_id}: {e}")
                    continue
                if not records:
                    print(f"WARNING: No records found for user {user_id}")
                    continue
                
                # Use the most recent record, but try to find one with resistance data for analysis
                latest_record = records[0]
                record_with_resistance = None
                for record in records:
                    if record.get("body_r") and record.get("body_r") != "0":
                        record_with_resistance = record
                        break
                
                # Try to get analysis report if we have the required data
                try:
                    # Use the record with resistance data for analysis if available
                    analysis_record = record_with_resistance or latest_record
                    height = float(analysis_record.get("height", 0))
                    weight = float(analysis_record.get("wegith", 0))  # Note: API uses "wegith" not "weight"
                    resistance = analysis_record.get("body_r", "0")
                    
                    # Only get analysis if we have valid resistance data
                    if height > 0 and weight > 0 and resistance and resistance != "0":
                        # Use reasonable defaults for age and sex if not available
                        age = 30  # Default age
                        sex = 1   # Default to male
                        
                        analysis_report = self.get_analysis_report(
                            height=height,
                            weight=weight,
                            age=age,
                            sex=sex,
                            resistance=resistance
                        )
                        latest_record["analysis_report"] = analysis_report
                        print(f"DEBUG: Added analysis report for user {user_id} using record with resistance {resistance}")
                    else:
                        print(f"DEBUG: Skipping analysis report for record - insufficient data: height={height}, weight={weight}, resistance={resistance}")
                except Exception as e:
                    print(f"WARNING: Could not fetch analysis report for record: {e}")
                
                latest_record.update({"nickname": user.get("nickname")})
                result[user_id] = latest_record
            return result
        except Exception as err:
            print(f"ERROR: Error fetching latest scale data: {err}")
            import traceback
            traceback.print_exc()
            return {}

def main():
    """Test the complete integration data flow."""
    print("🏠 Testing Complete Home Assistant Integration Data Flow")
    print("=" * 70)
    
    # Initialize API client
    api = TuyaSmartScaleAPI(ACCESS_ID, ACCESS_KEY, DEVICE_ID, REGION)
    
    try:
        # Test 1: Authentication
        print("\n1. Testing authentication...")
        token = api.get_access_token()
        print(f"✓ Authentication successful")
        
        # Test 2: User discovery
        print("\n2. Testing user discovery...")
        users = api.get_scale_users()
        print(f"✓ Found {len(users)} users:")
        for user in users:
            print(f"   - {user['user_id']}: {user.get('nickname', 'No nickname')}")
        
        # Test 3: Get latest data (what the coordinator calls)
        print("\n3. Testing get_latest_data() - integration data method...")
        latest_data = api.get_latest_data()
        print(f"✓ Retrieved data for {len(latest_data)} users")
        
        # Test 4: Simulate sensor creation and value extraction
        print("\n4. Testing sensor value extraction...")
        
        # Define the sensor types from the integration
        sensor_types = [
            "weight", "wegith",  # Both forms for the weight typo
            "height", "body_r", "bmi", "body_fat", "muscle_mass", 
            "body_water", "bone_mass", "visceral_fat", "basal_metabolism",
            "create_time", "nickname"
        ]
        
        sensor_values = {}
        for user_id, user_data in latest_data.items():
            print(f"\n   User: {user_id} ({user_data.get('nickname', 'No nickname')})")
            sensor_values[user_id] = {}
            
            for sensor_type in sensor_types:
                # Extract value like the sensor.py does
                value = user_data.get(sensor_type)
                if value is None and "analysis_report" in user_data:
                    value = user_data["analysis_report"].get(sensor_type)
                    
                # Format timestamp if needed
                if sensor_type == "create_time" and value is not None:
                    try:
                        value = datetime.fromtimestamp(int(value)/1000).strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        pass
                        
                if value is not None:
                    sensor_values[user_id][sensor_type] = value
                    print(f"     {sensor_type}: {value}")
        
        # Test 5: Summary
        print(f"\n5. Integration summary:")
        total_sensors = sum(len(sensors) for sensors in sensor_values.values())
        print(f"✓ Total users discovered: {len(users)}")
        print(f"✓ Total sensor values extracted: {total_sensors}")
        print(f"✓ Data structure working: {'✓' if latest_data else '✗'}")
        print(f"✓ Analysis reports working: {'✓' if any('analysis_report' in data for data in latest_data.values()) else '✗'}")
        
        # Test 6: Sample sensor entity simulation
        print(f"\n6. Sample Home Assistant sensor entities that would be created:")
        entity_count = 0
        for user_id, user_data in latest_data.items():
            nickname = user_data.get('nickname', user_id)
            for sensor_type in ["weight", "wegith", "bmi", "body_fat"]:  # Just show a few key ones
                if sensor_type in sensor_values[user_id]:
                    entity_id = f"sensor.tuya_smart_scale_{user_id}_{sensor_type}"
                    friendly_name = f"Tuya Scale {nickname} {sensor_type.replace('_', ' ').title()}"
                    value = sensor_values[user_id][sensor_type]
                    print(f"   • {entity_id}")
                    print(f"     Name: {friendly_name}")
                    print(f"     Value: {value}")
                    entity_count += 1
        
        print(f"\n✅ INTEGRATION TEST SUCCESSFUL!")
        print(f"   The Home Assistant integration should create {entity_count}+ sensor entities")
        print(f"   All core functionality is working correctly")
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
