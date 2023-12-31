# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from http import HTTPStatus

from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from esani_pantportal.forms import (
    RegisterBranchUserMultiForm,
    RegisterCompanyUserMultiForm,
    RegisterKioskUserMultiForm,
)
from esani_pantportal.models import (
    BranchUser,
    Company,
    CompanyBranch,
    CompanyUser,
    EsaniUser,
    Kiosk,
    KioskUser,
)


class RegisterNewUserFormTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.existing_company = Company.objects.create(
            name="existing company",
            cvr=12312345,
            address="foo",
            postal_code="123",
            city="test city",
            phone="+4544457845",
            permit_number=2,
        )

        cls.existing_branch = CompanyBranch.objects.create(
            company=cls.existing_company,
            name="existing branch",
            address="food",
            postal_code="12311",
            city="test town",
            phone="+4542457845",
            location_id=2,
        )

        cls.existing_branch2 = CompanyBranch.objects.create(
            company=cls.existing_company,
            name="existing branch2",
            address="foodora",
            postal_code="12311",
            city="test town",
            phone="+4542457845",
            location_id=3,
        )

        cls.existing_kiosk = Kiosk.objects.create(
            name="existing kiosk",
            address="koo",
            postal_code="12311",
            city="test town",
            phone="+4542457845",
            location_id=2,
            cvr=11221122,
        )

        cls.branch_admin = BranchUser.objects.create_user(
            username="branch_admin",
            password="12345",
            email="test@test.com",
            branch=cls.existing_branch2,
        )

        cls.kiosk_admin = KioskUser.objects.create_user(
            username="kiosk_admin",
            password="12345",
            email="test@test.com",
            branch=cls.existing_kiosk,
        )

        cls.company_admin = CompanyUser.objects.create_user(
            username="company_admin",
            password="12345",
            email="test@test.com",
            company=cls.existing_company,
        )
        cls.company_user = CompanyUser.objects.create_user(
            username="company_user",
            password="12345",
            email="test@test.com",
            company=cls.existing_company,
        )

        cls.esani_admin = EsaniUser.objects.create_user(
            username="esani_admin",
            password="12345",
            email="test@test.com",
        )

        call_command("create_groups")
        cls.branch_admin.groups.add(Group.objects.get(name="BranchAdmins"))
        cls.company_admin.groups.add(Group.objects.get(name="CompanyAdmins"))
        cls.esani_admin.groups.add(Group.objects.get(name="EsaniAdmins"))
        cls.kiosk_admin.groups.add(Group.objects.get(name="KioskAdmins"))
        cls.company_user.groups.add(Group.objects.get(name="CompanyUsers"))

        cls.user_data = {
            "user-username": "angus_mc_fife",
            "user-password": "i_am_awesome_123!!",
            "user-password2": "i_am_awesome_123!!",
            "user-phone": "+4531224214",
            "user-first_name": "Angus",
            "user-last_name": "McFife",
            "user-email": "angus@dundee.com",
            "user-branch": "",
            "user-admin": True,
        }

        cls.branch_data = {
            "branch-name": "The Unicorn fields",
            "branch-address": "Old Road 12",
            "branch-postal_code": "1245",
            "branch-city": "Dundee",
            "branch-phone": "+12125552368",
            "branch-location_id": 2,
            "branch-customer_id": 3,
            "branch-company": "",
            "branch-branch_type": "D",
            "branch-registration_number": 2222,
            "branch-account_number": 102010,
            "branch-invoice_mail": "pay_me@moneyplz.dk",
            "branch-municipality": "Scotland",
        }
        cls.kiosk_data = {
            "branch-name": "The Unicorn fields",
            "branch-address": "Old Road 12",
            "branch-postal_code": "1245",
            "branch-city": "Dundee",
            "branch-phone": "+12125552368",
            "branch-location_id": 2,
            "branch-customer_id": 3,
            "branch-company": "",
            "branch-branch_type": "D",
            "branch-registration_number": 2222,
            "branch-account_number": 102010,
            "branch-invoice_mail": "pay_me@moneyplz.dk",
            "branch-municipality": "Scotland",
            "branch-cvr": 1017196402,
            "branch-permit_number": 3,
        }

        cls.company_data = {
            "company-name": "Dundee HQ",
            "company-address": "New Road 12",
            "company-postal_code": "2211",
            "company-city": "Fife",
            "company-phone": "+4544457845",
            "company-cvr": 1017196401,
            "company-permit_number": 123,
            "company-company_type": "E",
            "company-registration_number": 2333,
            "company-account_number": 102033,
            "company-invoice_mail": "pay_me@goldmember.dk",
            "company-country": "UK",
            "company-municipality": "Scotland",
        }


