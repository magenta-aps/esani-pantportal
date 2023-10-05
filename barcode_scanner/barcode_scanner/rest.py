#!/usr/bin/env python

# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
import requests
from django.conf import settings


class RestClient:
    def __init__(self):
        self.rest_domain = settings.REST_DOMAIN
        self.page_limit = 100

    def get(self, route, *args, **kwargs):
        return requests.get(self.rest_domain + route, *args, **kwargs)

    def get_all_items(self, route):
        limit = self.page_limit
        offset = 0
        items = []

        response = self.get(route, params={"limit": limit, "offset": offset})
        data = response.json()
        items.extend(data["items"])
        while len(data["items"]) == limit:
            offset += limit
            response = self.get(route, params={"limit": limit, "offset": offset})
            data = response.json()
            items.extend(data["items"])

        return items

    @property
    def all_products(self):
        return {
            product["barcode"]: product
            for product in self.get_all_items("api/produkter")
        }
