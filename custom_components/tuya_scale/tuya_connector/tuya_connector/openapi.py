#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""Tuya Open API."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import base64
from typing import Any, Dict, Optional, Tuple

import aiohttp
import logging

from .openlogging import filter_logger, logger
from .version import VERSION

TUYA_ERROR_CODE_TOKEN_INVALID = 1010

TO_B_REFRESH_TOKEN_API = "/v1.0/token/{}"

TO_B_TOKEN_API = "/v1.0/token"

_LOGGER = logging.getLogger(__name__)


class TuyaTokenInfo:
    """Tuya token info.

    Attributes:
        access_token: Access token.
        expire_time: Valid period in seconds.
        refresh_token: Refresh token.
        uid: Tuya user ID.
    """

    def __init__(self, response: Dict[str, Any]):
        """Init TuyaTokenInfo."""
        self.access_token = response.get("access_token", "")
        self.refresh_token = response.get("refresh_token", "")
        self.uid = response.get("uid", "")
        self.expire_time = response.get("expire_time", 0)


class TuyaOpenAPI:
    """Open Api.

    Typical usage example:

    openapi = TuyaOpenAPI(ENDPOINT, ACCESS_ID, ACCESS_KEY)
    """

    def __init__(
        self,
        endpoint: str,
        access_id: str,
        access_secret: str,
        lang: str = "en",
    ):
        """Init TuyaOpenAPI."""
        self.endpoint = endpoint
        self.access_id = access_id
        self.access_secret = access_secret
        self.lang = lang
        self.token_info: TuyaTokenInfo = None
        self.session: Optional[aiohttp.ClientSession] = None

        self.dev_channel: str = ""

    # https://developer.tuya.com/docs/iot/open-api/api-reference/singnature?id=Ka43a5mtx1gsc
    def _calculate_sign(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, int]:

        # HTTPMethod
        str_to_sign = method
        str_to_sign += "\n"

        # Content-SHA256
        content_to_sha256 = (
            "" if body is None or len(body.keys()) == 0 else json.dumps(body)
        )

        str_to_sign += (
            hashlib.sha256(content_to_sha256.encode(
                "utf8")).hexdigest().lower()
        )
        str_to_sign += "\n"

        # Header
        str_to_sign += "\n"

        # URL
        str_to_sign += path

        if params is not None and len(params.keys()) > 0:
            str_to_sign += "?"

            query_builder = ""
            params_keys = sorted(params.keys())

            for key in params_keys:
                query_builder += f"{key}={params[key]}&"
            str_to_sign += query_builder[:-1]

        # Sign
        t = int(time.time() * 1000)

        message = self.access_id
        if self.token_info is not None:
            message += self.token_info.access_token
        message += str(t) + str_to_sign
        sign = (
            hmac.new(
                self.access_secret.encode("utf8"),
                msg=message.encode("utf8"),
                digestmod=hashlib.sha256,
            )
            .hexdigest()
            .upper()
        )
        return sign, t

    def set_dev_channel(self, dev_channel: str):
        """Set dev channel."""
        self.dev_channel = dev_channel

    async def connect(self) -> None:
        """Connect to Tuya API."""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        await self._get_token()

    async def _get_token(self) -> None:
        """Get token."""
        response = await self._request("GET", TO_B_TOKEN_API, {"grant_type": 1})
        if response.get("success"):
            self.token_info = TuyaTokenInfo(response.get("result", {}))
        else:
            raise Exception(f"Failed to get token: {response}")

    async def _refresh_token(self) -> None:
        """Refresh token."""
        if not self.token_info or not self.token_info.refresh_token:
            await self._get_token()
            return

        response = await self._request(
            "GET", 
            TO_B_REFRESH_TOKEN_API.format(self.token_info.refresh_token)
        )
        if response.get("success"):
            self.token_info = TuyaTokenInfo(response.get("result", {}))
        else:
            await self._get_token()

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Request Tuya API."""
        if self.session is None:
            await self.connect()

        # Check if token is expired
        if self.token_info and time.time() * 1000 >= self.token_info.expire_time:
            await self._refresh_token()

        sign, t = self._calculate_sign(method, path, params, body)
        headers = {
            "client_id": self.access_id,
            "sign": sign,
            "sign_method": "HMAC-SHA256",
            "access_token": self.token_info.access_token if self.token_info else "",
            "t": str(t),
            "lang": self.lang,
        }

        headers["dev_lang"] = "python"
        headers["dev_version"] = VERSION
        headers["dev_channel"] = f"cloud_{self.dev_channel}"

        logger.debug(
            f"Request: method = {method}, \
                url = {self.endpoint + path},\
                params = {params},\
                body = {filter_logger(body)},\
                t = {int(time.time()*1000)}, \
                headers = {headers}"
        )

        url = f"{self.endpoint}{path}"
        if params:
            url += "?" + "&".join(f"{k}={v}" for k, v in params.items())

        try:
            async with self.session.request(method, url, headers=headers, json=body) as response:
                if not response.ok:
                    logger.error(
                        f"Response error: code={response.status}, body={await response.text()}"
                    )
                    return None

                result = await response.json()
                logger.debug(
                    f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}"
                )
                return result
        except Exception as e:
            logger.error("Request failed: %s", str(e))
            raise

    async def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """GET request."""
        return await self._request("GET", path, params)

    async def post(self, path: str, body: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """POST request."""
        return await self._request("POST", path, params, body)

    async def put(self, path: str, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """PUT request."""
        return await self._request("PUT", path, None, body)

    async def delete(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """DELETE request."""
        return await self._request("DELETE", path, params)

    async def close(self) -> None:
        """Close the session."""
        if self.session:
            await self.session.close()
            self.session = None
