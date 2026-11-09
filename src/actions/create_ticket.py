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
from soar_sdk.abstract import SOARClient
from soar_sdk.action_results import ActionOutput, OutputField
from soar_sdk.exceptions import ActionFailure
from soar_sdk.params import Param, Params

from ..asset import Asset
from ..auth import basic_auth
from ..validators import validate_case_url
from .utils import (
    BASE_URL,
    DEFAULT_TIMEOUT,
    PhishLabsAPIError,
    http_status_message,
    response_json,
)


class CreateTicketParams(Params):
    title: str = Param(description="Title")
    url: str | None = Param(description="URL", primary=True, cef_types=["url"])
    description: str | None = Param(description="Description of the case")
    case_type: str = Param(
        description="Type of case", primary=True, cef_types=["phishlabs case type"]
    )
    brand: str = Param(
        description="Brand for the case", primary=True, cef_types=["phishlabs brand"]
    )


class CreatedcaseOutput(ActionOutput):
    caseId: str = OutputField(
        cef_types=["phishlabs case id"],
        example_values=["c88dc75c-1756-11e8-8a25-0a799650b9c8"],
    )
    caseNumber: float = OutputField(example_values=[714441])
    status: str = OutputField(example_values=["New"])


class UpdatedcaseOutput(ActionOutput):
    caseId: str | None = OutputField(
        example_values=["c88dc75c-1756-11e8-8a25-0a799650b9c8"]
    )
    caseNumber: float | None = OutputField(example_values=[714441])
    status: str | None = OutputField(example_values=["New"])


class CreateTicketOutput(ActionOutput):
    createdCase: CreatedcaseOutput
    updatedCase: UpdatedcaseOutput | None = None


class CreateTicketSummary(ActionOutput):
    case_id: str = OutputField(
        cef_types=["phishlabs case id"],
        example_values=["c88dc75c-1756-11e8-8a25-0a799650b9c8"],
    )
    case_number: float = OutputField(example_values=[714441])
    status: str = OutputField(example_values=["New"])


def create_ticket(
    params: CreateTicketParams, soar: SOARClient, asset: Asset
) -> CreateTicketOutput:
    """Create one PhishLabs case and report its confirmation."""
    try:
        normalized_url = validate_case_url(params.case_type, params.url)
    except ValueError as error:
        raise ActionFailure(str(error)) from error
    payload = {
        "newCase": {
            "title": params.title,
            "caseType": params.case_type,
            "brand": params.brand,
            "url": normalized_url,
            "description": params.description or "",
        }
    }

    try:
        response = httpx.post(
            f"{BASE_URL}/create/newCase",
            auth=basic_auth(asset.username, asset.password),
            json=payload,
            timeout=DEFAULT_TIMEOUT,
            follow_redirects=True,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as error:
        response = error.response
        if not 200 <= response.status_code < 399:
            raise ActionFailure(http_status_message(response)) from error
    except httpx.RequestError as error:
        raise ActionFailure("Unable to connect to PhishLabs") from error

    try:
        response_data = response_json(response)
    except PhishLabsAPIError as error:
        raise ActionFailure(str(error)) from error

    created_case = (
        response_data.get("createdCase") if isinstance(response_data, dict) else None
    )
    if not isinstance(created_case, dict) or not created_case.get("caseId"):
        raise ActionFailure("PhishLabs did not confirm ticket creation")

    updated_case = (
        response_data.get("updatedCase") if isinstance(response_data, dict) else None
    )
    output = CreateTicketOutput(createdCase=created_case, updatedCase=updated_case)
    summary = CreateTicketSummary(
        status=created_case.get("status"),
        case_id=created_case.get("caseId"),
        case_number=created_case.get("caseNumber"),
    )
    soar.set_summary(summary)
    soar.set_message(
        f"Status: {summary.status}, Case id: {summary.case_id}, Case number: {summary.case_number}"
    )
    return output
