import json

from bs4 import BeautifulSoup
from django.http import HttpRequest
from django.test import TestCase
from django.urls import reverse

from esani_pantportal.forms import ProductFilterForm
from esani_pantportal.models import Product
from esani_pantportal.views import ProductSearchView


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


class ProductListGetQuerysetTest(TestCase):
    def setUp(self) -> None:
        self.prod1 = Product.objects.create(
            product_name="prod1",
            barcode="0010",
            refund_value=3,
            approved=False,
            material_type="A",
            height=100,
            diameter=60,
            weight=20,
            capacity=500,
            shape="F",
        )
        self.prod2 = Product.objects.create(
            product_name="prod2",
            barcode="0002",
            refund_value=3,
            approved=True,
            material_type="A",
            height=100,
            diameter=60,
            weight=20,
            capacity=500,
            shape="F",
        )

    def test_get_queryset_normal(self):
        view = ProductSearchView()
        view.paginate_by = 20
        view.form = ProductFilterForm()
        view.form.cleaned_data = {"offset": 0, "limit": 10}
        qs = view.get_queryset()
        self.assertIn(self.prod1, qs)
        self.assertIn(self.prod2, qs)

    def test_get_queryset_filter_name(self):
        view = ProductSearchView()
        view.form = ProductFilterForm()
        view.form.cleaned_data = {"offset": 0, "limit": 10, "product_name": "PROD1"}
        qs = view.get_queryset()
        self.assertIn(self.prod1, qs)
        self.assertNotIn(self.prod2, qs)

        view = ProductSearchView()
        view.form = ProductFilterForm()
        view.form.cleaned_data = {"offset": 0, "limit": 10, "product_name": "PROD2"}
        qs = view.get_queryset()
        self.assertNotIn(self.prod1, qs)
        self.assertIn(self.prod2, qs)

        view = ProductSearchView()
        view.form = ProductFilterForm()
        view.form.cleaned_data = {"offset": 0, "limit": 10, "product_name": "1"}
        qs = view.get_queryset()
        self.assertIn(self.prod1, qs)
        self.assertNotIn(self.prod2, qs)

        view = ProductSearchView()
        view.form = ProductFilterForm()
        view.form.cleaned_data = {"offset": 0, "limit": 10, "product_name": "d2"}
        qs = view.get_queryset()
        self.assertNotIn(self.prod1, qs)
        self.assertIn(self.prod2, qs)

        view = ProductSearchView()
        view.form = ProductFilterForm()
        view.form.cleaned_data = {"offset": 0, "limit": 10, "product_name": "foobar"}
        qs = view.get_queryset()
        self.assertNotIn(self.prod1, qs)
        self.assertNotIn(self.prod2, qs)

    def test_get_queryset_filter_barcode(self):
        view = ProductSearchView()
        view.paginate_by = 20
        view.form = ProductFilterForm()
        view.form.cleaned_data = {"offset": 0, "limit": 10, "barcode": "0010"}
        qs = view.get_queryset()
        self.assertIn(self.prod1, qs)
        self.assertNotIn(self.prod2, qs)

        view = ProductSearchView()
        view.form = ProductFilterForm()
        view.form.cleaned_data = {"offset": 0, "limit": 10, "barcode": "0002"}
        qs = view.get_queryset()
        self.assertNotIn(self.prod1, qs)
        self.assertIn(self.prod2, qs)

        view = ProductSearchView()
        view.form = ProductFilterForm()
        view.form.cleaned_data = {"offset": 0, "limit": 10, "barcode": "1"}
        qs = view.get_queryset()
        self.assertIn(self.prod1, qs)
        self.assertNotIn(self.prod2, qs)

        view = ProductSearchView()
        view.form = ProductFilterForm()
        view.form.cleaned_data = {"offset": 0, "limit": 10, "barcode": "02"}
        qs = view.get_queryset()
        self.assertNotIn(self.prod1, qs)
        self.assertIn(self.prod2, qs)

        view = ProductSearchView()
        view.form = ProductFilterForm()
        view.form.cleaned_data = {"offset": 0, "limit": 10, "barcode": "3"}
        qs = view.get_queryset()
        self.assertNotIn(self.prod1, qs)
        self.assertNotIn(self.prod2, qs)

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


