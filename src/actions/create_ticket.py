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

from soar_sdk.abstract import SOARClient
from soar_sdk.action_results import ActionOutput, OutputField
from soar_sdk.exceptions import ActionFailure
from soar_sdk.params import Param, Params

from ..app import Asset
from ..client import PhishLabsAPIError, PhishLabsClient, PhishLabsError, process_response


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


class CreateTicketOutput(ActionOutput):
    createdCase: CreatedcaseOutput


class CreateTicketSummary(ActionOutput):
    case_id: str = OutputField(example_values=["c88dc75c-1756-11e8-8a25-0a799650b9c8"])
    case_number: float = OutputField(example_values=[714441])
    status: str = OutputField(example_values=["New"])


def build_new_case_payload(
    *,
    title: str,
    case_type: str,
    brand: str,
    url: str | None,
    description: str | None,
) -> dict[str, dict[str, str]]:
    """Validate legacy URL requirements and build the vendor request body."""
    normalized_url = url or ""
    if case_type in ("Phishing", "Phishing Redirect") and normalized_url == "":
        raise ValueError(f"Case type '{case_type}' requires a URL")

    return {
        "newCase": {
            "title": title,
            "caseType": case_type,
            "brand": brand,
            "url": normalized_url,
            "description": description or "",
        }
    }


def create_case(
    client: PhishLabsClient,
    *,
    title: str,
    case_type: str,
    brand: str,
    url: str | None,
    description: str | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Create a case and return the confirmed response and legacy summary."""
    payload = build_new_case_payload(
        title=title,
        case_type=case_type,
        brand=brand,
        url=url,
        description=description,
    )
    response = process_response(client.request("post", "/create/newCase", data=payload))
    created_case = response.get("createdCase") if isinstance(response, dict) else None
    if not isinstance(created_case, dict) or not created_case.get("caseId"):
        raise PhishLabsAPIError("PhishLabs did not confirm ticket creation")

    summary = {
        "status": created_case.get("status"),
        "case_id": created_case.get("caseId"),
        "case_number": created_case.get("caseNumber"),
    }
    return {"createdCase": created_case}, summary


def create_ticket(
    params: CreateTicketParams, soar: SOARClient, asset: Asset
) -> CreateTicketOutput:
    """Create one PhishLabs case and report its confirmation."""
    try:
        output, summary = create_case(
            PhishLabsClient(asset.username, asset.password),
            title=params.title,
            case_type=params.case_type,
            brand=params.brand,
            url=params.url,
            description=params.description,
        )
    except (PhishLabsError, ValueError) as error:
        raise ActionFailure(str(error)) from error

    soar.set_summary(summary)
    soar.set_message(
        "Status: {status}, Case id: {case_id}, Case number: {case_number}".format(
            **summary
        )
    )
    return CreateTicketOutput(**output)
