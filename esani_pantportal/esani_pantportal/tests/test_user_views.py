from http import HTTPStatus

from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from esani_pantportal.models import (
    BranchUser,
    Company,
    CompanyBranch,
    CompanyUser,
    EsaniUser,
    Kiosk,
    KioskUser,
)

from .conftest import LoginMixin


class BaseUserTest(LoginMixin, TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.facebook = Company.objects.create(
            name="facebook",
            cvr=12312345,
            address="foo",
            postal_code="123",
            city="test city",
            phone="+4544457845",
            permit_number=2,
        )

        cls.google = Company.objects.create(
            name="google",
            cvr=12312346,
            address="foo",
            postal_code="123",
            city="test city",
            phone="+4544457845",
            permit_number=2,
        )

        cls.facebook_branch = CompanyBranch.objects.create(
            company=cls.facebook,
            name="facebook_branch",
            address="food",
            postal_code="12311",
            city="test town",
            phone="+4542457845",
            location_id=2,
        )

        cls.kiosk = Kiosk.objects.create(
            name="kiosk",
            address="food",
            postal_code="12311",
            city="test town",
            phone="+4542457845",
            location_id=2,
            cvr=11221122,
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


class EsaniAdminUserUpdateViewTest(BaseUserTest):
    def setUp(self):
        self.facebook_admin_url = reverse(
            "pant:user_view",
            kwargs={"pk": self.facebook_admin.pk},
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
            "pant:change_password",
            kwargs={"pk": self.facebook_branch_user.pk},
        )

        self.google_employee_password_url = reverse(
            "pant:change_password",
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