class ProductListFormValidTest(TestCase):
    def setUp(self) -> None:
        self.prod1 = Product.objects.create(
            product_name="prod1",
            barcode="0010",
            refund_value=3,
            approved=False,
            material_type="A",
            height=100,
            diameter=60,
            weight=20,
            capacity=500,
            shape="F",
        )
        self.prod2 = Product.objects.create(
            product_name="prod2",
            barcode="0002",
            refund_value=3,
            approved=True,
            material_type="A",
            height=100,
            diameter=60,
            weight=20,
            capacity=500,
            shape="F",
        )

    def test_form_valid(self):
        self.maxDiff = None
        view = ProductSearchView()
        view.paginate_by = 20
        view.form = ProductFilterForm()
        view.form.cleaned_data = {"offset": 0, "limit": 10, "json": "1"}
        view.request = HttpRequest()
        view.request.method = "GET"
        view.object_list = view.get_queryset()
        view.kwargs = {}
        response = view.form_valid(view.form)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(
            json.loads(response.content),
            {
                "items": [
                    {
                        "actions": '<a href="/produkt/1?back=" class="btn btn-sm '
                        'btn-primary">Vis</a>\n',
                        "approved": "Nej",
                        "barcode": "0010",
                        "capacity": 500,
                        "diameter": 60,
                        "height": 100,
                        "id": 1,
                        "material_type": "A",
                        "product_name": "prod1",
                        "refund_value": 3,
                        "shape": "F",
                        "weight": 20,
                    },
                    {
                        "actions": '<a href="/produkt/2?back=" class="btn btn-sm '
                        'btn-primary">Vis</a>\n',
                        "approved": "Ja",
                        "barcode": "0002",
                        "capacity": 500,
                        "diameter": 60,
                        "height": 100,
                        "id": 2,
                        "material_type": "A",
                        "product_name": "prod2",
                        "refund_value": 3,
                        "shape": "F",
                        "weight": 20,
                    },
                ],
                "total": 2,
            },
        )

        view = ProductSearchView()
        view.paginate_by = 20
        view.form = ProductFilterForm()
        view.form.cleaned_data = {
            "offset": 0,
            "limit": 10,
            "json": "1",
            "product_name": "1",
        }
        view.request = HttpRequest()
        view.request.method = "GET"
        view.object_list = view.get_queryset()
        view.kwargs = {}
        response = view.form_valid(view.form)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(
            json.loads(response.content),
            {
                "items": [
                    {
                        "actions": '<a href="/produkt/1?back=" class="btn btn-sm '
                        'btn-primary">Vis</a>\n',
                        "approved": "Nej",
                        "barcode": "0010",
                        "capacity": 500,
                        "diameter": 60,
                        "height": 100,
                        "id": 1,
                        "material_type": "A",
                        "product_name": "prod1",
                        "refund_value": 3,
                        "shape": "F",
                        "weight": 20,
                    }
                ],
                "total": 1,
            },
        )


