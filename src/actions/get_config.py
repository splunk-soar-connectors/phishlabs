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
from typing import cast

import httpx
from pydantic import Field
from soar_sdk.abstract import SOARClient
from soar_sdk.action_results import ActionOutput, ActionResult, OutputField
from soar_sdk.exceptions import ActionFailure
from soar_sdk.params import Params

from ..asset import Asset
from ..auth import basic_auth
from .utils import (
    BASE_URL,
    DEFAULT_TIMEOUT,
    PhishLabsAPIError,
    http_status_message,
    response_json,
)


class BrandsOutput(ActionOutput):
    name: str = OutputField(cef_types=["phishlabs brand"], example_values=["BRAND1"])


class CaseTypesOutput(ActionOutput):
    name: str = OutputField(
        cef_types=["phishlabs case type"], example_values=["Phishing"]
    )


class GetConfigOutput(ActionOutput):
    brands: list[BrandsOutput]
    case_types: list[CaseTypesOutput] = Field(
        default_factory=list,
        json_schema_extra={"cef_types": ["phishlabs case type"]},
    )


class GetConfigSummary(ActionOutput):
    num_brands: int = OutputField(example_values=[3])
    num_case_types: int = OutputField(example_values=[4])


def get_config(params: Params, soar: SOARClient, asset: Asset) -> GetConfigOutput:
    """Return configured brands and case types, retaining brands on a second-call failure."""
    del params
    try:
        brand_response = httpx.get(
            f"{BASE_URL}/create/brands",
            auth=basic_auth(asset.username, asset.password),
            timeout=DEFAULT_TIMEOUT,
            follow_redirects=True,
        )
        brand_response.raise_for_status()
    except httpx.HTTPStatusError as error:
        brand_response = error.response
        if not 200 <= brand_response.status_code < 399:
            raise ActionFailure(http_status_message(brand_response)) from error
    except httpx.RequestError as error:
        raise ActionFailure("Unable to connect to PhishLabs") from error

    try:
        brand_data = response_json(brand_response)
    except PhishLabsAPIError as error:
        raise ActionFailure(str(error)) from error
    brand_list = brand_data.get("brands") if isinstance(brand_data, dict) else None
    if not isinstance(brand_list, list):
        raise ActionFailure("PhishLabs returned invalid brand data")
    brand_values = [{"name": str(brand)} for brand in brand_list]

    # Keep this SDK's single-output annotation; its runtime still accepts ActionResult.
    try:
        case_type_response = httpx.get(
            f"{BASE_URL}/create/caseTypes",
            auth=basic_auth(asset.username, asset.password),
            timeout=DEFAULT_TIMEOUT,
            follow_redirects=True,
        )
        case_type_response.raise_for_status()
        case_type_data = response_json(case_type_response)
    except httpx.HTTPStatusError as error:
        case_type_response = error.response
        if not 200 <= case_type_response.status_code < 399:
            result = ActionResult(False, http_status_message(case_type_response))
            result.add_data({"brands": brand_values})
            return cast(GetConfigOutput, result)
    except httpx.RequestError:
        result = ActionResult(False, "Unable to connect to PhishLabs")
        result.add_data({"brands": brand_values})
        return cast(GetConfigOutput, result)
    except PhishLabsAPIError as error:
        result = ActionResult(False, str(error))
        result.add_data({"brands": brand_values})
        return cast(GetConfigOutput, result)

    case_type_list = (
        case_type_data.get("caseType") if isinstance(case_type_data, dict) else None
    )
    if not isinstance(case_type_list, list):
        result = ActionResult(False, "PhishLabs returned invalid case type data")
        result.add_data({"brands": brand_values})
        return cast(GetConfigOutput, result)

    case_type_values = [{"name": str(case_type)} for case_type in case_type_list]

    summary = GetConfigSummary(
        num_brands=len(brand_values), num_case_types=len(case_type_values)
    )
    soar.set_summary(summary)
    soar.set_message(
        f"Num case types: {summary.num_case_types}, Num brands: {summary.num_brands}"
    )
    return GetConfigOutput(brands=brand_values, case_types=case_type_values)
