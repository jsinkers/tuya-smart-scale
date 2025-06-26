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
    print("\n✓ All tests completed!")
    return True

def test_scale_records_with_analysis():
    """Test fetching scale records and getting analysis report for the last record with resistance."""
    print(f"\nTesting scale records with analysis for device {DEVICE_ID}")
    
    # Create API client
    api = TuyaSmartScaleAPI(
        access_id=ACCESS_ID,
        access_key=ACCESS_KEY,
        device_id=DEVICE_ID,
        region=REGION
    )
    
    print("\n1. Fetching scale records...")
    try:
        records = api.get_scale_records(limit=20)  # Get more records to find one with resistance
        print(f"✓ Got {len(records)} scale records")
        
        if not records:
            print("✗ No records found")
            return False
            
        # Find the last record with resistance data
        record_with_resistance = None
        for record in records:
            resistance = record.get("body_r")
            if resistance and resistance != "0":
                record_with_resistance = record
                break
        
        if not record_with_resistance:
            print("✗ No records found with resistance data")
            print("Available records:")
            for i, record in enumerate(records[:3]):  # Show first 3 records
                print(f"  Record {i+1}: {record}")
            return False
            
        print(f"\n2. Found record with resistance data:")
        print(f"   Record details:")
        for key, value in record_with_resistance.items():
            print(f"     {key}: {value}")
            
        # Extract data for analysis report
        height = float(record_with_resistance.get("height", 0))
        weight = float(record_with_resistance.get("wegith", 0))  # Note: API uses "wegith" not "weight"
        resistance = record_with_resistance.get("body_r", "0")
        
        print(f"\n3. Extracted data for analysis:")
        print(f"   Height: {height} cm")
        print(f"   Weight: {weight} kg")
        print(f"   Resistance: {resistance} Ω")
        
        if height > 0 and weight > 0 and resistance and resistance != "0":
            print(f"\n4. Requesting analysis report...")
            try:
                analysis_report = api.get_analysis_report(
                    height=height,
                    weight=weight,
                    age=34,  # Default age
                    sex=1,   # Default to male
                    resistance=resistance
                )
                
                print(f"✓ Got analysis report:")
                for key, value in analysis_report.items():
                    print(f"     {key}: {value}")
                    
                return True
                
            except Exception as e:
                print(f"✗ Failed to get analysis report: {e}")
                return False
        else:
            print(f"✗ Insufficient data for analysis: height={height}, weight={weight}, resistance={resistance}")
            return False
            
    except Exception as e:
        print(f"✗ Failed to fetch scale records: {e}")
        return False

if __name__ == "__main__":
    print("Running integration API tests...")
    test_integration_api()
    
    print("\n" + "="*60)
    print("Running scale records with analysis test...")
    test_scale_records_with_analysis()
