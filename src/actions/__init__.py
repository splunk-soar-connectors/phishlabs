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
from soar_sdk.app import App
from soar_sdk.params import Params

from .create_ticket import (
    CreateTicketOutput,
    CreateTicketParams,
    CreateTicketSummary,
    create_ticket,
)
from .get_config import GetConfigOutput, GetConfigSummary, get_config
from .get_ticket import GetTicketOutput, GetTicketParams, GetTicketSummary, get_ticket
from .list_tickets import ListTicketsOutput, ListTicketsSummary, list_tickets
from .make_request import make_request
from ..views.get_config import display_config


def register_actions(app: App) -> App:
    """Register ordinary PhishLabs actions."""
    app.make_request()(make_request)
    app.register_action(
        action=create_ticket,
        description="Create a new case submission",
        action_type="generic",
        read_only=False,
        params_class=CreateTicketParams,
        output_class=CreateTicketOutput,
        summary_type=CreateTicketSummary,
    )
    app.register_action(
        action=get_ticket,
        description="Get case (issue) information",
        action_type="generic",
        read_only=True,
        params_class=GetTicketParams,
        output_class=GetTicketOutput,
        summary_type=GetTicketSummary,
    )
    app.register_action(
        action=list_tickets,
        description="Get a list of cases in PhishLabs",
        action_type="generic",
        read_only=True,
        params_class=Params,
        output_class=ListTicketsOutput,
        summary_type=ListTicketsSummary,
    )
    app.register_action(
        action=get_config,
        description="Return the list of brands and case types currently configured in PhishLabs",
        action_type="investigate",
        read_only=True,
        params_class=Params,
        output_class=GetConfigOutput,
        summary_type=GetConfigSummary,
        view_handler=display_config,
        view_template="display_config.html",
    )
    return app
