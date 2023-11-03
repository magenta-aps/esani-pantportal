from bs4 import BeautifulSoup
from django.forms import model_to_dict
from django.test import TestCase
from django.urls import reverse

from esani_pantportal.models import TAX_GROUP_CHOICES, Product

tax_group_dict = dict(TAX_GROUP_CHOICES)


class ProductViewGuiTest(TestCase):
    def setUp(self) -> None:
        self.prod1 = Product.objects.create(
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
            tax_group=13,
            danish="J",
        )
        self.prod2 = Product.objects.create(
            product_name="prod2",
            barcode="00020002",
            refund_value=3,
            approved=True,
            material="A",
            height=100,
            diameter=60,
            weight=20,
            capacity=500,
            shape="F",
            tax_group=13,
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

    def test_render(self):
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
                    "Stregkode": "00101122",
                    "Pantværdi": "3 øre",
                    "Godkendt": "nej",
                    "Afgiftsgruppe": f"{tax_group_dict[13]} (13)",
                    "Dansk Pant": "Ja",
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

    def test_approve(self):
        response = self.client.get(
            reverse("pant:product_view", kwargs={"pk": self.prod1.pk})
            + "?login_bypass=1"
        )

        form = response.context_data["form"]

        form_data = self.make_form_data(form)
        form_data["approved"] = True
        self.assertFalse(self.prod1.approved)
        response = self.client.post(
            reverse("pant:product_view", kwargs={"pk": self.prod1.pk}),
            form_data,
        )

        self.assertEquals(response.status_code, 302)
        self.prod1.refresh_from_db()
        self.assertTrue(self.prod1.approved)
        self.assertRedirects(response, reverse("pant:product_list"))

        response = self.client.post(
            reverse("pant:product_view", kwargs={"pk": self.prod1.pk})
            + "?back=/produkt/%3Fproduct_name%3Dprod1",
            form_data,
        )

        self.assertRedirects(
            response,
            reverse("pant:product_list") + "?product_name=prod1",
        )

    def test_edit(self):
        response = self.client.get(
            reverse("pant:product_view", kwargs={"pk": self.prod1.pk})
            + "?login_bypass=1"
        )

        form = response.context_data["form"]

        form_data = self.make_form_data(form)
        form_data["weight"] = 1223

        response = self.client.post(
            reverse("pant:product_view", kwargs={"pk": self.prod1.pk}),
            form_data,
        )

        self.assertEquals(response.status_code, 302)
        self.prod1.refresh_from_db()
        self.assertEqual(self.prod1.weight, 1223)
        self.assertRedirects(
            response, reverse("pant:product_view", kwargs={"pk": self.prod1.pk})
        )

    def test_others_fail(self):
        response = self.client.get(
            reverse("pant:product_view", kwargs={"pk": self.prod1.pk})
            + "?login_bypass=1"
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
