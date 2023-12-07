from django.contrib import admin

from esani_pantportal.models import DepositPayout, DepositPayoutItem


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
    ]


class DepositPayoutAdmin(admin.ModelAdmin):
    inlines = [DepositPayoutItemAdmin]
    readonly_fields = ["filename", "from_date", "to_date", "item_count"]


admin.site.register(DepositPayout, DepositPayoutAdmin)
