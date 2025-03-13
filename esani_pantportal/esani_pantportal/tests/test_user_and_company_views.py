# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
from http import HTTPStatus

from bs4 import BeautifulSoup
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django_otp.util import random_hex
from unittest_parametrize import ParametrizedTestCase, parametrize

from esani_pantportal.models import (
    MUNICIPALITY_CHOICES,
    BranchUser,
    Company,
    CompanyBranch,
    CompanyUser,
    EsaniUser,
    Kiosk,
    KioskUser,
    ReverseVendingMachine,
    User,
)
from esani_pantportal.templatetags.pant_tags import (
    has_fasttrack_enabled,
    has_two_factor,
)

from .conftest import LoginMixin

TEST_DATA_MUNICIPALITY_SERMERSOOQ = MUNICIPALITY_CHOICES[len(MUNICIPALITY_CHOICES) - 3][
    0
]


class TestPrevalidateCreateView(TestCase):
    def test_form_prevalidation_invalid_data(self):
        """Verify that POSTing a 'prevalidate' payload to a view inheriting from `
        _PrevalidateCreateView` returns a JSON response listing the form validation
        errors.
        """
        response = self.client.post(
            reverse("pant:branch_user_register"),
            # Prevalidate the 'branch' subform, but don't provide any other form data,
            # in order to trigger form validation errors.
            data={"prevalidate": "branch"},
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn("errors", response.json())

        self.assertSetEqual(
            set(response.json()["errors"]),
            {
                "city",
                "address",
                "branch_type",
                "name",
                "phone",
                "company",
                "postal_code",
                "municipality",
                "prefix",
                "qr_compensation",
            },
        )

    def test_form_prevalidation_valid_data(self):
        """Verify that POSTing a 'prevalidate' payload to a view inheriting from `
        _PrevalidateCreateView` returns a JSON response without errors, if the provided
        form data is indeed valid.
        """
        response = self.client.post(
            reverse("pant:branch_user_register"),
            # Prevalidate the 'company' subform, providing all the necessary data
            data={
                "prevalidate": "company",
                "company-address": "Adresse",
                "company-city": "By",
                "company-company_type": "A",
                "company-country": "GL",
                "company-cvr": "123",
                "company-name": "Navn",
                "company-phone": "Telefon",
                "company-postal_code": "Postnummer",
                "company-prefix": "Landekode",
                "company-municipality": TEST_DATA_MUNICIPALITY_SERMERSOOQ,
            },
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn("errors", response.json())
        self.assertDictEqual(response.json()["errors"], {})


class BaseUserTest(LoginMixin, TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.facebook = Company.objects.create(
            name="facebook",
            cvr=12312345,
            address="foo",
            postal_code="123",
            city="test city",
            country="USA",
            phone="+4544457845",
            municipality=TEST_DATA_MUNICIPALITY_SERMERSOOQ,
            company_type="E",
            registration_number="112",
            account_number="112",
            invoice_mail="foo@bar.com",
        )

        cls.google = Company.objects.create(
            name="google",
            cvr=12312346,
            address="foo",
            postal_code="123",
            city="test city",
            country="USA",
            phone="+4544457845",
            municipality=TEST_DATA_MUNICIPALITY_SERMERSOOQ,
            company_type="A",
            registration_number="112",
            account_number="112",
            invoice_mail="foo@bar.com",
        )

        cls.facebook_branch = CompanyBranch.objects.create(
            company=cls.facebook,
            name="facebook_branch",
            address="food",
            postal_code="12311",
            city="test town",
            phone="+4542457845",
            location_id=2,
            municipality=TEST_DATA_MUNICIPALITY_SERMERSOOQ,
            branch_type="A",
            customer_id=2,
            registration_number="112",
            account_number="112",
            invoice_mail="foo@bar.com",
        )

        cls.kiosk = Kiosk.objects.create(
            name="kiosk",
            address="food",
            postal_code="12311",
            city="test town",
            phone="+4542457845",
            location_id=2,
            cvr=11221122,
            municipality=TEST_DATA_MUNICIPALITY_SERMERSOOQ,
            branch_type="A",
            customer_id=2,
            registration_number="112",
            account_number="112",
            invoice_mail="foo@bar.com",
        )

        cls.facebook_admin = CompanyUser.objects.create_user(
            username="facebook_admin",
            password="12345",
            email="test@test.com",
            phone="+4542457845",
            company=cls.facebook,
        )

        cls.google_admin = CompanyUser.objects.create_user(
            username="google_admin",
            password="12345",
            email="test@test.com",
            phone="+4542457845",
            company=cls.google,
        )

        cls.facebook_branch_admin = BranchUser.objects.create_user(
            username="facebook_branch_admin",
            password="12345",
            email="test@test.com",
            phone="+4542457845",
            branch=cls.facebook_branch,
        )

        cls.facebook_branch_user = BranchUser.objects.create_user(
            username="facebook_branch_user",
            password="12345",
            email="test@test.com",
            phone="+4542457845",
            branch=cls.facebook_branch,
        )

        cls.kiosk_admin = KioskUser.objects.create_user(
            username="kiosk_admin",
            password="12345",
            email="test@test.com",
            phone="+4542457845",
            branch=cls.kiosk,
        )

        cls.esani_admin = EsaniUser.objects.create_user(
            username="esani_admin",
            password="12345",
            email="test@test.com",
            phone="+4542457845",
        )

        call_command("create_groups")
        cls.esani_admin.groups.add(Group.objects.get(name="EsaniAdmins"))
        cls.facebook_admin.groups.add(Group.objects.get(name="CompanyAdmins"))
        cls.google_admin.groups.add(Group.objects.get(name="CompanyAdmins"))
        cls.facebook_branch_admin.groups.add(Group.objects.get(name="BranchAdmins"))
        cls.facebook_branch_user.groups.add(Group.objects.get(name="BranchUsers"))
        cls.kiosk_admin.groups.add(Group.objects.get(name="KioskAdmins"))

        # Create RVMs
        cls.facebook_rvm1 = ReverseVendingMachine.objects.create(
            compensation=11,
            serial_number="1",
            company_branch=cls.facebook_branch,
        )

        cls.kiosk_rvm1 = ReverseVendingMachine.objects.create(
            compensation=12,
            serial_number="2",
            kiosk=cls.kiosk,
        )

    @staticmethod
    def make_form_data(form):
        form_data = {}
        for field_name, field in form.fields.items():
            form_data[field_name] = form.get_initial_for_field(field, field_name)
        return form_data


class UserListTest(BaseUserTest):
    def test_esani_admin_view(self):
        self.client.login(username="esani_admin", password="12345")
        response = self.client.get(reverse("pant:user_list"))
        self.assertEqual(response.status_code, HTTPStatus.OK)

        ids = [i["id"] for i in response.context_data["items"]]

        self.assertIn(self.facebook_admin.id, ids)
        self.assertIn(self.google_admin.id, ids)
        self.assertIn(self.facebook_branch_admin.id, ids)
        self.assertIn(self.facebook_branch_user.id, ids)
        self.assertIn(self.kiosk_admin.id, ids)
        self.assertIn(self.esani_admin.id, ids)
        self.assertEqual(len(ids), 6)

    def test_esani_admin_filter_view(self):
        self.client.login(username="esani_admin", password="12345")
        response = self.client.get(reverse("pant:user_list") + "?username=esani_admin")
        self.assertEqual(response.status_code, HTTPStatus.OK)

        ids = [i["id"] for i in response.context_data["items"]]

        self.assertIn(self.esani_admin.id, ids)
        self.assertEqual(len(ids), 1)

    def test_facebook_admin_view(self):
        self.client.login(username="facebook_admin", password="12345")
        response = self.client.get(reverse("pant:user_list"))
        self.assertEqual(response.status_code, HTTPStatus.OK)

        ids = [i["id"] for i in response.context_data["items"]]

        self.assertIn(self.facebook_admin.id, ids)
        self.assertIn(self.facebook_branch_admin.id, ids)
        self.assertIn(self.facebook_branch_user.id, ids)
        self.assertEqual(len(ids), 3)

    def test_google_admin_view(self):
        self.client.login(username="google_admin", password="12345")
        response = self.client.get(reverse("pant:user_list"))
        self.assertEqual(response.status_code, HTTPStatus.OK)

        ids = [i["id"] for i in response.context_data["items"]]

        self.assertIn(self.google_admin.id, ids)
        self.assertEqual(len(ids), 1)

    def test_kiosk_admin_view(self):
        self.client.login(username="kiosk_admin", password="12345")
        response = self.client.get(reverse("pant:user_list"))
        self.assertEqual(response.status_code, HTTPStatus.OK)

        ids = [i["id"] for i in response.context_data["items"]]

        self.assertIn(self.kiosk_admin.id, ids)
        self.assertEqual(len(ids), 1)

    def test_branch_filter(self):
        self.client.login(username="esani_admin", password="12345")
        response = self.client.get(reverse("pant:user_list") + "?branch=facebook")
        self.assertEqual(response.status_code, HTTPStatus.OK)

        branch_names = [i["branch"] for i in response.context_data["items"]]
        self.assertGreater(len(branch_names), 0)
        for branch_name in branch_names:
            self.assertIn("facebook", branch_name)

    def test_company_filter(self):
        self.client.login(username="esani_admin", password="12345")
        response = self.client.get(reverse("pant:user_list") + "?company=google")
        self.assertEqual(response.status_code, HTTPStatus.OK)

        company_names = [i["company"] for i in response.context_data["items"]]
        self.assertGreater(len(company_names), 0)
        for company_name in company_names:
            self.assertIn("google", company_name)


class NonAdminUserUpdateViewTest(BaseUserTest):
    def setUp(self):
        self.facebook_branch_user_url = reverse(
            "pant:user_view",
            kwargs={"pk": self.facebook_branch_user.pk},
        )

    def test_facebook_branch_user_view(self):
        self.client.login(username="facebook_branch_user", password="12345")
        response = self.client.get(self.facebook_branch_user_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context_data["object"].username, "facebook_branch_user"
        )

        form_data = self.make_form_data(response.context_data["form"])
        form_data["first_name"] = "Mark"
        response = self.client.post(self.facebook_branch_user_url, form_data)
        self.assertEquals(response.status_code, HTTPStatus.FOUND)


class EsaniAdminUserUpdateViewTest(BaseUserTest):
    def setUp(self):
        self.facebook_admin_url = reverse(
            "pant:user_view",
            kwargs={"pk": self.facebook_admin.pk},
        )

        self.esani_admin_url = reverse(
            "pant:user_view",
            kwargs={"pk": self.esani_admin.pk},
        )

    def test_esani_admin_view(self):
        self.client.login(username="esani_admin", password="12345")
        response = self.client.get(self.facebook_admin_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context_data["object"].username, "facebook_admin")
        self.assertEqual(self.facebook_admin.approved, False)

        form_data = self.make_form_data(response.context_data["form"])
        form_data["approved"] = True

        response = self.client.post(self.facebook_admin_url, form_data)

        self.assertEquals(response.status_code, HTTPStatus.FOUND)
        self.facebook_admin.refresh_from_db()
        self.assertTrue(self.facebook_admin.approved)

    def test_forbidden(self):
        self.client.login(username="facebook_admin", password="12345")
        response = self.client.get(self.facebook_admin_url)
        form_data = self.make_form_data(response.context_data["form"])
        form_data["approved"] = True

        response = self.client.post(self.facebook_admin_url, form_data)
        self.assertEquals(response.status_code, HTTPStatus.FORBIDDEN)

    def test_disable_2fa(self):
        self.client.login(username="esani_admin", password="12345")

        self.esani_admin.totpdevice_set.create(name="default", key=random_hex())
        self.assertTrue(has_two_factor(self.esani_admin))

        response = self.client.get(self.esani_admin_url)
        form_data = self.make_form_data(response.context_data["form"])
        form_data["disable_two_factor"] = "True"

        self.client.post(self.esani_admin_url, form_data)

        self.esani_admin.refresh_from_db()
        self.assertFalse(has_two_factor(self.esani_admin))

    def test_change_fasttrack_enabled(self):
        self.client.login(username="esani_admin", password="12345")

        # Initial value is False
        self.assertFalse(has_fasttrack_enabled(self.esani_admin))

        # Change value using form POST
        response = self.client.get(self.esani_admin_url)
        form_data = self.make_form_data(response.context_data["form"])
        form_data["fasttrack_enabled"] = "True"
        self.client.post(self.esani_admin_url, form_data)

        # Assert value is persisted
        self.esani_admin.refresh_from_db()
        self.assertFalse(has_two_factor(self.esani_admin))


class CompanyAdminUserUpdateViewTest(BaseUserTest):
    def setUp(self):
        self.facebook_admin_url = reverse(
            "pant:user_view",
            kwargs={"pk": self.facebook_admin.pk},
        )
        self.google_admin_url = reverse(
            "pant:user_view",
            kwargs={"pk": self.google_admin.pk},
        )

        self.facebook_branch_user_url = reverse(
            "pant:user_view",
            kwargs={"pk": self.facebook_branch_user.pk},
        )

        self.esani_admin_url = reverse(
            "pant:user_view",
            kwargs={"pk": self.esani_admin.pk},
        )
        self.kiosk_admin_url = reverse(
            "pant:user_view",
            kwargs={"pk": self.kiosk_admin.pk},
        )

    def test_facebook_admin_view_change_own_name(self):
        self.client.login(username="facebook_admin", password="12345")
        response = self.client.get(self.facebook_admin_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data["object"].username, "facebook_admin")

        form_data = self.make_form_data(response.context_data["form"])
        form_data["first_name"] = "Mark"
        response = self.client.post(self.facebook_admin_url, form_data)

        self.assertEquals(response.status_code, HTTPStatus.FOUND)
        self.facebook_admin.refresh_from_db()
        self.assertEqual(self.facebook_admin.first_name, "Mark")

    def test_facebook_admin_view_change_facebook_employee_name(self):
        self.client.login(username="facebook_admin", password="12345")
        response = self.client.get(self.facebook_branch_user_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context_data["object"].username, "facebook_branch_user"
        )

        form_data = self.make_form_data(response.context_data["form"])
        form_data["first_name"] = "Jim"
        response = self.client.post(self.facebook_branch_user_url, form_data)

        self.assertEquals(response.status_code, HTTPStatus.FOUND)
        self.facebook_branch_user.refresh_from_db()
        self.assertEqual(self.facebook_branch_user.first_name, "Jim")

        self.client.logout()
        self.client.login(username="google_admin", password="12345")
        response = self.client.post(self.facebook_branch_user_url, form_data)
        self.assertEquals(response.status_code, HTTPStatus.FORBIDDEN)

    def test_facebook_admin_view_google_employee_404(self):
        self.client.login(username="facebook_admin", password="12345")
        response = self.client.get(self.google_admin_url)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_facebook_admin_view_esani_admin_404(self):
        self.client.login(username="facebook_admin", password="12345")
        response = self.client.get(self.esani_admin_url)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_kiosk_user_view(self):
        self.client.login(username="kiosk_admin", password="12345")
        response = self.client.get(self.kiosk_admin_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data["object"].branch.cvr, self.kiosk.cvr)
        self.assertEqual(response.context_data["object"].username, "kiosk_admin")


class ResetPasswordTest(BaseUserTest):
    def setUp(self):
        self.facebook_employee_password_url = reverse(
            "pant:password_set",
            kwargs={"pk": self.facebook_branch_user.pk},
        )

        self.google_employee_password_url = reverse(
            "pant:password_set",
            kwargs={"pk": self.google_admin.pk},
        )

    def test_facebook_admin_reset_facebook_employee_password(self):
        self.client.login(username="facebook_admin", password="12345")
        response = self.client.get(self.facebook_employee_password_url)
        self.assertEqual(response.status_code, 200)

        form_data = self.make_form_data(response.context_data["form"])
        form_data["password"] = "new_pass"
        form_data["password2"] = "new_pass"
        response = self.client.post(self.facebook_employee_password_url, form_data)

        self.assertEquals(response.status_code, HTTPStatus.FOUND)

        ok = self.client.login(username="facebook_branch_user", password="new_pass")
        self.assertTrue(ok)
        ok = self.client.login(username="facebook_branch_user", password="12345")
        self.assertFalse(ok)

    def test_facebook_admin_reset_google_employee_password(self):
        self.client.login(username="facebook_admin", password="12345")
        response = self.client.get(self.google_employee_password_url)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_esani_admin_reset_google_employee_password(self):
        self.client.login(username="esani_admin", password="12345")
        response = self.client.get(self.google_employee_password_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

        form_data = self.make_form_data(response.context_data["form"])
        form_data["password"] = "new_pass"
        form_data["password2"] = "new_pass"
        response = self.client.post(self.google_employee_password_url, form_data)

        self.assertEquals(response.status_code, HTTPStatus.FOUND)

        ok = self.client.login(username="google_admin", password="new_pass")
        self.assertTrue(ok)
        ok = self.client.login(username="google_admin", password="12345")
        self.assertFalse(ok)


class ChangePasswordTest(BaseUserTest):
    def test_change_password(self):
        url = reverse("pant:password_change", kwargs={"pk": self.facebook_admin.pk})

        self.client.login(username="facebook_admin", password="12345")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        form_data = self.make_form_data(response.context_data["form"])
        form_data["old_password"] = "12345"
        form_data["new_password1"] = "new_pass"
        form_data["new_password2"] = "new_pass"

        response = self.client.post(url, form_data, follow=True)
        self.assertEquals(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "esani_pantportal/user/view.html")

        ok = self.client.login(username="facebook_admin", password="new_pass")
        self.assertTrue(ok)

    def test_change_password_bad_pw(self):
        url = reverse("pant:password_change", kwargs={"pk": self.facebook_admin.pk})
        self.client.login(username="facebook_admin", password="12345")
        response = self.client.get(url)
        form_data = self.make_form_data(response.context_data["form"])

        # Password is too short
        form_data["old_password"] = "12345"
        form_data["new_password1"] = "pw"
        form_data["new_password2"] = "pw"
        response = self.client.post(url, form_data)
        self.assertFalse(response.context_data["form"].is_valid())

        # Wrong old password
        form_data["old_password"] = "wrong_pw"
        form_data["new_password1"] = "new_pass"
        form_data["new_password2"] = "new_pass"
        response = self.client.post(url, form_data)
        self.assertFalse(response.context_data["form"].is_valid())

        # Too simple password
        form_data["old_password"] = "12345"
        form_data["new_password1"] = "hahahaha"
        form_data["new_password2"] = "hahahaha"
        response = self.client.post(url, form_data)
        self.assertFalse(response.context_data["form"].is_valid())


class DeleteUserTest(BaseUserTest):
    def test_delete_user_by_esani_admin(self):
        self.client.login(username="esani_admin", password="12345")
        username = self.facebook_admin.username
        url = reverse("pant:user_delete", kwargs={"pk": self.facebook_admin.pk})

        self.assertTrue(User.objects.filter(username=username).exists())
        self.assertTrue(CompanyUser.objects.filter(username=username).exists())

        response = self.client.post(url)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertFalse(User.objects.filter(username=username).exists())
        self.assertFalse(CompanyUser.objects.filter(username=username).exists())

    def test_delete_user_by_facebook_admin(self):
        self.client.login(username="facebook_admin", password="12345")
        username = self.facebook_branch_admin.username
        url = reverse("pant:user_delete", kwargs={"pk": self.facebook_branch_admin.pk})

        self.assertTrue(User.objects.filter(username=username).exists())
        self.assertTrue(BranchUser.objects.filter(username=username).exists())

        response = self.client.post(url)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertFalse(User.objects.filter(username=username).exists())
        self.assertFalse(BranchUser.objects.filter(username=username).exists())

    def test_delete_self(self):
        self.client.login(username="facebook_admin", password="12345")
        username = self.facebook_admin.username
        url = reverse("pant:user_delete", kwargs={"pk": self.facebook_admin.pk})
        self.assertTrue(User.objects.filter(username=username).exists())
        self.assertTrue(CompanyUser.objects.filter(username=username).exists())

        response = self.client.post(url, follow=True)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFalse(User.objects.filter(username=username).exists())
        self.assertFalse(CompanyUser.objects.filter(username=username).exists())
        self.assertTemplateUsed(response, "two_factor/core/login.html")

    def test_delete_user_from_other_company(self):
        self.client.login(username="facebook_admin", password="12345")
        url = reverse("pant:user_delete", kwargs={"pk": self.google_admin.pk})

        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)


class UpdateCompanyTest(ParametrizedTestCase, BaseUserTest):
    def update_name(self, url):
        response = self.client.get(url)
        form_data = self.make_form_data(response.context_data["form"])

        form_data["name"] = "x"
        response = self.client.post(url, form_data)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def assert_forbidden(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_update_facebook_by_facebook_admin(self):
        self.client.login(username="facebook_admin", password="12345")
        url = reverse("pant:company_update", kwargs={"pk": self.facebook.pk})

        self.update_name(url)
        self.facebook.refresh_from_db()
        self.assertEqual(self.facebook.name, "x")

    def test_update_facebook_by_google_admin(self):
        self.client.login(username="google_admin", password="12345")
        url = reverse("pant:company_update", kwargs={"pk": self.facebook.pk})
        self.assert_forbidden(url)

    def test_update_facebook_branch_by_facebook_admin(self):
        self.client.login(username="facebook_admin", password="12345")
        url = reverse(
            "pant:company_branch_update", kwargs={"pk": self.facebook_branch.pk}
        )

        self.update_name(url)
        self.facebook_branch.refresh_from_db()
        self.assertEqual(self.facebook_branch.name, "x")

        # Only ESANI admins can update a branch's parent-company
        response = self.client.get(url)
        form_data = self.make_form_data(response.context_data["form"])
        form_data["company"] = self.google.pk
        with self.assertRaises(ValidationError):
            self.client.post(url, form_data)

    def test_update_facebook_branch_by_facebook_branch_admin(self):
        self.client.login(username="facebook_branch_admin", password="12345")
        url = reverse(
            "pant:company_branch_update", kwargs={"pk": self.facebook_branch.pk}
        )

        self.update_name(url)
        self.facebook_branch.refresh_from_db()
        self.assertEqual(self.facebook_branch.name, "x")

    def test_update_facebook_branch_by_facebook_branch_user(self):
        self.client.login(username="facebook_branch_user", password="12345")
        url = reverse(
            "pant:company_branch_update", kwargs={"pk": self.facebook_branch.pk}
        )
        self.assert_forbidden(url)  # Only admins can update company info

    def test_update_facebook_branch_by_kiosk_admin(self):
        self.client.login(username="kiosk_admin", password="12345")
        url = reverse(
            "pant:company_branch_update", kwargs={"pk": self.facebook_branch.pk}
        )
        self.assert_forbidden(url)

    def test_update_kiosk_by_kiosk_admin(self):
        self.client.login(username="kiosk_admin", password="12345")
        url = reverse("pant:kiosk_update", kwargs={"pk": self.kiosk.pk})

        self.update_name(url)
        self.kiosk.refresh_from_db()
        self.assertEqual(self.kiosk.name, "x")

    def test_update_kiosk_by_facebook_admin(self):
        self.client.login(username="facebook_admin", password="12345")
        url = reverse("pant:kiosk_update", kwargs={"pk": self.kiosk.pk})
        self.assert_forbidden(url)

    @staticmethod
    def get_back_button(html):
        soup = BeautifulSoup(html, "html.parser")
        button = soup.find(id="back_button")
        return button

    def test_back_url(self):
        self.login()
        kwargs = {"pk": self.facebook.pk}
        url1 = reverse("pant:company_update", kwargs=kwargs)
        url2 = reverse("pant:company_update", kwargs=kwargs) + "?back=foo"

        response = self.client.get(url1)
        back_button = self.get_back_button(response.content)
        self.assertEqual(back_button, None)

        response = self.client.get(url2)
        back_button = self.get_back_button(response.content)
        self.assertEqual(back_button["href"], "foo")

    def test_no_compensation(self):
        self.client.login(username="facebook_admin", password="12345")
        url = reverse("pant:company_update", kwargs={"pk": self.facebook.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        """
        self.assertSetEqual(
            set(response.json()["errors"]),
            {
                "city",
                "address",
                "branch_type",
                "name",
                "phone",
                "company",
                "postal_code",
                "municipality",
                "prefix",
                "qr_compensation",
            },
        )
        """

    def test_context_has_external_customer_id(self):
        self.login()
        response = self.client.get(
            reverse("pant:company_update", kwargs={"pk": self.facebook.pk})
        )
        self.assertEqual(
            response.context["object"].external_customer_id,
            f"{Company.customer_id_prefix}-{self.facebook.pk:05}",
        )

    @parametrize(
        "input_value,expected_value",
        [
            ("0", False),
            ("1", True),
        ],
    )
    def test_update_invoice_company_branch(self, input_value, expected_value):
        # Login and retrieve page with form
        self.client.login(username="esani_admin", password="12345")
        url = reverse("pant:company_update", kwargs={"pk": self.facebook.pk})
        response = self.client.get(url)
        # Post updated data
        form_data = self.make_form_data(response.context_data["form"])
        form_data["invoice_company_branch"] = input_value
        response = self.client.post(url, form_data)
        # Assert object is updated as expected
        self.facebook.refresh_from_db()
        self.assertEqual(self.facebook.invoice_company_branch, expected_value)
