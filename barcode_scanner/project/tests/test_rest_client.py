#!/usr/bin/env python

# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from unittest import mock

from django.test import TestCase

from barcode_scanner.rest import RestClient


# This method will be used by the mock to replace requests.get
def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    def mock_response(items, kwargs):
        params = kwargs.get("params", {})
        limit = params.get("limit", 100)
        offset = params.get("offset", 0)

        items_to_return = items[offset:][:limit]
        return {"count": len(items_to_return), "items": items_to_return}

    products = [
        {
            "product_name": "test_item1",
            "product_type": "coke",
            "tax_group": 2,
            "barcode": 100,
        },
        {
            "product_name": "test_item2",
            "product_type": "cola",
            "tax_group": 3,
            "barcode": 200,
        },
    ]

    if args[0] == "http://mocked_api/api/produkter":
        return MockResponse(mock_response(products, kwargs), 200)

    return MockResponse(None, 404)


class RestClientTestCase(TestCase):
    def setUp(self):
        self.rest_client = RestClient()
        self.rest_client.rest_domain = "http://mocked_api/"

    @mock.patch("requests.get", side_effect=mocked_requests_get)
    def test_get_response(self, mock_get):
        response = self.rest_client.get("api/produkter")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.json()["count"], 2)
        self.assertEquals(len(response.json()["items"]), 2)

        response = self.rest_client.get(
            "api/produkter",
            params={"limit": 1, "offset": 0},
        )
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.json()["count"], 1)
        self.assertEquals(response.json()["items"][0]["product_name"], "test_item1")

        response = self.rest_client.get(
            "api/produkter",
            params={"limit": 1, "offset": 1},
        )
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.json()["count"], 1)
        self.assertEquals(response.json()["items"][0]["product_name"], "test_item2")

        response = self.rest_client.get(
            "api/produkter",
            params={"limit": 1, "offset": 2},
        )
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.json()["count"], 0)
        self.assertEquals(len(response.json()["items"]), 0)

    @mock.patch("requests.get", side_effect=mocked_requests_get)
    def test_get_response_404(self, mock_get):
        response = self.rest_client.get("api/non_existing_route")
        self.assertEquals(response.status_code, 404)

    @mock.patch("requests.get", side_effect=mocked_requests_get)
    def test_get_all_items(self, mock_get):
        # Set the limit to 1, we have 2 items in the test data so we expect 3
        # requests. One for each item and one which is empty.
        self.rest_client.page_limit = 1
        self.rest_client.get_all_items("api/produkter")
        self.assertEquals(mock_get.call_count, 3)

        # When the limit is 100 we get all items in a single request.
        mock_get.reset_mock()
        self.rest_client.page_limit = 100
        self.rest_client.get_all_items("api/produkter")
        self.assertEquals(mock_get.call_count, 1)

    @mock.patch("requests.get", side_effect=mocked_requests_get)
    def test_get_all_products(self, mock_get):
        products = self.rest_client.all_products
        self.assertIn(100, products)
        self.assertIn(200, products)

        self.assertEquals(products[100]["product_name"], "test_item1")
        self.assertEquals(products[200]["product_name"], "test_item2")
