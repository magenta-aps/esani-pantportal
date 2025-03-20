# SPDX-FileCopyrightText: 2025 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from django.test import TestCase
from ninja_extra.testing import TestClient
from project.api import CustomJWTController

from .conftest import LoginMixin


class TestCustomJWTController(LoginMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.api_client = TestClient(CustomJWTController)

    def test_token_includes_fasttrack_enabled(self):
        # Arrange: use the `login` method to ensure that an ESANI user exists beforehand
        esani_user = self.login("EsaniAdmins")
        # Arrange
        for expected_fasttrack_value in (False, True):
            with self.subTest(expected_fasttrack_value=expected_fasttrack_value):
                if expected_fasttrack_value is True:
                    esani_user.fasttrack_enabled = True
                    esani_user.save(update_fields=["fasttrack_enabled"])
                # Act: obtain pair
                pair_response = self.api_client.post(
                    "/pair",
                    json={
                        "username": esani_user.username,
                        "password": "12345",
                    },
                    content_type="application/json",
                )
                # Assert: custom field is present and has expected value
                self.assertEqual(
                    pair_response.json()["fasttrack_enabled"], expected_fasttrack_value
                )
                # Act: refresh token
                refresh_response = self.api_client.post(
                    "/refresh",
                    json={"refresh": pair_response.json()["refresh"]},
                    content_type="application/json",
                )
                # Assert: custom field is present and has expected value
                self.assertEqual(
                    refresh_response.json()["fasttrack_enabled"],
                    expected_fasttrack_value,
                )
