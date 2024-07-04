# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from django.urls import path
from metrics.views import health_check_database, health_check_storage

urlpatterns = [
    path("health/storage", health_check_storage, name="health_check_storage"),
    path("health/database", health_check_database, name="health_check_database"),
]
