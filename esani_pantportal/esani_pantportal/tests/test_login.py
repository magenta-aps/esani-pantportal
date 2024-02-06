# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from binascii import unhexlify
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.shortcuts import resolve_url
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django_otp.oath import totp
from django_otp.util import random_hex
from two_factor.utils import totp_digits

from esani_pantportal.models import BRANCH_USER, EsaniUser, User


def totp_str(key):
    return str(totp(key)).zfill(totp_digits())


@override_settings(BYPASS_2FA=False)
class LoginTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("create_groups")

    def setUp(self):
        self.branch_user = User.objects.create_user(
            username="branch_user1", password="foo", user_type=BRANCH_USER
        )

        self.esani_user = EsaniUser.objects.create_user(
            username="esani_user", password="foo"
        )
        self.esani_user.groups.add(Group.objects.get(name="EsaniAdmins"))

    def test_login(self):
        data = {
            "auth-username": "esani_user",
            "auth-password": "foo",
            "pantportal_login_view-current_step": "auth",
        }

        response = self.client.post(reverse("pant:login"), data, follow=True)

        self.assertEquals(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "esani_pantportal/product/list.html")
        self.assertEqual(response.context_data["form"].is_valid(), True)

        response = self.client.post(
            reverse("pant:login"),
            {
                "auth-username": "esani_user",
                "auth-password": "wrong_password",
                "pantportal_login_view-current_step": "auth",
            },
        )
        self.assertEqual(response.context_data["form"].is_valid(), False)

    def test_login_user_not_approved(self):
        data = {
            "auth-username": "branch_user1",
            "auth-password": "foo",
            "pantportal_login_view-current_step": "auth",
        }

        response = self.client.post(reverse("pant:login"), data)
        self.assertEqual(response.context_data["form"].is_valid(), False)

    def test_login_user_approved(self):
        self.branch_user.approved = True
        self.branch_user.save()
        data = {
            "auth-username": "branch_user1",
            "auth-password": "foo",
            "pantportal_login_view-current_step": "auth",
        }

        response = self.client.post(reverse("pant:login"), data, follow=True)
        self.assertEquals(response.status_code, HTTPStatus.OK)

    def test_token_step(self):
        device = self.esani_user.totpdevice_set.create(name="default", key=random_hex())

        data = {
            "auth-username": "esani_user",
            "auth-password": "foo",
            "pantportal_login_view-current_step": "auth",
        }
        response = self.client.post(reverse("pant:login"), data)
        self.assertContains(response, "Kode:")

        data = {
            "token-otp_token": "123456",
            "pantportal_login_view-current_step": "token",
        }
        response = self.client.post(reverse("pant:login"), data)
        self.assertEqual(
            response.context_data["wizard"]["form"].errors,
            {
                "__all__": [
                    "Invalid token. Please make sure you have entered it correctly."
                ]
            },
        )

        data = {
            "token-otp_token": totp_str(device.bin_key),
            "pantportal_login_view-current_step": "token",
        }
        device.throttle_reset()

        response = self.client.post(reverse("pant:login"), data, follow=True)
        self.assertRedirects(response, resolve_url(settings.LOGIN_REDIRECT_URL))

    @override_settings(BYPASS_2FA=True)
    def test_bypass_token_step(self):
        self.esani_user.totpdevice_set.create(name="default", key=random_hex())

        data = {
            "auth-username": "esani_user",
            "auth-password": "foo",
            "pantportal_login_view-current_step": "auth",
        }
        response = self.client.post(reverse("pant:login"), data)

        self.assertRedirects(response, resolve_url(settings.LOGIN_REDIRECT_URL))

    def test_two_factor_setup(self):
        self.client.login(username="esani_user", password="foo")

        response = self.client.post(
            reverse("pant:two_factor_setup"),
            data={"two_factor_setup-current_step": "generator"},
        )

        self.assertEqual(
            response.context_data["wizard"]["form"].errors,
            {"token": ["Dette felt er påkrævet."]},
        )

        response = self.client.post(
            reverse("pant:two_factor_setup"),
            data={
                "two_factor_setup-current_step": "generator",
                "generator-token": "123456",
            },
        )
        self.assertEqual(
            response.context_data["wizard"]["form"].errors,
            {"token": ["Den indtastet kode er ikke gyldig."]},
        )

        key = response.context_data["keys"].get("generator")
        bin_key = unhexlify(key.encode())
        response = self.client.post(
            reverse("pant:two_factor_setup"),
            data={
                "two_factor_setup-current_step": "generator",
                "generator-token": totp(bin_key),
            },
        )

        success_url = (
            reverse("pant:user_view", kwargs={"pk": self.esani_user.pk})
            + "?two_factor_success=1"
        )

        self.assertEqual(1, self.esani_user.totpdevice_set.count())
        self.assertRedirects(response, success_url)

    def test_2fa_required(self):
        self.client.login(username="esani_user", password="foo")
        self.assertEqual(0, self.esani_user.totpdevice_set.count())

        response = self.client.get(reverse("pant:user_list"))

        self.assertTemplateUsed(response, "two_factor/core/otp_required.html")
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
