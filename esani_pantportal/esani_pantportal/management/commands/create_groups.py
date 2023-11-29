# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from esani_pantportal.models import BranchUser, CompanyUser, EsaniUser, Product, User


class Command(BaseCommand):
    help = "Creates groups"

    def handle(self, *args, **options):
        company_users, _ = Group.objects.update_or_create(
            name="CompanyUsers",
        )

        company_admins, _ = Group.objects.update_or_create(
            name="CompanyAdmins",
        )

        esani_admins, _ = Group.objects.update_or_create(
            name="EsaniAdmins",
        )

        product_model = ContentType.objects.get_for_model(
            Product, for_concrete_model=False
        )
        esani_user_model = ContentType.objects.get_for_model(
            EsaniUser, for_concrete_model=False
        )
        branch_user_model = ContentType.objects.get_for_model(
            BranchUser, for_concrete_model=False
        )
        company_user_model = ContentType.objects.get_for_model(
            CompanyUser, for_concrete_model=False
        )
        user_model = ContentType.objects.get_for_model(User, for_concrete_model=False)

        for action, model in (
            ("view", product_model),
            ("add", product_model),
            ("change", product_model),
            ("view", branch_user_model),
            ("add", branch_user_model),
            ("change", branch_user_model),
            ("delete", branch_user_model),
            ("view", user_model),
            ("view", company_user_model),
            ("add", company_user_model),
            ("change", company_user_model),
            ("delete", company_user_model),
        ):
            company_admins.permissions.add(
                Permission.objects.get(
                    codename=f"{action}_{model.name}", content_type=model
                )
            )

        for action, model in (
            ("view", product_model),
            ("view", branch_user_model),
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
            ("delete", product_model),
            ("view", branch_user_model),
            ("add", branch_user_model),
            ("change", branch_user_model),
            ("delete", branch_user_model),
            ("view", esani_user_model),
            ("add", esani_user_model),
            ("change", esani_user_model),
            ("delete", esani_user_model),
            ("view", user_model),
            ("add", user_model),
            ("change", user_model),
            ("delete", user_model),
            ("view", company_user_model),
            ("add", company_user_model),
            ("change", company_user_model),
            ("delete", company_user_model),
        ):
            esani_admins.permissions.add(
                Permission.objects.get(
                    codename=f"{action}_{model.name}", content_type=model
                )
            )
