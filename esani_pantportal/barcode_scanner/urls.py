#!/usr/bin/env python

# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from barcode_scanner.views import BarcodeCheckView
from django.urls import path

app_name = "barcode_scanner"

urlpatterns = [
    path("scan/", BarcodeCheckView.as_view(), name="scan"),
]
