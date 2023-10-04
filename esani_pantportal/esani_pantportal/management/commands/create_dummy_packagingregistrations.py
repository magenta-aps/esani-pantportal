# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from django.conf import settings
from django.core.management.base import BaseCommand

from esani_pantportal.models import PackagingRegistration, Product, Company


class Command(BaseCommand):
    help = "Created dummy products"

    def handle(self, *args, **options):
        if settings.ENVIRONMENT in ("production", "staging"):
            raise Exception(
                f"Will not create dummy registrations in {settings.ENVIRONMENT}"
            )

        PackagingRegistration.objects.create(
            registration_number=1,
            company=Company.objects.order_by("?").first(),
            quantity=117,
            product=Product.objects.filter(approved=True).order_by("?").first(),
        )
