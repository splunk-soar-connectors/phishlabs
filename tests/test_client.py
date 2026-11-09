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
import base64
import importlib
import json
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from typing import Any

import pytest
from soar_sdk.action_results import ActionResult
from soar_sdk.exceptions import ActionFailure
from soar_sdk.params import MakeRequestParams, Params

from src import app as app_module

create_ticket_module = importlib.import_module("src.actions.create_ticket")
get_config_module = importlib.import_module("src.actions.get_config")
get_ticket_module = importlib.import_module("src.actions.get_ticket")
list_tickets_module = importlib.import_module("src.actions.list_tickets")
make_request_module = importlib.import_module("src.actions.make_request")
connectivity_module = importlib.import_module("src.actions.test_connectivity")
from src.actions.create_ticket import CreateTicketParams, create_ticket
from src.actions.get_config import get_config
from src.actions.get_ticket import GetTicketParams, get_ticket
from src.actions.list_tickets import list_tickets
from src.actions.make_request import make_request
from src.actions.test_connectivity import run_test_connectivity
from src.asset import Asset


@contextmanager
def _serve(
    routes: dict[str, tuple[int, str]],
) -> Iterator[tuple[str, list[tuple[str, str, str | None, bytes]]]]:
    observed: list[tuple[str, str, str | None, bytes]] = []

    class Handler(BaseHTTPRequestHandler):
        def _respond(self) -> None:
            request_body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            observed.append(
                (
                    self.command,
                    self.path,
                    self.headers.get("Authorization"),
                    request_body,
                )
            )
            status, body = routes[self.path]
            response_body = body.encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response_body)))
            self.end_headers()
            self.wfile.write(response_body)

        do_GET = _respond
        do_POST = _respond

        def log_message(self, fmt: str, *args: object) -> None:
            del fmt, args

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}", observed
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def _use_test_server(
    monkeypatch: pytest.MonkeyPatch, module: Any, base_url: str
) -> None:
    """Point one action at the real loopback HTTP server used by a test."""
    monkeypatch.setattr(module, "BASE_URL", base_url)


def _asset() -> Asset:
    credential_value = "pw"
    return Asset(username="test-user", password=credential_value)


def _case_payload(case_id: str, date_closed: str | None) -> dict[str, Any]:
    return {
        "brand": "Brand A",
        "caseId": case_id,
        "caseNumber": 123,
        "caseStatus": "New",
        "caseType": "Phishing",
        "createdBy": {
            "id": "user-id",
            "name": "user",
            "displayName": "Test User",
            "organization": "Splunk",
        },
        "customer": "Splunk",
        "dateClosed": date_closed,
        "dateCreated": "2018-02-21T22:30:13Z",
        "dateModified": "2018-02-21T22:30:13Z",
        "description": "test case",
        "formReceiver": True,
        "header": {
            "id": "header-id",
            "queryParams": {"format": "json"},
            "requestDate": "2018-02-21T22:30:53Z",
            "returnResult": 1,
            "totalResult": 1,
            "user": "user",
        },
        "notes": [],
        "resolutionStatus": "Open",
        "title": "test case",
        "appDate": "0001-01-01T00:00:00Z",
        "sourceName": "Client Submitted (CCAPI)",
        "brandAbuseFlag": False,
        "sourcePhishlabs": True,
        "primaryMarketplace": False,
        "crimewareLoadFailure": False,
        "resolution": "",
    }


def _list_case_payload(case_id: str, date_closed: str | None) -> dict[str, Any]:
    return {
        **_case_payload(case_id, date_closed),
        "attachments": [],
        "caseLinks": [],
    }


def test_list_tickets_uses_basic_auth_and_legacy_summary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = json.dumps({"data": [], "header": {"totalResult": 0}})
    with _serve({"/data/cases": (200, body)}) as (base_url, observed):
        _use_test_server(monkeypatch, list_tickets_module, base_url)
        result = list_tickets(Params(), app_module.app.soar_client, _asset())

    expected_auth = "Basic " + base64.b64encode(b"test-user:pw").decode()
    assert result == []
    assert observed == [("GET", "/data/cases", expected_auth, b"")]
    assert app_module.app.soar_client.get_summary().total_cases == 0
    assert app_module.app.soar_client.get_message() == "Total cases: 0"


