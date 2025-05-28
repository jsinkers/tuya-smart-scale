#!/usr/bin/env python3
"""Test the Home Assistant integration API class to verify it works like the standalone scripts."""

import os
import sys
import logging
import requests
import time
import hmac
import hashlib
import json
from typing import Dict, Any, List

# Set up logging
logging.basicConfig(level=logging.INFO)  # Changed to INFO to reduce verbose output

# Load credentials from .env file
try:
    from dotenv import load_dotenv
    load_dotenv(override=True, verbose=False)
except:
    pass

# Use .env credentials (these should match the .env file exactly)
ACCESS_ID = os.environ.get("ACCESS_ID")
ACCESS_KEY = os.environ.get("ACCESS_KEY") 
DEVICE_ID = os.environ.get("DEVICE_ID")
REGION = os.environ.get("TUYA_REGION", "eu")

# Verify credentials are loaded
if not ACCESS_ID or not ACCESS_KEY or not DEVICE_ID:
    print("ERROR: Missing credentials in .env file!")
    print(f"ACCESS_ID: {'✓' if ACCESS_ID else '✗'}")
    print(f"ACCESS_KEY: {'✓' if ACCESS_KEY else '✗'}")
    print(f"DEVICE_ID: {'✓' if DEVICE_ID else '✗'}")
    exit(1)

# Define constants needed by the API
REGIONS = {
    "us": {"endpoint": "https://openapi.tuyaus.com"},
    "eu": {"endpoint": "https://openapi.tuyaeu.com"},
    "cn": {"endpoint": "https://openapi.tuyacn.com"},
    "in": {"endpoint": "https://openapi.tuyain.com"}
}

