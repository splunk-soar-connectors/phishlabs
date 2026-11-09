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
from soar_sdk.action_results import ActionResult

from src.actions.get_config import GetConfigOutput
from src.app import app


def _render_get_config(result: ActionResult) -> str:
    action = app.actions_manager.get_action("get_config")
    assert action is not None
    assert action.meta.view_handler is not None

    context = {
        "QS": {},
        "container": 753,
        "app": 1,
        "no_connection": False,
        "google_maps_key": False,
    }
    return action.meta.view_handler(
        "get_config",
        [
            (
                {
                    "total_objects": 1,
                    "total_objects_successful": int(result.get_status()),
                },
                [result],
            )
        ],
        context,
    )


def test_registered_sdk_view_renders_brands_and_case_types() -> None:
    output = GetConfigOutput(
        brands=[{"name": "Brand A"}],
        case_types=[{"name": "Phishing"}],
    )
    result = ActionResult(True, "configuration loaded")
    result.add_data(output.model_dump(by_alias=True))

    rendered = _render_get_config(result)

    assert "Brand A" in rendered
    assert "Phishing" in rendered
    assert "context_menu(this" in rendered
    assert "phishlabs brand" in rendered
    assert "phishlabs case type" in rendered
    assert ", 0, 753, null, false);" in rendered
    assert "No Brands in results" not in rendered
    assert "No Case Types in results" not in rendered


def test_registered_sdk_view_parses_and_renders_partial_brands_result() -> None:
    result = ActionResult(False, "PhishLabs returned an error response (HTTP 503)")
    result.add_data({"brands": [{"name": "Brand A"}]})

    rendered = _render_get_config(result)

    assert "Brand A" in rendered
    assert "No Case Types in results" in rendered
    assert "context_menu(this" in rendered
    assert "phishlabs brand" in rendered


def test_registered_sdk_view_displays_legacy_empty_states() -> None:
    result = ActionResult(True, "empty configuration")
    result.add_data(GetConfigOutput(brands=[], case_types=[]).model_dump(by_alias=True))

    rendered = _render_get_config(result)

    assert "No Brands in results" in rendered
    assert "No Case Types in results" in rendered


def test_registered_action_metadata_matches_legacy_contract() -> None:
    expected_contract = {
        "create_ticket": {
            "action_type": "generic",
            "read_only": False,
            "parameters": {
                "title": True,
                "url": False,
                "description": False,
                "case_type": True,
                "brand": True,
            },
            "output_paths": {
                "action_result.data.*.createdCase.caseId",
                "action_result.data.*.createdCase.caseNumber",
                "action_result.data.*.createdCase.status",
                "action_result.data.*.updatedCase.caseId",
                "action_result.data.*.updatedCase.status",
                "action_result.data.*.updatedCase.caseNumber",
                "action_result.summary.case_id",
                "action_result.summary.case_number",
                "action_result.summary.status",
            },
        },
        "get_ticket": {
            "action_type": "generic",
            "read_only": True,
            "parameters": {"case_id": True},
            "output_paths": {
                "action_result.summary.case_id",
                "action_result.summary.return_result",
                "action_result.summary.total_result",
            },
        },
        "list_tickets": {
            "action_type": "generic",
            "read_only": True,
            "parameters": {},
            "output_paths": {"action_result.summary.total_cases"},
        },
        "get_config": {
            "action_type": "investigate",
            "read_only": True,
            "parameters": {},
            "output_paths": {
                "action_result.data.*.brands.*.name",
                "action_result.data.*.case_types.*.name",
                "action_result.summary.num_brands",
                "action_result.summary.num_case_types",
            },
        },
    }

    for action_name, expected in expected_contract.items():
        action = app.actions_manager.get_action(action_name)
        assert action is not None
        metadata = action.meta.model_dump()
        assert metadata["type"] == expected["action_type"]
        assert metadata["read_only"] is expected["read_only"]
        assert {
            name: parameter["required"]
            for name, parameter in metadata["parameters"].items()
        } == expected["parameters"]
        assert expected["output_paths"].issubset(
            {output["data_path"] for output in metadata["output"]}
        )
        if action_name in {"create_ticket", "get_ticket"}:
            case_id_summary = next(
                output
                for output in metadata["output"]
                if output["data_path"] == "action_result.summary.case_id"
            )
            assert case_id_summary["contains"] == ["phishlabs case id"]
