"""API client for Tuya Smart Scale integration."""
import logging
import requests
import time
import hmac
import hashlib
import json
from typing import Dict, Any, List

from .const import REGIONS, SMART_SCALE_DEVICE_TYPE, CONF_ACCESS_ID, CONF_ACCESS_KEY

_LOGGER = logging.getLogger(__name__)

class TuyaSmartScaleAPI:
    """API client for Tuya Smart Scale."""

    def __init__(self, api_key: str, api_secret: str, device_id: str, region: str = "us"):
        """Initialize the API client."""
        self.api_key = api_key
        self.api_secret = api_secret
        self.device_id = device_id
        self.region = region
        self.endpoint = REGIONS.get(region, REGIONS["us"])["endpoint"]
        self.access_token = None
        self.token_expires = 0

    def sign(self, method: str, path: str, params: Dict = None, body: Dict = None) -> Dict[str, str]:
        """Calculate signature for Tuya API requests."""
        timestamp = str(int(time.time() * 1000))
        message = self.api_key + timestamp
        
        if params:
            sorted_params = sorted(params.items(), key=lambda x: x[0])
            for param_name, param_value in sorted_params:
                message += param_name + str(param_value)
        
        if body:
            message += json.dumps(body)
            
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            msg=message.encode('utf-8'),
            digestmod=hashlib.sha256
        ).hexdigest().upper()
        
        return {
            "client_id": self.api_key,
            "signature": signature,
            "t": timestamp,
            "sign_method": "HMAC-SHA256",
        }

    def get_access_token(self) -> str:
        """Get access token from Tuya API."""
        if self.access_token and time.time() < self.token_expires - 60:
            return self.access_token
        # For /v1.0/token, Tuya does NOT require a signature, only client_id and sign_method
        headers = {
            "client_id": self.api_key,
            "sign_method": "HMAC-SHA256",
        }
        url = f"{self.endpoint}/v1.0/token?grant_type=1"
        _LOGGER.debug(f"Requesting token: url={url} headers={headers}")
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            _LOGGER.error(f"Failed to get access token: {response.text}")
            raise Exception(f"Failed to get access token: {response.text}")
        try:
            data = response.json()
        except Exception as e:
            _LOGGER.error(f"Failed to parse JSON response for access token: {e}")
            raise Exception(f"Failed to parse JSON response for access token: {e}")
        if not isinstance(data, dict) or "result" not in data:
            _LOGGER.error(f"Unexpected response structure for access token (missing 'result'): {data}")
            raise Exception(f"Unexpected response structure for access token (missing 'result'): {data}")
        self.access_token = data["result"].get("access_token")
        self.token_expires = time.time() + data["result"].get("expire_time", 0)
        return self.access_token

    def get_device_info(self) -> Dict[str, Any]:
        """Get device information."""
        token = self.get_access_token()
        
        headers = self.sign("GET", f"/v1.0/devices/{self.device_id}")
        headers["access_token"] = token
        
        url = f"{self.endpoint}/v1.0/devices/{self.device_id}"
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"Failed to get device info: {response.text}")
            
        return response.json().get("result", {})

    def get_scale_records(self, start_time: int = None, end_time: int = None, 
                         limit: int = 10, user_id: str = None) -> List[Dict[str, Any]]:
        """Get scale measurement records.
        
        Args:
            start_time: Start time in milliseconds since epoch
            end_time: End time in milliseconds since epoch
            limit: Maximum number of records to return (default 10, max 100)
            user_id: Optional user ID to filter records
            
        Returns:
            List of scale records
        """
        token = self.get_access_token()
        
        params = {"device_id": self.device_id, "limit": limit}
        
        if start_time:
            params["start_time"] = start_time
        
        if end_time:
            params["end_time"] = end_time
            
        if user_id:
            params["user_id"] = user_id
            
        headers = self.sign("GET", "/v1.0/devices/scale/records", params=params)
        headers["access_token"] = token
        
        param_str = "&".join([f"{key}={value}" for key, value in params.items()])
        url = f"{self.endpoint}/v1.0/devices/scale/records?{param_str}"
        
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            _LOGGER.error(f"Failed to get scale records: {response.text}")
            return []
        try:
            data = response.json()
        except Exception as e:
            _LOGGER.error(f"Failed to parse JSON response: {e}")
            return []
        # Defensive: check for 'result' and 'records' keys
        if not isinstance(data, dict) or "result" not in data or not isinstance(data["result"], dict):
            _LOGGER.error(f"Unexpected response structure (missing 'result'): {data}")
            return []
        if "records" not in data["result"] or not isinstance(data["result"]["records"], list):
            _LOGGER.error(f"Unexpected response structure (missing 'records'): {data}")
            return []
        return data["result"]["records"]

    def get_scale_users(self) -> List[Dict[str, Any]]:
        """Get users for this scale device."""
        token = self.get_access_token()
        params = {"device_id": self.device_id}
        headers = self.sign("GET", "/v1.0/devices/scale/users", params=params)
        headers["access_token"] = token
        url = f"{self.endpoint}/v1.0/devices/scale/users?device_id={self.device_id}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            _LOGGER.error(f"Failed to get scale users: {response.text}")
            return []
        try:
            data = response.json()
        except Exception as e:
            _LOGGER.error(f"Failed to parse JSON response for users: {e}")
            return []
        if not isinstance(data, dict) or "result" not in data:
            _LOGGER.error(f"Unexpected response structure for users (missing 'result'): {data}")
            return []
        return data["result"]
        
    def get_latest_data(self) -> Dict[str, Dict[str, Any]]:
        """Get latest measurement data for all users of this scale, including analysis report."""
        try:
            users = self.get_scale_users()
            if not users:
                _LOGGER.error("No users found for this scale device.")
                return {}
            result = {}
            for user in users:
                user_id = user.get("user_id")
                if not user_id:
                    continue
                try:
                    records = self.get_scale_records(user_id=user_id, limit=1)
                except Exception as e:
                    _LOGGER.error(f"Error fetching records for user {user_id}: {e}")
                    continue
                if not records:
                    _LOGGER.warning(f"No records found for user {user_id}")
                    continue
                latest_record = records[0]
                record_id = latest_record.get("id")
                if record_id:
                    try:
                        analysis_report = self.get_analysis_report(record_id)
                        latest_record["analysis_report"] = analysis_report
                    except Exception as e:
                        _LOGGER.warning(f"Could not fetch analysis report for record {record_id}: {e}")
                latest_record.update({"nickname": user.get("nickname")})
                result[user_id] = latest_record
            return result
        except Exception as err:
            import traceback
            _LOGGER.error(f"Error fetching latest scale data: {err}\nTraceback:\n{traceback.format_exc()}")
            return {}
            
    def validate_credentials(self) -> bool:
        """Validate API credentials."""
        try:
            self.get_access_token()
            return True
        except Exception as err:
            _LOGGER.error("Failed to validate credentials: %s", err)
            return False
        
    def get_analysis_report(self, record_id: str) -> dict:
        """Get the analysis report for a given weighing record."""
        token = self.get_access_token()
        headers = self.sign("GET", f"/v1.0/devices/scale/records/{record_id}/analysis_report")
        headers["access_token"] = token
        url = f"{self.endpoint}/v1.0/devices/scale/records/{record_id}/analysis_report"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            _LOGGER.error(f"Failed to get analysis report: {response.text}")
            return {}
        try:
            data = response.json()
        except Exception as e:
            _LOGGER.error(f"Failed to parse JSON response for analysis report: {e}")
            return {}
        if not isinstance(data, dict) or "result" not in data:
            _LOGGER.error(f"Unexpected response structure for analysis report (missing 'result'): {data}")
            return {}
        return data.get("result", {})