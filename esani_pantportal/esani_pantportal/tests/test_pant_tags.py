# SPDX-FileCopyrightText: 2024 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
from django.test import TestCase
from django.utils.translation import gettext
from unittest_parametrize import ParametrizedTestCase, parametrize

from esani_pantportal.models import Company, EsaniUser
from esani_pantportal.templatetags.pant_tags import (
    get_display_name,
    has_fasttrack_enabled,
)

from .conftest import LoginMixin
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


class TestHasFasttrackEnabled(LoginMixin, TestCase):
    def test_when_esani_user_exists(self):
        # Arrange: use the `login` method just to create a suitable ESANI user
        esani_user = self.login("EsaniAdmins")
        # Arrange: alter `fasttrack_enabled` from its default value of `False`
        esani_user.fasttrack_enabled = True
        esani_user.save(update_fields=["fasttrack_enabled"])
        # Act
        self.assertTrue(has_fasttrack_enabled(esani_user))

    def test_when_esani_user_does_not_exist(self):
        # Arrange: use non-existent ESANI user
        esani_user = EsaniUser()
        # Act
        self.assertFalse(has_fasttrack_enabled(esani_user))

    def test_when_user_is_wrong_type(self):
        # Arrange: use the `login` method to create a user of the wrong type
        branch_user = self.login("BranchUsers")
        # Act
        self.assertFalse(has_fasttrack_enabled(branch_user))