def test_list_tickets_sanitizes_http_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    private_detail = "private vendor response"
    with _serve({"/data/cases": (503, json.dumps({"message": private_detail}))}) as (
        base_url,
        _observed,
    ):
        _use_test_server(monkeypatch, list_tickets_module, base_url)
        with pytest.raises(ActionFailure, match="HTTP 503") as error:
            list_tickets(Params(), app_module.app.soar_client, _asset())

    assert private_detail not in str(error.value)


def test_list_tickets_paginates_and_normalizes_open_case_dates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = _list_case_payload("case-1", "0001-01-01T00:00:00Z")
    second = _list_case_payload("case-2", "2021-10-01T00:00:00Z")
    routes = {
        "/data/cases": (
            200,
            json.dumps({"data": [first], "header": {"totalResult": 2}}),
        ),
        "/data/cases?offset=1": (
            200,
            json.dumps({"data": [second], "header": {"totalResult": 2}}),
        ),
    }
    with _serve(routes) as (base_url, observed):
        _use_test_server(monkeypatch, list_tickets_module, base_url)
        result = list_tickets(Params(), app_module.app.soar_client, _asset())

    assert [case.caseId for case in result] == ["case-1", "case-2"]
    assert result[0].dateClosed is None
    assert result[1].dateClosed == "2021-10-01T00:00:00Z"
    assert [request[1] for request in observed] == [
        "/data/cases",
        "/data/cases?offset=1",
    ]
    assert app_module.app.soar_client.get_summary().total_cases == 2


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ('{"data": {}, "header": {"totalResult": 0}}', "invalid case data"),
        ('{"data": [], "header": {"totalResult": -1}}', "invalid total case count"),
        ('{"data": [], "header": {"totalResult": 2}}', "incomplete case listing"),
    ],
)
def test_list_tickets_rejects_invalid_page_data(
    monkeypatch: pytest.MonkeyPatch, body: str, message: str
) -> None:
    with _serve({"/data/cases": (200, body)}) as (base_url, _observed):
        _use_test_server(monkeypatch, list_tickets_module, base_url)
        with pytest.raises(ActionFailure, match=message):
            list_tickets(Params(), app_module.app.soar_client, _asset())


def test_list_tickets_stops_at_the_page_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(list_tickets_module, "MAX_PAGE_COUNT", 2)
    page = json.dumps(
        {"data": [_list_case_payload("case-1", None)], "header": {"totalResult": 3}}
    )
    routes = {"/data/cases": (200, page), "/data/cases?offset=1": (200, page)}
    with _serve(routes) as (base_url, observed):
        _use_test_server(monkeypatch, list_tickets_module, base_url)
        with pytest.raises(ActionFailure, match="safety limit"):
            list_tickets(Params(), app_module.app.soar_client, _asset())

    assert len(observed) == 2


def test_get_ticket_quotes_case_identifier(monkeypatch: pytest.MonkeyPatch) -> None:
    with _serve({"/data/cases/case%20id%2F1": (200, '{"data": []}')}) as (
        base_url,
        observed,
    ):
        _use_test_server(monkeypatch, get_ticket_module, base_url)
        with pytest.raises(ActionFailure, match="No case found for id"):
            get_ticket(
                GetTicketParams(case_id="case id/1"),
                app_module.app.soar_client,
                _asset(),
            )

    assert observed[0][1] == "/data/cases/case%20id%2F1"


def test_get_ticket_returns_case_and_legacy_summary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case = _case_payload("case-123", "0001-01-01T00:00:00Z")
    body = json.dumps(
        {
            "data": [case, {**case, "caseId": "unrequested-case"}],
            "header": {"returnResult": 1, "totalResult": 2},
        }
    )
    with _serve({"/data/cases/case-123": (200, body)}) as (base_url, observed):
        _use_test_server(monkeypatch, get_ticket_module, base_url)
        result = get_ticket(
            GetTicketParams(case_id="case-123"),
            app_module.app.soar_client,
            _asset(),
        )

    assert result.caseId == "case-123"
    assert result.dateClosed is None
    assert observed[0][1] == "/data/cases/case-123"
    assert app_module.app.soar_client.get_summary().return_result == 1


