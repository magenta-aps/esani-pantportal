from bs4 import BeautifulSoup
from django.forms import model_to_dict
from django.test import TestCase
from django.urls import reverse

from esani_pantportal.models import Product


class ProductViewGuiTest(TestCase):
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
    def get_html_data(html):
        soup = BeautifulSoup(html, "html.parser")
        output = []
        for table in soup.find_all("table"):
            output.append(
                {
                    row.find("th").text: row.find("td").text
                    for row in table.tbody.find_all("tr")
                }
            )
        return output

    def test_render1(self):
        response = self.client.get(
            reverse("pant:product_view", kwargs={"pk": self.prod1.pk})
            + "?login_bypass=1"
        )
        data = self.get_html_data(response.content)
        self.assertEquals(
            data,
            [
                {
                    "Produktnavn": "prod1",
                    "Stregkode": "0010",
                    "Pantværdi": "3 øre",
                    "Godkendt": "nej",
                },
                {
                    "Materialetype": "Aluminium",
                    "Højde": "100 mm",
                    "Diameter": "60 mm",
                    "Vægt": "20 g",
                    "Volumenkapacitet": "500 ml",
                    "Form": "Flaske",
                },
            ],
        )

    def test_render2(self):
        response = self.client.get(
            reverse("pant:product_view", kwargs={"pk": self.prod1.pk})
            + "?login_bypass=1"
        )
        data = self.get_html_data(response.content)
        self.assertEquals(
            data,
            [
                {
                    "Produktnavn": "prod1",
                    "Stregkode": "0010",
                    "Pantværdi": "3 øre",
                    "Godkendt": "nej",
                },
                {
                    "Materialetype": "Aluminium",
                    "Højde": "100 mm",
                    "Diameter": "60 mm",
                    "Vægt": "20 g",
                    "Volumenkapacitet": "500 ml",
                    "Form": "Flaske",
                },
            ],
        )

    def test_approve(self):
        self.client.get(
            reverse("pant:product_view", kwargs={"pk": self.prod1.pk})
            + "?login_bypass=1"
        )
        self.assertFalse(self.prod1.approved)
        response = self.client.post(
            reverse("pant:product_view", kwargs={"pk": self.prod1.pk}),
            {"approved": "1"},
        )
        self.assertEquals(response.status_code, 302)
        self.prod1.refresh_from_db()
        self.assertTrue(self.prod1.approved)

    def test_others_fail(self):
        self.client.get(
            reverse("pant:product_view", kwargs={"pk": self.prod1.pk})
            + "?login_bypass=1"
        )
        original = model_to_dict(self.prod1)
        for field in original.keys():
            if field == "approved":
                continue
            self.client.post(
                reverse("pant:product_view", kwargs={"pk": self.prod1.pk}), {field: "1"}
            )
            self.prod1.refresh_from_db()
            self.assertDictEqual(model_to_dict(self.prod1), original)
