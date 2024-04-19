# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from simple_history.admin import SimpleHistoryAdmin

from esani_pantportal.models import (
    DepositPayout,
    DepositPayoutItem,
    ERPCreditNoteExport,
    ERPProductMapping,
    Product,
)


class DepositPayoutItemAdmin(admin.TabularInline):
    model = DepositPayoutItem
    extra = 0
    readonly_fields = [
        "deposit_payout",
        "location_id",
        "rvm_serial",
        "date",
        "barcode",
        "count",
        "consumer_session_id",
        "consumer_identity",
    ]


class DepositPayoutAdmin(admin.ModelAdmin):
    inlines = [DepositPayoutItemAdmin]
    readonly_fields = [
        "source_type",
        "source_identifier",
        "from_date",
        "to_date",
        "item_count",
    ]


class ERPCreditNoteExportAdmin(admin.ModelAdmin):
    _fields: list = [
        "file_id",
        "from_date",
        "to_date",
        "created_by",
        "created_at",
    ]
    list_display = _fields
    readonly_fields = _fields
    ordering = ["-to_date"]


class ERPProductMappingAdmin(admin.ModelAdmin):
    list_display = [
        "item_number",
        "category",
        "specifier",
        "text",
        "rate",
    ]
    ordering = ["item_number"]


class CreationDateNullFilter(admin.SimpleListFilter):
    title = _("oprettelsesdato")
    parameter_name = "cd"

    def lookups(self, request, model_admin):
        return [
            ("all", _("alle")),
            ("null", _("blank")),
            ("notnull", _("udfyldt")),
        ]

    def queryset(self, request, queryset):
        if self.value() == "null":
            return queryset.filter(creation_date__isnull=True)
        if self.value() == "notnull":
            return queryset.filter(creation_date__isnull=False)


class ApprovalDateNullFilter(admin.SimpleListFilter):
    title = _("godkendelsesdato")
    parameter_name = "ad"

    def lookups(self, request, model_admin):
        return [
            ("all", _("alle")),
            ("null", _("blank")),
            ("notnull", _("udfyldt")),
        ]

    def queryset(self, request, queryset):
        if self.value() == "null":
            return queryset.filter(approval_date__isnull=True)
        if self.value() == "notnull":
            return queryset.filter(approval_date__isnull=False)


class ProductAdmin(SimpleHistoryAdmin):
    list_display = [
        "product_name",
        "barcode",
        "state",
        "creation_date",
        "approval_date",
    ]
    list_filter = [
        "state",
        CreationDateNullFilter,
        ApprovalDateNullFilter,
    ]
    search_fields = [
        "product_name",
        "barcode",
    ]

    def creation_date(self, obj):
        return obj.creation_date

    creation_date.admin_order_field = "creation_date"  # type: ignore

    def approval_date(self, obj):
        return obj.approval_date

    approval_date.admin_order_field = "approval_date"  # type: ignore


admin.site.register(DepositPayout, DepositPayoutAdmin)
admin.site.register(ERPCreditNoteExport, ERPCreditNoteExportAdmin)
admin.site.register(ERPProductMapping, ERPProductMappingAdmin)
admin.site.register(Product, ProductAdmin)
