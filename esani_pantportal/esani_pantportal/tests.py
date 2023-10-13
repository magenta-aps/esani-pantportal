from django.core.exceptions import ValidationError
from django.test import TestCase

from esani_pantportal.models import validate_barcode_length, validate_digit


class ValidationTest(TestCase):
    __test__ = True

    invalid_barcode = "1234"

    def test_barcode_length(self):
        self.assertRaises(
            ValidationError,
            validate_barcode_length,
            self.invalid_barcode,
        )

    def test_digit(self):
        self.assertRaises(
            ValidationError,
            validate_digit,
            self.invalid_barcode,
        )
