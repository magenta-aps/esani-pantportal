# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

import random

from django.conf import settings
from django.core.management.base import BaseCommand

from esani_pantportal.models import (  # isort: skip
    PRODUCT_MATERIAL_CHOICES,
    PRODUCT_SHAPE_CHOICES,
    Product,
)


class Command(BaseCommand):
    help = "Created dummy products"

    def handle(self, *args, **options):
        if settings.ENVIRONMENT in ("production", "staging"):
            raise Exception(f"Will not create dummy products in {settings.ENVIRONMENT}")

        if Product.objects.all().count() != 0:
            return

        vowels = "aeiouyæøå"
        consonants = "bcdfghjklmnpqrstvwxz"

        for i in range(100):
            barcode = ""
            for i in range(random.choice([8, 12, 13])):
                barcode += str(random.randint(0, 9))

            product_type = random.choice(["Øl", "Vand", "Juice", "Smoothie", "Saft"])

            product_name = "".join(
                [
                    random.choice(vowels),
                    random.choice(consonants) * 2,
                    random.choice(vowels),
                    "-",
                    product_type,
                ]
            )

            Product.objects.create(
                product_name=product_name,
                barcode=barcode,
                approved=random.choice([True, False]),
                material_type=random.choice(PRODUCT_MATERIAL_CHOICES)[0],
                height=random.randint(10, 100),
                diameter=random.randint(10, 100),
                weight=random.randint(100, 1000),
                capacity=random.randint(100, 1000),
                shape=random.choice(PRODUCT_SHAPE_CHOICES)[0],
            )
