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
from typing import Any, cast

from pydantic import Field
from soar_sdk.abstract import SOARClient
from soar_sdk.action_results import ActionOutput, ActionResult, OutputField
from soar_sdk.exceptions import ActionFailure
from soar_sdk.params import Params

from ..app import Asset
from ..client import PhishLabsAPIError, PhishLabsClient, PhishLabsError, process_response


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
    num_brands: float = OutputField(example_values=[3])
    num_case_types: float = OutputField(example_values=[4])


def fetch_config(
    client: PhishLabsClient, params: Params
) -> tuple[GetConfigOutput, dict[str, int]] | ActionResult:
    """Fetch configuration, preserving brands if the second request fails."""
    brand_response = process_response(client.request("get", "/create/brands"))
    brand_list = brand_response.get("brands") if isinstance(brand_response, dict) else None
    if not isinstance(brand_list, list):
        raise PhishLabsAPIError("PhishLabs returned invalid brand data")
    brand_values = [{"name": str(brand)} for brand in brand_list]

    try:
        case_type_response = process_response(
            client.request("get", "/create/caseTypes")
        )
        case_type_list = (
            case_type_response.get("caseType")
            if isinstance(case_type_response, dict)
            else None
        )
        if not isinstance(case_type_list, list):
            raise PhishLabsAPIError("PhishLabs returned invalid case type data")
    except PhishLabsError as error:
        result = ActionResult(False, str(error), params.model_dump())
        result.add_data({"brands": brand_values})
        return result

    case_type_values = [{"name": str(case_type)} for case_type in case_type_list]

    return (
        GetConfigOutput(brands=brand_values, case_types=case_type_values),
        {"num_brands": len(brand_values), "num_case_types": len(case_type_values)},
    )


def config_message(summary: dict[str, int]) -> str:
    """Format the legacy get-config summary message."""
    return "Num case types: {num_case_types}, Num brands: {num_brands}".format(
        **summary
    )


def get_config(
    params: Params, soar: SOARClient, asset: Asset
) -> GetConfigOutput:
    """Return the vendor's configured brands and case types."""
    try:
        result = fetch_config(
            PhishLabsClient(asset.username, asset.password), params
        )
    except PhishLabsError as error:
        raise ActionFailure(str(error)) from error

    if isinstance(result, ActionResult):
        return cast(GetConfigOutput, result)

    output, summary = result
    soar.set_summary(summary)
    soar.set_message(config_message(summary))
    return output