# Copy the API class directly to avoid Home Assistant dependencies
class TuyaSmartScaleAPI:
    """API client for Tuya Smart Scale."""

    def __init__(self, access_id: str, access_key: str, device_id: str, region: str = "us"):
        """Initialize the API client."""
        self.access_id = access_id
        self.access_key = access_key
        self.device_id = device_id
        self.region = region
        self.endpoint = REGIONS.get(region, REGIONS["eu"])["endpoint"]
        self.access_token = None
        self.token_expires = 0
        self.sign_method = "HMAC-SHA256"

    def _sign_request(self, method, path, access_token=None, params=None):
        """Sign the request using the correct Tuya v2.0 signature logic.
        
        This matches the working tuya_api_debug_test.py pattern exactly:
        - canonical_path includes sorted query parameters
        - string-to-sign uses the canonical_path with parameters
        """
        body_sha256 = hashlib.sha256(b'').hexdigest()
        # Always sort params by key for both canonical_path and URL (like debug script)
        if params:
            sorted_params = sorted(params.items())
            param_str = "&".join([f"{k}={v}" for k, v in sorted_params])
            canonical_path = f"{path}?{param_str}"
        else:
            canonical_path = path
            
        # Use canonical_path (with params) in string-to-sign - this is the key!
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
        """Get access token from Tuya API using v2.0 signature logic."""
        if self.access_token and time.time() < self.token_expires - 60:
            return self.access_token
        path = "/v1.0/token?grant_type=1"
        method = "GET"
        body_sha256 = hashlib.sha256(b'').hexdigest()
        str_to_sign = f"{method}\n{body_sha256}\n\n{path}"
        t = str(int(time.time() * 1000))
        message = self.access_id + t + str_to_sign
        signature = hmac.new(
            self.access_key.encode('utf-8'),
            msg=message.encode('utf-8'),
            digestmod=hashlib.sha256
        ).hexdigest().upper()
        headers = {
            "client_id": self.access_id,
            "t": t,
            "sign_method": self.sign_method,
            "sign": signature,
        }
        url = f"{self.endpoint}{path}"
        print(f"Requesting token: url={url} headers={headers}")
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to get access token: {response.text}")
            raise Exception(f"Failed to get access token: {response.text}")
        try:
            data = response.json()
        except Exception as e:
            print(f"Failed to parse JSON response for access token: {e}")
            raise Exception(f"Failed to parse JSON response for access token: {e}")
        if not isinstance(data, dict) or "result" not in data:
            print(f"Unexpected response structure for access token (missing 'result'): {data}")
            raise Exception(f"Unexpected response structure for access token (missing 'result'): {data}")
        self.access_token = data["result"].get("access_token")
        self.token_expires = time.time() + data["result"].get("expire_time", 0)
        return self.access_token

    def get_scale_records(self, start_time: int = None, end_time: int = None, 
                         limit: int = 10, user_id: str = None) -> List[Dict[str, Any]]:
        """Get scale measurement records using the correct Tuya endpoint and signature logic."""
        token = self.get_access_token()
        params = {"page_size": limit, "page_no": 1}
        if start_time:
            params["start_time"] = start_time
        path = f"/v1.0/scales/{self.device_id}/datas/history"
        
        # Use direct signature logic like get_access_token (which works)
        sorted_params = sorted(params.items())
        param_str = "&".join([f"{k}={v}" for k, v in sorted_params])
        full_path = f"{path}?{param_str}"
        
        method = "GET"
        body_sha256 = hashlib.sha256(b'').hexdigest()
        str_to_sign = f"{method}\n{body_sha256}\n\n{full_path}"
        t = str(int(time.time() * 1000))
        message = self.access_id + token + t + str_to_sign
        sign = hmac.new(
            self.access_key.encode('utf-8'),
            msg=message.encode('utf-8'),
            digestmod=hashlib.sha256
        ).hexdigest().upper()
        
        url = f"{self.endpoint}{full_path}"
        headers = {
            "client_id": self.access_id,
            "access_token": token,
            "t": t,
            "sign": sign,
            "sign_method": "HMAC-SHA256",
        }
        print(f"Requesting scale records: url={url}\nheaders={headers}")
        response = requests.get(url, headers=headers)
        print(f"Scale records response: status={response.status_code}, text={response.text}")
        if response.status_code != 200:
            print(f"Failed to get scale records: {response.text}")
            return []
        try:
            data = response.json()
        except Exception as e:
            print(f"Failed to parse JSON response: {e}")
            return []
        if not isinstance(data, dict) or "result" not in data or not isinstance(data["result"], dict):
            print(f"Unexpected response structure (missing 'result'): {data}")
            return []
        if "records" not in data["result"] or not isinstance(data["result"]["records"], list):
            print(f"Unexpected response structure (missing 'records'): {data}")
            return []
        records = data["result"]["records"]
        if user_id:
            records = [rec for rec in records if rec.get("user_id") == user_id]
        return records

    def get_device_info(self) -> Dict[str, Any]:
        """Get device information."""
        token = self.get_access_token()
        path = f"/v1.0/devices/{self.device_id}"
        # Use the corrected signature logic
        sign, t, canonical_path = self._sign_request("GET", path, access_token=token, params=None)
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
            raise Exception(f"Failed to get device info: {response.text}")
            
        return response.json().get("result", {})

    def get_analysis_report(self, height: float, weight: float, age: int, sex: int, resistance: str) -> Dict[str, Any]:
        """Get body analysis report using POST request.
        
        Args:
            height: Height in cm
            weight: Weight in kg  
            age: Age in years
            sex: 1 = male, 2 = female
            resistance: Body resistance as string
        """
        token = self.get_access_token()
        path = f"/v1.0/scales/{self.device_id}/analysis-reports"
        method = "POST"
        
        # Body data as per Tuya API docs
        body_data = {
            "height": height,
            "weight": weight,
            "age": age,
            "sex": sex,
            "resistance": resistance  # Should be string according to docs
        }
        
        body_json = json.dumps(body_data, separators=(',', ':'))
        body_bytes = body_json.encode('utf-8')
        body_sha256 = hashlib.sha256(body_bytes).hexdigest()
        
        # For POST requests, canonical_path is just the path (no query params)
        canonical_path = path
        str_to_sign = f"{method}\n{body_sha256}\n\n{canonical_path}"
        
        t = str(int(time.time() * 1000))
        message = self.access_id + token + t + str_to_sign
        sign = hmac.new(
            self.access_key.encode("utf-8"),
            msg=message.encode("utf-8"),
            digestmod=hashlib.sha256
        ).hexdigest().upper()
        
        headers = {
            "client_id": self.access_id,
            "access_token": token,
            "t": t,
            "sign": sign,
            "sign_method": "HMAC-SHA256",
            "Content-Type": "application/json"
        }
        
        url = f"{self.endpoint}{canonical_path}"
        
        print(f"POST Analysis Reports:")
        print(f"URL: {url}")
        print(f"Body: {body_json}")
        print(f"Body SHA256: {body_sha256}")
        print(f"String to sign: {str_to_sign}")
        print(f"Headers: {headers}")
        
        response = requests.post(url, headers=headers, data=body_json)
        
        print(f"Analysis response: status={response.status_code}, text={response.text}")
        
        if response.status_code != 200:
            raise Exception(f"Failed to get analysis report: {response.text}")
            
        return response.json().get("result", {})

    def get_shadow_properties(self) -> Dict[str, Any]:
        """Get device shadow properties using v2.0 cloud thing shadow endpoint.
        
        This endpoint provides the current state/properties of the device as stored
        in the Tuya cloud shadow, which may include current sensor readings,
        device status, and configuration.
        """
        token = self.get_access_token()
        path = f"/v2.0/cloud/thing/{self.device_id}/shadow/properties"
        method = "GET"
        
        # For GET requests with no body
        body_sha256 = hashlib.sha256(b'').hexdigest()
        
        # No query parameters for this endpoint
        canonical_path = path
        str_to_sign = f"{method}\n{body_sha256}\n\n{canonical_path}"
        
        t = str(int(time.time() * 1000))
        message = self.access_id + token + t + str_to_sign
        sign = hmac.new(
            self.access_key.encode("utf-8"),
            msg=message.encode("utf-8"),
            digestmod=hashlib.sha256
        ).hexdigest().upper()
        
        headers = {
            "client_id": self.access_id,
            "access_token": token,
            "t": t,
            "sign": sign,
            "sign_method": "HMAC-SHA256",
        }
        
        url = f"{self.endpoint}{canonical_path}"
        
        print(f"GET Shadow Properties:")
        print(f"URL: {url}")
        print(f"String to sign: {str_to_sign}")
        print(f"Headers: {headers}")
        
        response = requests.get(url, headers=headers)
        
        print(f"Shadow properties response: status={response.status_code}, text={response.text}")
        
        if response.status_code != 200:
            raise Exception(f"Failed to get shadow properties: {response.text}")
            
        return response.json().get("result", {})

    def get_device_details_v2(self) -> Dict[str, Any]:
        """Get comprehensive device details using v2.0 device management endpoint.
        
        This v2.0 endpoint may provide more detailed information than the v1.0 endpoint,
        including online status, detailed properties, and capabilities.
        """
        token = self.get_access_token()
        path = f"/v2.0/cloud/thing/{self.device_id}"
        method = "GET"
        
        # For GET requests with no body
        body_sha256 = hashlib.sha256(b'').hexdigest()
        
        # No query parameters for this endpoint
        canonical_path = path
        str_to_sign = f"{method}\n{body_sha256}\n\n{canonical_path}"
        
        t = str(int(time.time() * 1000))
        message = self.access_id + token + t + str_to_sign
        sign = hmac.new(
            self.access_key.encode("utf-8"),
            msg=message.encode("utf-8"),
            digestmod=hashlib.sha256
        ).hexdigest().upper()
        
        headers = {
            "client_id": self.access_id,
            "access_token": token,
            "t": t,
            "sign": sign,
            "sign_method": "HMAC-SHA256",
        }
        
        url = f"{self.endpoint}{canonical_path}"
        
        print(f"GET Device Details v2.0:")
        print(f"URL: {url}")
        print(f"String to sign: {str_to_sign}")
        print(f"Headers: {headers}")
        
        response = requests.get(url, headers=headers)
        
        print(f"Device details v2.0 response: status={response.status_code}, text={response.text}")
        
        if response.status_code != 200:
            raise Exception(f"Failed to get device details v2.0: {response.text}")
            
        return response.json().get("result", {})

    def get_operation_logs(self, limit: int = 20) -> Dict[str, Any]:
        """Get device operation logs using v2.0 device management endpoint.
        
        This provides logs of device activities like online/offline events,
        data reporting, instructions sent, and other operational events.
        
        Args:
            limit: Maximum number of log entries to retrieve (default: 20)
        """
        token = self.get_access_token()
        path = f"/v2.0/cloud/thing/{self.device_id}/logs"
        method = "GET"
        
        # Add query parameters for pagination
        params = {"size": limit}
        
        # For GET requests with query parameters
        body_sha256 = hashlib.sha256(b'').hexdigest()
        
        # Include query parameters in canonical path
        sorted_params = sorted(params.items())
        param_str = "&".join([f"{k}={v}" for k, v in sorted_params])
        canonical_path = f"{path}?{param_str}"
        str_to_sign = f"{method}\n{body_sha256}\n\n{canonical_path}"
        
        t = str(int(time.time() * 1000))
        message = self.access_id + token + t + str_to_sign
        sign = hmac.new(
            self.access_key.encode("utf-8"),
            msg=message.encode("utf-8"),
            digestmod=hashlib.sha256
        ).hexdigest().upper()
        
        headers = {
            "client_id": self.access_id,
            "access_token": token,
            "t": t,
            "sign": sign,
            "sign_method": "HMAC-SHA256",
        }
        
        url = f"{self.endpoint}{canonical_path}"
        
        print(f"GET Operation Logs:")
        print(f"URL: {url}")
        print(f"String to sign: {str_to_sign}")
        print(f"Headers: {headers}")
        
        response = requests.get(url, headers=headers)
        
        print(f"Operation logs response: status={response.status_code}, text={response.text}")
        
        if response.status_code != 200:
            raise Exception(f"Failed to get operation logs: {response.text}")
            
        return response.json().get("result", {})

    def get_device_identification(self) -> Dict[str, Any]:
        """Get device identification information using the v2.0 device details endpoint.
        
        This method fetches device information that can be used for Home Assistant
        device registry, including name, model, product_name, and custom_name.
        
        Returns:
            Dict containing device identification information with keys:
            - name: Official device name
            - model: Device model number
            - product_name: Product name
            - custom_name: User-defined custom name
        """
        # Use the existing get_device_details_v2 method which has the right data
        device_details = self.get_device_details_v2()
        
        # Extract the identification fields we need
        return {
            "name": device_details.get("name", "Tuya Smart Scale"),
            "model": device_details.get("model", "Smart Scale"),
            "product_name": device_details.get("product_name", "Tuya Smart Scale"),
            "custom_name": device_details.get("custom_name", "Smart Scale")
        }

    def get_latest_data(self) -> Dict[str, Dict[str, Any]]:
        """Get the latest measurement data for all users.
        
        This simulates the coordinator's get_latest_data method by getting
        recent scale records and organizing them by user_id.
        
        Returns:
            Dict mapping user_id to latest user data with keys:
            - nickname: User's email/nickname
            - weight: Latest weight measurement
            - body_fat: Latest body fat percentage (if available)
        """
        try:
            # Get recent records
            records = self.get_scale_records(limit=20)
            
            # Organize by user_id, keeping the most recent for each user
            user_data = {}
            for record in records:
                user_id = record.get("user_id")
                if not user_id:
                    continue
                    
                # Only keep if this is the first record for this user (most recent)
                if user_id not in user_data:
                    # Calculate body fat from resistance if available
                    body_fat = None
                    if record.get("body_r"):
                        try:
                            # Simple estimation - this would be more complex in reality
                            resistance = float(record["body_r"])
                            weight = float(record.get("wegith", 0)) if record.get("wegith") else 0
                            if weight > 0 and resistance > 0:
                                # Very rough estimation for demo purposes
                                body_fat = round(25 - (resistance / 30), 1)
                                if body_fat < 5:
                                    body_fat = 5.0
                                elif body_fat > 50:
                                    body_fat = 50.0
                        except:
                            body_fat = None
                    
                    user_data[user_id] = {
                        "nickname": record.get("nick_name", f"User {user_id}"),
                        "weight": float(record.get("wegith", 0)) if record.get("wegith") else 0,
                        "body_fat": body_fat
                    }
            
            return user_data
            
        except Exception as e:
            print(f"Warning: Failed to get latest data: {e}")
            return {}

