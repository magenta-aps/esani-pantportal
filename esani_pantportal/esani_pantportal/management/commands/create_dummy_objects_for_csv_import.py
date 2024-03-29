# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

from esani_pantportal.models import Kiosk, Product, ReverseVendingMachine


class Command(BaseCommand):
    help = "Create dummy objects for CSV import"

    def handle(self, *args, **options):
        if settings.ENVIRONMENT in ("production", "staging"):
            raise Exception(
                "Will not create dummy objects for CSV import in "
                + f"{settings.ENVIRONMENT}"
            )

        # Add `ReverseVendingMachine` objects matching "Kamik" kiosk.
        # This matches the RVM serial numbers in `example_with_valid_ids.csv`
        kamik = Kiosk.objects.get(cvr=15787407)
        ReverseVendingMachine.objects.update_or_create(
            kiosk=kamik,
            serial_number="3",
        )
        ReverseVendingMachine.objects.update_or_create(
            kiosk=kamik,
            serial_number="4",
        )

        # Add `Product` objects matching the barcodes in `example_with_valid_ids.csv`
        defaults = {
            "height": 200,
            "diameter": 100,
            "weight": 20,
            "capacity": 330,
            "shape": "F",
        }
        Product.objects.update_or_create(
            product_name="Foo",
            barcode="839728179970",
            defaults=defaults,
        )
        Product.objects.update_or_create(
            product_name="Bar",
            barcode="3662195622914",
            defaults=defaults,
        )

        call_command("import_deposit_payouts")
