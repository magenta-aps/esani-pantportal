# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
from datetime import datetime
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from django.test.utils import override_settings
from django.utils import timezone

from esani_pantportal.clients.tomra.api import TomraAPI
from esani_pantportal.clients.tomra.data_models import (
    ConsumerSession,
    ConsumerSessionQueryResponse,
    Datum,
)


@override_settings(
    TOMRA_API_ENV="env",
    TOMRA_API_KEY="api_key",
    TOMRA_API_CLIENT_ID="client_id",
    TOMRA_API_CLIENT_SECRET="client_secret",
)
class TestTomraAPI(SimpleTestCase):
    def test_from_settings(self):
        # Act
        instance = TomraAPI.from_settings()
        # Assert
        self.assertEqual(instance._env, "env"),
        self.assertEqual(instance._api_key, "api_key")
        self.assertEqual(instance._client_id, "client_id")
        self.assertEqual(instance._client_secret, "client_secret")

    def test_get_url(self):
        # Act
        url = TomraAPI.from_settings()._get_url("/path", subdomain="subdomain")
        # Assert
        self.assertEqual(url, "https://env.subdomain.developer.tomra.cloud/path")

    def test_get_access_token(self):
        # Arrange
        instance = TomraAPI.from_settings()
        mock_response = MagicMock()
        with patch("requests.post", return_value=mock_response) as mock_post:
            # Act
            instance._get_access_token()
            # Assert
            mock_post.assert_called_once_with(
                "https://env.auth.developer.tomra.cloud/oauth2/token",
                auth=("client_id", "client_secret"),
                data=instance._oauth2_scope_and_grant,
                headers={"User-Agent": instance._user_agent},
            )
            mock_response.raise_for_status.assert_called_once()
            mock_response.json.assert_called_once()

    def test_api_request(self):
        # Arrange
        instance = TomraAPI.from_settings()
        mock_response = MagicMock()
        with patch("requests.request", return_value=mock_response) as mock_request:
            with patch.object(
                instance,
                "_get_access_token",
                return_value="access_token",
            ) as mock_get_access_token:
                # Act
                instance._api_request("GET", "/resource", query={"foo": "bar"})
                # Assert
                mock_request.assert_called_once_with(
                    "GET",
                    "https://env.api.developer.tomra.cloud/resource",
                    params={"foo": "bar"},
                    headers={
                        "X-Api-Key": "api_key",
                        "Authorization": "Bearer access_token",
                        "User-Agent": instance._user_agent,
                    },
                )
                mock_get_access_token.assert_called_once()
                mock_response.raise_for_status.assert_called_once()
                mock_response.json.assert_called_once()

    def test_to_iso8601_in_utc(self):
        # Arrange
        local_dt = timezone.localtime()
        local_dt_with_tz = local_dt.astimezone(
            timezone.zoneinfo.ZoneInfo("Europe/Copenhagen")
        )
        instance = TomraAPI.from_settings()
        # Act
        result = instance._to_iso8601_in_utc(local_dt_with_tz)
        # Assert
        self.assertEqual(result, local_dt.isoformat(timespec="seconds"))

    def test_get_consumer_sessions_follows_continuation_token(self):
        # Arrange
        instance = TomraAPI.from_settings()
        mock_responses = [{"next": "something"}, {"next": None}]
        with patch.object(
            instance,
            "_api_request",
            side_effect=mock_responses,  # returns one item per call
        ) as mock_request:
            # Act
            instance.get_consumer_sessions(datetime(2020, 1, 1))
            # Assert
            self.assertEqual(mock_request.call_count, 2)

    def test_get_consumer_sessions_collects_data(self):
        # Arrange
        instance = TomraAPI.from_settings()
        mock_parsed_data = ConsumerSessionQueryResponse(
            data=[Datum(consumer_session=ConsumerSession())]
        )
        with patch.object(
            instance,
            "_api_request",
            side_effect=[{"next": None}],
        ):
            with patch(
                "esani_pantportal.clients.tomra.api.parse_obj_as",
                return_value=mock_parsed_data,
            ):
                # Act
                result = instance.get_consumer_sessions(datetime(2020, 1, 1))
                self.assertEqual(len(result), 1)
                self.assertIsInstance(result, list)
                self.assertIsInstance(result[0], Datum)
