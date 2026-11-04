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
from soar_sdk.abstract import SOARClient
from soar_sdk.app import App
from soar_sdk.params import Param, Params
from soar_sdk.action_results import ActionOutput, OutputField
from soar_sdk.asset import BaseAsset, AssetField
from soar_sdk.logging import getLogger

logger = getLogger()


class Asset(BaseAsset):
    username: str = AssetField(description="Username")
    password: str = AssetField(description="Password")


app = App(
    name="phishlabs",
    app_type="ticketing",
    logo="logo_phishlabs.svg",
    logo_dark="logo_phishlabs_dark.svg",
    product_vendor="PhishLabs",
    product_name="PhishLabs",
    publisher="Splunk",
    appid="ad83a63d-5564-4ea4-8f1f-3d71ec07c0d5",
    fips_compliant=True,
    encrypt_cache_state=True,
    encrypt_ingest_state=True,
    asset_cls=Asset,
)


@app.test_connectivity()
def test_connectivity(soar: SOARClient, asset: Asset) -> None:
    raise NotImplementedError()


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
    dateClosed: str = OutputField(example_values=["0001-01-01T00:00:00Z"])
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


@app.action(description="Get case (issue) information", action_type="generic")
def get_ticket(
    params: GetTicketParams, soar: SOARClient, asset: Asset
) -> GetTicketOutput:
    raise NotImplementedError()


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
    caseId: str = OutputField(example_values=["dbf4a861-2b1a-11ec-b1c8-0efb1918365c"])
    status: str = OutputField(example_values=["New"])
    caseNumber: float = OutputField(example_values=[2648042])


class CreateTicketOutput(ActionOutput):
    createdCase: CreatedcaseOutput
    updatedCase: UpdatedcaseOutput


@app.action(
    description="Create a new case submission", action_type="generic", read_only=False
)
def create_ticket(
    params: CreateTicketParams, soar: SOARClient, asset: Asset
) -> CreateTicketOutput:
    raise NotImplementedError()


class CreatedbyOutput(ActionOutput):
    id: str = OutputField(example_values=["b2aff1a8-0d16-11e8-9e8e-0ee0a3f3cb1c"])
    name: str = OutputField(example_values=["user"])
    displayName: str = OutputField(example_values=["Test User"])
    organization: str = OutputField(example_values=["Splunk"])


class QueryparamsOutput(ActionOutput):
    format: str = OutputField(example_values=["json"])


class HeaderOutput(ActionOutput):
    id: str = OutputField(example_values=["ef7d1b80-1756-11e8-822a-0a8e0de89b4e"])
    queryParams: QueryparamsOutput
    requestDate: str = OutputField(example_values=["2018-02-21T22:31:18.738015606Z"])
    returnResult: float = OutputField(example_values=[42])
    totalResult: float = OutputField(example_values=[42])
    user: str = OutputField(example_values=["user"])


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
    dateClosed: str = OutputField(example_values=["0001-01-01T00:00:00Z"])
    dateCreated: str = OutputField(example_values=["2018-02-21T22:30:13Z"])
    dateModified: str = OutputField(example_values=["2018-02-21T22:30:13Z"])
    description: str = OutputField(
        example_values=["This is my description\n\nhttp://suspiciousurl.com/1"]
    )
    formReceiver: bool = OutputField(example_values=[True])
    header: HeaderOutput
    notes: list[NotesOutput]
    resolutionStatus: str
    title: str = OutputField(example_values=["my_case_title"])
    appDate: str = OutputField(example_values=["0001-01-01T00:00:00Z"])
    sourceName: str = OutputField(example_values=["Client Submitted (CCAPI)"])
    brandAbuseFlag: bool
    sourcePhishlabs: bool
    primaryMarketplace: bool
    crimewareLoadFailure: bool
    attachments: list[AttachmentsOutput]
    resolution: str = OutputField(example_values=["This is a test case."])
    caseLinks: list[CaselinksOutput]


@app.action(description="Get a list of cases in PhishLabs", action_type="generic")
def list_tickets(params: Params, soar: SOARClient, asset: Asset) -> ListTicketsOutput:
    raise NotImplementedError()


class BrandsOutput(ActionOutput):
    name: str = OutputField(cef_types=["phishlabs brand"], example_values=["BRAND1"])


class CaseTypesOutput(ActionOutput):
    name: str = OutputField(
        cef_types=["phishlabs case type"], example_values=["Phishing"]
    )


class GetConfigOutput(ActionOutput):
    brands: list[BrandsOutput]
    case_types: list[CaseTypesOutput]


@app.action(
    description="Return the list of brands and case types currently configured in PhishLabs",
    action_type="investigate",
)
def get_config(params: Params, soar: SOARClient, asset: Asset) -> GetConfigOutput:
    raise NotImplementedError()


if __name__ == "__main__":
    app.cli()
