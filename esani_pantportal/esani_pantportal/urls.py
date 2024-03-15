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
    CsvCompaniesView,
    CsvDebtorView,
    CsvProductsView,
    CsvTemplateView,
    CsvUsersView,
    DepositItemFormSetView,
    DepositPayoutSearchView,
    ERPCreditNoteExportSearchView,
    ExcelTemplateView,
    GenerateQRView,
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
    QRBagHistoryView,
    QRBagSearchView,
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
    TwoFactorSetup,
    UpdateListViewPreferences,
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
    path("qrpose/", QRBagSearchView.as_view(), name="qrbag_list"),
    path(
        "qrpose/<int:pk>/history",
        QRBagHistoryView.as_view(),
        name="qrbag_history",
    ),
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
    path(
        "udbetaling/arkiv/",
        ERPCreditNoteExportSearchView.as_view(),
        name="erp_credit_note_export_list",
    ),
    path("produkt/<int:pk>", ProductUpdateView.as_view(), name="product_view"),
    path(
        "produkt/<int:pk>/history",
        ProductHistoryView.as_view(),
        name="product_history",
    ),
    path("produkt/<int:pk>/fjern", ProductDeleteView.as_view(), name="product_delete"),
    path("bruger/<int:pk>", UserUpdateView.as_view(), name="user_view"),
    path("bruger/<int:pk>/fjern", UserDeleteView.as_view(), name="user_delete"),
    path("bruger/download/", CsvUsersView.as_view(), name="all_users_csv_download"),
    path(
        "virksomhed/download/",
        CsvCompaniesView.as_view(),
        name="all_companies_csv_download",
    ),
    path(
        "virksomhed/download_debitor/",
        CsvDebtorView.as_view(),
        name="all_companies_csv_debtor_download",
    ),
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
        name="password_set",
    ),
    path(
        "bruger/<int:pk>/adgangskode/skift",
        ChangePasswordView.as_view(),
        name="password_change",
    ),
    path(
        "produkt/bruger/<int:pk>/indstillinger",
        UpdateListViewPreferences.as_view(),
        name="preferences_update",
    ),
    path(
        "produkt/opret/flere",
        MultipleProductRegisterView.as_view(),
        name="product_multiple_register",
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
        name="excel_template_download",
    ),
    path(
        "produkt/opret/flere/csv_sample",
        CsvTemplateView.as_view(),
        name="csv_template_download",
    ),
    path(
        "send_nyhedsbrev",
        NewsEmailView.as_view(),
        name="newsletter_send",
    ),
    path(
        "produkt/download<int:approved>/",
        CsvProductsView.as_view(),
        name="registered_products_csv_download",
    ),
    path("virksomhed/<int:pk>", CompanyUpdateView.as_view(), name="company_update"),
    path(
        "butik/<int:pk>",
        CompanyBranchUpdateView.as_view(),
        name="company_branch_update",
    ),
    path("kiosk/<int:pk>", KioskUpdateView.as_view(), name="kiosk_update"),
    path("about/", AboutView.as_view(), name="about"),
    path("two_factor/setup", TwoFactorSetup.as_view(), name="two_factor_setup"),
    path("qr/generate", GenerateQRView.as_view(), name="qr_generate"),
    path(
        "udbetaling/opret",
        DepositItemFormSetView.as_view(),
        name="deposit_payout_register",
    ),
]
