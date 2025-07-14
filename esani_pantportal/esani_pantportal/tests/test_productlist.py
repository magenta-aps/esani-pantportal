# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
import datetime
import json
from http import HTTPStatus

from bs4 import BeautifulSoup
from django.http import HttpRequest
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import make_aware

from esani_pantportal.forms import ProductFilterForm
from esani_pantportal.models import (
    DepositPayout,
    DepositPayoutItem,
    EsaniUser,
    ImportJob,
    Kiosk,
    Product,
    ProductState,
)
from esani_pantportal.views import ProductSearchView

from .conftest import LoginMixin
from .helpers import ProductFixtureMixin


class ProductListSearchDataTest(TestCase):
    def test_search_data_pagination_int(self):
        view = ProductSearchView()
        view.paginate_by = 20
        view.form = ProductFilterForm()
        view.form.cleaned_data = {"offset": 40, "limit": 10, "foobar": 42}
        data = view.search_data
        self.assertEquals(data["offset"], 40)
        self.assertEquals(data["limit"], 10)
        self.assertEquals(data["foobar"], 42)
        self.assertEquals(data["page_number"], 5)

    def test_search_data_pagination_str(self):
        view = ProductSearchView()
        view.paginate_by = 20
        view.form = ProductFilterForm()
        view.form.cleaned_data = {"offset": "40", "limit": "10", "foobar": "42"}
        data = view.search_data
        self.assertEquals(data["offset"], 40)
        self.assertEquals(data["limit"], 10)
        self.assertEquals(data["foobar"], "42")
        self.assertEquals(data["page_number"], 5)

    def test_search_data_pagination_negative(self):
        view = ProductSearchView()
        view.paginate_by = 20
        view.form = ProductFilterForm()
        view.form.cleaned_data = {"offset": "-2", "limit": "-2", "foobar": 42}
        data = view.search_data
        self.assertEquals(data["offset"], 0)
        self.assertEquals(data["limit"], 1)
        self.assertEquals(data["foobar"], 42)
        self.assertEquals(data["page_number"], 1)


