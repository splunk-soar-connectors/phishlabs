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
import json
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

import pytest

from src.client import PhishLabsAPIError, PhishLabsClient, process_response
from src.actions.create_ticket import create_case
from src.actions.get_config import config_message, fetch_config
from src.actions.get_ticket import fetch_case
from src.actions.list_tickets import fetch_cases
from soar_sdk.action_results import ActionResult
from soar_sdk.params import Params


@contextmanager
def _serve_response(
    status: int, content_type: str, body: str
) -> Iterator[tuple[str, list[tuple[str, str | None]]]]:
    requests: list[tuple[str, str | None]] = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            requests.append((self.path, self.headers.get("Authorization")))
            response_body = body.encode()
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(response_body)))
            self.end_headers()
            self.wfile.write(response_body)

        def log_message(self, fmt: str, *args: object) -> None:
            del fmt, args

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}", requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@contextmanager
def _serve_post_response(
    status: int, body: str
) -> Iterator[tuple[str, list[tuple[str, str | None, bytes]]]]:
    requests: list[tuple[str, str | None, bytes]] = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            request_body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            requests.append(
                (self.path, self.headers.get("Authorization"), request_body)
            )
            response_body = body.encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response_body)))
            self.end_headers()
            self.wfile.write(response_body)

        def log_message(self, fmt: str, *args: object) -> None:
            del fmt, args

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}", requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@contextmanager
def _serve_get_pages(
    bodies: list[str],
) -> Iterator[tuple[str, list[tuple[str, str | None]]]]:
    requests: list[tuple[str, str | None]] = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            page_index = len(requests)
            requests.append((self.path, self.headers.get("Authorization")))
            response_body = bodies[min(page_index, len(bodies) - 1)].encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response_body)))
            self.end_headers()
            self.wfile.write(response_body)

        def log_message(self, fmt: str, *args: object) -> None:
            del fmt, args

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}", requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@contextmanager
def _serve_get_routes(
    routes: dict[str, tuple[int, str]],
) -> Iterator[tuple[str, list[tuple[str, str | None]]]]:
    requests: list[tuple[str, str | None]] = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            requests.append((self.path, self.headers.get("Authorization")))
            status, body = routes[self.path]
            response_body = body.encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response_body)))
            self.end_headers()
            self.wfile.write(response_body)

        def log_message(self, fmt: str, *args: object) -> None:
            del fmt, args

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}", requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_request_uses_basic_auth_and_cases_path() -> None:
    username = "test-user"
    credential_value = "pw"
    expected_auth = (
        "Basic " + base64.b64encode(f"{username}:{credential_value}".encode()).decode()
    )

    with _serve_response(200, "application/json", '{"cases": []}') as (
        base_url,
        observed_requests,
    ):
        client = PhishLabsClient(username, credential_value, base_url=base_url)
        response = client.request("get", "/data/cases")

    assert process_response(response) == {"cases": []}
    assert observed_requests == [("/data/cases", expected_auth)]


def test_error_response_does_not_expose_response_body() -> None:
    private_detail = "response detail that should not appear in the error"

    with _serve_response(
        401,
        "application/json",
        json.dumps({"message": private_detail}),
    ) as (base_url, _observed_requests):
        client = PhishLabsClient("test-user", "test-password", base_url=base_url)
        response = client.request("get", "/data/cases")

    with pytest.raises(PhishLabsAPIError, match="HTTP 401") as error:
        process_response(response)
    assert private_detail not in str(error.value)


def test_fetch_case_quotes_identifier_and_preserves_legacy_normalization() -> None:
    case = {"caseId": "case id/1", "dateClosed": "0001-01-01T00:00:00Z"}
    response_body = json.dumps(
        {
            "data": [case, {"caseId": "second"}],
            "header": {"returnResult": 1, "totalResult": 2},
        }
    )

    with _serve_response(200, "application/json", response_body) as (
        base_url,
        observed_requests,
    ):
        client = PhishLabsClient("test-user", "test-password", base_url=base_url)
        normalized_case, summary = fetch_case("case id/1", client)

    assert observed_requests[0][0] == "/data/cases/case%20id%2F1"
    assert normalized_case == {"caseId": "case id/1", "dateClosed": None}
    assert summary == {
        "case_id": "case id/1",
        "return_result": 1,
        "total_result": 2,
    }


def test_fetch_case_rejects_empty_or_malformed_case_data() -> None:
    for data in ([], [None], "not-a-list"):
        with _serve_response(
            200,
            "application/json",
            json.dumps({"data": data}),
        ) as (base_url, _observed_requests):
            client = PhishLabsClient("test-user", "test-password", base_url=base_url)
            with pytest.raises(PhishLabsAPIError, match="No case found for id case-1"):
                fetch_case("case-1", client)


