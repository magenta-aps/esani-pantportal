# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from http import HTTPStatus

from django.test import TestCase, override_settings
from django.urls import reverse

from .conftest import LoginMixin


class AboutViewTest(LoginMixin, TestCase):
    @override_settings(VERSION="TEST")
    def test_about_view(self):
        self.login()
        response = self.client.get(reverse("pant:about"))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context_data["version"], "TEST")
