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
from soar_sdk.abstract import SOARClient
from soar_sdk.action_results import ActionOutput, OutputField
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

MAX_PAGE_COUNT = 500
OPEN_DATE_SENTINEL = "0001-01-01T00:00:00Z"


class CreatedbyOutput(ActionOutput):
    id: str = OutputField(example_values=["b2aff1a8-0d16-11e8-9e8e-0ee0a3f3cb1c"])
    name: str = OutputField(example_values=["user"])
    displayName: str = OutputField(example_values=["Test User"])
    organization: str = OutputField(example_values=["Splunk"])


class NotesOutput(ActionOutput):
    author: str = OutputField(example_values=["soc"])
    dateCreated: str = OutputField(example_values=["2018-02-21T03:24:14Z"])
    dateModified: str = OutputField(example_values=["2018-02-21T03:24:14Z"])
    note: str = OutputField(
        example_values=[
            "Whois info for www.invalidurl.com:\nRecord last updated: 2018-02-20\nWhois record:\n\tDomain Name: InvalidUrl.com\nRegistry Domain ID: 1614701904_DOMAIN_COM-VRSN\nRegistrar WHOIS server: whois.NameBright.com\nRegistrar URL: http://www.NameBright.com\nUpdated Date: 2017-09-08T00:00:00.000Z\nCreation Date: 2010-09-07T18:49:01.000Z\nRegistrar Registration Expiration Date: 2018-09-07T00:00:00.000Z\nRegistrar: TurnCommerce, Inc. DBA NameBright.com..."
        ]
    )


class AttachmentsOutput(ActionOutput):
    id: str = OutputField(example_values=["1b27a1db-2a97-11ec-984b-0ad24386a0d6"])
    type: str = OutputField(example_values=["Email"])
    fileURL: str = OutputField(
        example_values=[
            "https://caseapi.phishlabs.com/v1/data/attachment/1b27a1db-2a97-11ec-984b-0ad24386a0d6"
        ]
    )
    fileName: str = OutputField(
        example_values=["requested-screenshot-2021-10-11T13:28:22Z.jpg"]
    )
    dateAdded: str = OutputField(example_values=["2021-10-11T13:28:22Z"])
    description: str = OutputField(
        example_values=["Automatic Screenshot for submitted URL"]
    )


class CaselinksOutput(ActionOutput):
    title: str = OutputField(example_values=["test1"])
    caseId: str = OutputField(example_values=["5a0321e3-273d-11ec-b912-0a8e0de89b4e"])
    caseType: str = OutputField(example_values=["Phishing"])
    linkType: str = OutputField(example_values=["Clone"])
    caseNumber: float = OutputField(example_values=[2639769])
    caseStatus: str = OutputField(example_values=["Rejected"])
    linkCreated: str = OutputField(example_values=["2021-10-11T13:48:55.568376569Z"])


class ListTicketsOutput(ActionOutput):
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
    dateClosed: str | None = OutputField(example_values=[OPEN_DATE_SENTINEL])
    dateCreated: str = OutputField(example_values=["2018-02-21T22:30:13Z"])
    dateModified: str = OutputField(example_values=["2018-02-21T22:30:13Z"])
    description: str = OutputField(
        example_values=["This is my description\n\nhttp://suspiciousurl.com/1"]
    )
    formReceiver: bool = OutputField(example_values=[True])
    notes: list[NotesOutput] | None = OutputField()
    resolutionStatus: str | None = OutputField()
    title: str = OutputField(example_values=["my_case_title"])
    appDate: str | None = OutputField(example_values=["0001-01-01T00:00:00Z"])
    sourceName: str | None = OutputField(example_values=["Client Submitted (CCAPI)"])
    brandAbuseFlag: bool | None = OutputField(example_values=[True, False])
    sourcePhishlabs: bool | None = OutputField(example_values=[True, False])
    primaryMarketplace: bool | None = OutputField(example_values=[True, False])
    crimewareLoadFailure: bool | None = OutputField(example_values=[True, False])
    attachments: list[AttachmentsOutput] | None = OutputField()
    resolution: str | None = OutputField(example_values=["This is a test case."])
    caseLinks: list[CaselinksOutput] | None = OutputField()


class ListTicketsSummary(ActionOutput):
    total_cases: float = OutputField(example_values=[42])


def list_tickets(
    params: Params, soar: SOARClient, asset: Asset
) -> list[ListTicketsOutput]:
    """List PhishLabs cases across all pages."""
    del params
    cases: list[dict[str, Any]] = []
    offset = 0

    for _ in range(MAX_PAGE_COUNT):
        query = {"offset": offset} if offset else None
        try:
            response = httpx.get(
                f"{BASE_URL}/data/cases",
                auth=basic_auth(asset.username, asset.password),
                params=query,
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

        page = response_data.get("data") if isinstance(response_data, dict) else None
        if not isinstance(page, list) or not all(
            isinstance(item, dict) for item in page
        ):
            raise ActionFailure("PhishLabs returned invalid case data")

        for item in page:
            normalized = dict(item)
            if str(normalized.get("dateClosed")) == OPEN_DATE_SENTINEL:
                normalized["dateClosed"] = None
            cases.append(normalized)

        offset += len(page)
        header = response_data.get("header")
        total_cases = header.get("totalResult") if isinstance(header, dict) else None
        if not isinstance(total_cases, int) or total_cases < 0:
            raise ActionFailure("PhishLabs returned an invalid total case count")
        if offset >= total_cases:
            summary = ListTicketsSummary(total_cases=total_cases)
            soar.set_summary(summary)
            soar.set_message(f"Total cases: {total_cases}")
            return [ListTicketsOutput(**case) for case in cases]
        if not page:
            raise ActionFailure("PhishLabs returned an incomplete case listing")

    raise ActionFailure("PhishLabs case pagination exceeded the safety limit")
