# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from django.conf import settings
from django.core.management.base import BaseCommand

from esani_pantportal.models import CompanyBranch, Kiosk, RefundMethod


class Command(BaseCommand):
    help = "Creates dummy users"

    def handle(self, *args, **options):
        if settings.ENVIRONMENT in ("production", "staging"):
            raise Exception(
                f"Will not create dummy refund methods in {settings.ENVIRONMENT}"
            )

        brugseni_natalie = CompanyBranch.objects.get(name="Brugseni Natalie")
        brugseni_nuuk = CompanyBranch.objects.get(name="Brugseni Nuuk")
        nuuk_kiosk = Kiosk.objects.get(cvr=15787407)

        RefundMethod.objects.update_or_create(
            serial_number=100000000,
            defaults={"compensation": 2.3, "method": "FK", "branch": brugseni_nuuk},
        )
        RefundMethod.objects.update_or_create(
            serial_number=110000000,
            defaults={"compensation": 2.1, "method": "FKS", "branch": brugseni_natalie},
        )
        RefundMethod.objects.update_or_create(
            serial_number=120000000,
            defaults={"compensation": 1.2, "method": "FKS", "branch": brugseni_natalie},
        )
        RefundMethod.objects.update_or_create(
            serial_number=130000000,
            defaults={"compensation": 2.6, "method": "S", "kiosk": nuuk_kiosk},
        )
