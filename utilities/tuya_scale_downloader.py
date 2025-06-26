#!/usr/bin/env python3
"""
Tuya Smart Scale Data Downloader

Downloads scale measurement data from Tuya Cloud API and enriches it with
body composition analysis reports. Uses direct API calls without tuya_connector dependency.

Based on the working API implementation from the Home Assistant integration.
"""

import os
import json
import time
import hmac
import hashlib
import requests
import logging
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration from environment variables
ACCESS_ID = os.environ.get('ACCESS_ID')
ACCESS_KEY = os.environ.get('ACCESS_KEY')
DEVICE_ID = os.environ.get('DEVICE_ID')
REGION = os.environ.get('TUYA_REGION', 'eu')
BIRTHDATE = os.environ.get('BIRTHDATE')  # Format: YYYY-MM-DD
SEX = int(os.environ.get('SEX', '1'))  # 1 = male, 2 = female
DATA_FILE = os.environ.get('DATA_FILE', 'scale_data.json')
DEBUG_LOGS = os.environ.get('DEBUG_LOGS', 'false').lower() == 'true'

# API endpoints by region
ENDPOINTS = {
    "us": "https://openapi.tuyaus.com",
    "eu": "https://openapi.tuyaeu.com", 
    "cn": "https://openapi.tuyacn.com",
    "in": "https://openapi.tuyain.com"
}

# Set up logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG_LOGS else logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TuyaScaleAPI:
    """Direct Tuya API client for scale data without external dependencies."""
    
    def __init__(self, access_id, access_key, region='us'):
        self.access_id = access_id
        self.access_key = access_key
        self.endpoint = ENDPOINTS.get(region, ENDPOINTS['us'])
        self.access_token = None
        
    def _sign_request(self, method, path, access_token=None, params=None, body=None):
        """Generate request signature for Tuya API."""
        # Handle query parameters
        if params:
            param_str = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
            full_path = f"{path}?{param_str}"
        else:
            full_path = path
            
        # Handle request body
        if body:
            if isinstance(body, str):
                body_bytes = body.encode('utf-8')
            else:
                body_bytes = json.dumps(body, separators=(',', ':')).encode('utf-8')
            body_sha256 = hashlib.sha256(body_bytes).hexdigest()
        else:
            body_sha256 = hashlib.sha256(b"").hexdigest()
            
        # Create string to sign
        if method == "POST":
            # For POST, use just the path (no query params in string_to_sign)
            str_to_sign = f"{method}\n{body_sha256}\n\n{path}"
        else:
            # For GET, include full path with query params
            str_to_sign = f"{method}\n{body_sha256}\n\n{full_path}"
        
        # Generate signature
        t = str(int(time.time() * 1000))
        token = access_token or ""
        message = self.access_id + token + t + str_to_sign
        
        sign = hmac.new(
            self.access_key.encode("utf-8"),
            msg=message.encode("utf-8"),
            digestmod=hashlib.sha256
        ).hexdigest().upper()
        
        return sign, t, full_path if method == "GET" else path
    
    def get_access_token(self):
        """Get access token from Tuya API."""
        path = "/v1.0/token"
        params = {"grant_type": "1"}
        
        sign, t, full_path = self._sign_request("GET", path, params=params)
        url = f"{self.endpoint}{full_path}"
        
        headers = {
            "client_id": self.access_id,
            "t": t,
            "sign_method": "HMAC-SHA256",
            "sign": sign
        }
        
        logger.debug(f"Requesting token: url={url}")
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                self.access_token = data["result"]["access_token"]
                logger.info("✓ Got access token")
                return self.access_token
            else:
                raise Exception(f"Token request failed: {data}")
        else:
            raise Exception(f"HTTP {response.status_code}: {response.text}")
    
    def get_scale_records(self, device_id, page_no=1, page_size=10, start_time=None):
        """Get scale measurement records."""
        if not self.access_token:
            self.get_access_token()
            
        path = f"/v1.0/scales/{device_id}/datas/history"
        params = {
            "page_no": page_no,
            "page_size": page_size
        }
        
        if start_time:
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time).replace(tzinfo=pytz.UTC)
            elif isinstance(start_time, datetime):
                start_time = start_time.replace(tzinfo=pytz.UTC)
            start_time_ms = int(start_time.timestamp() * 1000)
            params["start_time"] = start_time_ms
        
        sign, t, full_path = self._sign_request("GET", path, access_token=self.access_token, params=params)
        url = f"{self.endpoint}{full_path}"
        
        headers = {
            "client_id": self.access_id,
            "access_token": self.access_token,
            "t": t,
            "sign": sign,
            "sign_method": "HMAC-SHA256"
        }
        
        logger.debug(f"Requesting scale records: url={url}")
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            logger.debug(f"Scale records response: status={response.status_code}")
            
            if data.get("success"):
                return data["result"]
            else:
                # Handle API errors
                error_msg = f"API error: {data.get('msg', 'Unknown error')} (code: {data.get('code', 'unknown')})"
                logger.error(error_msg)
                raise Exception(error_msg)
        else:
            raise Exception(f"HTTP {response.status_code}: {response.text}")
    
    def get_analysis_report(self, device_id, height, weight, age, sex, resistance):
        """Get body composition analysis report."""
        if not self.access_token:
            self.get_access_token()
            
        path = f"/v1.0/scales/{device_id}/analysis-reports"
        
        body_data = {
            "height": float(height),
            "weight": float(weight),
            "age": int(age),
            "sex": int(sex),
            "resistance": str(resistance)
        }
        
        body_json = json.dumps(body_data, separators=(',', ':'))
        
        sign, t, canonical_path = self._sign_request("POST", path, access_token=self.access_token, body=body_json)
        url = f"{self.endpoint}{canonical_path}"
        
        headers = {
            "client_id": self.access_id,
            "access_token": self.access_token,
            "t": t,
            "sign": sign,
            "sign_method": "HMAC-SHA256",
            "Content-Type": "application/json"
        }
        
        logger.debug(f"Requesting analysis report: url={url}")
        response = requests.post(url, headers=headers, data=body_json)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return data["result"]
            else:
                error_msg = f"Analysis report error: {data.get('msg', 'Unknown error')}"
                logger.error(error_msg)
                return None
        else:
            logger.error(f"Analysis report HTTP error: {response.status_code}")
            return None

