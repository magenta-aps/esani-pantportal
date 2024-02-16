# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

import random

from django.core.management.base import BaseCommand

from esani_pantportal.models import Company

company_names = [
    "Greenland Brewhouse",
    "Pisiffik",
]


class Command(BaseCommand):
    def handle(self, *args, **options):
        if Company.objects.all().count() != 0:
            return

        for company_name in company_names:
            Company.objects.create(
                name=company_name,
                cvr=company_names.index(company_name),
                address="Væskevej " + str(company_names.index(company_name)),
                city="Nuuk",
                postal_code="1234",
                phone="(+299) 3635" + str(random.randint(10, 99)),
                country="Grønland",
                company_type="A",
                registration_number=random.randint(1000, 9999),
                account_number=random.randint(10000000, 99999999),
                invoice_mail=company_name[:3].lower() + "@finansafdeling.gl",
                invoice_company_branch=False,
            )
