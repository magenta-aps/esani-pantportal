#!/usr/bin/env python

# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from barcode_scanner.rest import RestClient
from django.views.generic import TemplateView


class BarcodeCheckView(TemplateView):
    template_name = "barcode_scanner/scan_barcode.html"

    def __init__(self, *args, **kwargs):
        self.rest_client = RestClient()
        super().__init__(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["barcodes"] = self.rest_client.all_products

        # TODO: Remove me when "refund_value" comes from API
        for product in context_data["barcodes"].values():
            product["refund_value"] = 2

        return context_data
