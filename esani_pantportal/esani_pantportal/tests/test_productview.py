# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
import datetime
import locale
from http import HTTPStatus

from bs4 import BeautifulSoup
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.forms import model_to_dict
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import get_language, to_locale

from esani_pantportal.models import (
    BranchUser,
    Company,
    CompanyBranch,
    CompanyUser,
    EsaniUser,
    Product,
)

from .conftest import LoginMixin

locale_name = to_locale(get_language())
locale.setlocale(locale.LC_ALL, locale_name + ".UTF-8")


class ProductViewGuiTest(LoginMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.company = Company.objects.create(
            name="existing company",
            cvr=12312345,
            address="foo",
            postal_code="123",
            city="test city",
            phone="+4544457845",
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
        cls.branch2 = CompanyBranch.objects.create(
            company=cls.company,
            name="existing branch2",
            address="food",
            postal_code="12311",
            city="test town",
            phone="+4542457845",
            location_id=2,
        )
        cls.admin_user = EsaniUser.objects.create_user(
            username="esani_admin",
            password="12345",
            email="test@test.com",
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
        cls.another_branch_admin = BranchUser.objects.create_user(
            username="favorite_colleague",
            password="12345",
            email="test@test.com",
            branch=cls.branch,
        )
        cls.branch_admin_from_other_branch = BranchUser.objects.create_user(
            username="rival_colleague",
            password="12345",
            email="test@test.com",
            branch=cls.branch2,
        )
        cls.company_admin = CompanyUser.objects.create_user(
            username="company_admin",
            password="12345",
            email="test@test.com",
            company=cls.company,
        )

        call_command("create_groups")
        company_admin_group = Group.objects.get(name="CompanyAdmins")
        branch_admin_group = Group.objects.get(name="BranchAdmins")
        branch_user_group = Group.objects.get(name="BranchUsers")
        esani_admin_group = Group.objects.get(name="EsaniAdmins")
        cls.admin_user.groups.add(esani_admin_group)
        cls.branch_admin.groups.add(branch_admin_group)
        cls.branch_user.groups.add(branch_user_group)
        cls.another_branch_admin.groups.add(branch_admin_group)
        cls.branch_admin_from_other_branch.groups.add(branch_admin_group)
        cls.company_admin.groups.add(company_admin_group)

        cls.prod1 = Product.objects.create(
            product_name="prod1",
            barcode="00101122",
            refund_value=3,
            approved=False,
            material="A",
            height=100,
            diameter=60,
            weight=20,
            capacity=500,
            shape="F",
            danish="J",
            created_by=cls.admin_user,
        )
        cls.prod2 = Product.objects.create(
            product_name="prod2",
            barcode="00020002",
            refund_value=3,
            approved=False,
            material="A",
            height=100,
            diameter=60,
            weight=20,
            capacity=500,
            shape="F",
            created_by=cls.branch_admin,
        )
        cls.prod3 = Product.objects.create(
            product_name="prod3",
            barcode="00020003",
            refund_value=3,
            approved=True,
            material="A",
            height=100,
            diameter=60,
            weight=20,
            capacity=500,
            shape="F",
            created_by=cls.branch_admin,
        )
        cls.prod4 = Product.objects.create(
            product_name="prod4",
            barcode="00020004",
            refund_value=3,
            approved=False,
            material="A",
            height=100,
            diameter=60,
            weight=20,
            capacity=500,
            shape="F",
            created_by=cls.another_branch_admin,
        )
        cls.prod5 = Product.objects.create(
            product_name="prod5",
            barcode="00020005",
            refund_value=3,
            approved=False,
            material="A",
            height=100,
            diameter=60,
            weight=20,
            capacity=500,
            shape="F",
            created_by=cls.branch_admin_from_other_branch,
        )

    @staticmethod
    def get_html_data(html):
        soup = BeautifulSoup(html, "html.parser")
        output = []

        def key(row):
            return row.find("th").text

        def value(row):
            return row.find("td").text.strip().split("\n")[0].strip()

        for table in soup.find_all("table"):
            output.append({key(row): value(row) for row in table.tbody.find_all("tr")})
        return output

    def test_render_esani_admin(self):
        self.login()
        response = self.client.get(
            reverse("pant:product_view", kwargs={"pk": self.prod1.pk})
        )
        data = self.get_html_data(response.content)
        self.assertEquals(
            data,
            [
                {
                    "Produktnavn": "prod1",
                    "Stregkode": "00101122",
                    "Godkendt": "Nej",
                    "Dansk pant": "Ja",
                    "Oprettet af": "esani_admin (test@test.com)",
                    "Godkendt dato": "-",
                    "Oprettelsesdato": datetime.date.today().strftime("%-d. %B %Y"),
                },
                {
                    "Materiale": "Aluminium",
                    "Højde": "100 mm",
                    "Diameter": "60 mm",
                    "Vægt": "20 g",
                    "Volumen": "500 ml",
                    "Form": "Flaske",
                },
            ],
        )

    def test_render_branch_admin(self):
        self.login("BranchAdmins")
        response = self.client.get(
            reverse("pant:product_view", kwargs={"pk": self.prod1.pk})
        )
        data = self.get_html_data(response.content)
        self.assertEquals(
            data,
            [
                {
                    "Produktnavn": "prod1",
                    "Stregkode": "00101122",
                    "Godkendt": "Nej",
                    "Dansk pant": "Ja",
                    "Godkendt dato": "-",
                    "Oprettelsesdato": datetime.date.today().strftime("%-d. %B %Y"),
                },
                {
                    "Materiale": "Aluminium",
                    "Højde": "100 mm",
                    "Diameter": "60 mm",
                    "Vægt": "20 g",
                    "Volumen": "500 ml",
                    "Form": "Flaske",
                },
            ],
        )

    @staticmethod
    def make_form_data(form):
        form_data = {}
        for field_name, field in form.fields.items():
            form_data[field_name] = form.get_initial_for_field(field, field_name)

        return form_data

    def get_form_data(self, pk=None):
        if not pk:
            pk = self.prod1.pk
        response = self.client.get(reverse("pant:product_view", kwargs={"pk": pk}))

        form = response.context_data["form"]

        form_data = self.make_form_data(form)
        return form_data

    def test_approve(self):
        self.login()
        form_data = self.get_form_data()
        form_data["approved"] = True
        self.assertFalse(self.prod1.approved)
        prod1_url = reverse("pant:product_view", kwargs={"pk": self.prod1.pk})
        response = self.client.post(
            prod1_url,
            form_data,
        )

        self.assertEquals(response.status_code, HTTPStatus.FOUND)
        self.prod1.refresh_from_db()
        self.assertTrue(self.prod1.approved)
        self.assertRedirects(response, reverse("pant:product_list"))

        form_data["product_name"] = "foo"

        response = self.client.post(
            reverse("pant:product_view", kwargs={"pk": self.prod1.pk}),
            form_data,
        )
        self.prod1.refresh_from_db()
        self.assertEqual(self.prod1.product_name, "foo")
        self.assertRedirects(response, prod1_url)

    def test_approve_with_back_url(self):
        self.login()
        form_data = self.get_form_data()
        form_data["approved"] = True
        response = self.client.post(
            reverse("pant:product_view", kwargs={"pk": self.prod1.pk})
            + "?back=/produkt/%3Fproduct_name%3Dprod1",
            form_data,
        )

        self.assertRedirects(
            response,
            reverse("pant:product_list") + "?product_name=prod1",
        )
        response = self.client.get(
            reverse("pant:product_view", kwargs={"pk": self.prod1.pk}),
        )
        self.assertIn(
            "Produkthistorik",
            response.content.decode(),
        )

    def test_disapprove(self):
        self.login()
        form_data = self.get_form_data()
        form_data["approved"] = True
        self.assertFalse(self.prod1.approved)
        response = self.client.post(
            reverse("pant:product_view", kwargs={"pk": self.prod1.pk}),
            form_data,
        )

        response = self.client.get(
            reverse("pant:product_view", kwargs={"pk": self.prod1.pk}),
        )
        self.assertNotIn(
            "Oprettet d.",
            response.content.decode(),
        )
        self.assertIn(
            "Produkthistorik",
            response.content.decode(),
        )

        form_data = self.get_form_data()
        form_data["approved"] = False
        response = self.client.post(
            reverse("pant:product_view", kwargs={"pk": self.prod1.pk})
            + "?back=/produkt/%3Fproduct_name%3Dprod1",
            form_data,
        )

        response = self.client.get(
            reverse("pant:product_view", kwargs={"pk": self.prod1.pk}),
        )
        self.assertIn(
            "Produkthistorik",
            response.content.decode(),
        )
        self.assertIn(
            "Gjort Inaktiv",
            response.content.decode(),
        )

    def test_approve_forbidden(self):
        self.client.login(username="branch_admin", password="12345")
        form_data = self.get_form_data()
        form_data["approved"] = True

        # Test that branch-users cannot approve products
        response = self.client.post(
            reverse("pant:product_view", kwargs={"pk": self.prod1.pk}),
            form_data,
        )
        self.assertEquals(response.status_code, HTTPStatus.FORBIDDEN)

    def test_edit(self):
        self.login()
        form_data = self.get_form_data()
        form_data["weight"] = 1223

        response = self.client.post(
            reverse("pant:product_view", kwargs={"pk": self.prod1.pk}),
            form_data,
        )

        self.assertEquals(response.status_code, HTTPStatus.FOUND)
        self.prod1.refresh_from_db()
        self.assertEqual(self.prod1.weight, 1223)
        self.assertRedirects(
            response, reverse("pant:product_view", kwargs={"pk": self.prod1.pk})
        )

    def test_view_as_branch_user(self):
        self.client.login(username="branch_user", password="12345")
        response = self.client.get(
            reverse("pant:product_view", kwargs={"pk": self.prod1.pk})
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

        form_data = self.get_form_data()
        form_data["weight"] = 1223

        response = self.client.post(
            reverse("pant:product_view", kwargs={"pk": self.prod1.pk}),
            form_data,
        )
        self.assertEquals(response.status_code, HTTPStatus.FORBIDDEN)

    def test_edit_forbidden_branch_admin(self):
        # A branch user should not be able to edit products created by esani admins
        self.client.login(username="branch_admin", password="12345")
        form_data = self.get_form_data()
        form_data["weight"] = 1223

        self.assertEqual(self.prod1.created_by.username, "esani_admin")
        response = self.client.post(
            reverse("pant:product_view", kwargs={"pk": self.prod1.pk}),
            form_data,
        )
        self.assertEquals(response.status_code, HTTPStatus.FORBIDDEN)

        # Unless he created the product that he is trying to edit.
        form_data = self.get_form_data(self.prod2.pk)
        form_data["weight"] = 1223

        self.assertEqual(self.prod2.created_by.username, "branch_admin")
        response = self.client.post(
            reverse("pant:product_view", kwargs={"pk": self.prod2.pk}),
            form_data,
        )
        self.assertEquals(response.status_code, HTTPStatus.FOUND)

        # But he should not be allowed to approve his own product
        form_data = self.get_form_data(self.prod2.pk)
        form_data["approved"] = True

        self.assertEqual(self.prod2.created_by.username, "branch_admin")
        response = self.client.post(
            reverse("pant:product_view", kwargs={"pk": self.prod2.pk}),
            form_data,
        )
        self.assertEquals(response.status_code, HTTPStatus.FORBIDDEN)

        # Or if the product was created by a colleague
        form_data = self.get_form_data(self.prod4.pk)
        form_data["weight"] = 1223

        self.assertEqual(self.prod4.created_by.username, "favorite_colleague")
        response = self.client.post(
            reverse("pant:product_view", kwargs={"pk": self.prod4.pk}),
            form_data,
        )
        self.assertEquals(response.status_code, HTTPStatus.FOUND)

        # But not if it was created by a colleague from another company
        form_data = self.get_form_data(self.prod5.pk)
        form_data["weight"] = 1223

        self.assertEqual(self.prod5.created_by.username, "rival_colleague")
        response = self.client.post(
            reverse("pant:product_view", kwargs={"pk": self.prod5.pk}),
            form_data,
        )
        self.assertEquals(response.status_code, HTTPStatus.FORBIDDEN)

        # If the product that he is trying to edit is already approved, he should not
        # be allowed to edit it.
        form_data = self.get_form_data(self.prod3.pk)
        form_data["weight"] = 1223

        self.assertEqual(self.prod3.approved, True)
        response = self.client.post(
            reverse("pant:product_view", kwargs={"pk": self.prod3.pk}),
            form_data,
        )
        self.assertEquals(response.status_code, HTTPStatus.FORBIDDEN)

    def test_edit_approved_product(self):
        # ESANI admins can edit approved products.
        # Branch admins cannot
        self.login()
        expected_status_dict = {
            "esani_admin": HTTPStatus.FOUND,
            "branch_admin": HTTPStatus.FORBIDDEN,
        }
        form_data = self.get_form_data(self.prod3.pk)
        form_data["weight"] = 1223
        self.assertEqual(self.prod3.approved, True)

        for username, expected_status in expected_status_dict.items():
            self.client.login(username=username, password="12345")
            response = self.client.post(
                reverse("pant:product_view", kwargs={"pk": self.prod3.pk}),
                form_data,
            )
            self.assertEquals(response.status_code, expected_status)

    def test_edit_forbidden_company_admin(self):
        # A company user should not be able to edit products created by esani admins
        self.client.login(username="company_admin", password="12345")
        form_data = self.get_form_data()
        form_data["weight"] = 1223

        self.assertEqual(self.prod1.created_by.username, "esani_admin")
        response = self.client.post(
            reverse("pant:product_view", kwargs={"pk": self.prod1.pk}),
            form_data,
        )
        self.assertEquals(response.status_code, HTTPStatus.FORBIDDEN)

        # But he can edit products created by his colleague
        form_data = self.get_form_data(self.prod2.pk)
        form_data["weight"] = 1223

        self.assertEqual(self.prod2.created_by.username, "branch_admin")
        response = self.client.post(
            reverse("pant:product_view", kwargs={"pk": self.prod2.pk}),
            form_data,
        )
        self.assertEquals(response.status_code, HTTPStatus.FOUND)

    def test_edit_form_invalid(self):
        self.login()
        form_data = self.get_form_data()
        form_data["weight"] = "one_hundred_and_eighty"

        response = self.client.post(
            reverse("pant:product_view", kwargs={"pk": self.prod1.pk}),
            form_data,
        )

        self.assertEquals(response.status_code, HTTPStatus.OK)
        context_data = response.context_data
        fields_to_show = context_data["form_fields_to_show"]
        self.assertIn("weight", fields_to_show)

    def test_others_fail(self):
        self.login()
        response = self.client.get(
            reverse("pant:product_view", kwargs={"pk": self.prod1.pk})
        )

        form = response.context_data["form"]
        original = model_to_dict(self.prod1)
        for field in original.keys():
            if field in form.fields:
                continue

            form_data = self.make_form_data(form)
            form_data[field] = "1"
            self.client.post(
                reverse("pant:product_view", kwargs={"pk": self.prod1.pk})
                + "?back=foo",
                form_data,
            )
            self.prod1.refresh_from_db()
            self.assertDictEqual(model_to_dict(self.prod1), original)

    def test_remove(self):
        self.client.login(username="branch_admin", password="12345")
        self.assertEqual(self.prod1.created_by.username, "esani_admin")
        self.assertEqual(self.prod2.created_by.username, "branch_admin")

        url_prod1 = reverse("pant:product_delete", kwargs={"pk": self.prod1.pk})
        url_prod2 = reverse("pant:product_delete", kwargs={"pk": self.prod2.pk})
        response = self.client.post(url_prod1)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

        response = self.client.post(url_prod2)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertFalse(Product.objects.filter(pk=self.prod2.pk).exists())

    def test_history(self):
        self.login()

        # Before approval, history should reflect no approval
        response = self.client.get(
            reverse("pant:product_history", kwargs={"pk": self.prod1.pk})
        )
        self.assertEquals(response.status_code, HTTPStatus.OK)
        self.assertNotIn(
            "Godkendt",
            response.content.decode(),
        )

        # Approve the product
        form_data = self.get_form_data()
        form_data["approved"] = True
        response = self.client.post(
            reverse("pant:product_view", kwargs={"pk": self.prod1.pk}),
            form_data,
        )
        self.prod1.refresh_from_db()

        # History should now show approval of product
        response = self.client.get(
            reverse("pant:product_history", kwargs={"pk": self.prod1.pk})
        )
        self.assertEquals(response.status_code, HTTPStatus.OK)
        self.assertIn(
            "Godkendt",
            response.content.decode(),
        )
