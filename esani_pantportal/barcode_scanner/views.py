#!/usr/bin/env python
# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from django.forms import model_to_dict
from django.views.generic import TemplateView

from esani_pantportal.models import Product


class BarcodeCheckView(TemplateView):
    template_name = "barcode_scanner/scan_barcode.html"

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["barcodes"] = {
            product.barcode: model_to_dict(product) for product in Product.objects.all()
        }
        return context_data