class RegisterNewBranchUserFormTest(RegisterNewUserFormTest):
    def make_user_data(self, include_branch_data=True, include_company_data=True):
        user_data = self.user_data
        if include_branch_data:
            user_data = {**user_data, **self.branch_data}
        if include_company_data:
            user_data = {**user_data, **self.company_data}

        return user_data

    def test_create_admin_user(self):
        user_data = self.make_user_data()
        form = RegisterBranchUserMultiForm(user_data)
        self.assertEquals(form.is_valid(), True)

        user = form.save()
        self.assertEquals(user.branch.name, user_data["branch-name"])
        self.assertEquals(user.branch.company.name, user_data["company-name"])
        self.assertTrue(user.groups.filter(name="BranchAdmins").exists())

    def test_create_non_admin_user(self):
        user_data = self.make_user_data()
        user_data["user-admin"] = False
        form = RegisterBranchUserMultiForm(user_data)
        self.assertEquals(form.is_valid(), True)

        user = form.save()
        self.assertEquals(user.branch.name, user_data["branch-name"])
        self.assertEquals(user.branch.company.name, user_data["company-name"])
        self.assertFalse(user.groups.filter(name="BranchAdmins").exists())
        self.assertTrue(user.groups.filter(name="BranchUsers").exists())

    def test_company_exists(self):
        user_data = self.make_user_data(include_company_data=False)
        user_data["branch-company"] = self.existing_company.pk

        form = RegisterBranchUserMultiForm(user_data)
        self.assertEquals(form.is_valid(), True)

        user = form.save()
        self.assertEquals(user.branch.name, user_data["branch-name"])
        self.assertEquals(user.branch.company, self.existing_company)

    def test_company_and_branch_exist(self):
        user_data = self.make_user_data(
            include_branch_data=False, include_company_data=False
        )

        user_data["branch-company"] = self.existing_company.pk
        user_data["user-branch"] = self.existing_branch.pk

        form = RegisterBranchUserMultiForm(user_data)
        self.assertEquals(form.is_valid(), True)

        user = form.save()
        self.assertEquals(user.branch.company, self.existing_company)
        self.assertEquals(user.branch, self.existing_branch)

    def test_branch_already_has_admin_user(self):
        user_data = self.make_user_data(
            include_branch_data=False, include_company_data=False
        )

        user_data["branch-company"] = self.existing_company.pk
        user_data["user-branch"] = self.existing_branch2.pk

        form = RegisterBranchUserMultiForm(user_data)
        self.assertEquals(form.is_valid(), False)
        self.assertIn(
            "Denne butik har allerede en admin bruger", str(form.crossform_errors)
        )

        form = RegisterBranchUserMultiForm(user_data, allow_multiple_admins=True)
        self.assertEquals(form.is_valid(), True)

    def test_no_company_selected(self):
        user_data = self.make_user_data(include_company_data=False)
        form = RegisterBranchUserMultiForm(user_data)
        self.assertEquals(form.is_valid(), False)
        self.assertEqual(form.errors["branch-company"], ["Dette felt må ikke være tom"])

    def test_company_speficied(self):
        user_data = self.make_user_data()
        form = RegisterBranchUserMultiForm(user_data, company=self.existing_company)
        self.assertEqual(form.forms["branch"].initial["company"], self.existing_company)

    def test_branch_speficied(self):
        user_data = self.make_user_data()
        form = RegisterBranchUserMultiForm(user_data, branch=self.existing_branch)
        self.assertEqual(form.forms["user"].initial["branch"], self.existing_branch)

    def test_no_branch_selected(self):
        user_data = self.make_user_data(
            include_company_data=False, include_branch_data=False
        )
        form = RegisterBranchUserMultiForm(user_data)
        self.assertEquals(form.is_valid(), False)
        self.assertEqual(form.errors["branch-company"], ["Dette felt må ikke være tom"])
        self.assertEqual(form.errors["user-branch"], ["Dette felt må ikke være tom"])

    def test_empty_fields(self):
        user_data = self.make_user_data()

        # These fields are not mandatory
        user_data["company-permit_number"] = None
        user_data["branch-customer_id"] = None

        form = RegisterBranchUserMultiForm(user_data)
        self.assertEquals(form.is_valid(), True)

    def test_empty_fields_failure(self):
        user_data = self.make_user_data()

        # These fields are mandatory
        user_data["company-cvr"] = None
        user_data["branch-phone"] = None

        form = RegisterBranchUserMultiForm(user_data)
        self.assertEquals(form.is_valid(), False)

        self.assertEqual(form.errors["company-cvr"], ["Dette felt må ikke være tom"])
        self.assertEqual(form.errors["branch-phone"], ["Dette felt må ikke være tom"])

    def test_passwords_not_equal(self):
        user_data = self.make_user_data()

        # These fields are mandatory
        user_data["user-password2"] = "wrong_password"

        form = RegisterBranchUserMultiForm(user_data)
        self.assertEquals(form.is_valid(), False)
        self.assertEqual(form.errors["user-password2"], ["Adgangskoder er ikke ens"])

    def test_passwords_too_short(self):
        user_data = self.make_user_data()

        # These fields are mandatory
        user_data["user-password2"] = "badpw"
        user_data["user-password"] = "badpw"

        form = RegisterBranchUserMultiForm(user_data)
        self.assertEquals(form.is_valid(), False)

        self.assertEqual(
            form.errors["user-password"],
            ["Denne adgangskode er for kort. Den skal indeholde mindst 8 tegn."],
        )

    def test_get_view(self):
        url = reverse("pant:branch_user_register")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        branch_dict = response.context_data["branch_dict"]
        self.assertEqual(
            branch_dict,
            {
                self.existing_company.pk: [
                    self.existing_branch.pk,
                    self.existing_branch2.pk,
                ]
            },
        )

        form = response.context_data["form"]
        self.assertEqual(form.allow_multiple_admins, False)

    def test_post_view(self):
        url = reverse("pant:branch_user_register")
        user_data = self.make_user_data()
        response = self.client.post(url, data=user_data)
        self.assertEqual(response.status_code, 302)

    def test_get_esani_admin_view(self):
        self.client.login(username="esani_admin", password="12345")
        url = reverse("pant:branch_user_register_by_admin")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        form = response.context_data["form"]
        self.assertEqual(form.allow_multiple_admins, True)

    def test_post_esani_admin_view(self):
        self.client.login(username="esani_admin", password="12345")
        url = reverse("pant:branch_user_register_by_admin")
        user_data = self.make_user_data()
        response = self.client.post(url, data=user_data)
        self.assertEqual(response.status_code, 302)

    def test_get_branch_admin_view(self):
        self.client.login(username="branch_admin", password="12345")
        url = reverse("pant:branch_user_register_by_admin")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_post_branch_admin_view(self):
        self.client.login(username="branch_admin", password="12345")
        url = reverse("pant:branch_user_register_by_admin")
        user_data = self.make_user_data(
            include_company_data=False, include_branch_data=False
        )
        user_data["branch-company"] = self.existing_company.pk
        user_data["user-branch"] = self.existing_branch.pk

        response = self.client.post(url, data=user_data)
        self.assertEqual(response.status_code, 302)

    def test_get_company_admin_view(self):
        self.client.login(username="company_admin", password="12345")
        url = reverse("pant:branch_user_register_by_admin")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_post_company_admin_view(self):
        self.client.login(username="company_admin", password="12345")
        url = reverse("pant:branch_user_register_by_admin")
        user_data = self.make_user_data(include_company_data=False)
        user_data["branch-company"] = self.existing_company.pk

        response = self.client.post(url, data=user_data)
        self.assertEqual(response.status_code, 302)


class RegisterNewEsaniAdminTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.company = Company.objects.create(
            name="existing company",
            cvr=12312345,
            address="foo",
            postal_code="123",
            city="test city",
            phone="+4544457845",
            permit_number=2,
        )

        cls.branch = CompanyBranch.objects.create(
            company=cls.company,
            name="existing branch",
            address="food",
            postal_code="12311",
            city="test town",
            phone="+4542457845",
            location_id=2,
        )

        cls.branch_admin = BranchUser.objects.create_user(
            username="branch_admin",
            password="12345",
            email="test@test.com",
            branch=cls.branch,
        )
        cls.branch_user = BranchUser.objects.create_user(
            username="branch_user",
            password="12345",
            email="test@test.com",
            branch=cls.branch,
        )
        cls.esani_admin = EsaniUser.objects.create_user(
            username="esani_admin",
            password="12345",
            email="test@test.com",
        )

        call_command("create_groups")
        cls.branch_user.groups.add(Group.objects.get(name="BranchUsers"))
        cls.branch_admin.groups.add(Group.objects.get(name="BranchAdmins"))
        cls.esani_admin.groups.add(Group.objects.get(name="EsaniAdmins"))

    def setUp(self):
        self.user_data = {
            "username": "john_doe",
            "password": "strong_password123",
            "password2": "strong_password123",
            "phone": "+4530214811",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@darkweb.com",
            "admin": True,
        }

    def test_get(self):
        self.client.login(username="esani_admin", password="12345")
        url = reverse("pant:esani_user_register")
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post(self):
        self.client.login(username="esani_admin", password="12345")
        url = reverse("pant:esani_user_register")
        response = self.client.post(url, self.user_data, follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)

        user = EsaniUser.objects.get(username="john_doe")
        user_groups = user.groups.all()

        self.assertEqual(len(user_groups), 1)
        self.assertEqual(user_groups[0].name, "EsaniAdmins")
        self.assertTemplateUsed(response, "esani_pantportal/user/success.html")

    def test_post_access_denied(self):
        for username in ["branch_user", "branch_admin"]:
            self.client.login(username=username, password="12345")
            url = reverse("pant:esani_user_register")
            response = self.client.post(url, self.user_data)
            self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
            self.client.logout()
            EsaniUser.objects.filter(username="john_doe").delete()