class ProductListGuiTest(TestCase):
    def setUp(self) -> None:
        self.prod1 = Product.objects.create(
            product_name="prod1",
            barcode="0010",
            refund_value=3,
            approved=False,
            material_type="A",
            height=100,
            diameter=60,
            weight=20,
            capacity=500,
            shape="F",
        )
        self.prod2 = Product.objects.create(
            product_name="prod2",
            barcode="0002",
            refund_value=3,
            approved=True,
            material_type="A",
            height=100,
            diameter=60,
            weight=20,
            capacity=500,
            shape="F",
        )

    @staticmethod
    def get_html_items(html):
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table")
        headers = [cell.text for cell in table.thead.tr.find_all("th")]
        output = []
        for row in table.tbody.find_all("tr"):
            rowdata = [cell.text.strip() for cell in row.find_all("td")]
            output.append(dict(zip(headers, rowdata)))
        return output

    @staticmethod
    def get_json_items(text):
        data = json.loads(text)
        return [
            {
                "Produktnavn": item["product_name"],
                "Stregkode": item["barcode"],
                "Godkendt": item["approved"],
                "Handlinger": "Vis",
            }
            for item in data["items"]
        ]

    def test_render(self):
        expected = [
            {
                "Produktnavn": "prod1",
                "Stregkode": "0010",
                "Godkendt": "Nej",
                "Handlinger": "Vis",
            },
            {
                "Produktnavn": "prod2",
                "Stregkode": "0002",
                "Godkendt": "Ja",
                "Handlinger": "Vis",
            },
        ]
        response = self.client.get(reverse("pant:product_list") + "?login_bypass=1")
        data = self.get_html_items(response.content)
        self.assertEquals(data, expected)
        response = self.client.get(
            reverse("pant:product_list") + "?login_bypass=1&json=1"
        )
        data = self.get_json_items(response.content)
        self.assertEquals(data, expected)

    def test_render_paginated(self):
        expected = [
            {
                "Produktnavn": "prod2",
                "Stregkode": "0002",
                "Godkendt": "Ja",
                "Handlinger": "Vis",
            },
        ]
        response = self.client.get(
            reverse("pant:product_list") + "?login_bypass=1&offset=1"
        )
        data = self.get_html_items(response.content)
        self.assertEquals(data, expected)
        response = self.client.get(
            reverse("pant:product_list") + "?login_bypass=1&json=1&offset=1"
        )
        data = self.get_json_items(response.content)
        self.assertEquals(data, expected)

    def test_filter_name(self):
        expected = [
            {
                "Produktnavn": "prod1",
                "Stregkode": "0010",
                "Godkendt": "Nej",
                "Handlinger": "Vis",
            },
        ]
        response = self.client.get(
            reverse("pant:product_list") + "?login_bypass=1&product_name=p+1"
        )
        data = self.get_html_items(response.content)
        self.assertEquals(data, expected)
        response = self.client.get(
            reverse("pant:product_list") + "?login_bypass=1&json=1&product_name=p+1"
        )
        data = self.get_json_items(response.content)
        self.assertEquals(data, expected)

    def test_filter_barcode(self):
        expected = [
            {
                "Produktnavn": "prod2",
                "Stregkode": "0002",
                "Godkendt": "Ja",
                "Handlinger": "Vis",
            }
        ]
        response = self.client.get(
            reverse("pant:product_list") + "?login_bypass=1&barcode=2"
        )
        data = self.get_html_items(response.content)
        self.assertEquals(data, expected)
        response = self.client.get(
            reverse("pant:product_list") + "?login_bypass=1&json=1&barcode=2"
        )
        data = self.get_json_items(response.content)
        self.assertEquals(data, expected)

    def test_filter_approved(self):
        expected = [
            {
                "Produktnavn": "prod2",
                "Stregkode": "0002",
                "Godkendt": "Ja",
                "Handlinger": "Vis",
            }
        ]
        response = self.client.get(
            reverse("pant:product_list") + "?login_bypass=1&approved=true"
        )
        data = self.get_html_items(response.content)
        self.assertEquals(data, expected)
        response = self.client.get(
            reverse("pant:product_list") + "?login_bypass=1&json=1&approved=true"
        )
        data = self.get_json_items(response.content)
        self.assertEquals(data, expected)

    def test_filter_approved_name(self):
        expected = []
        response = self.client.get(
            reverse("pant:product_list")
            + "?login_bypass=1&approved=true&product_name=1"
        )
        data = self.get_html_items(response.content)
        self.assertEquals(data, expected)
        response = self.client.get(
            reverse("pant:product_list")
            + "?login_bypass=1&json=1&approved=true&product_name=1"
        )
        data = self.get_json_items(response.content)
        self.assertEquals(data, expected)
