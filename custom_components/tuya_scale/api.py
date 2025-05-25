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
        """Calculate signature for Tuya v2.0 API requests. Allows passing t for debug consistency."""
        method = method.upper()
        if t is None:
            t = str(int(time.time() * 1000))
        if body:
            body_str = json.dumps(body, separators=(",", ":"))
        else:
            body_str = ''
        body_sha256 = hashlib.sha256(body_str.encode('utf-8')).hexdigest()
        str_to_sign = f"{method}\n{body_sha256}\n\n{path}"
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
        _LOGGER.debug(f"Tuya v2 sign() for {method} {path}: t={t} str_to_sign={str_to_sign} message={message} signature={signature}")
        return headers

    def _build_canonical_path(self, path, params=None):
        """Build the canonical path for the request, sorting query parameters."""
        if params:
            sorted_params = sorted(params.items())
            param_str = "&".join([f"{k}={v}" for k, v in sorted_params])
            return f"{path}?{param_str}"
        return path

    def _sign_request(self, method, path, access_token=None, params=None):
        """Sign the request using the correct Tuya v2.0 signature logic."""
        body_sha256 = hashlib.sha256(b'').hexdigest()
        canonical_path = self._build_canonical_path(path, params)
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

    def _request(self, method, path, access_token=None, params=None):
        """Generic request handler for making API requests."""
        sign, t, canonical_path = self._sign_request(method, path, access_token, params)
        url = f"{self.endpoint}{canonical_path}"
        headers = {
            "client_id": self.access_id,
            "t": t,
            "sign": sign,
            "sign_method": "HMAC-SHA256",
        }
        if access_token:
            headers["access_token"] = access_token
        _LOGGER.debug(f"Requesting {method} {url} with headers {headers}")
        response = requests.request(method, url, headers=headers, params=params)
        _LOGGER.debug(f"Response: status={response.status_code}, text={response.text}")
        if response.status_code != 200:
            _LOGGER.error(f"API request failed: {response.text}")
            response.raise_for_status()
        return response.json()

    def get_access_token(self) -> str:
        """Get access token from Tuya API using v2.0 signature logic."""
        if self.access_token and time.time() < self.token_expires - 60:
            return self.access_token
        path = "/v1.0/token?grant_type=1"
        method = "GET"
        headers = self.sign(method, path)
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
        
        headers = self.sign("GET", f"/v1.0/devices/{self.device_id}")
        headers["access_token"] = token
        
        url = f"{self.endpoint}/v1.0/devices/{self.device_id}"
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
        t = str(int(time.time() * 1000))
        headers = self.sign("GET", path, access_token=token, t=t)
        param_str = "&".join([f"{key}={value}" for key, value in params.items()])
        url = f"{self.endpoint}{path}?{param_str}"
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
        """Get the analysis report for a given weighing record using the correct endpoint and signature logic."""
        token = self.get_access_token()
        # Find the record data for this record_id
        all_records = self.get_scale_records(limit=100)
        record = next((r for r in all_records if r.get("id") == record_id), None)
        if not record:
            _LOGGER.error(f"No record found with id {record_id} for analysis report.")
            return {}
        # Prepare body for analysis report (see tuya_scale_downloader.py for mapping)
        body = {
            "height": record.get("height"),
            "weight": record.get("wegith"),
            "resistance": record.get("body_r"),
            "age": record.get("body_age", 30),  # fallback if not present
            "sex": record.get("sex", 1),  # fallback if not present
        }
        # Only the path and body are used in the string to sign for POST requests, not the query params
        headers = self.sign("POST", f"/v1.0/scales/{self.device_id}/analysis-reports/", body=body, access_token=token)
        url = f"{self.endpoint}/v1.0/scales/{self.device_id}/analysis-reports/"
        response = requests.post(url, headers=headers, json=body)
        _LOGGER.debug(f"Analysis report response: status={response.status_code}, text={response.text}")
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