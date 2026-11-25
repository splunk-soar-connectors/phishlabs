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

import httpx

BASE_URL = "https://caseapi.phishlabs.com/v1"
DEFAULT_TIMEOUT = 30


class PhishLabsError(Exception):
    """Base error for PhishLabs API failures."""


class PhishLabsAPIError(PhishLabsError):
    """Raised when PhishLabs returns an unusable response."""


def http_status_message(response: httpx.Response) -> str:
    """Format a status error without exposing the vendor response body."""
    return f"PhishLabs returned an error response (HTTP {response.status_code})"


def response_json(response: httpx.Response) -> Any:
    """Parse a successful JSON response while preserving legacy content rules."""
    content_type = response.headers.get("Content-Type", "").lower()
    if "json" in content_type:
        try:
            return response.json()
        except ValueError as error:
            raise PhishLabsAPIError(
                f"PhishLabs returned invalid JSON (HTTP {response.status_code})"
            ) from error

    if "html" in content_type:
        raise PhishLabsAPIError(
            f"PhishLabs returned an unexpected HTML response (HTTP {response.status_code})"
        )

    if not response.text and response.status_code == 200:
        return {}

    if not response.text:
        raise PhishLabsAPIError(
            f"PhishLabs returned an empty response (HTTP {response.status_code})"
        )

    raise PhishLabsAPIError(
        f"PhishLabs returned an unsupported response (HTTP {response.status_code})"
    )
