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
                phone=random.randint(100000, 999999),
                permit_number=company_names.index(company_name),
            )
