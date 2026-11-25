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
import json
from typing import Any
from urllib.parse import urlsplit


def validate_case_url(case_type: str, url: str | None) -> str:
    """Return the submitted URL, enforcing the legacy URL-based case types."""
    normalized_url = url or ""
    if case_type in ("Phishing", "Phishing Redirect") and not normalized_url:
        raise ValueError(f"Case type '{case_type}' requires a URL")
    return normalized_url


def validate_relative_endpoint(endpoint: str) -> str:
    """Reject absolute or authority-relative URLs for Make Request."""
    parsed = urlsplit(endpoint)
    if parsed.scheme or parsed.netloc or endpoint.startswith("//"):
        raise ValueError("Endpoint must be relative to the PhishLabs API")
    return endpoint.lstrip("/")


def parse_json_object(value: str | None, field_name: str) -> dict[str, Any] | None:
    """Parse an optional Make Request object field and reject non-object JSON."""
    if not value:
        return None
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as error:
        raise ValueError(f"{field_name} must be valid JSON") from error
    if not isinstance(parsed, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return parsed


def parse_query_parameters(
    value: str | None,
) -> dict[str, Any] | str | None:
    """Accept Make Request query parameters as an object or query string."""
    if not value:
        return None
    if value.startswith("?"):
        return value[1:]
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return value
    if not isinstance(parsed, dict):
        raise ValueError("query_parameters must be a JSON object or query string")
    return parsed
