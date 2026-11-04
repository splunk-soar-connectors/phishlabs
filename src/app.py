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
from soar_sdk.asset import BaseAsset, AssetField
from soar_sdk.exceptions import ActionFailure

from .client import PhishLabsError
from .test_connectivity import run_test_connectivity


class Asset(BaseAsset):
    username: str = AssetField(description="Username")
    password: str = AssetField(description="Password", sensitive=True)


def create_phishlabs_app() -> App:
    app = App(
        name="PhishLabs",
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
        python_version="3.13",
        min_phantom_version="7.0.0",
    )

    @app.test_connectivity()
    def test_connectivity(soar: SOARClient, asset: Asset) -> None:
        del soar
        try:
            run_test_connectivity(asset.username, asset.password)
        except PhishLabsError as error:
            raise ActionFailure(str(error)) from error
        except Exception as error:
            raise ActionFailure("PhishLabs connectivity test failed") from error

    return app


app = create_phishlabs_app()


from .actions import register_actions

register_actions(app)


if __name__ == "__main__":
    app.cli()
