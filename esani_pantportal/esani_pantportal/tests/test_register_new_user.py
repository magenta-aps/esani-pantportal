# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from esani_pantportal.forms import UserRegisterMultiForm
from esani_pantportal.models import Branch, Company, CompanyUser


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

        cls.existing_branch = Branch.objects.create(
            company=cls.existing_company,
            name="existing branch",
            address="food",
            postal_code="12311",
            city="test town",
            phone="+4542457845",
            location_id=2,
        )

        cls.existing_branch2 = Branch.objects.create(
            company=cls.existing_company,
            name="existing branch2",
            address="foodora",
            postal_code="12311",
            city="test town",
            phone="+4542457845",
            location_id=3,
        )

        cls.company_admin = CompanyUser.objects.create_user(
            username="company_admin",
            password="12345",
            email="test@test.com",
            branch=cls.existing_branch2,
        )

        call_command("create_groups")
        cls.company_admin.groups.add(Group.objects.get(name="CompanyAdmins"))

    @staticmethod
    def make_user_data(include_branch_data=True, include_company_data=True):
        user_data = {
            "user-username": "angus_mc_fife",
            "user-password": "i_am_awesome_123!!",
            "user-password2": "i_am_awesome_123!!",
            "user-phone": "+4531224214",
            "user-first_name": "Angus",
            "user-last_name": "McFife",
            "user-email": "angus@dundee.com",
            "user-branch": "",
            "branch-name": "The Unicorn fields",
            "branch-address": "Old Road 12",
            "branch-postal_code": "1245",
            "branch-city": "Dundee",
            "branch-phone": "+12125552368",
            "branch-location_id": 2,
            "branch-customer_id": 3,
            "branch-company": "",
            "company-name": "Dundee HQ",
            "company-address": "New Road 12",
            "company-postal_code": "2211",
            "company-city": "Fife",
            "company-phone": "+4544457845",
            "company-cvr": 1017196401,
            "company-permit_number": 123,
        }

        if not include_branch_data:
            for key in user_data.keys():
                if key.startswith("branch-"):
                    user_data[key] = None

        if not include_company_data:
            for key in user_data.keys():
                if key.startswith("company-"):
                    user_data[key] = None

        return user_data

    def test_create_user(self):
        user_data = self.make_user_data()
        form = UserRegisterMultiForm(user_data)
        self.assertEquals(form.is_valid(), True)

        user = form.save()
        self.assertEquals(user.branch.name, user_data["branch-name"])
        self.assertEquals(user.branch.company.name, user_data["company-name"])

    def test_company_exists(self):
        user_data = self.make_user_data(include_company_data=False)
        user_data["branch-company"] = self.existing_company.pk

        form = UserRegisterMultiForm(user_data)
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

        form = UserRegisterMultiForm(user_data)
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

        form = UserRegisterMultiForm(user_data)
        self.assertEquals(form.is_valid(), False)
        self.assertIn(
            "Denne butik har allerede en admin bruger", str(form.crossform_errors)
        )

    def test_no_company_selected(self):
        user_data = self.make_user_data(include_company_data=False)
        form = UserRegisterMultiForm(user_data)
        self.assertEquals(form.is_valid(), False)
        self.assertEqual(form.errors["branch-company"], ["Dette felt må ikke være tom"])

    def test_no_branch_selected(self):
        user_data = self.make_user_data(
            include_company_data=False, include_branch_data=False
        )
        form = UserRegisterMultiForm(user_data)
        self.assertEquals(form.is_valid(), False)
        self.assertEqual(form.errors["branch-company"], ["Dette felt må ikke være tom"])
        self.assertEqual(form.errors["user-branch"], ["Dette felt må ikke være tom"])

    def test_empty_fields(self):
        user_data = self.make_user_data()

        # These fields are not mandatory
        user_data["company-permit_number"] = None
        user_data["branch-customer_id"] = None

        form = UserRegisterMultiForm(user_data)
        self.assertEquals(form.is_valid(), True)

    def test_empty_fields_failure(self):
        user_data = self.make_user_data()

        # These fields are mandatory
        user_data["company-cvr"] = None
        user_data["branch-phone"] = None

        form = UserRegisterMultiForm(user_data)
        self.assertEquals(form.is_valid(), False)

        self.assertEqual(form.errors["company-cvr"], ["Dette felt må ikke være tom"])
        self.assertEqual(form.errors["branch-phone"], ["Dette felt må ikke være tom"])

    def test_passwords_not_equal(self):
        user_data = self.make_user_data()

        # These fields are mandatory
        user_data["user-password2"] = "wrong_password"

        form = UserRegisterMultiForm(user_data)
        self.assertEquals(form.is_valid(), False)
        self.assertEqual(form.errors["user-password2"], ["Adgangskoder er ikke ens"])

    def test_passwords_too_short(self):
        user_data = self.make_user_data()

        # These fields are mandatory
        user_data["user-password2"] = "badpw"
        user_data["user-password"] = "badpw"

        form = UserRegisterMultiForm(user_data)
        self.assertEquals(form.is_valid(), False)

        self.assertEqual(
            form.errors["user-password"],
            ["Denne adgangskode er for kort. Den skal indeholde mindst 8 tegn."],
        )

    def test_get_view(self):
        url = reverse("pant:user_register")
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

    def test_post_view(self):
        url = reverse("pant:user_register")
        user_data = self.make_user_data()
        response = self.client.post(url, data=user_data)
        self.assertEqual(response.status_code, 302)
