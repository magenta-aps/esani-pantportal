# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from django.urls import path, reverse_lazy
from django.views.generic import RedirectView, TemplateView
from django_mitid_auth.saml.views import AccessDeniedView

from esani_pantportal.views import (
    ChangePasswordView,
    CsvTemplateView,
    ExcelTemplateView,
    MultipleProductRegisterView,
    PantportalLoginView,
    PantportalLogoutView,
    ProductRegisterView,
    ProductSearchView,
    ProductUpdateView,
    RegisterBranchUserAdminView,
    RegisterBranchUserPublicView,
    RegisterCompanyUserAdminView,
    RegisterCompanyUserPublicView,
    RegisterEsaniUserView,
    RegisterKioskUserAdminView,
    RegisterKioskUserPublicView,
    SetPasswordView,
    UserSearchView,
    UserUpdateView,
)

app_name = "esani_pantportal"


urlpatterns = [
    path("", RedirectView.as_view(url=reverse_lazy("pant:product_list"))),
    path("login", PantportalLoginView.as_view(), name="login"),
    path("logout", PantportalLogoutView.as_view(), name="logout"),
    path("produkt/opret", ProductRegisterView.as_view(), name="product_register"),
    path(
        "butik_bruger/opret/offentlig",
        RegisterBranchUserPublicView.as_view(),
        name="branch_user_register",
    ),
    path(
        "butik_bruger/opret/admin",
        RegisterBranchUserAdminView.as_view(),
        name="branch_user_register_by_admin",
    ),
    path(
        "virksomhed_bruger/opret/offentlig",
        RegisterCompanyUserPublicView.as_view(),
        name="company_user_register",
    ),
    path(
        "virksomhed_bruger/opret/admin",
        RegisterCompanyUserAdminView.as_view(),
        name="company_user_register_by_admin",
    ),
    path(
        "kiosk_bruger/opret/offentlig",
        RegisterKioskUserPublicView.as_view(),
        name="kiosk_user_register",
    ),
    path(
        "kiosk_bruger/opret/admin",
        RegisterKioskUserAdminView.as_view(),
        name="kiosk_user_register_by_admin",
    ),
    path(
        "esani_bruger/opret",
        RegisterEsaniUserView.as_view(),
        name="esani_user_register",
    ),
    path(
        "produkt/opret/success",
        TemplateView.as_view(template_name="esani_pantportal/product/success.html"),
        name="product_register_success",
    ),
    path(
        "bruger/opret/success",
        TemplateView.as_view(template_name="esani_pantportal/user/success.html"),
        name="user_register_success",
    ),
    path("produkt/", ProductSearchView.as_view(), name="product_list"),
    path("bruger/", UserSearchView.as_view(), name="user_list"),
    path("produkt/<int:pk>", ProductUpdateView.as_view(), name="product_view"),
    path(
        "bruger/<int:pk>",
        UserUpdateView.as_view(),
        name="user_view",
    ),
    path(
        "bruger/<int:pk>/adgangskode/nulstil",
        SetPasswordView.as_view(),
        name="set_password",
    ),
    path(
        "bruger/<int:pk>/adgangskode/skift",
        ChangePasswordView.as_view(),
        name="change_password",
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
