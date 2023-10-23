# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from django.urls import path, reverse_lazy
from django.views.generic import RedirectView, TemplateView
from django_mitid_auth.saml.views import AccessDeniedView

from esani_pantportal.views import (  # isort: skip
    ProductRegisterView,
    ProductDetailView,
    ProductSearchView,
    MultipleProductRegisterView,
    ExcelTemplateView,
    CsvTemplateView,
)


app_name = "esani_pantportal"


urlpatterns = [
    path("", RedirectView.as_view(url=reverse_lazy("pant:product_list"))),
    path("produkt/opret", ProductRegisterView.as_view(), name="product_register"),
    path(
        "produkt/opret/success",
        TemplateView.as_view(template_name="esani_pantportal/product/success.html"),
        name="product_register_success",
    ),
    path("produkt/", ProductSearchView.as_view(), name="product_list"),
    path("produkt/<int:pk>", ProductDetailView.as_view(), name="product_view"),
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
    path(
        "produkt/opret/multiple",
        MultipleProductRegisterView.as_view(),
        name="multiple_product_register",
    ),
    path(
        "produkt/opret/multiple/excel_sample",
        ExcelTemplateView.as_view(),
        name="example_excel",
    ),
    path(
        "produkt/opret/multiple/csv_sample",
        CsvTemplateView.as_view(),
        name="example_csv",
    ),
]
