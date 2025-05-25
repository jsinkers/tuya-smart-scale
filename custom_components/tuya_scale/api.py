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

    def sign(self, method: str, path: str, params: Dict = None, body: Dict = None, access_token: str = None, t: str = None) -> Dict[str, str]:
        """Calculate signature for Tuya v2.0 API requests. Matches working test script exactly."""
        method = method.upper()
        if t is None:
            t = str(int(time.time() * 1000))
        if body:
            body_str = json.dumps(body, separators=(",", ":"))
        else:
            body_str = ''
        body_sha256 = hashlib.sha256(body_str.encode('utf-8')).hexdigest()
        
        # Match the working test script logic exactly:
        # For paths that already contain query parameters (like "/v1.0/token?grant_type=1"), use as-is
        # For paths with separate params dict, build canonical path with sorted parameters
        if params:
            sorted_params = sorted(params.items())
            param_str = "&".join([f"{k}={v}" for k, v in sorted_params])
            canonical_path = f"{path}?{param_str}"
        else:
            canonical_path = path
            
        str_to_sign = f"{method}\n{body_sha256}\n\n{canonical_path}"
        if access_token:
            message = self.access_id + access_token + t + str_to_sign
        else:
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
        if access_token:
            headers["access_token"] = access_token
        _LOGGER.debug(f"Tuya v2 sign() for {method} {canonical_path}: t={t} str_to_sign={str_to_sign} message={message} signature={signature}")
        return headers

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
        path = f"/v1.0/devices/{self.device_id}"
        headers = self.sign("GET", path, access_token=token)
        url = f"{self.endpoint}{path}"
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"Failed to get device info: {response.text}")
            
        return response.json().get("result", {})

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
        
        _LOGGER.debug(f"Requesting scale records: url={url}\nheaders={headers}")
        response = requests.get(url, headers=headers)
        _LOGGER.debug(f"Scale records response: status={response.status_code}, text={response.text}")
        if response.status_code != 200:
            _LOGGER.error(f"Failed to get scale records: {response.text}")
            return []
        try:
            data = response.json()
        except Exception as e:
            _LOGGER.error(f"Failed to parse JSON response: {e}")
            return []
        if not isinstance(data, dict) or "result" not in data or not isinstance(data["result"], dict):
            _LOGGER.error(f"Unexpected response structure (missing 'result'): {data}")
            return []
        if "records" not in data["result"] or not isinstance(data["result"]["records"], list):
            _LOGGER.error(f"Unexpected response structure (missing 'records'): {data}")
            return []
        records = data["result"]["records"]
        if user_id:
            records = [rec for rec in records if rec.get("user_id") == user_id]
        return records

    def get_scale_users(self) -> List[Dict[str, Any]]:
        """Get users for this scale device by extracting from measurement records."""
        records = self.get_scale_records(limit=100)
        users = {}
        for rec in records:
            user_id = rec.get("user_id")
            nickname = rec.get("nickname")
            if user_id and user_id not in users:
                users[user_id] = {"user_id": user_id, "nickname": nickname}
        user_list = list(users.values())
        if not user_list:
            _LOGGER.warning("No users found in recent measurement records.")
        else:
            _LOGGER.debug(f"Discovered users from records: {user_list}")
        return user_list
        
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
                
                # Try to get analysis report if we have the required data
                try:
                    height = float(latest_record.get("height", 0))
                    weight = float(latest_record.get("wegith", 0))  # Note: API uses "wegith" not "weight"
                    resistance = latest_record.get("body_r", "0")
                    
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
                    else:
                        _LOGGER.debug(f"Skipping analysis report for record - insufficient data: height={height}, weight={weight}, resistance={resistance}")
                except Exception as e:
                    _LOGGER.warning(f"Could not fetch analysis report for record: {e}")
                
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
        
        _LOGGER.debug(f"POST Analysis Reports:")
        _LOGGER.debug(f"URL: {url}")
        _LOGGER.debug(f"Body: {body_json}")
        _LOGGER.debug(f"Body SHA256: {body_sha256}")
        _LOGGER.debug(f"String to sign: {str_to_sign}")
        _LOGGER.debug(f"Headers: {headers}")
        
        response = requests.post(url, headers=headers, data=body_json)
        
        _LOGGER.debug(f"Analysis response: status={response.status_code}, text={response.text}")
        
        if response.status_code != 200:
            _LOGGER.error(f"Failed to get analysis report: {response.text}")
            raise Exception(f"Failed to get analysis report: {response.text}")
            
        return response.json().get("result", {})