class RegisterNewCompanyUserFormTest(RegisterNewUserFormTest):
    def make_user_data(self, include_company_data=True):
        if include_company_data:
            return {**self.user_data, **self.company_data}
        else:
            return self.user_data

    def test_create_admin_user(self):
        user_data = self.make_user_data()
        form = RegisterCompanyUserMultiForm(user_data)
        self.assertEquals(form.is_valid(), True)

        user = form.save()
        self.assertEquals(user.company.name, user_data["company-name"])
        self.assertTrue(user.groups.filter(name="CompanyAdmins").exists())

    def test_create_non_admin_user(self):
        user_data = self.make_user_data()
        user_data["user-admin"] = False
        form = RegisterCompanyUserMultiForm(user_data)
        self.assertEquals(form.is_valid(), True)

        user = form.save()
        self.assertEquals(user.company.name, user_data["company-name"])
        self.assertFalse(user.groups.filter(name="CompanyAdmins").exists())

    def test_get_company_admin_view(self):
        self.client.login(username="company_admin", password="12345")
        url = reverse("pant:company_user_register_by_admin")
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_company_admin_view(self):
        self.client.login(username="company_admin", password="12345")
        url = reverse("pant:company_user_register_by_admin")
        user_data = self.make_user_data(include_company_data=False)
        user_data["user-company"] = self.company_admin.company.pk

        response = self.client.post(url, data=user_data)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_access_denied(self):
        for username in ["branch_admin", "company_user", "kiosk_admin"]:
            self.client.login(username=username, password="12345")
            url = reverse("pant:company_user_register_by_admin")
            response = self.client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
            self.client.logout()

    def test_get_esani_admin_view(self):
        self.client.login(username="esani_admin", password="12345")
        url = reverse("pant:company_user_register_by_admin")
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_esani_admin_view(self):
        self.client.login(username="esani_admin", password="12345")
        url = reverse("pant:company_user_register_by_admin")
        user_data = self.make_user_data()
        response = self.client.post(url, data=user_data)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_post_company_admin_public_view(self):
        url = reverse("pant:company_user_register")
        user_data = self.make_user_data()

        # Add a user in a company that does not exist.
        response = self.client.post(url, data=user_data)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        created_company = Company.objects.get(name=user_data["company-name"])

        # Try to add another user in the same company
        user_data = self.make_user_data(include_company_data=False)
        user_data["user-username"] = "another_user"
        user_data["user-company"] = created_company.pk
        response = self.client.post(url, data=user_data)
        form = response.context_data["form"]
        errors = form.crossform_errors
        self.assertIn("Denne virksomhed har allerede en admin bruger", str(errors))


