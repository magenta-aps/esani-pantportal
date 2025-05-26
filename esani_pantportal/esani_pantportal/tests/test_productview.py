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
from unittest_parametrize import ParametrizedTestCase, parametrize

from esani_pantportal.models import (
    BranchUser,
    Company,
    CompanyBranch,
    CompanyUser,
    EsaniUser,
    Product,
    ProductState,
)

from .conftest import LoginMixin

locale_name = to_locale(get_language())
locale.setlocale(locale.LC_ALL, locale_name + ".UTF-8")


class ProductViewGuiTest(ParametrizedTestCase, LoginMixin, TestCase):
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.company = Company.objects.create(
            name="existing company",
            cvr=12312345,
            address="foo",
            postal_code="123",
            city=cls._test_city,
            phone="+4544457845",
        )
        cls.branch = CompanyBranch.objects.create(
            company=cls.company,
            name="existing branch",
            address="food",
            postal_code="12311",
            city=cls._test_city,
            phone="+4542457845",
            location_id=2,
        )
        cls.branch2 = CompanyBranch.objects.create(
            company=cls.company,
            name="existing branch2",
            address="food",
            postal_code="12311",
            city=cls._test_town,
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

        cls.prod1 = cls._create_product("prod1", "00101122", False, cls.admin_user)
        cls.prod2 = cls._create_product("prod2", "00020002", False, cls.branch_admin)
        cls.prod3 = cls._create_product("prod3", "00020003", True, cls.branch_admin)
        cls.prod4 = cls._create_product(
            "prod4", "00020004", False, cls.another_branch_admin
        )
        cls.prod5 = cls._create_product(
            "prod5", "00020005", False, cls.branch_admin_from_other_branch
        )

    @classmethod
    def _create_product(cls, name, barcode, approved, created_by):
        product = Product.objects.create(
            product_name=name,
            barcode=barcode,
            # Values below are not used in tests
            refund_value=3,
            material="A",
            height=100,
            diameter=60,
            weight=20,
            capacity=500,
            shape="F",
            danish="J",
        )

        if approved:
            product.approve()
            product.save()

        history_entry = product.history.first()
        history_entry.history_user = created_by
        history_entry.save()

        # Re-read product using its manager - which decorates the Product instance with
        # `approved`, etc.
        return Product.objects.get(id=product.id)

    @staticmethod
    def get_html_data(html, exclude=None):
        soup = BeautifulSoup(html, "html.parser")
        output = []

        def key(row):
            return row.find("th").text.strip()

        def value(row):
            return row.find("td").text.strip().split("\n")[0].strip()

        for table in soup.find_all("table"):
            output.append(
                {
                    key(row): value(row)
                    for row in table.tbody.find_all("tr")
                    if (exclude is None) or (key(row) not in exclude)
                }
            )
        return output

    def test_render_esani_admin(self):
        self.login()
        response = self.client.get(
            reverse("pant:product_view", kwargs={"pk": self.prod1.pk})
        )
        data = self.get_html_data(response.content, exclude=["Produkthistorik"])
        self.assertEquals(
            data,
            [
                {
                    "Produktnavn": "prod1",
                    "Stregkode": "00101122",
                    "Status": "Afventer godkendelse",
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
        data = self.get_html_data(response.content, exclude=["Produkthistorik"])
        self.assertEquals(
            data,
            [
                {
                    "Produktnavn": "prod1",
                    "Stregkode": "00101122",
                    "Status": "Afventer godkendelse",
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
    def make_form_data(form, exclude=None):
        form_data = {}
        for field_name, field in form.fields.items():
            if exclude and field_name in exclude:
                continue
            initial_value = form.get_initial_for_field(field, field_name)
            if initial_value is not None:
                form_data[field_name] = initial_value

        return form_data

    def get_form_data(self, pk=None, exclude=None):
        if not pk:
            pk = self.prod1.pk
        response = self.client.get(reverse("pant:product_view", kwargs={"pk": pk}))

        form = response.context_data["form"]

        form_data = self.make_form_data(form, exclude=exclude)
        return form_data

    def test_approve(self):
        self.login()
        form_data = self.get_form_data()
        form_data["action"] = "approve"
        self.prod1 = Product.objects.get(id=self.prod1.id)
        self.assertFalse(self.prod1.approved)
        prod1_url = reverse("pant:product_view", kwargs={"pk": self.prod1.pk})
        response = self.client.post(
            prod1_url,
            form_data,
        )
        self.assertEquals(response.status_code, HTTPStatus.FOUND)
        self.prod1 = Product.objects.get(id=self.prod1.id)
        self.assertTrue(self.prod1.approved)
        self.assertRedirects(response, prod1_url)

        # An approved product cannot be approved again. So we unapprove it instead, as
        # we are testing that submitting a new `action` along with a different field
        # works as expected.
        form_data["action"] = "unapprove"
        form_data["product_name"] = "foo"
        response = self.client.post(
            reverse("pant:product_view", kwargs={"pk": self.prod1.pk}),
            form_data,
        )
        self.prod1 = Product.objects.get(id=self.prod1.id)
        self.assertEqual(self.prod1.product_name, "foo")
        self.assertRedirects(response, prod1_url)

    def test_approve_with_back_url(self):
        self.login()
        form_data = self.get_form_data()
        form_data["action"] = "approve"
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

        # Approve product (to test that it can be rejected?)
        form_data = self.get_form_data()
        form_data["action"] = "approve"
        self.prod1 = Product.objects.get(id=self.prod1.id)
        self.assertFalse(self.prod1.approved)
        response = self.client.post(
            reverse("pant:product_view", kwargs={"pk": self.prod1.pk}),
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
            "Godkendt",
            response.content.decode(),
        )

        # Reject product
        form_data = self.get_form_data()
        form_data["action"] = "reject"
        form_data["rejection_message"] = "Begrundelse for afvisning"
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
            "Afvist",
            response.content.decode(),
        )
        self.assertIn(
            "Begrundelse for afvisning",
            response.content.decode(),
        )

        # "Unreject" product, e.g. undo the previous "reject" action.
        # This will set the product state to AWAITING_APPROVAL.
        form_data = self.get_form_data()
        form_data["action"] = "unreject"
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
            "Status ændret fra Afvist til Afventer godkendelse",
            response.content.decode(),
        )

    @parametrize("username", [("branch_admin",), ("company_admin",)])
    def test_approve_forbidden(self, username):
        """Branch users and company users cannot change product state"""
        self.client.login(username=username, password="12345")
        form_data = self.get_form_data()
        form_data["action"] = "approve"
        # Try to approve product 1 (which is awaiting approval)
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
        self.prod1 = Product.objects.get(id=self.prod1.id)
        self.assertEqual(self.prod1.weight, 1223)
        self.assertRedirects(
            response, reverse("pant:product_view", kwargs={"pk": self.prod1.pk})
        )

    def test_edit_fails_on_duplicate_barcode(self):
        # Try to give product 1 the same barcode as product 2, and observe that
        # a form error is displayed.
        self.login()
        form_data = self.get_form_data()
        form_data["barcode"] = self.prod2.barcode
        response = self.client.post(
            reverse("pant:product_view", kwargs={"pk": self.prod1.pk}),
            form_data,
        )
        self.assertEqual(
            response.context["form"].errors["barcode"],
            [f"Der findes allerede et produkt med stregkoden {self.prod2.barcode}"],
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

        self.prod1 = Product.objects.get(id=self.prod1.id)
        self.assertEqual(self.prod1.created_by.username, "esani_admin")
        response = self.client.post(
            reverse("pant:product_view", kwargs={"pk": self.prod1.pk}),
            form_data,
        )
        self.assertEquals(response.status_code, HTTPStatus.FORBIDDEN)

        # Unless he created the product that he is trying to edit.
        form_data = self.get_form_data(self.prod2.pk)
        form_data["weight"] = 1223

        self.prod2 = Product.objects.get(id=self.prod2.id)
        self.assertEqual(self.prod2.created_by.username, "branch_admin")
        response = self.client.post(
            reverse("pant:product_view", kwargs={"pk": self.prod2.pk}),
            form_data,
        )
        self.assertEquals(response.status_code, HTTPStatus.FOUND)

        # But he should not be allowed to approve his own product
        form_data = self.get_form_data(self.prod2.pk)
        form_data["action"] = "approve"

        self.assertEqual(self.prod2.created_by.username, "branch_admin")
        response = self.client.post(
            reverse("pant:product_view", kwargs={"pk": self.prod2.pk}),
            form_data,
        )
        self.assertEquals(response.status_code, HTTPStatus.FORBIDDEN)

        # Or if the product was created by a colleague
        form_data = self.get_form_data(self.prod4.pk)
        form_data["weight"] = 1223

        self.prod4 = Product.objects.get(id=self.prod4.id)
        self.assertEqual(self.prod4.created_by.username, "favorite_colleague")
        response = self.client.post(
            reverse("pant:product_view", kwargs={"pk": self.prod4.pk}),
            form_data,
        )
        self.assertEquals(response.status_code, HTTPStatus.FOUND)

        # But not if it was created by a colleague from another company
        form_data = self.get_form_data(self.prod5.pk)
        form_data["weight"] = 1223

        self.prod5 = Product.objects.get(id=self.prod5.id)
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
        self.prod3 = Product.objects.get(id=self.prod3.id)
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

        self.prod1 = Product.objects.get(id=self.prod1.id)
        self.assertEqual(self.prod1.created_by.username, "esani_admin")
        response = self.client.post(
            reverse("pant:product_view", kwargs={"pk": self.prod1.pk}),
            form_data,
        )
        self.assertEquals(response.status_code, HTTPStatus.FORBIDDEN)

        # But he can edit products created by his colleague
        form_data = self.get_form_data(self.prod2.pk)
        form_data["weight"] = 1223

        self.prod2 = Product.objects.get(id=self.prod2.id)
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
            self.prod1 = Product.objects.get(id=self.prod1.id)
            self.assertDictEqual(model_to_dict(self.prod1), original)

    def test_remove(self):
        self.client.login(username="branch_admin", password="12345")
        self.assertEqual(self.prod1.created_by.username, "esani_admin")
        self.assertEqual(self.prod2.created_by.username, "branch_admin")

        url_prod1 = reverse("pant:product_delete", kwargs={"pk": self.prod1.pk})
        url_prod2 = reverse("pant:product_delete", kwargs={"pk": self.prod2.pk})
        url_prod3 = reverse("pant:product_delete", kwargs={"pk": self.prod3.pk})

        # Test 1: we cannot delete product 1 as it is not created/owned by us
        response = self.client.post(url_prod1)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

        # Test 2: we can delete product 2 as it is owned by us, and not yet approved
        response = self.client.post(url_prod2)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertQuerySetEqual(
            Product.objects.filter(pk=self.prod2.pk).values_list("state", flat=True),
            [ProductState.DELETED],
        )

        # Test 3: we cannot delete product 3 as it is approved (even though it is
        # owned by us.)
        self.client.login(username="esani_admin", password="12345")
        response = self.client.post(url_prod3)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

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
        form_data["action"] = "approve"
        response = self.client.post(
            reverse("pant:product_view", kwargs={"pk": self.prod1.pk}),
            form_data,
        )
        self.prod1 = Product.objects.get(id=self.prod1.id)

        # History should now show approval of product
        response = self.client.get(
            reverse("pant:product_history", kwargs={"pk": self.prod1.pk})
        )
        self.assertEquals(response.status_code, HTTPStatus.OK)
        self.assertIn(
            "Godkendt",
            response.content.decode(),
        )
