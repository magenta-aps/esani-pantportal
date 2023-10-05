# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from django.urls import path

from esani_pantportal.views import PantportalLoginView

# from project.api import api

urlpatterns = [
    path("", PantportalLoginView.as_view(), name="login"),
    #    path("api/", api.urls),
]
