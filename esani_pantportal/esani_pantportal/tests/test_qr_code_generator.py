# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

import os

import pandas as pd
from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse

from esani_pantportal.models import QRCodeGenerator

from .conftest import LoginMixin


class QRCodeGeneratorTests(LoginMixin, TestCase):
    @override_settings(QR_OUTPUT_DIR=".")
    def test_generate_qr_code_view(self):
        self.login()
        url = reverse("pant:qr_generate")

        for bag_type in settings.QR_GENERATOR_SERIES.keys():
            data = {"number_of_codes": 2, "bag_type": bag_type}
            response = self.client.post(url, data=data)
            df = pd.read_excel(response.content)
            self.assertEqual(len(df), 2)

            # Generate more qrs; the ID should increment with respect to the last batch
            response = self.client.post(url, data=data)
            df = pd.read_excel(response.content)
            self.assertGreater(df.Id.astype(float).max(), 1)

            qr_generator = QRCodeGenerator.objects.get(
                **settings.QR_GENERATOR_SERIES[bag_type]
            )

            for qr in df.loc[:, "QR-kode"]:
                self.assertNotEqual(qr_generator.check_qr_code(qr), None)

        for file in os.listdir(settings.QR_OUTPUT_DIR):
            if file.endswith(".csv") and "codes" in file:
                os.remove(file)
