# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from typing import Literal

from django.db.models import Aggregate, Case, ExpressionWrapper, F, Q
from django.db.models.functions import Coalesce, Concat

from esani_pantportal.models import (
    CompanyListViewPreferences,
    ProductListViewPreferences,
    UserListViewPreferences,
)

# Django annotation classes. Add more as needed
ANNOTATION = Case | F | Q | Concat | Coalesce | ExpressionWrapper | Aggregate

BOOTSTRAP_BUTTON = Literal[
    "btn btn-sm btn-primary",
    "btn btn-sm btn-secondary",
    "btn btn-sm btn-success",
    "btn btn-sm btn-danger",
    "btn btn-sm btn-warning",
    "btn btn-sm btn-info",
    "btn btn-sm btn-light",
    "btn btn-sm btn-dark",
    "btn btn-sm btn-link",
]

PREFERENCES_CLASS = (
    type[ProductListViewPreferences]
    | type[UserListViewPreferences]
    | type[CompanyListViewPreferences]
)
