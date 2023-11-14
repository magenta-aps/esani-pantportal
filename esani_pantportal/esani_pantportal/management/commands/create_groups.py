# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from esani_pantportal.models import Product


class Command(BaseCommand):
    help = "Creates groups"

    def handle(self, *args, **options):
        company_users, _ = Group.objects.update_or_create(
            name="CompanyUsers",
        )

        esani_users, _ = Group.objects.update_or_create(
            name="EsaniAdmins",
        )

        product_model = ContentType.objects.get_for_model(
            Product, for_concrete_model=False
        )

        for action, model in (
            ("view", product_model),
            ("add", product_model),
            ("change", product_model),
            # Ingen delete
        ):
            company_users.permissions.add(
                Permission.objects.get(
                    codename=f"{action}_{model.name}", content_type=model
                )
            )

        for action, model in (
            ("view", product_model),
            ("add", product_model),
            ("change", product_model),
            # Ingen delete
        ):
            esani_users.permissions.add(
                Permission.objects.get(
                    codename=f"{action}_{model.name}", content_type=model
                )
            )
