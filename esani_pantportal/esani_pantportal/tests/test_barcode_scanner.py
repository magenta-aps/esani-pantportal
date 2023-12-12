#!/usr/bin/env python

# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
from django.test import TestCase

from esani_pantportal.models import Product


class BarcodeScannerTestCase(TestCase):
    def test_call_view_load(self):
        Product.objects.create(
            product_name="test_item1",
            barcode=100,
            refund_value=200,
            material="P",
            height=200,
            diameter=100,
            weight=50,
            capacity=200,
            shape="F",
        )

        Product.objects.create(
            product_name="test_item2",
            barcode=200,
            refund_value=200,
            material="P",
            height=200,
            diameter=100,
            weight=50,
            capacity=200,
            shape="F",
        )

        response = self.client.get("/barcode/scan/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "barcode_scanner/scan_barcode.html")

        barcodes = response.context["barcodes"]
        self.assertIn("100", barcodes)
        self.assertIn("200", barcodes)
        self.assertEquals(barcodes["100"]["product_name"], "test_item1")
        self.assertEquals(barcodes["200"]["product_name"], "test_item2")

        self.assertEquals(barcodes["100"]["refund_value"], 200)
        self.assertEquals(barcodes["200"]["refund_value"], 200)
