# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from django.urls import path, reverse_lazy
from django.views.generic import RedirectView, TemplateView

from esani_pantportal.views import (
    ChangePasswordView,
    CsvTemplateView,
    ExcelTemplateView,
    MultipleProductRegisterView,
    PantportalLoginView,
    PantportalLogoutView,
    ProductDeleteView,
    ProductRegisterView,
    ProductSearchView,
    ProductUpdateView,
    RefundMethodDeleteView,
    RefundMethodRegisterView,
    RefundMethodSearchView,
    RegisterBranchUserAdminView,
    RegisterBranchUserPublicView,
    RegisterCompanyUserAdminView,
    RegisterCompanyUserPublicView,
    RegisterEsaniUserView,
    RegisterKioskUserAdminView,
    RegisterKioskUserPublicView,
    SetPasswordView,
    UserDeleteView,
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
        "pantmaskine/opret",
        RefundMethodRegisterView.as_view(),
        name="refund_method_register",
    ),
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
    path("pantmaskine/", RefundMethodSearchView.as_view(), name="refund_method_list"),
    path(
        "pantmaskine/<int:pk>/fjern",
        RefundMethodDeleteView.as_view(),
        name="refund_method_delete",
    ),
    path("produkt/<int:pk>", ProductUpdateView.as_view(), name="product_view"),
    path("produkt/<int:pk>/fjern", ProductDeleteView.as_view(), name="product_delete"),
    path("bruger/<int:pk>", UserUpdateView.as_view(), name="user_view"),
    path("bruger/<int:pk>/fjern", UserDeleteView.as_view(), name="user_delete"),
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
