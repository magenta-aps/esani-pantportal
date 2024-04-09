# SPDX-FileCopyrightText: 2024 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
from esani_pantportal.forms import EMPTY_CHOICE, ProductFilterForm
from esani_pantportal.models import ProductState

from .conftest import LoginMixin
from .helpers import ProductFixtureMixin


class TestProductFilterForm(LoginMixin, ProductFixtureMixin):
    def test_state_choices(self):
        """The choices for `state` should exclude "deleted" and contain a product count
        for each distinct state.
        """
        expected_choices = [EMPTY_CHOICE] + [
            (state, f"{state} (1)")
            for state in (
                ProductState.AWAITING_APPROVAL,
                ProductState.APPROVED,
                ProductState.REJECTED,
            )
        ]
        form = ProductFilterForm()
        self.assertSetEqual(
            set(form.fields["state"].choices),
            set(expected_choices),
        )
