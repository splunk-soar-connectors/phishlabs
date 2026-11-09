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
import httpx
from soar_sdk.action_results import MakeRequestOutput
from soar_sdk.exceptions import ActionFailure
from soar_sdk.params import MakeRequestParams

from ..asset import Asset
from ..auth import basic_auth
from ..validators import (
    parse_json_object,
    parse_query_parameters,
    validate_relative_endpoint,
)
from .utils import BASE_URL, DEFAULT_TIMEOUT


def make_request(params: MakeRequestParams, asset: Asset) -> MakeRequestOutput:
    """Send an arbitrary request to the configured PhishLabs API."""
    try:
        endpoint = validate_relative_endpoint(params.endpoint)
        headers = parse_json_object(params.headers, "headers")
        query_parameters = parse_query_parameters(params.query_parameters)
        body = parse_json_object(params.body, "body")
    except ValueError as error:
        raise ActionFailure(str(error)) from error

    timeout = params.timeout if params.timeout is not None else DEFAULT_TIMEOUT
    if timeout <= 0:
        raise ActionFailure("Timeout must be greater than zero")

    try:
        response = httpx.request(
            params.http_method,
            f"{BASE_URL}/{endpoint}",
            auth=basic_auth(asset.username, asset.password),
            headers=headers,
            params=query_parameters,
            json=body,
            timeout=timeout,
            verify=params.verify_ssl,
            follow_redirects=True,
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            # Make Request returns status and body so callers can inspect API errors.
            response = error.response
    except httpx.RequestError as error:
        raise ActionFailure("Unable to connect to PhishLabs") from error

    return MakeRequestOutput(
        status_code=response.status_code,
        response_body=response.text,
    )
