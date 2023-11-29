# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse

from esani_pantportal.models import BRANCH_USER, EsaniUser, User


class LoginTest(TestCase):
    def test_login(self):
        credentials = {"username": "nj", "password": "foo"}
        EsaniUser.objects.create_user(**credentials)
        response = self.client.post(reverse("pant:login"), credentials, follow=True)

        self.assertEquals(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "esani_pantportal/product/list.html")
        self.assertEqual(response.context_data["form"].is_valid(), True)

        response = self.client.post(
            reverse("pant:login"),
            {"username": "nj", "password": "wrong_password"},
        )
        self.assertEqual(response.context_data["form"].is_valid(), False)

    def test_login_user_not_approved(self):
        credentials = {"username": "nj", "password": "foo"}
        User.objects.create_user(user_type=BRANCH_USER, **credentials)

        response = self.client.post(reverse("pant:login"), credentials)
        self.assertEqual(response.context_data["form"].is_valid(), False)

    def test_login_user_approved(self):
        credentials = {"username": "nj", "password": "foo"}
        User.objects.create_user(user_type=BRANCH_USER, approved=True, **credentials)

        response = self.client.post(reverse("pant:login"), credentials, follow=True)
        self.assertEquals(response.status_code, HTTPStatus.OK)