def test_create_ticket_sends_legacy_body_and_summary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = json.dumps(
        {
            "createdCase": {
                "caseId": "case-123",
                "caseNumber": 714441,
                "status": "New",
            },
            "updatedCase": {
                "caseId": "updated-case-456",
                "caseNumber": 714442,
                "status": "Updated",
            },
        }
    )
    with _serve({"/create/newCase": (200, body)}) as (base_url, observed):
        _use_test_server(monkeypatch, create_ticket_module, base_url)
        result = create_ticket(
            CreateTicketParams(
                title="A test case",
                case_type="Phishing",
                brand="Example brand",
                url="https://example.invalid/report",
                description=None,
            ),
            app_module.app.soar_client,
            _asset(),
        )

    assert observed[0][0:2] == ("POST", "/create/newCase")
    assert observed[0][2] == "Basic " + base64.b64encode(b"test-user:pw").decode()
    assert json.loads(observed[0][3]) == {
        "newCase": {
            "title": "A test case",
            "caseType": "Phishing",
            "brand": "Example brand",
            "url": "https://example.invalid/report",
            "description": "",
        }
    }
    assert result.model_dump(by_alias=True) == {
        "createdCase": {
            "caseId": "case-123",
            "caseNumber": 714441.0,
            "status": "New",
        },
        "updatedCase": {
            "caseId": "updated-case-456",
            "caseNumber": 714442.0,
            "status": "Updated",
        },
    }
    assert app_module.app.soar_client.get_summary().case_id == "case-123"


@pytest.mark.parametrize("case_type", ["Phishing", "Phishing Redirect"])
def test_create_ticket_requires_url_before_sending(
    monkeypatch: pytest.MonkeyPatch, case_type: str
) -> None:
    with _serve({}) as (base_url, observed):
        _use_test_server(monkeypatch, create_ticket_module, base_url)
        with pytest.raises(ActionFailure, match="requires a URL"):
            create_ticket(
                CreateTicketParams(
                    title="A test case",
                    case_type=case_type,
                    brand="Example brand",
                    url=None,
                    description=None,
                ),
                app_module.app.soar_client,
                _asset(),
            )

    assert observed == []


def test_create_ticket_requires_confirmed_case_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with _serve({"/create/newCase": (200, '{"createdCase": {"status": "New"}}')}) as (
        base_url,
        _observed,
    ):
        _use_test_server(monkeypatch, create_ticket_module, base_url)
        with pytest.raises(ActionFailure, match="did not confirm ticket creation"):
            create_ticket(
                CreateTicketParams(
                    title="A test case",
                    case_type="Malware",
                    brand="Example brand",
                    url=None,
                    description=None,
                ),
                app_module.app.soar_client,
                _asset(),
            )


def test_create_ticket_sanitizes_http_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    private_detail = "private create response"
    with _serve(
        {"/create/newCase": (503, json.dumps({"message": private_detail}))}
    ) as (base_url, _observed):
        _use_test_server(monkeypatch, create_ticket_module, base_url)
        with pytest.raises(ActionFailure, match="HTTP 503") as error:
            create_ticket(
                CreateTicketParams(
                    title="A test case",
                    case_type="Malware",
                    brand="Example brand",
                    url=None,
                    description=None,
                ),
                app_module.app.soar_client,
                _asset(),
            )

    assert private_detail not in str(error.value)


def test_get_config_returns_combined_sdk_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    routes = {
        "/create/brands": (302, '{"brands": ["Brand A", 17]}'),
        "/create/caseTypes": (200, '{"caseType": ["Phishing", "Malware"]}'),
    }
    with _serve(routes) as (base_url, observed):
        _use_test_server(monkeypatch, get_config_module, base_url)
        result = get_config(Params(), app_module.app.soar_client, _asset())

    assert result.model_dump() == {
        "brands": [{"name": "Brand A"}, {"name": "17"}],
        "case_types": [{"name": "Phishing"}, {"name": "Malware"}],
    }
    assert app_module.app.soar_client.get_summary().num_brands == 2
    assert app_module.app.soar_client.get_summary().num_case_types == 2
    assert app_module.app.soar_client.get_message() == (
        "Num case types: 2, Num brands: 2"
    )
    assert [request[1] for request in observed] == [
        "/create/brands",
        "/create/caseTypes",
    ]