def test_fetch_case_reports_http_status_without_vendor_body() -> None:
    private_detail = "private case lookup detail"

    with _serve_response(
        404,
        "application/json",
        json.dumps({"message": private_detail}),
    ) as (base_url, _observed_requests):
        client = PhishLabsClient("test-user", "test-password", base_url=base_url)
        with pytest.raises(PhishLabsAPIError, match="HTTP 404") as error:
            fetch_case("case-1", client)

    assert private_detail not in str(error.value)


def test_create_case_posts_legacy_body_and_returns_created_case_summary() -> None:
    response_body = json.dumps(
        {
            "createdCase": {
                "caseId": "case-123",
                "caseNumber": 714441,
                "status": "New",
            },
            "updatedCase": {"caseId": "stale-field-must-not-be-returned"},
        }
    )
    with _serve_post_response(200, response_body) as (base_url, observed_requests):
        client = PhishLabsClient("test-user", "test-password", base_url=base_url)
        output, summary = create_case(
            client,
            title="A test case",
            case_type="Phishing",
            brand="Example brand",
            url="https://example.invalid/report",
            description=None,
        )

    assert observed_requests[0][0] == "/create/newCase"
    assert (
        observed_requests[0][1]
        == "Basic " + base64.b64encode(b"test-user:test-password").decode()
    )
    assert json.loads(observed_requests[0][2]) == {
        "newCase": {
            "title": "A test case",
            "caseType": "Phishing",
            "brand": "Example brand",
            "url": "https://example.invalid/report",
            "description": "",
        }
    }
    assert output == {
        "createdCase": {"caseId": "case-123", "caseNumber": 714441, "status": "New"}
    }
    assert summary == {
        "status": "New",
        "case_id": "case-123",
        "case_number": 714441,
    }


@pytest.mark.parametrize("case_type", ["Phishing", "Phishing Redirect"])
def test_create_case_requires_url_for_url_based_types(case_type: str) -> None:
    with _serve_post_response(200, "{}") as (base_url, observed_requests):
        client = PhishLabsClient("test-user", "test-password", base_url=base_url)
        with pytest.raises(ValueError, match=f"Case type '{case_type}' requires a URL"):
            create_case(
                client,
                title="A test case",
                case_type=case_type,
                brand="Example brand",
                url=None,
                description=None,
            )

    assert observed_requests == []


def test_create_case_rejects_unconfirmed_creation_without_exposing_body() -> None:
    private_detail = "private vendor response"
    with _serve_post_response(
        200,
        json.dumps({"message": private_detail, "createdCase": {"status": "New"}}),
    ) as (base_url, _observed_requests):
        client = PhishLabsClient("test-user", "test-password", base_url=base_url)
        with pytest.raises(
            PhishLabsAPIError, match="did not confirm ticket creation"
        ) as error:
            create_case(
                client,
                title="A test case",
                case_type="Malware",
                brand="Example brand",
                url=None,
                description=None,
            )

    assert private_detail not in str(error.value)


def test_fetch_cases_paginates_normalizes_and_reports_total() -> None:
    first_case = {"caseId": "case-1", "dateClosed": "0001-01-01T00:00:00Z"}
    second_case = {"caseId": "case-2", "dateClosed": "2021-10-01T00:00:00Z"}
    bodies = [
        json.dumps({"data": [first_case], "header": {"totalResult": 2}}),
        json.dumps({"data": [second_case], "header": {"totalResult": 2}}),
    ]

    with _serve_get_pages(bodies) as (base_url, observed_requests):
        client = PhishLabsClient("test-user", "test-password", base_url=base_url)
        cases, total_cases = fetch_cases(client)

    assert [request[0] for request in observed_requests] == [
        "/data/cases",
        "/data/cases?offset=1",
    ]
    assert cases == [
        {"caseId": "case-1", "dateClosed": None},
        second_case,
    ]
    assert total_cases == 2


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ('{"data": {}}', "invalid case data"),
        ('{"data": [], "header": {"totalResult": -1}}', "invalid total case count"),
        ('{"data": [], "header": {"totalResult": 2}}', "incomplete case listing"),
    ],
)
def test_fetch_cases_validates_pages_and_headers(body: str, message: str) -> None:
    with _serve_get_pages([body]) as (base_url, _observed_requests):
        client = PhishLabsClient("test-user", "test-password", base_url=base_url)
        with pytest.raises(PhishLabsAPIError, match=message):
            fetch_cases(client)


