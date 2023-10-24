# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
from django.core.exceptions import ValidationError
from django.test import TestCase

from esani_pantportal.models import validate_barcode_length, validate_digit


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
