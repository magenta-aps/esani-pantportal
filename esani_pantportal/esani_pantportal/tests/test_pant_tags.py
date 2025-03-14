# SPDX-FileCopyrightText: 2024 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
from django.utils.translation import gettext
from unittest_parametrize import ParametrizedTestCase, parametrize

from esani_pantportal.models import Company
from esani_pantportal.templatetags.pant_tags import get_display_name

from .helpers import ProductFixtureMixin


class TestGetDisplayName(ParametrizedTestCase, ProductFixtureMixin):
    @parametrize(
        "input_value,expected_output",
        [
            (True, gettext("Ja")),
            (False, gettext("Nej")),
        ],
    )
    def test_get_display_name_for_boolean_field(self, input_value, expected_output):
        obj = Company(invoice_company_branch=input_value)
        result = get_display_name(obj, "invoice_company_branch")
        self.assertEqual(result, expected_output)

    def test_get_display_name_for_invalid_annotation(self):
        """Passing an invalid annotation name does not cause an exception"""
        obj = Company()  # we just need any Django model instance
        result = get_display_name(obj, "invalid_annotation_name")
        self.assertEqual(result, gettext("Udefineret"))

    def test_get_display_name_for_valid_annotation(self):
        """Passing a valid annotation should return its value"""
        result = get_display_name(self.prod1, "approved")
        self.assertEqual(result, gettext("Nej"))
