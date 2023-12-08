# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from django.conf import settings
from django.core.management.base import BaseCommand

from esani_pantportal.models import REFUND_METHOD_CHOICES, Kiosk, Product, RefundMethod


class Command(BaseCommand):
    help = "Create dummy objects for CSV import"

    def handle(self, *args, **options):
        if settings.ENVIRONMENT in ("production", "staging"):
            raise Exception(
                f"Will not create dummy objects for CSV import in {settings.ENVIRONMENT}"
            )

        # Add `RefundMethod` objects matching "Kamik" kiosk.
        # This matches the RVM serial numbers in `example_with_valid_ids.csv`
        kamik = Kiosk.objects.get(cvr=15787407)
        RefundMethod.objects.update_or_create(
            kiosk=kamik,
            serial_number="3",
            defaults={"method": REFUND_METHOD_CHOICES[0]},
        )
        RefundMethod.objects.update_or_create(
            kiosk=kamik,
            serial_number="4",
            defaults={"method": REFUND_METHOD_CHOICES[0]},
        )

        # Add `Product` objects matching the barcodes in `example_with_valid_ids.csv`
        defaults = {
            "height": 250,
            "diameter": 15,
            "weight": 20,
            "capacity": 330,
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
