from django.test import TestCase

from esani_pantportal.models import Product

from .conftest import LoginMixin


class ProductViewGuiTest(LoginMixin, TestCase):
    def setUp(self) -> None:
        self.prod1 = Product.objects.create(
            product_name="prod1",
            barcode="00101122",
            refund_value=3,
            approved=True,
            material="A",
            height=100,
            diameter=60,
            weight=20,
            capacity=500,
            shape="F",
            danish="J",
        )
        self.prod2 = Product.objects.create(
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
        )

    def test_get_products(self):
        response = self.client.get("/api/produkter")
        output = response.json()

        self.assertEqual(output["count"], 1)
        self.assertEqual(output["items"][0]["product_name"], self.prod1.product_name)
        self.assertEqual(output["items"][0]["barcode"], self.prod1.barcode)