class RegisterNewKioskUserFormTest(RegisterNewUserFormTest):
    def make_user_data(self, include_kiosk_data=True):
        if include_kiosk_data:
            return {**self.user_data, **self.kiosk_data}
        else:
            return self.user_data

    def test_create_admin_user(self):
        user_data = self.make_user_data()
        form = RegisterKioskUserMultiForm(user_data)
        self.assertEquals(form.is_valid(), True)

        user = form.save()
        self.assertEquals(user.branch.name, user_data["branch-name"])
        self.assertTrue(user.groups.filter(name="KioskAdmins").exists())

    def test_create_non_admin_user(self):
        user_data = self.make_user_data()
        user_data["user-admin"] = False
        form = RegisterKioskUserMultiForm(user_data)
        self.assertEquals(form.is_valid(), True)

        user = form.save()
        self.assertEquals(user.branch.name, user_data["branch-name"])
        self.assertFalse(user.groups.filter(name="KioskAdmins").exists())
        self.assertTrue(user.groups.filter(name="KioskUsers").exists())

    def test_get_kiosk_admin_view(self):
        self.client.login(username="kiosk_admin", password="12345")
        url = reverse("pant:kiosk_user_register_by_admin")
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_kiosk_admin_view(self):
        self.client.login(username="kiosk_admin", password="12345")
        url = reverse("pant:kiosk_user_register_by_admin")
        user_data = self.make_user_data(include_kiosk_data=False)
        user_data["user-branch"] = self.kiosk_admin.branch.pk

        response = self.client.post(url, data=user_data)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_access_denied(self):
        for username in ["branch_admin", "company_user", "company_admin"]:
            self.client.login(username=username, password="12345")
            url = reverse("pant:kiosk_user_register_by_admin")
            response = self.client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
            self.client.logout()

    def test_get_esani_admin_view(self):
        self.client.login(username="esani_admin", password="12345")
        url = reverse("pant:kiosk_user_register_by_admin")
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_esani_admin_view(self):
        self.client.login(username="esani_admin", password="12345")
        url = reverse("pant:kiosk_user_register_by_admin")
        user_data = self.make_user_data()
        response = self.client.post(url, data=user_data)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_post_company_admin_public_view(self):
        url = reverse("pant:kiosk_user_register")
        user_data = self.make_user_data()

        # Add a user in a branch that does not exist.
        response = self.client.post(url, data=user_data)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        created_branch = Kiosk.objects.get(name=user_data["branch-name"])

        # Try to add another user in the same branch
        user_data = self.make_user_data(include_kiosk_data=False)
        user_data["user-username"] = "another_user"
        user_data["user-branch"] = created_branch.pk
        response = self.client.post(url, data=user_data)
        form = response.context_data["form"]
        errors = form.crossform_errors
        self.assertIn("Denne butik har allerede en admin bruger", str(errors))
