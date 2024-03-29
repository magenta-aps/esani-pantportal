# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

"""
The data models in `data_models.py` are autogenerated from the Tomra API
OpenAPI specification (`TomraConsumerSessionApi.yaml`.)

To (re)generate the data models, run the following:
    $ datamodel-codegen \
        --input TomraConsumerSessionApi.yaml \
        --output ./data_models.py \
        --target-python-version=3.11 \
        --snake-case-field \
        --wrap-string-literal \
        --use-double-quotes \
        --use-schema-description \
        --use-standard-collections \
        --use-union-operator \
        --disable-appending-item-suffix \
        --collapse-root-models \
        --reuse-model \
        --allow-population-by-field-name \
        --strict-nullable
"""

from dataclasses import dataclass
from datetime import datetime

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from pydantic import parse_obj_as

from .data_models import ConsumerSessionQueryResponse, Datum


@dataclass
class _APIResponse:
    url: str | None
    doc: dict


@dataclass
class ConsumerSessionCollection:
    url: str | None
    from_date: datetime
    to_date: datetime
    data: list[Datum]


class TomraAPI:
    _user_agent = f"ESANI-Pantportal/{settings.VERSION}"
    """User agent sent with all Tomra API requests"""

    _oauth2_scope_and_grant = {
        "grant_type": "client_credentials",
        "scope": "tomra-apis/external",
    }

    @classmethod
    def from_settings(cls):
        if all(
            [
                settings.TOMRA_API_ENV,
                settings.TOMRA_API_KEY,
                settings.TOMRA_API_CLIENT_ID,
                settings.TOMRA_API_CLIENT_SECRET,
            ]
        ):
            return cls(
                settings.TOMRA_API_ENV,
                settings.TOMRA_API_KEY,
                settings.TOMRA_API_CLIENT_ID,
                settings.TOMRA_API_CLIENT_SECRET,
            )
        else:
            raise ImproperlyConfigured(
                "One or more of `TOMRA_API_ENV`, `TOMRA_API_KEY`, "
                "`TOMRA_API_CLIENT_ID`, and `TOMRA_API_CLIENT_SECRET` are missing "
                "from settings."
            )

    def __init__(self, env: str, api_key: str, client_id: str, client_secret: str):
        self._env = env
        self._api_key = api_key
        self._client_id = client_id
        self._client_secret = client_secret

    def _get_url(self, path: str, subdomain: str = "api") -> str:
        return f"https://{self._env}.{subdomain}.developer.tomra.cloud{path}"

    def _get_access_token(self) -> str:
        response = requests.post(
            self._get_url("/oauth2/token", subdomain="auth"),
            auth=(self._client_id, self._client_secret),
            data=self._oauth2_scope_and_grant,
            headers={"User-Agent": self._user_agent},
        )
        response.raise_for_status()
        return response.json()["access_token"]

    def _api_request(
        self, method: str, resource: str, query: dict | None = None
    ) -> _APIResponse:
        # TODO: don't request a new access token on every API request.
        # (Tomra access tokens are valid for 1 hour.)
        response = requests.request(
            method,
            self._get_url(resource),
            params=query,
            headers={
                "X-Api-Key": self._api_key,
                "Authorization": f"Bearer {self._get_access_token()}",
                "User-Agent": self._user_agent,
            },
        )
        response.raise_for_status()
        return _APIResponse(url=response.request.url, doc=response.json())

    def _to_iso8601_in_utc(self, val: datetime) -> str:
        return val.astimezone().isoformat(timespec="seconds")

    def get_consumer_sessions(
        self,
        after: datetime,
        before: datetime,
        rvm_serials: list[int] | None = None,
    ) -> ConsumerSessionCollection:
        data: list[Datum] = []
        continuation_token: str | None = "initial"
        initial_url: str | None

        while continuation_token is not None:
            next = None if continuation_token == "initial" else continuation_token
            response: _APIResponse = self._api_request(
                "GET",
                "/consumer-sessions",
                query={
                    "receivedBefore": self._to_iso8601_in_utc(before),
                    "receivedAfter": self._to_iso8601_in_utc(after),
                    "serialNumbers": rvm_serials,
                    "next": next,
                },
            )
            continuation_token = response.doc.get("next")
            parsed = parse_obj_as(ConsumerSessionQueryResponse, response.doc)
            if parsed.data:
                data.extend(parsed.data)
            if next is None:
                initial_url = response.url

        return ConsumerSessionCollection(
            # URL without continuation token (`next`)
            url=initial_url,
            from_date=after,
            to_date=before,
            data=data,
        )