def test_get_config_preserves_brands_on_case_type_http_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private_detail = "private case type response"
    routes = {
        "/create/brands": (200, '{"brands": ["Brand A"]}'),
        "/create/caseTypes": (
            503,
            json.dumps({"message": private_detail}),
        ),
    }
    with _serve(routes) as (base_url, observed):
        _use_test_server(monkeypatch, get_config_module, base_url)
        result = get_config(Params(), app_module.app.soar_client, _asset())

    assert isinstance(result, ActionResult)
    assert result.get_status() is False
    assert result.get_data() == [{"brands": [{"name": "Brand A"}]}]
    assert "HTTP 503" in result.get_message()
    assert private_detail not in result.get_message()
    assert [request[1] for request in observed] == [
        "/create/brands",
        "/create/caseTypes",
    ]


def test_get_config_preserves_brands_on_invalid_case_type_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    routes = {
        "/create/brands": (200, '{"brands": ["Brand A"]}'),
        "/create/caseTypes": (200, '{"caseType": {"bad": "shape"}}'),
    }
    with _serve(routes) as (base_url, _observed):
        _use_test_server(monkeypatch, get_config_module, base_url)
        result = get_config(Params(), app_module.app.soar_client, _asset())

    assert isinstance(result, ActionResult)
    assert result.get_data() == [{"brands": [{"name": "Brand A"}]}]
    assert "invalid case type data" in result.get_message()


def test_get_config_rejects_invalid_brand_response_before_second_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    routes = {
        "/create/brands": (200, '{"brands": {"bad": "shape"}}'),
        "/create/caseTypes": (200, '{"caseType": ["Phishing"]}'),
    }
    with _serve(routes) as (base_url, observed):
        _use_test_server(monkeypatch, get_config_module, base_url)
        with pytest.raises(ActionFailure, match="invalid brand data"):
            get_config(Params(), app_module.app.soar_client, _asset())

    assert [request[1] for request in observed] == ["/create/brands"]


def test_connectivity_checks_cases_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    with _serve({"/data/cases": (200, '{"data": []}')}) as (
        base_url,
        observed,
    ):
        _use_test_server(monkeypatch, connectivity_module, base_url)
        run_test_connectivity("test-user", "test-password")

    assert observed[0][0:2] == ("GET", "/data/cases")


def test_make_request_returns_sdk_status_and_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with _serve({"/data/cases": (404, '{"message": "not found"}')}) as (
        base_url,
        observed,
    ):
        _use_test_server(monkeypatch, make_request_module, base_url)
        result = make_request(
            MakeRequestParams(http_method="GET", endpoint="/data/cases"),
            _asset(),
        )

    assert result.status_code == 404
    assert result.response_body == '{"message": "not found"}'
    assert observed[0][0:2] == ("GET", "/data/cases")


def test_make_request_accepts_query_string(monkeypatch: pytest.MonkeyPatch) -> None:
    with _serve({"/data/cases?limit=1": (200, '{"data": []}')}) as (
        base_url,
        observed,
    ):
        _use_test_server(monkeypatch, make_request_module, base_url)
        result = make_request(
            MakeRequestParams(
                http_method="GET",
                endpoint="data/cases",
                query_parameters="?limit=1",
            ),
            _asset(),
        )

    assert result.status_code == 200
    assert observed[0][1] == "/data/cases?limit=1"


def test_make_request_rejects_absolute_endpoint_before_sending() -> None:
    with pytest.raises(ActionFailure, match="Endpoint must be relative"):
        make_request(
            MakeRequestParams(
                http_method="GET",
                endpoint="https://example.invalid/data/cases",
            ),
            _asset(),
        )
