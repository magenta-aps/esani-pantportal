# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from django.contrib import admin

from esani_pantportal.models import DepositPayout, DepositPayoutItem, ERPProductMapping


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


class ERPProductMappingAdmin(admin.ModelAdmin):
    list_display = [
        "item_number",
        "category",
        "specifier",
        "text",
        "rate",
    ]
    ordering = ["item_number"]


admin.site.register(DepositPayout, DepositPayoutAdmin)
admin.site.register(ERPProductMapping, ERPProductMappingAdmin)
