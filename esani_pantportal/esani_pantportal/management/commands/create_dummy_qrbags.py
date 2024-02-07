# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

import random

from django.conf import settings
from django.core.management.base import BaseCommand

from esani_pantportal.models import CompanyBranch, Kiosk, QRBag, QRCodeGenerator


class Command(BaseCommand):
    def handle(self, *args, **options):
        if settings.ENVIRONMENT in ("production", "staging"):
            raise Exception(f"Will not create dummy qr bags in {settings.ENVIRONMENT}")

        brugseni_natalie = CompanyBranch.objects.get(name="Brugseni Natalie")
        brugseni_nuuk = CompanyBranch.objects.get(name="Brugseni Nuuk")
        nuuk_kiosk = Kiosk.objects.get(cvr=15787407)

        kwargs_list = [
            {"company_branch": brugseni_natalie},
            {"company_branch": brugseni_nuuk},
            {"kiosk": nuuk_kiosk},
        ]

        qrgen_small_bags = QRCodeGenerator.objects.create(name="Små sække", prefix=0)
        qrgen_large_bags = QRCodeGenerator.objects.create(name="Store sække", prefix=1)

        for kwargs in kwargs_list:
            small_qr_codes = qrgen_small_bags.generate_qr_codes(5)
            large_qr_codes = qrgen_large_bags.generate_qr_codes(5)

            for qr_code in small_qr_codes + large_qr_codes:
                kwargs["owner"] = (
                    kwargs.get("company_branch", kwargs.get("kiosk"))
                    .users.order_by("?")
                    .first()
                )
                kwargs["active"] = random.choice([True, False])
                kwargs["status"] = random.choice(
                    ["Oprettet", "Under transport", "Afsluttet"]
                )

                QRBag.objects.update_or_create(
                    qr=qr_code,
                    defaults=kwargs,
                )
