# SPDX-FileCopyrightText: 2024 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
from django.core.exceptions import ValidationError
from unittest_parametrize import ParametrizedTestCase, parametrize

from esani_pantportal.forms import (
    EMPTY_CHOICE,
    ProductFilterForm,
    ProductUpdateForm,
    QRBagFilterForm,
)
from esani_pantportal.models import ProductState, User
from esani_pantportal.tests.test_qrbaglist import BaseQRBagTest

from .conftest import LoginMixin
from .helpers import ProductFixtureMixin


class TestProductFilterForm(ParametrizedTestCase, LoginMixin, ProductFixtureMixin):
    @parametrize(
        "group,expected_fmt",
        [
            ("EsaniAdmins", "%(label)s (1)"),
            ("BranchUsers", "%(label)s"),
        ],
    )
    def test_state_choices(self, group, expected_fmt):
        """The choices for `state` should exclude "deleted"
        The choices should contain a product count for each distinct state, but
        only if the user is an ESANI admin. Otherwise, only the state names
        should be visible.
        """
        user = self.login(group)
        expected_choices = [EMPTY_CHOICE] + [
            (state, expected_fmt % dict(label=state.label))
            for state in (
                ProductState.AWAITING_APPROVAL,
                ProductState.APPROVED,
                ProductState.REJECTED,
            )
        ]
        form = ProductFilterForm(user=user)
        self.assertSetEqual(
            set(form.fields["state"].choices),
            set(expected_choices),
        )


class TestProductUpdateForm(ProductFixtureMixin):
    def test_rejection_message_validation(self):
        instance = ProductUpdateForm(
            data={"action": "reject", "rejection_message": None}
        )
        instance.is_valid()  # Trigger validation
        with self.assertRaises(ValidationError):
            instance.clean()


class TestQRBagFilterForm(ParametrizedTestCase, BaseQRBagTest):
    @parametrize(
        "username,expected_choices",
        [
            (
                "esani_admin",
                [
                    ("Oprettet", "Oprettet (3)"),
                    ("Under transport", "Under transport (1)"),
                ],
            ),
            (
                "company_admin",
                [
                    ("Oprettet", "Oprettet (2)"),
                    ("Under transport", "Under transport (1)"),
                ],
            ),
        ],
    )
    def test_populates_status_choices(self, username, expected_choices):
        user = User.objects.get(username=username)
        form = QRBagFilterForm(user=user, cities=[])
        expected_choices = [("", "-")] + expected_choices
        self.assertSetEqual(set(form.fields["status"].choices), set(expected_choices))
