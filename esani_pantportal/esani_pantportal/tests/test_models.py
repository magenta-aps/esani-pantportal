# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import TestCase

from esani_pantportal.models import (  # isort: skip
    QRCodeGenerator,
    validate_barcode_length,
    validate_digit,
)


class ValidationTest(TestCase):
    def test_barcode_length(self):
        self.assertRaises(
            ValidationError,
            validate_barcode_length,
            "1234",
        )

    def test_digit(self):
        self.assertRaises(
            ValidationError,
            validate_digit,
            "abc",
        )


class QRCodeGeneratorTest(TestCase):
    def setUp(self):
        QRCodeGenerator.objects.create(name="Små sække", prefix=0)
        QRCodeGenerator.objects.create(name="Store sække", prefix=1)

    def test_generate_qr(self):
        små_generator = QRCodeGenerator.objects.get(prefix=0)
        store_generator = QRCodeGenerator.objects.get(prefix=1)
        id_length = settings.QR_ID_LENGTH + 1
        små_qrs_1 = små_generator.generate_qr_codes(10)
        små_qrs_2 = små_generator.generate_qr_codes(5, salt="salt")  # noqa

        store_generator.generate_qr_codes(5)

        sm_qr_first = små_qrs_1[0]
        sm_qr_last = små_qrs_2[-1]

        self.assertEqual(len(små_generator.check_qr_code(sm_qr_first)), id_length)
        self.assertEqual(len(små_generator.check_qr_code(sm_qr_last)), id_length)
        self.assertEqual(store_generator.check_qr_code(sm_qr_first), None)

        sm_qr_wrong = sm_qr_first[:-1] + "x"  # 'x' can't be part of a hex digest
        self.assertEqual(store_generator.check_qr_code(sm_qr_wrong), None)
