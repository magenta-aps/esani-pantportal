#!/usr/bin/env python

# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from django.urls import path

from barcode_scanner.views import BarcodeCheckView

urlpatterns = [
    path("scan_barcode", BarcodeCheckView.as_view(), name="scan_barcode"),
]
