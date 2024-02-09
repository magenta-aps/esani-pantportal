# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

import random
from datetime import datetime, timedelta

import pytz
from django.conf import settings
from django.core.management.base import BaseCommand
from override_autonow import override_autonow

from esani_pantportal.models import (
    CompanyBranch,
    EsaniUser,
    Kiosk,
    QRBag,
    QRCodeGenerator,
)


def random_date(start_year, end_year):
    """
    This function will return a random datetime between 2020 and 2024
    """
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 1, 1)
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = random.randrange(int_delta)
    tz = pytz.timezone("Europe/Copenhagen")
    return tz.localize(start + timedelta(seconds=random_second))


class Command(BaseCommand):
    def handle(self, *args, **options):
        if settings.ENVIRONMENT in ("production", "staging"):
            raise Exception(f"Will not create dummy qr bags in {settings.ENVIRONMENT}")

        brugseni_natalie = CompanyBranch.objects.get(name="Brugseni Natalie")
        brugseni_nuuk = CompanyBranch.objects.get(name="Brugseni Nuuk")
        nuuk_kiosk = Kiosk.objects.get(cvr=15787407)
        user = EsaniUser.objects.get(username="admin")
        kwargs_list = [
            {"company_branch": brugseni_natalie},
            {"company_branch": brugseni_nuuk},
            {"kiosk": nuuk_kiosk},
        ]

        qrgen_small_bags, _ = QRCodeGenerator.objects.get_or_create(
            name="Små sække", prefix=0
        )
        qrgen_large_bags, _ = QRCodeGenerator.objects.get_or_create(
            name="Store sække", prefix=1
        )

        for kwargs in kwargs_list:
            small_qr_codes = qrgen_small_bags.generate_qr_codes(5)
            large_qr_codes = qrgen_large_bags.generate_qr_codes(5)

            for qr_code in small_qr_codes + large_qr_codes:
                kwargs["owner"] = (
                    kwargs.get("company_branch", kwargs.get("kiosk"))
                    .users.order_by("?")
                    .first()
                )
                if random.randint(0, 10) < 2:
                    # It is possible for a bag to be without owner
                    kwargs["owner"] = None
                kwargs["active"] = random.choice([True, False])

                statusses = random.choice(
                    [
                        ["Oprettet"],
                        ["Oprettet", "Under transport"],
                        ["Oprettet", "Under transport", "Afsluttet"],
                    ]
                )

                date_dict = {
                    "Oprettet": random_date(2020, 2021),
                    "Under transport": random_date(2021, 2022),
                    "Afsluttet": random_date(2022, 2023),
                }

                for status in statusses:
                    kwargs["status"] = status
                    kwargs["updated"] = date_dict[status]

                    with override_autonow():
                        qrbag, _ = QRBag.objects.update_or_create(
                            qr=qr_code,
                            defaults=kwargs,
                        )

                        record = qrbag.history.first()

                        record.history_date = kwargs["updated"]
                        record.history_user = user
                        record.save()
