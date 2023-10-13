# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from django.urls import path
from django_mitid_auth.saml.views import AccessDeniedView

from esani_pantportal.views import LoginRequiredView

urlpatterns = [
    path("", LoginRequiredView.as_view()),
    path(
        "error/login-timeout/",
        AccessDeniedView.as_view(
            template_name="esani_pantportal/error/login_timeout.html"
        ),
        name="login-timeout",
    ),
    path(
        "error/login-repeat/",
        AccessDeniedView.as_view(
            template_name="esani_pantportal/error/login_repeat.html"
        ),
        name="login-repeat",
    ),
]
