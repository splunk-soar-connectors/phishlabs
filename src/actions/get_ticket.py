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
from urllib.parse import quote

from soar_sdk.abstract import SOARClient
from soar_sdk.action_results import ActionOutput, OutputField
from soar_sdk.exceptions import ActionFailure
from soar_sdk.params import Param, Params

from ..client import (
    PhishLabsAPIError,
    PhishLabsClient,
    PhishLabsError,
    process_response,
)
from ..app import Asset


class GetTicketParams(Params):
    case_id: str = Param(
        description="Case Id", primary=True, cef_types=["phishlabs case id"]
    )


class CreatedbyOutput(ActionOutput):
    id: str = OutputField(example_values=["b2aff1a8-0d16-11e8-9e8e-0ee0a3f3cb1c"])
    name: str = OutputField(example_values=["user"])
    displayName: str = OutputField(example_values=["Test User"])
    organization: str = OutputField(example_values=["Splunk"])


class QueryparamsOutput(ActionOutput):
    format: str = OutputField(example_values=["json"])


class HeaderOutput(ActionOutput):
    id: str = OutputField(example_values=["e08b33e0-1756-11e8-bd82-0a799650b9c8"])
    queryParams: QueryparamsOutput
    requestDate: str = OutputField(example_values=["2018-02-21T22:30:53.664564894Z"])
    returnResult: float = OutputField(example_values=[1])
    totalResult: float = OutputField(example_values=[1])
    user: str = OutputField(example_values=["user"])


class NotesOutput(ActionOutput):
    author: str = OutputField(example_values=["soap.api"])
    dateCreated: str = OutputField(example_values=["2018-03-12T08:48:05Z"])
    dateModified: str = OutputField(example_values=["2018-03-12T08:48:05Z"])
    note: str = OutputField(
        example_values=[
            "Case rejected.The client-submitted URL (https://www.suspiciousurl.com) is non-malicious."
        ]
    )


class GetTicketOutput(ActionOutput):
    brand: str = OutputField(cef_types=["phishlabs brand"], example_values=["BRAND1"])
    caseId: str = OutputField(
        cef_types=["phishlabs case id"],
        example_values=["c88dc75c-1756-11e8-8a25-0a799650b9c8"],
    )
    caseNumber: float = OutputField(example_values=[714441])
    caseStatus: str = OutputField(example_values=["New"])
    caseType: str = OutputField(
        cef_types=["phishlabs case type"], example_values=["Phishing"]
    )
    createdBy: CreatedbyOutput
    customer: str = OutputField(example_values=["Splunk"])
    dateClosed: str | None = OutputField(example_values=["0001-01-01T00:00:00Z"])
    dateCreated: str = OutputField(example_values=["2018-02-21T22:30:13Z"])
    dateModified: str = OutputField(example_values=["2018-02-21T22:30:13Z"])
    description: str = OutputField(
        example_values=["This is my description\n\nhttp://suspiciousurl.com/1"]
    )
    formReceiver: bool = OutputField(example_values=[True])
    header: HeaderOutput
    notes: list[NotesOutput]
    resolutionStatus: str = OutputField(
        example_values=["No malicious content, referred to client."]
    )
    title: str = OutputField(example_values=["my_case_title"])
    appDate: str = OutputField(example_values=["0001-01-01T00:00:00Z"])
    sourceName: str = OutputField(example_values=["Client Submitted (CCAPI)"])
    brandAbuseFlag: bool
    sourcePhishlabs: bool
    primaryMarketplace: bool
    crimewareLoadFailure: bool
    resolution: str = OutputField(example_values=["This is a test case"])


class GetTicketSummary(ActionOutput):
    case_id: str = OutputField(example_values=["c88dc75c-1756-11e8-8a25-0a799650b9c8"])
    return_result: float | None = OutputField(example_values=[1])
    total_result: float | None = OutputField(example_values=[1])


def fetch_case(
    case_id: str, client: PhishLabsClient
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Fetch and normalize one case while keeping HTTP details in the client."""
    endpoint = f"/data/cases/{quote(str(case_id), safe='')}"
    response = process_response(client.request("get", endpoint))
    case_data = response.get("data") if isinstance(response, dict) else None
    if (
        not isinstance(case_data, list)
        or not case_data
        or not all(isinstance(case, dict) for case in case_data)
    ):
        raise PhishLabsAPIError(f"No case found for id {case_id}")

    normalized_case = dict(case_data[0])
    if str(normalized_case.get("dateClosed")) == "0001-01-01T00:00:00Z":
        normalized_case["dateClosed"] = None

    header = response.get("header")
    header = header if isinstance(header, dict) else {}
    summary = {
        "case_id": case_id,
        "return_result": header.get("returnResult"),
        "total_result": header.get("totalResult"),
    }
    return normalized_case, summary


def get_ticket(
    params: GetTicketParams, soar: SOARClient, asset: Asset
) -> GetTicketOutput:
    """Return one case and its legacy summary fields."""
    try:
        case, summary = fetch_case(
            params.case_id, PhishLabsClient(asset.username, asset.password)
        )
    except PhishLabsError as error:
        raise ActionFailure(str(error)) from error

    soar.set_summary(summary)
    soar.set_message(
        "Case id: {case_id}, Return result: {return_result}, Total result: {total_result}".format(
            **summary
        )
    )
    return GetTicketOutput(**case)
