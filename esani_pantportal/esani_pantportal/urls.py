# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from django.urls import path, reverse_lazy
from django.views.generic import RedirectView, TemplateView

from esani_pantportal.views import (
    AboutView,
    ChangePasswordView,
    CompanyBranchDeleteView,
    CompanyBranchUpdateView,
    CompanyDeleteView,
    CompanySearchView,
    CompanyUpdateView,
    CsvProductsView,
    CsvTemplateView,
    DepositPayoutSearchView,
    ExcelTemplateView,
    KioskDeleteView,
    KioskUpdateView,
    MultipleProductApproveView,
    MultipleProductDeleteView,
    MultipleProductRegisterView,
    NewsEmailView,
    PantportalLoginView,
    PantportalLogoutView,
    ProductDeleteView,
    ProductHistoryView,
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
    ReverseVendingMachineDeleteView,
    ReverseVendingMachineRegisterView,
    ReverseVendingMachineSearchView,
    SetPasswordView,
    UpdateProductViewPreferences,
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
        ReverseVendingMachineRegisterView.as_view(),
        name="rvm_register",
    ),
    path(
        "bruger/opret",
        TemplateView.as_view(
            template_name="esani_pantportal/user/user_register_begin.html",
        ),
        name="user_register_begin",
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
    path("virksomhed/", CompanySearchView.as_view(), name="company_list"),
    path("bruger/", UserSearchView.as_view(), name="user_list"),
    path(
        "pantmaskine/",
        ReverseVendingMachineSearchView.as_view(),
        name="rvm_list",
    ),
    path(
        "pantmaskine/<int:pk>/fjern",
        ReverseVendingMachineDeleteView.as_view(),
        name="rvm_delete",
    ),
    path("udbetaling/", DepositPayoutSearchView.as_view(), name="deposit_payout_list"),
    path("produkt/<int:pk>", ProductUpdateView.as_view(), name="product_view"),
    path(
        "produkt/<int:pk>/history",
        ProductHistoryView.as_view(),
        name="product_history",
    ),
    path("produkt/<int:pk>/fjern", ProductDeleteView.as_view(), name="product_delete"),
    path("bruger/<int:pk>", UserUpdateView.as_view(), name="user_view"),
    path("bruger/<int:pk>/fjern", UserDeleteView.as_view(), name="user_delete"),
    path(
        "virksomhed/<int:pk>/fjern", CompanyDeleteView.as_view(), name="company_delete"
    ),
    path(
        "butik/<int:pk>/fjern",
        CompanyBranchDeleteView.as_view(),
        name="company_branch_delete",
    ),
    path("kiosk/<int:pk>/fjern", KioskDeleteView.as_view(), name="kiosk_delete"),
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
        "produkt/bruger/<int:pk>/indstillinger",
        UpdateProductViewPreferences.as_view(),
        name="update_preferences",
    ),
    path(
        "produkt/opret/flere",
        MultipleProductRegisterView.as_view(),
        name="multiple_product_register",
    ),
    path(
        "produkt/flere/godkend",
        MultipleProductApproveView.as_view(),
        name="product_multiple_approve",
    ),
    path(
        "produkt/flere/fjern",
        MultipleProductDeleteView.as_view(),
        name="product_multiple_delete",
    ),
    path(
        "produkt/opret/flere/excel_sample",
        ExcelTemplateView.as_view(),
        name="example_excel",
    ),
    path(
        "produkt/opret/flere/csv_sample",
        CsvTemplateView.as_view(),
        name="example_csv",
    ),
    path(
        "send_nyhedsbrev",
        NewsEmailView.as_view(),
        name="send_newsletter",
    ),
    path(
        "produkt/download<int:approved>/",
        CsvProductsView.as_view(),
        name="registered_products_csv",
    ),
    path("virksomhed/<int:pk>", CompanyUpdateView.as_view(), name="update_company"),
    path(
        "butik/<int:pk>",
        CompanyBranchUpdateView.as_view(),
        name="update_company_branch",
    ),
    path("kiosk/<int:pk>", KioskUpdateView.as_view(), name="update_kiosk"),
    path("about/", AboutView.as_view(), name="about"),
]