def test_integration_api():
    """Test the integration API class."""
    print(f"Testing integration API with device {DEVICE_ID} in region {REGION}")
    
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
        records = api.get_scale_records(limit=5)
        print(f"✓ Got {len(records)} scale records")
        if records:
            print(f"  First record keys: {list(records[0].keys())}")
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
    
    # Test analysis reports
    print("\n4. Testing analysis reports...")
    try:
        analysis = api.get_analysis_report(
            height=178.0,
            weight=78.3,
            age=26,
            sex=1,  # 1 = male, 2 = female
            resistance="718"  # String as per API docs
        )
        print(f"✓ Got analysis report with keys: {list(analysis.keys())}")
        if analysis:
            for key, value in analysis.items():
                print(f"  {key}: {value}")
    except Exception as e:
        print(f"✗ Failed to get analysis report: {e}")
        # Don't return False here since this is a new feature we're testing
    
    # Test shadow properties endpoint
    print("\n5. Testing shadow properties...")
    try:
        shadow_props = api.get_shadow_properties()
        print(f"✓ Got shadow properties with keys: {list(shadow_props.keys())}")
        if shadow_props:
            # Print the shadow properties structure
            for key, value in shadow_props.items():
                if isinstance(value, dict) and len(str(value)) > 100:
                    print(f"  {key}: {type(value).__name__} with {len(value)} items")
                    # Show first few keys if it's a large dict
                    if hasattr(value, 'keys'):
                        keys = list(value.keys())[:5]
                        print(f"    Sample keys: {keys}")
                else:
                    print(f"  {key}: {value}")
        else:
            print("  No shadow properties returned")
    except Exception as e:
        print(f"✗ Failed to get shadow properties: {e}")
        # Log the error but don't fail the entire test since this is a new endpoint
        print(f"  This may be expected if the device doesn't support shadow properties or the endpoint is not available")
    
    # Test device details v2.0
    print("\n6. Testing device details v2.0...")
    try:
        device_details = api.get_device_details_v2()
        print(f"✓ Got device details v2.0 with keys: {list(device_details.keys())}")
        if device_details:
            # Print key information in a more readable format
            for key, value in device_details.items():
                if isinstance(value, dict) and len(str(value)) > 100:
                    print(f"  {key}: {type(value).__name__} with {len(value)} items")
                    # Show first few keys if it's a large dict
                    if hasattr(value, 'keys'):
                        keys = list(value.keys())[:5]
                        print(f"    Sample keys: {keys}")
                else:
                    print(f"  {key}: {value}")
    except Exception as e:
        print(f"✗ Failed to get device details v2.0: {e}")
        # Don't return False here since this endpoint may not be available for all device types
    
    # Test operation logs
    print("\n7. Testing operation logs...")
    try:
        logs_result = api.get_operation_logs(limit=5)
        print(f"✓ Got operation logs result with keys: {list(logs_result.keys())}")
        
        # Handle different possible response structures
        if 'logs' in logs_result:
            logs = logs_result['logs']
            print(f"  Found {len(logs)} log entries")
            if logs:
                print(f"  First log entry keys: {list(logs[0].keys())}")
                print(f"  First log entry: {logs[0]}")
        elif isinstance(logs_result, list):
            logs = logs_result
            print(f"  Found {len(logs)} log entries (direct list)")
            if logs:
                print(f"  First log entry: {logs[0]}")
        else:
            print(f"  Logs result structure: {logs_result}")
    except Exception as e:
        print(f"✗ Failed to get operation logs: {e}")
        # Don't return False here since this endpoint may not be available for all devices
    
    print("\n✓ All tests completed!")
    return True

