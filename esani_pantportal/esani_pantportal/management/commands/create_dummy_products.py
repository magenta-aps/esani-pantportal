# SPDX-FileCopyrightText: 2023 Magenta 2023
#
# SPDX-License-Identifier: MPL-2.0

from django.conf import settings
from django.core.management.base import BaseCommand
from esani_pantportal.models import Product


class Command(BaseCommand):
    help = "Created dummy products"

    def handle(self, *args, **options):
        if settings.ENVIRONMENT in ("production", "staging"):
            raise Exception(f"Will not create dummy products in {settings.ENVIRONMENT}")

        Product.objects.create(
            product_name="Sofavand",
            barcode=1,
            tax_group=1,
            product_type="Vand",
            approved=True,
        )
        Product.objects.create(
            product_name="Smedeøl",
            barcode=2,
            tax_group=2,
            product_type="Øl",
            approved=True,
        )
        Product.objects.create(
            product_name="Sovende And",
            barcode=3,
            tax_group=1,
            product_type="Vand",
            approved=False,
        )
