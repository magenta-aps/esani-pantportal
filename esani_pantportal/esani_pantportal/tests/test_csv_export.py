import datetime
import os
from io import StringIO
from unittest.mock import MagicMock, patch

import pandas as pd
from django.core.management import call_command
from django.test import TestCase

from esani_pantportal.models import Product

datetime_mock = MagicMock()
datetime_mock.datetime.now.side_effect = [
    datetime.datetime(2021, 1, 1),
    datetime.datetime(2021, 1, 2),
    datetime.datetime(2021, 1, 3),
]
datetime_mock.datetime.strptime = datetime.datetime.strptime


class ExportProductsToCSVTests(TestCase):
    def call_command(self, *args, **kwargs):
        out = StringIO()
        call_command("export_approved_products_to_csv", *args, **kwargs, stdout=out)
        return out.getvalue().strip()

    def setUp(self) -> None:
        self.prod1 = Product.objects.create(
            product_name="prod1",
            barcode="0010",
            refund_value=3,
            approved=True,
            material="A",
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
            material="A",
            height=100,
            diameter=60,
            weight=20,
            capacity=500,
            shape="F",
        )

        self.prod3 = Product.objects.create(
            product_name="prod3",
            barcode="0003",
            refund_value=3,
            approved=False,
            material="A",
            height=100,
            diameter=60,
            weight=20,
            capacity=500,
            shape="F",
        )

        for file in os.listdir("."):
            if file.endswith(".csv"):
                os.remove(file)

    def test_csv_export(self):
        filename = self.call_command(".")
        self.assertIn(filename, os.listdir("."))

        df = pd.read_csv(filename, sep=";", dtype={"Barcode": str})
        self.assertEqual(len(df), 2)  # There are two approved products
        self.assertEqual(list(df.loc[:, "Barcode"]), ["0010", "0002"])

    @patch(
        "esani_pantportal.management.commands."
        "export_approved_products_to_csv.datetime",
        datetime_mock,
    )
    def test_csv_export_cleanup(self):
        # Export three csv files
        filenames = []
        for i in range(3):
            filename = self.call_command(".", max_number_of_files=2)
            filenames.append(filename)

        # Validate that the first one is cleaned up
        self.assertNotIn(filenames[0], os.listdir("."))
        self.assertIn(filenames[1], os.listdir("."))
        self.assertIn(filenames[2], os.listdir("."))