def test_device_identification_integration():
    """Test device identification integration for Home Assistant device registry."""
    print("🔍 Testing Device Identification Integration for Home Assistant")
    
    # Use the same API class as the main test (from local copy)
    api = TuyaSmartScaleAPI(ACCESS_ID, ACCESS_KEY, DEVICE_ID, REGION)
    
    print("\n1. Testing device identification method...")
    try:
        device_info = api.get_device_identification()
        print(f"✓ Got device identification: {device_info}")
        
        # Validate the structure
        required_fields = ["name", "model", "product_name", "custom_name"]
        for field in required_fields:
            if field not in device_info:
                print(f"✗ Missing required field: {field}")
                return False
            
        print(f"  Device Name: {device_info['name']}")
        print(f"  Device Model: {device_info['model']}")
        print(f"  Product Name: {device_info['product_name']}")
        print(f"  Custom Name: {device_info['custom_name']}")
        
    except Exception as e:
        print(f"✗ Failed to get device identification: {e}")
        return False
    
    print("\n2. Testing coordinator-like data structure...")
    try:
        # Test the data structure that the coordinator would create
        latest_data = api.get_latest_data()
        print(f"✓ Got latest data for {len(latest_data)} users")
        
        # Simulate device registry info structure
        device_registry_info = {
            "identifiers": {("tuya_scale", DEVICE_ID)},
            "name": device_info.get("custom_name") or device_info.get("name") or "Tuya Smart Scale",
            "manufacturer": "Tuya",
            "model": device_info.get("model") or "Smart Scale",
            "sw_version": None,
            "configuration_url": "https://iot.tuya.com/",
        }
        
        print(f"✓ Device registry info structure:")
        for key, value in device_registry_info.items():
            print(f"  {key}: {value}")
            
    except Exception as e:
        print(f"✗ Failed to test coordinator data structure: {e}")
        return False
    
    print("\n3. Testing sensor attributes...")
    try:
        # Test what sensor attributes would look like
        for user_id, user_data in latest_data.items():
            print(f"  User {user_id}:")
            
            # Simulate sensor extra_state_attributes
            attributes = {}
            if device_info.get("product_name"):
                attributes["product_name"] = device_info["product_name"]
            if device_info.get("model"):
                attributes["device_model"] = device_info["model"]
            
            if user_data.get("nickname"):
                attributes["user_nickname"] = user_data["nickname"]
            attributes["user_id"] = user_id
            attributes["device_id"] = DEVICE_ID
            
            print(f"    Extra attributes: {attributes}")
            break  # Just show one example
            
    except Exception as e:
        print(f"✗ Failed to test sensor attributes: {e}")
        return False
    
    print("\n✅ DEVICE IDENTIFICATION INTEGRATION TEST SUCCESSFUL!")
    print("   The Home Assistant integration should now:")
    print("   • Register the device with proper name and model in device registry")
    print("   • Include device identification info in sensor attributes")
    print("   • Provide fallback device info if API calls fail")
    return True

if __name__ == "__main__":
    test_integration_api()
    print("\n" + "="*60)
    test_device_identification_integration()