class ProductListGetQuerysetTest(LoginMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.prod1 = Product.objects.create(
            product_name="cider",
            barcode="0010",
            refund_value=3,
            material="A",
            height=100,
            diameter=60,
            weight=20,
            capacity=500,
            shape="F",
        )
        cls.prod2 = Product.objects.create(
            product_name="juice",
            barcode="0002",
            refund_value=3,
            material="A",
            height=100,
            diameter=60,
            weight=20,
            capacity=500,
            shape="F",
        )
        cls.prod2.approve()
        cls.prod2.save()

    def test_get_queryset_normal(self):
        view = ProductSearchView()
        view.paginate_by = 20
        view.form = ProductFilterForm()
        view.form.cleaned_data = {"offset": 0, "limit": 10}
        qs = view.get_queryset()
        self.assertIn(self.prod1, qs)
        self.assertIn(self.prod2, qs)

    def test_get_queryset_filter_name(self):
        # `DER` should retrieve `self.prod1` whose name is `cider`.
        view = ProductSearchView()
        view.form = ProductFilterForm()
        view.form.cleaned_data = {"offset": 0, "limit": 10, "search": "DER"}
        qs = view.get_queryset()
        self.assertIn(self.prod1, qs)
        self.assertNotIn(self.prod2, qs)

        # `ICE` should retrieve `self.prod2` whose name is `juice`.
        view = ProductSearchView()
        view.form = ProductFilterForm()
        view.form.cleaned_data = {"offset": 0, "limit": 10, "search": "ICE"}
        qs = view.get_queryset()
        self.assertNotIn(self.prod1, qs)
        self.assertIn(self.prod2, qs)

    def test_get_queryset_filter_barcode(self):
        # Exact match on `self.prod1.barcode`
        view = ProductSearchView()
        view.paginate_by = 20
        view.form = ProductFilterForm()
        view.form.cleaned_data = {"offset": 0, "limit": 10, "barcode": "0010"}
        qs = view.get_queryset()
        self.assertIn(self.prod1, qs)
        self.assertNotIn(self.prod2, qs)

        # Exact match on `self.prod2.barcode`
        view = ProductSearchView()
        view.form = ProductFilterForm()
        view.form.cleaned_data = {"offset": 0, "limit": 10, "barcode": "0002"}
        qs = view.get_queryset()
        self.assertNotIn(self.prod1, qs)
        self.assertIn(self.prod2, qs)

    def test_get_queryset_filter_approved(self):
        view = ProductSearchView()
        view.form = ProductFilterForm()
        view.form.cleaned_data = {"offset": 0, "limit": 10, "approved": False}
        qs = view.get_queryset()
        self.assertIn(self.prod1, qs)
        self.assertNotIn(self.prod2, qs)

        view = ProductSearchView()
        view.form = ProductFilterForm()
        view.form.cleaned_data = {"offset": 0, "limit": 10, "approved": True}
        qs = view.get_queryset()
        self.assertNotIn(self.prod1, qs)
        self.assertIn(self.prod2, qs)

    def test_get_queryset_sort_product_name(self):
        view = ProductSearchView()
        view.form = ProductFilterForm()
        view.form.cleaned_data = {
            "offset": 0,
            "limit": 10,
            "sort": "product_name",
            "order": "asc",
        }
        qs = view.get_queryset()
        self.assertEquals(self.prod1, qs[0])
        self.assertEquals(self.prod2, qs[1])

        view = ProductSearchView()
        view.form = ProductFilterForm()
        view.form.cleaned_data = {
            "offset": 0,
            "limit": 10,
            "sort": "product_name",
            "order": "desc",
        }
        qs = view.get_queryset()
        self.assertEquals(self.prod1, qs[1])
        self.assertEquals(self.prod2, qs[0])

    def test_get_queryset_sort_barcode(self):
        view = ProductSearchView()
        view.form = ProductFilterForm()
        view.form.cleaned_data = {
            "offset": 0,
            "limit": 10,
            "sort": "barcode",
            "order": "asc",
        }
        qs = view.get_queryset()
        self.assertEquals(self.prod1, qs[1])
        self.assertEquals(self.prod2, qs[0])

        view = ProductSearchView()
        view.form = ProductFilterForm()
        view.form.cleaned_data = {
            "offset": 0,
            "limit": 10,
            "sort": "barcode",
            "order": "desc",
        }
        qs = view.get_queryset()
        self.assertEquals(self.prod1, qs[0])
        self.assertEquals(self.prod2, qs[1])


class ProductListFormValidTest(LoginMixin, TestCase):
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        cls.user = EsaniUser.objects.create_user(
            username="testuser_EsaniAdmins",
            password="12345",
            email="test@test.com",
        )
        cls.job = ImportJob.objects.create(
            imported_by=cls.user,
            file_name="dummy_products.csv",
            date=make_aware(datetime.datetime(2020, 1, 1)),
        )
        cls.prod1 = Product.objects.create(
            product_name="cider",
            barcode="0010",
            refund_value=3,
            material="A",
            height=100,
            diameter=60,
            weight=20,
            capacity=500,
            shape="F",
            id=1,
            # created_by=cls.user,
            import_job=cls.job,
        )
        cls.prod2 = Product.objects.create(
            product_name="juice",
            barcode="0002",
            refund_value=3,
            material="A",
            height=100,
            diameter=60,
            weight=20,
            capacity=500,
            shape="F",
            id=2,
            # created_by=cls.user,
        )
        cls.prod2.approve()
        cls.prod2.save()

    def test_form_valid(self):
        user = self.login()
        self.maxDiff = None
        view = ProductSearchView()
        view.paginate_by = 20
        view.form = ProductFilterForm()
        view.form.cleaned_data = {"offset": 0, "limit": 10, "json": "1"}
        view.request = HttpRequest()
        view.request.method = "GET"
        view.request.user = user
        view.kwargs = {}
        response = view.form_valid(view.form)
        doc = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertListEqual(
            doc["items"],
            [
                {
                    "actions": '<a href="/produkt/1" class="btn btn-sm btn-primary">'
                    "Vis</a>",
                    "status": ProductState.AWAITING_APPROVAL.label,
                    "approval_date": "-",
                    "creation_date": datetime.date.today().strftime("%-d. %b %Y"),
                    "barcode": "0010",
                    "capacity": 500,
                    "diameter": 60,
                    "height": 100,
                    "id": 1,
                    "material": "Aluminium",
                    "product_name": "cider",
                    "shape": "Flaske",
                    "weight": 20,
                    "danish": "Ukendt",
                    "file_name": self.job.file_name,
                    "select": (
                        '<div class="p-1"><input type="checkbox" id="select_1" '
                        'value="1" /></div>'
                    ),
                },
                {
                    "actions": '<a href="/produkt/2" class="btn btn-sm btn-primary">'
                    "Vis</a>",
                    "status": ProductState.APPROVED.label,
                    "approval_date": datetime.date.today().strftime("%-d. %b %Y"),
                    "creation_date": datetime.date.today().strftime("%-d. %b %Y"),
                    "barcode": "0002",
                    "capacity": 500,
                    "diameter": 60,
                    "height": 100,
                    "id": 2,
                    "material": "Aluminium",
                    "product_name": "juice",
                    "shape": "Flaske",
                    "weight": 20,
                    "danish": "Ukendt",
                    "file_name": "-",
                    "select": (
                        '<div class="p-1"><input type="checkbox" id="select_2" '
                        'value="2" /></div>'
                    ),
                },
            ],
        )
        self.assertEqual(doc["total"], 2)

        view = ProductSearchView()
        view.paginate_by = 20
        view.form = ProductFilterForm()
        view.form.cleaned_data = {
            "offset": 0,
            "limit": 10,
            "json": "1",
            "search": "cidr",
        }
        view.request = HttpRequest()
        view.request.method = "GET"
        view.request.user = user
        view.kwargs = {}
        response = view.form_valid(view.form)
        doc = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(
            doc["items"],
            [
                {
                    "actions": '<a href="/produkt/1" class="btn btn-sm btn-primary">'
                    "Vis</a>",
                    "status": ProductState.AWAITING_APPROVAL.label,
                    "approval_date": "-",
                    "creation_date": datetime.date.today().strftime("%-d. %b %Y"),
                    "barcode": "0010",
                    "capacity": 500,
                    "diameter": 60,
                    "height": 100,
                    "id": 1,
                    "material": "Aluminium",
                    "product_name": "cider",
                    "shape": "Flaske",
                    "weight": 20,
                    "danish": "Ukendt",
                    "file_name": self.job.file_name,
                    "select": (
                        '<div class="p-1"><input type="checkbox" id="select_1" '
                        'value="1" /></div>'
                    ),
                }
            ],
        )
        self.assertEqual(doc["total"], 1)


class ProductListGuiTest(LoginMixin, TestCase):
    def setUp(self):
        self.user = self.login()

    @classmethod
    def setUpTestData(cls):
        importer = EsaniUser.objects.create_user(
            username="importer",
            password="12345",
            email="test@test.com",
        )

        cls.job = ImportJob.objects.create(
            imported_by=importer,
            file_name="dummy_products.csv",
            date=make_aware(datetime.datetime(2020, 1, 1)),
        )
        cls.prod1 = Product.objects.create(
            product_name="cider",
            barcode="0010",
            refund_value=3,
            material="A",
            height=100,
            diameter=60,
            weight=20,
            capacity=500,
            shape="F",
            import_job=cls.job,
        )
        cls.prod2 = Product.objects.create(
            product_name="juice",
            barcode="0002",
            refund_value=3,
            material="A",
            height=100,
            diameter=60,
            weight=20,
            capacity=500,
            shape="F",
        )
        cls.prod2.approve()
        cls.prod2.save()

        cls.prod1_expected_response = {
            "Produktnavn": cls.prod1.product_name,
            "Stregkode": cls.prod1.barcode,
            "Status": ProductState.AWAITING_APPROVAL.label,
            "Godkendt dato": "-",
            "Oprettelsesdato": datetime.date.today().strftime("%-d. %b %Y"),
            "Volumen": str(cls.prod1.capacity),
            "Materiale": "Aluminium",
            "Højde": str(cls.prod1.height),
            "Diameter": str(cls.prod1.diameter),
            "Vægt": str(cls.prod1.weight),
            "Form": "Flaske",
            "Dansk pant": "Ukendt",
            "Filnavn": cls.job.file_name,
            "Handlinger": "Vis",
        }

        cls.prod2_expected_response = {
            "Produktnavn": cls.prod2.product_name,
            "Stregkode": cls.prod2.barcode,
            "Status": ProductState.APPROVED.label,
            "Godkendt dato": datetime.date.today().strftime("%-d. %b %Y"),
            "Oprettelsesdato": datetime.date.today().strftime("%-d. %b %Y"),
            "Volumen": str(cls.prod2.capacity),
            "Materiale": "Aluminium",
            "Højde": str(cls.prod2.height),
            "Diameter": str(cls.prod2.diameter),
            "Vægt": str(cls.prod2.weight),
            "Form": "Flaske",
            "Dansk pant": "Ukendt",
            "Filnavn": "-",
            "Handlinger": "Vis",
        }

    @staticmethod
    def get_table_headers(html):
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table")
        return [
            cell.attrs.get("data-field")
            for cell in table.thead.tr.find_all("th")
            if cell.attrs.get("data-visible", "true") == "true"
        ]

    @staticmethod
    def get_html_items(html):
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table")
        headers = [cell.text.strip() for cell in table.thead.tr.find_all("th")]
        output = []
        for row in table.tbody.find_all("tr"):
            rowdata = [cell.text.strip() for cell in row.find_all("td")]
            output.append(
                {
                    k: v
                    for k, v in dict(zip(headers, rowdata)).items()
                    if k and k != "ID"  # The ID column is always hidden
                }
            )
        return output

    @staticmethod
    def get_json_items(text):
        data = json.loads(text)
        return [
            {
                "Produktnavn": item["product_name"],
                "Stregkode": item["barcode"],
                "Status": item["status"],
                "Volumen": str(item["capacity"]),
                "Materiale": item["material"],
                "Højde": str(item["height"]),
                "Diameter": str(item["diameter"]),
                "Vægt": str(item["weight"]),
                "Form": item["shape"],
                "Dansk pant": item["danish"],
                "Godkendt dato": item["approval_date"],
                "Oprettelsesdato": item["creation_date"],
                "Filnavn": item["file_name"],
                "Handlinger": "Vis",
            }
            for item in data["items"]
        ]

    def test_render(self):
        expected = [self.prod1_expected_response, self.prod2_expected_response]
        response = self.client.get(reverse("pant:product_list"))
        data = self.get_html_items(response.content)
        self.assertEquals(data, expected)
        response = self.client.get(reverse("pant:product_list") + "?json=1")
        data = self.get_json_items(response.content)
        self.assertEquals(data, expected)

    def test_render_paginated(self):
        expected = [self.prod2_expected_response]

        response = self.client.get(reverse("pant:product_list") + "?offset=1")
        data = self.get_html_items(response.content)
        self.assertEquals(data, expected)

        response = self.client.get(reverse("pant:product_list") + "?json=1&offset=1")
        data = self.get_json_items(response.content)
        self.assertEquals(data, expected)

    def test_filter_name(self):
        expected = [self.prod1_expected_response]
        response = self.client.get(reverse("pant:product_list") + "?search=CIDER")
        data = self.get_html_items(response.content)
        self.assertEquals(data, expected)
        response = self.client.get(
            reverse("pant:product_list") + "?json=1&search=CIDER"
        )
        data = self.get_json_items(response.content)
        self.assertEquals(data, expected)

    def test_filter_barcode(self):
        expected = [self.prod2_expected_response]
        response = self.client.get(reverse("pant:product_list") + "?barcode=0002")
        data = self.get_html_items(response.content)
        self.assertEquals(data, expected)
        response = self.client.get(
            reverse("pant:product_list") + "?json=1&barcode=0002"
        )
        data = self.get_json_items(response.content)
        self.assertEquals(data, expected)

    def test_filter_approved(self):
        expected = [self.prod2_expected_response]
        response = self.client.get(reverse("pant:product_list") + "?approved=true")
        data = self.get_html_items(response.content)
        self.assertEquals(data, expected)
        response = self.client.get(
            reverse("pant:product_list") + "?json=1&approved=true"
        )
        data = self.get_json_items(response.content)
        self.assertEquals(data, expected)

    def test_filter_approved_name(self):
        expected = []
        response = self.client.get(
            reverse("pant:product_list") + "?approved=true&search=DER"
        )
        data = self.get_html_items(response.content)
        self.assertEquals(data, expected)
        response = self.client.get(
            reverse("pant:product_list") + "?json=1&approved=true&search=DER"
        )
        data = self.get_json_items(response.content)
        self.assertEquals(data, expected)

    def test_column_preferences(self):
        # Load the page with default settings
        response = self.client.get(reverse("pant:product_list"))
        data = self.get_table_headers(response.content)
        self.assertIn("material", data)

        # Edit preferences
        self.client.post(
            reverse("pant:preferences_update", kwargs={"pk": self.user.pk}),
            data={
                "show_material": "false",
                "preferences_class_name": "ProductListViewPreferences",
            },
        )

        # Reload the page
        response = self.client.get(reverse("pant:product_list"))
        data = self.get_table_headers(response.content)
        self.assertNotIn("material", data)


class ProductListBulkApprovalTest(LoginMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.prod1 = Product.objects.create(
            product_name="prod1",
            barcode="0010",
            refund_value=3,
            material="A",
            height=100,
            diameter=60,
            weight=20,
            capacity=500,
            shape="F",
        )
        cls.prod2 = Product.objects.create(
            product_name="prod2",
            barcode="0002",
            refund_value=3,
            material="A",
            height=100,
            diameter=60,
            weight=20,
            capacity=500,
            shape="F",
        )

    def test_bulk_approval(self):
        self.user = self.login("EsaniAdmins")
        data = {"ids[]": [self.prod1.id, self.prod2.id]}
        response = self.client.post(reverse("pant:product_multiple_approve"), data)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.prod1 = Product.objects.get(id=self.prod1.id)
        self.prod2 = Product.objects.get(id=self.prod2.id)
        self.assertTrue(self.prod1.approved)
        self.assertTrue(self.prod2.approved)

    def test_bulk_approval_access_denied(self):
        self.user = self.login("BranchAdmins")
        data = {"ids[]": [self.prod1.id, self.prod2.id]}
        response = self.client.post(reverse("pant:product_multiple_approve"), data)

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)


class ProductListBulkDeleteTest(LoginMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user = self.login("EsaniAdmins")

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        kiosk = Kiosk.objects.create(cvr="123", city=cls._test_city)

        deposit_payout = DepositPayout.objects.create(
            source_type=DepositPayout.SOURCE_TYPE_CSV,
            source_identifier="already_processed.csv",
            from_date=datetime.date.today(),
            to_date=datetime.date.today(),
            item_count=0,
        )

        # Product that can be deleted
        cls.prod1 = Product.objects.create(
            product_name="prod1",
            barcode="0010",
            refund_value=3,
            material="A",
            height=100,
            diameter=60,
            weight=20,
            capacity=500,
            shape="F",
        )

        # Approved product - cannot be deleted
        cls.prod2 = Product.objects.create(
            product_name="prod2",
            barcode="0002",
            refund_value=3,
            material="A",
            height=100,
            diameter=60,
            weight=20,
            capacity=500,
            shape="F",
        )
        cls.prod2.approve()
        cls.prod2.save()

        # Product linked to DepositPayoutItem - cannot be deleted
        cls.prod3 = Product.objects.create(
            product_name="prod3",
            barcode="0003",
            refund_value=3,
            material="A",
            height=100,
            diameter=60,
            weight=20,
            capacity=500,
            shape="F",
        )

        DepositPayoutItem.objects.create(
            deposit_payout=deposit_payout,
            kiosk=kiosk,
            product=cls.prod3,
            location_id=1,
            rvm_serial=2,
            date=datetime.date.today(),
            barcode="11221122",
            count=200,
        )

        cls.delete_multiple_url = reverse("pant:product_multiple_delete")

    def test_bulk_delete(self):
        data = {"ids[]": [self.prod1.id]}

        self.assertQuerySetEqual(
            Product.objects.filter(id=self.prod1.id).values("state"),
            [{"state": ProductState.AWAITING_APPROVAL}],
        )

        response = self.client.post(self.delete_multiple_url, data)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertQuerySetEqual(
            Product.objects.filter(id=self.prod1.id).values("state"),
            [{"state": ProductState.DELETED}],
        )

    def test_bulk_delete_as_company_user(self):
        self.login("BranchAdmins")
        data = {"ids[]": [self.prod1.id]}
        response = self.client.post(self.delete_multiple_url, data)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_bulk_delete_approved_products(self):
        data = {"ids[]": [self.prod1.id, self.prod2.id]}
        response = self.client.post(self.delete_multiple_url, data)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_bulk_delete_payout_item_products(self):
        # self.assertTrue(Product.objects.filter(id=self.prod1.id).exists())
        # self.assertTrue(Product.objects.filter(id=self.prod3.id).exists())
        self.assertQuerySetEqual(
            Product.objects.filter(id__in=(self.prod1.id, self.prod3.id)).values(
                "id", "state"
            ),
            [
                {"id": self.prod1.id, "state": ProductState.AWAITING_APPROVAL},
                {"id": self.prod3.id, "state": ProductState.AWAITING_APPROVAL},
            ],
        )

        data = {"ids[]": [self.prod1.id, self.prod3.id]}
        response = self.client.post(self.delete_multiple_url, data)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertQuerySetEqual(
            Product.objects.filter(id__in=(self.prod1.id, self.prod3.id)).values(
                "id", "state"
            ),
            [
                {"id": self.prod1.id, "state": ProductState.DELETED},
                {"id": self.prod3.id, "state": ProductState.DELETED},
            ],
        )


class ProductListBulkRejectionTest(LoginMixin, ProductFixtureMixin):
    def _post_rejection(self, product: Product, **data):
        post_data = {"ids[]": [product.id]}
        post_data.update(**data)
        return self.client.post(
            reverse("pant:product_multiple_reject"),
            data=post_data,
        )

    def _assert_state(self, product: Product, state: ProductState):
        product = Product.objects.get(id=product.id)
        self.assertEqual(product.state, state)

    def test_allowed_states(self):
        self.login()

        # Test 1: a product awaiting approval can be rejected
        response = self._post_rejection(self.prod1)
        self._assert_state(self.prod1, ProductState.REJECTED)
        self.assertEqual(response.json()["updated"], 1)

        # Test 2: an approved product can be rejected
        response = self._post_rejection(self.prod2)
        self._assert_state(self.prod2, ProductState.REJECTED)
        self.assertEqual(response.json()["updated"], 1)

        # Test 3: a rejected product *cannot* be rejected
        response = self._post_rejection(self.prod3)
        self._assert_state(self.prod3, ProductState.REJECTED)
        self.assertEqual(response.json()["updated"], 0)

        # Test 4: a deleted product *cannot* be rejected
        response = self._post_rejection(self.prod4)
        self._assert_state(self.prod4, ProductState.DELETED)
        self.assertEqual(response.json()["updated"], 0)

    def test_rejection_message(self):
        self.login()
        rejection = "Produktet kan ikke pantes"
        self._post_rejection(self.prod1, rejection=rejection)
        self.assertQuerySetEqual(
            Product.objects.filter(id=self.prod1.id).values_list(
                "rejection", flat=True
            ),
            [rejection],
        )
