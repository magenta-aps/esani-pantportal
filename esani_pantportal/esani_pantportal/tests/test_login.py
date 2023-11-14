# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from django.test import TestCase
from django.urls import reverse

from esani_pantportal.models import CompanyUser


class LoginTest(TestCase):
    def test_login(self):
        credentials = {"username": "nj", "password": "foo"}

        CompanyUser.objects.create_user(**credentials)

        response = self.client.post(reverse("pant:login"), credentials, follow=True)

        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, "esani_pantportal/product/list.html")
        self.assertEqual(response.context_data["form"].is_valid(), True)

        response = self.client.post(
            reverse("pant:login"),
            {"username": "nj", "password": "wrong_password"},
            follow=True,
        )

        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, "esani_pantportal/login.html")
        self.assertEqual(response.context_data["form"].is_valid(), False)
