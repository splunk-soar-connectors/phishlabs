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
from urllib.parse import quote

import httpx
from soar_sdk.abstract import SOARClient
from soar_sdk.action_results import ActionOutput, OutputField
from soar_sdk.exceptions import ActionFailure
from soar_sdk.params import Param, Params

from ..asset import Asset
from ..auth import basic_auth
from .utils import (
    BASE_URL,
    DEFAULT_TIMEOUT,
    PhishLabsAPIError,
    http_status_message,
    response_json,
)


class GetTicketParams(Params):
    case_id: str = Param(
        description="Case Id", primary=True, cef_types=["phishlabs case id"]
    )


class CreatedbyOutput(ActionOutput):
    id: str = OutputField(example_values=["b2aff1a8-0d16-11e8-9e8e-0ee0a3f3cb1c"])
    name: str = OutputField(example_values=["user"])
    displayName: str = OutputField(example_values=["Test User"])
    organization: str = OutputField(example_values=["Splunk"])


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
    customer: str = OutputField(column_name="Customer", example_values=["Splunk"])
    caseType: str = OutputField(
        cef_types=["phishlabs case type"],
        column_name="Case Type",
        example_values=["Phishing"],
    )
    caseNumber: float = OutputField(column_name="Case Number", example_values=[714441])
    title: str = OutputField(column_name="Case Title", example_values=["my_case_title"])
    caseStatus: str = OutputField(column_name="Status", example_values=["New"])
    resolutionStatus: str | None = OutputField(
        column_name="Resolution Status",
        example_values=["No malicious content, referred to client."],
    )
    description: str = OutputField(
        column_name="Description",
        example_values=["This is my description\n\nhttp://suspiciousurl.com/1"],
    )
    dateCreated: str = OutputField(
        column_name="Date Created", example_values=["2018-02-21T22:30:13Z"]
    )
    dateClosed: str | None = OutputField(
        column_name="Date Closed", example_values=["0001-01-01T00:00:00Z"]
    )
    dateModified: str = OutputField(
        column_name="Date Modified", example_values=["2018-02-21T22:30:13Z"]
    )
    brand: str = OutputField(cef_types=["phishlabs brand"], example_values=["BRAND1"])
    caseId: str = OutputField(
        cef_types=["phishlabs case id"],
        example_values=["c88dc75c-1756-11e8-8a25-0a799650b9c8"],
    )
    createdBy: CreatedbyOutput
    formReceiver: bool = OutputField(example_values=[True])
    notes: list[NotesOutput] | None = OutputField()
    appDate: str | None = OutputField(example_values=["0001-01-01T00:00:00Z"])
    sourceName: str | None = OutputField(example_values=["Client Submitted (CCAPI)"])
    brandAbuseFlag: bool | None = OutputField(example_values=[True, False])
    sourcePhishlabs: bool | None = OutputField(example_values=[True, False])
    primaryMarketplace: bool | None = OutputField(example_values=[True, False])
    crimewareLoadFailure: bool | None = OutputField(example_values=[True, False])
    resolution: str | None = OutputField(example_values=["This is a test case"])


class GetTicketSummary(ActionOutput):
    case_id: str = OutputField(
        cef_types=["phishlabs case id"],
        example_values=["c88dc75c-1756-11e8-8a25-0a799650b9c8"],
    )
    return_result: float | None = OutputField(example_values=[1])
    total_result: float | None = OutputField(example_values=[1])


def get_ticket(
    params: GetTicketParams, soar: SOARClient, asset: Asset
) -> GetTicketOutput:
    """Return one case and its legacy summary fields."""
    case_id = params.case_id
    endpoint = quote(str(case_id), safe="")
    try:
        response = httpx.get(
            f"{BASE_URL}/data/cases/{endpoint}",
            auth=basic_auth(asset.username, asset.password),
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

    case_data = response_data.get("data") if isinstance(response_data, dict) else None
    if (
        not isinstance(case_data, list)
        or not case_data
        or not all(isinstance(case, dict) for case in case_data)
    ):
        raise ActionFailure(f"No case found for id {case_id}")

    normalized_case = dict(case_data[0])
    if str(normalized_case.get("dateClosed")) == "0001-01-01T00:00:00Z":
        normalized_case["dateClosed"] = None

    header = response_data.get("header")
    header = header if isinstance(header, dict) else {}
    return_result = header.get("returnResult")
    total_result = header.get("totalResult")
    summary = GetTicketSummary(
        case_id=case_id,
        return_result=return_result,
        total_result=total_result,
    )
    soar.set_summary(summary)
    soar.set_message(
        f"Case id: {summary.case_id}, Return result: {return_result}, Total result: {total_result}"
    )
    return GetTicketOutput(**normalized_case)