def test_fetch_cases_stops_at_the_page_safety_limit() -> None:
    page = json.dumps({"data": [{"caseId": "case-1"}], "header": {"totalResult": 3}})
    with _serve_get_pages([page]) as (base_url, observed_requests):
        client = PhishLabsClient("test-user", "test-password", base_url=base_url)
        with pytest.raises(PhishLabsAPIError, match="safety limit"):
            fetch_cases(client, max_page_count=2)

    assert len(observed_requests) == 2


def test_fetch_cases_accepts_zero_total_with_an_empty_page() -> None:
    body = json.dumps({"data": [], "header": {"totalResult": 0}})
    with _serve_get_pages([body]) as (base_url, observed_requests):
        client = PhishLabsClient("test-user", "test-password", base_url=base_url)
        cases, total_cases = fetch_cases(client)

    assert cases == []
    assert total_cases == 0
    assert len(observed_requests) == 1


def test_fetch_config_calls_endpoints_in_order_and_returns_legacy_summary() -> None:
    routes = {
        "/create/brands": (200, json.dumps({"brands": ["Brand A", 17]})),
        "/create/caseTypes": (
            200,
            json.dumps({"caseType": ["Phishing", "Malware"]}),
        ),
    }
    with _serve_get_routes(routes) as (base_url, observed_requests):
        client = PhishLabsClient("test-user", "test-password", base_url=base_url)
        result = fetch_config(client, Params())

    assert not isinstance(result, ActionResult)
    output, summary = result
    assert output.model_dump() == {
        "brands": [{"name": "Brand A"}, {"name": "17"}],
        "case_types": [{"name": "Phishing"}, {"name": "Malware"}],
    }
    assert summary == {"num_brands": 2, "num_case_types": 2}
    assert config_message(summary) == "Num case types: 2, Num brands: 2"
    assert [path for path, _auth in observed_requests] == [
        "/create/brands",
        "/create/caseTypes",
    ]


def test_fetch_config_rejects_invalid_brand_list_before_second_request() -> None:
    routes = {
        "/create/brands": (200, json.dumps({"brands": {"bad": "shape"}})),
        "/create/caseTypes": (200, json.dumps({"caseType": ["Phishing"]})),
    }
    with _serve_get_routes(routes) as (base_url, observed_requests):
        client = PhishLabsClient("test-user", "test-password", base_url=base_url)
        with pytest.raises(PhishLabsAPIError, match="invalid brand data"):
            fetch_config(client, Params())

    assert [path for path, _auth in observed_requests] == ["/create/brands"]


def test_fetch_config_first_request_failure_is_sanitized() -> None:
    private_detail = "private brand endpoint response"
    routes = {
        "/create/brands": (503, json.dumps({"message": private_detail})),
        "/create/caseTypes": (200, json.dumps({"caseType": ["Phishing"]})),
    }
    with _serve_get_routes(routes) as (base_url, observed_requests):
        client = PhishLabsClient("test-user", "test-password", base_url=base_url)
        with pytest.raises(PhishLabsAPIError, match="HTTP 503") as error:
            fetch_config(client, Params())

    assert private_detail not in str(error.value)
    assert [path for path, _auth in observed_requests] == ["/create/brands"]


def test_fetch_config_second_request_failure_retains_partial_brands_safely() -> None:
    private_detail = "private case-type endpoint response"
    routes = {
        "/create/brands": (200, json.dumps({"brands": ["Brand A"]})),
        "/create/caseTypes": (503, json.dumps({"message": private_detail})),
    }
    with _serve_get_routes(routes) as (base_url, observed_requests):
        client = PhishLabsClient("test-user", "test-password", base_url=base_url)
        result = fetch_config(client, Params())

    assert isinstance(result, ActionResult)
    assert result.get_status() is False
    assert result.get_data() == [{"brands": [{"name": "Brand A"}]}]
    assert "HTTP 503" in result.get_message()
    assert private_detail not in result.get_message()
    assert [path for path, _auth in observed_requests] == [
        "/create/brands",
        "/create/caseTypes",
    ]


def test_fetch_config_malformed_case_type_list_retains_brands() -> None:
    routes = {
        "/create/brands": (200, json.dumps({"brands": ["Brand A"]})),
        "/create/caseTypes": (200, json.dumps({"caseType": {"bad": "shape"}})),
    }
    with _serve_get_routes(routes) as (base_url, _observed_requests):
        client = PhishLabsClient("test-user", "test-password", base_url=base_url)
        result = fetch_config(client, Params())

    assert isinstance(result, ActionResult)
    assert result.get_status() is False
    assert result.get_data() == [{"brands": [{"name": "Brand A"}]}]
    assert "invalid case type data" in result.get_message()
