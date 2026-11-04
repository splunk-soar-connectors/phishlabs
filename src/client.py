# Copyright (c) 2026 Splunk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from typing import Any

import requests
from requests import Response
from requests.exceptions import RequestException

BASE_URL = "https://caseapi.phishlabs.com/v1"
DEFAULT_TIMEOUT = 30


class PhishLabsError(Exception):
    """Base error for PhishLabs API failures."""


class PhishLabsConnectionError(PhishLabsError):
    """Raised when a request cannot reach the PhishLabs API."""


class PhishLabsAPIError(PhishLabsError):
    """Raised when the PhishLabs API returns an unusable response."""


class PhishLabsClient:
    """Small HTTP client that centralizes PhishLabs request policy."""

    def __init__(
        self, username: str, password: str, *, base_url: str = BASE_URL
    ) -> None:
        self._auth = (username, password)
        self._base_url = base_url.rstrip("/")

    def request(
        self,
        method: str,
        endpoint: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> Response:
        url = f"{self._base_url}/{endpoint.lstrip('/')}"
        try:
            return requests.request(
                method,
                url,
                auth=self._auth,
                json=data,
                headers=headers,
                params=params,
                timeout=DEFAULT_TIMEOUT,
            )
        except RequestException as error:
            raise PhishLabsConnectionError("Unable to connect to PhishLabs") from error


def process_response(response: Response) -> Any:
    """Apply the legacy connector's response-type and status rules safely."""
    content_type = response.headers.get("Content-Type", "").lower()

    if "json" in content_type:
        try:
            data = response.json()
        except ValueError as error:
            raise PhishLabsAPIError(
                f"PhishLabs returned invalid JSON (HTTP {response.status_code})"
            ) from error
        if 200 <= response.status_code < 399:
            return data
        raise PhishLabsAPIError(
            f"PhishLabs returned an error response (HTTP {response.status_code})"
        )

    if "html" in content_type:
        raise PhishLabsAPIError(
            f"PhishLabs returned an unexpected HTML response (HTTP {response.status_code})"
        )

    if not response.text:
        if response.status_code == 200:
            return {}
        raise PhishLabsAPIError(
            f"PhishLabs returned an empty response (HTTP {response.status_code})"
        )

    raise PhishLabsAPIError(
        f"PhishLabs returned an unsupported response (HTTP {response.status_code})"
    )
