# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from django.conf import settings
from django.core.management.base import BaseCommand

from esani_pantportal.models import DepositPayout, DepositPayoutItem, Kiosk


class Command(BaseCommand):
    help = 'Create "manually uploaded" dummy objects'

    def handle(self, *args, **options):
        if settings.ENVIRONMENT in ("production", "staging"):
            raise Exception(
                "Will not create dummy objects in " + f"{settings.ENVIRONMENT}"
            )

        kamik = Kiosk.objects.get(cvr=15787407)
        deposit_payout, _ = DepositPayout.objects.get_or_create(
            source_identifier="Admin - 2024-02-01",
            defaults={
                "source_type": "manual",
                "from_date": "2024-01-01",
                "to_date": "2024-02-01",
                "item_count": 2,
            },
        )

        DepositPayoutItem.objects.get_or_create(
            date="2024-01-01",
            defaults={"kiosk": kamik, "count": 22, "deposit_payout": deposit_payout},
        )
        DepositPayoutItem.objects.get_or_create(
            date="2024-02-01",
            defaults={"kiosk": kamik, "count": 33, "deposit_payout": deposit_payout},
        )
