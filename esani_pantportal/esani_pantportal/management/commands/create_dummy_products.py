# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

import random
from datetime import datetime, timedelta
from random import randrange

from django.conf import settings
from django.core.management.base import BaseCommand

from esani_pantportal.models import (
    PRODUCT_MATERIAL_CHOICES,
    PRODUCT_SHAPE_CHOICES,
    EsaniUser,
    Product,
)


def random_date():
    """
    This function will return a random datetime between 2020 and 2024
    """
    start = datetime(2020, 1, 1)
    end = datetime(2024, 1, 1)
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = randrange(int_delta)
    return start + timedelta(seconds=random_second)


class Command(BaseCommand):
    help = "Created dummy products"

    def handle(self, *args, **options):
        if settings.ENVIRONMENT in ("production", "staging"):
            raise Exception(f"Will not create dummy products in {settings.ENVIRONMENT}")

        if Product.objects.all().count() != 0:
            return

        vowels = "aeiouyæøå"
        consonants = "bcdfghjklmnpqrstvwxz"
        user = EsaniUser.objects.get(username="admin")

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

            approved = random.choice([True, False])
            Product.objects.create(
                product_name=product_name,
                barcode=barcode,
                approved=approved,
                material=random.choice(PRODUCT_MATERIAL_CHOICES)[0],
                height=random.randint(85, 200),
                diameter=random.randint(50, 100),
                weight=random.randint(100, 1000),
                capacity=random.randint(150, 1000),
                shape=random.choice(PRODUCT_SHAPE_CHOICES)[0],
                created_by=user,
                approval_date=random_date() if approved else None,
                creation_date=random_date(),
            )
