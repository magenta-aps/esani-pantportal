#!/usr/bin/env python

# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0


from unittest import mock

from django.test import TestCase


class RestClientMock:
    @property
    def all_products(self):
        return {
            100: {
                "product_name": "test_item1",
                "product_type": "coke",
                "tax_group": 2,
                "barcode": 100,
                "refund_value": 200,
            },
            200: {
                "product_name": "test_item2",
                "product_type": "cola",
                "tax_group": 3,
                "barcode": 200,
                "refund_value": 200,
            },
        }


class BarcodeScannerTestCase(TestCase):
    @mock.patch("barcode_scanner.views.RestClient", RestClientMock)
    def test_call_view_load(self):
        response = self.client.get("/scan_barcode")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "barcode_scanner/scan_barcode.html")

        barcodes = response.context["barcodes"]
        self.assertIn(100, barcodes)
        self.assertIn(200, barcodes)
        self.assertEquals(barcodes[100]["product_name"], "test_item1")
        self.assertEquals(barcodes[200]["product_name"], "test_item2")

        self.assertEquals(barcodes[100]["refund_value"], 200)
        self.assertEquals(barcodes[200]["refund_value"], 200)