def age_at_time(time_ms, birth_date_str):
    """Calculate age at a given time based on birth date."""
    birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d")
    record_date = datetime.fromtimestamp(time_ms / 1000)
    age = record_date.year - birth_date.year - ((record_date.month, record_date.day) < (birth_date.month, birth_date.day))
    return age

def load_existing_data(file_path):
    """Load existing data from JSON file."""
    if os.path.exists(file_path):
        logger.info(f"Loading existing data from {file_path}")
        with open(file_path, 'r') as file:
            return json.load(file)
    else:
        logger.info(f"No existing data found at {file_path}")
    return []

def save_data(file_path, data):
    """Save data to JSON file."""
    logger.info(f"Saving {len(data)} records to {file_path}")
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=2)

def get_last_record_time(data):
    """Get the timestamp of the most recent record."""
    if data:
        last_record = max(data, key=lambda x: x['create_time'])   
        return datetime.fromtimestamp(last_record['create_time'] / 1000, tz=pytz.UTC)
    return None

def get_all_scale_data_history(api, device_id, page_size=100, start_time=None):
    """Retrieve all scale history data with pagination."""
    all_data = []
    page_no = 1
    total_records_retrieved = 0
    total_records = 1  # Initialize to ensure the loop runs at least once

    logger.info(f"Starting data retrieval from {start_time or 'beginning'}")

    while total_records_retrieved < total_records:
        try:
            result = api.get_scale_records(device_id, page_no, page_size, start_time)
            if result and 'records' in result:
                num_records = len(result['records'])
                total_records_retrieved += num_records
                total_records = result.get('total', total_records_retrieved)
                
                logger.info(f"Retrieved {num_records} records from page {page_no}, {total_records_retrieved} of {total_records}")
                all_data.extend(result['records'])
                page_no += 1
                
                # If we got fewer records than requested, we've reached the end
                if num_records < page_size:
                    break
            else:
                logger.warning(f"No records in result for page {page_no}")
                break
                
        except Exception as e:
            logger.error(f"Error retrieving page {page_no}: {e}")
            break

    logger.info(f"Total records retrieved: {len(all_data)}")
    return all_data

def enrich_with_analysis_reports(api, device_id, records, birth_date):
    """Enrich records with body composition analysis reports."""
    enriched_count = 0
    
    for record in records:
        # Skip if already has analysis report
        if 'analysis_report' in record:
            continue
            
        # Skip if missing required data
        weight = record.get('wegith')  # Note: Tuya API uses "wegith" typo
        height = record.get('height')
        resistance = record.get('body_r', '0')
        
        if not weight or not height or resistance == '0':
            logger.debug(f"Skipping analysis for record {record.get('id')} - insufficient data")
            continue
        try:
            age = age_at_time(record['create_time'], birth_date)
            sex = SEX  # Use configured sex value
            
            analysis_report = api.get_analysis_report(
                device_id=device_id,
                height=float(height),
                weight=float(weight),
                age=age,
                sex=sex,
                resistance=str(resistance)
            )
            
            if analysis_report:
                record['analysis_report'] = analysis_report
                enriched_count += 1
                logger.debug(f"Added analysis report for record {record.get('id')}")
            else:
                logger.warning(f"Failed to get analysis report for record {record.get('id')}")
                
        except Exception as e:
            logger.error(f"Error getting analysis report for record {record.get('id')}: {e}")
    
    logger.info(f"Enriched {enriched_count} records with analysis reports")
    return records

def update_data():
    """Main function to update scale data."""
    # Validate required environment variables
    if not all([ACCESS_ID, ACCESS_KEY, DEVICE_ID, BIRTHDATE]):
        logger.error("Missing required environment variables: ACCESS_ID, ACCESS_KEY, DEVICE_ID, BIRTHDATE")
        return
    
    try:
        # Initialize API client
        api = TuyaScaleAPI(ACCESS_ID, ACCESS_KEY, REGION)
        
        # Load existing data
        existing_data = load_existing_data(DATA_FILE)
        last_record_time = get_last_record_time(existing_data)
        
        # Add 1 ms to last record time to avoid retrieving duplicate records
        if last_record_time:
            last_record_time += timedelta(milliseconds=1)
        
        # Get new data
        new_data = get_all_scale_data_history(api, DEVICE_ID, start_time=last_record_time, page_size=100)
        
        if new_data:
            # Combine and sort data
            all_data = existing_data + new_data
            all_data = sorted(all_data, key=lambda x: x['create_time'])
            
            # Enrich with analysis reports
            all_data = enrich_with_analysis_reports(api, DEVICE_ID, all_data, BIRTHDATE)
            
            # Save updated data
            save_data(DATA_FILE, all_data)
            logger.info(f"✓ Successfully updated data file with {len(new_data)} new records")
        else:
            logger.info("No new records found")
            
    except Exception as e:
        logger.error(f"Error updating data: {e}")
        raise

if __name__ == '__main__':
    logger.info("Starting Tuya Scale Data Downloader")
    update_data()
    logger.info("Data update complete")
