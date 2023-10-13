# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from django.urls import path
from django.views.generic import TemplateView
from django_mitid_auth.saml.views import AccessDeniedView

from esani_pantportal.views import (  # isort: skip
    LoginRequiredView,
    ProductRegisterView,
)


urlpatterns = [
    path("", LoginRequiredView.as_view()),
    path("nyt_produkt/", ProductRegisterView.as_view(), name="product_register"),
    path(
        "nyt_produkt/success",
        TemplateView.as_view(template_name="esani_pantportal/product/success.html"),
        name="product_register_success",
    ),
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
