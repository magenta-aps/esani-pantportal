# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from esani_pantportal.models import (  # isort: skip
    BranchUser,
    CompanyUser,
    DepositPayout,
    DepositPayoutItem,
    EsaniUser,
    KioskUser,
    Product,
    QRBag,
    RefundMethod,
    SentEmail,
    User,
    Kiosk,
    CompanyBranch,
    Company,
)


class Command(BaseCommand):
    help = "Creates groups"

    def handle(self, *args, **options):
        company_users, _ = Group.objects.update_or_create(
            name="CompanyUsers",
        )
        branch_users, _ = Group.objects.update_or_create(
            name="BranchUsers",
        )
        kiosk_users, _ = Group.objects.update_or_create(
            name="KioskUsers",
        )

        company_admins, _ = Group.objects.update_or_create(
            name="CompanyAdmins",
        )

        branch_admins, _ = Group.objects.update_or_create(
            name="BranchAdmins",
        )
        kiosk_admins, _ = Group.objects.update_or_create(
            name="KioskAdmins",
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
        kiosk_user_model = ContentType.objects.get_for_model(
            KioskUser, for_concrete_model=False
        )
        company_user_model = ContentType.objects.get_for_model(
            CompanyUser, for_concrete_model=False
        )
        user_model = ContentType.objects.get_for_model(User, for_concrete_model=False)
        refund_method_model = ContentType.objects.get_for_model(
            RefundMethod, for_concrete_model=False
        )
        deposit_payout_model = ContentType.objects.get_for_model(
            DepositPayout, for_concrete_model=False
        )
        deposit_payout_item_model = ContentType.objects.get_for_model(
            DepositPayoutItem, for_concrete_model=False
        )
        email_model = ContentType.objects.get_for_model(
            SentEmail, for_concrete_model=False
        )
        qrbagmodel = ContentType.objects.get_for_model(QRBag, for_concrete_model=False)
        kiosk_model = ContentType.objects.get_for_model(Kiosk, for_concrete_model=False)
        company_branch_model = ContentType.objects.get_for_model(
            CompanyBranch, for_concrete_model=False
        )
        company_model = ContentType.objects.get_for_model(
            Company, for_concrete_model=False
        )

        def get_permission(action, content_type):
            return Permission.objects.get(
                codename=f"{action}_{content_type.model}",
                content_type=content_type,
            )

        for action, model in (
            ("view", product_model),
            ("add", product_model),
            ("change", product_model),
            ("delete", product_model),
            ("view", user_model),
            ("view", branch_user_model),
            ("add", branch_user_model),
            ("change", branch_user_model),
            ("delete", branch_user_model),
            ("view", company_user_model),
            ("add", company_user_model),
            ("change", company_user_model),
            ("delete", company_user_model),
            ("view", refund_method_model),
            ("add", refund_method_model),
            ("change", refund_method_model),
            ("delete", refund_method_model),
            ("view", qrbagmodel),
            ("change", qrbagmodel),
            ("view", company_model),
            ("change", company_model),
            ("view", company_branch_model),
            ("change", company_branch_model),
        ):
            company_admins.permissions.add(get_permission(action, model))

        for action, model in (
            ("view", product_model),
            ("add", product_model),
            ("change", product_model),
            ("delete", product_model),
            ("view", branch_user_model),
            ("add", branch_user_model),
            ("change", branch_user_model),
            ("delete", branch_user_model),
            ("view", user_model),
            ("view", refund_method_model),
            ("add", refund_method_model),
            ("change", refund_method_model),
            ("delete", refund_method_model),
            ("view", qrbagmodel),
            ("add", qrbagmodel),
            ("change", qrbagmodel),
            ("view", company_branch_model),
            ("change", company_branch_model),
            ("view", company_model),
            ("change", company_model),
        ):
            branch_admins.permissions.add(get_permission(action, model))

        for action, model in (
            ("view", product_model),
            ("add", product_model),
            ("change", product_model),
            ("delete", product_model),
            ("view", kiosk_user_model),
            ("add", kiosk_user_model),
            ("change", kiosk_user_model),
            ("delete", kiosk_user_model),
            ("view", user_model),
            ("view", refund_method_model),
            ("add", refund_method_model),
            ("change", refund_method_model),
            ("delete", refund_method_model),
            ("view", qrbagmodel),
            ("add", qrbagmodel),
            ("change", qrbagmodel),
            ("view", kiosk_model),
            ("change", kiosk_model),
        ):
            kiosk_admins.permissions.add(get_permission(action, model))

        for action, model in (
            ("view", product_model),
            ("view", branch_user_model),
            ("view", company_user_model),
            ("view", qrbagmodel),
            ("change", qrbagmodel),
        ):
            company_users.permissions.add(get_permission(action, model))

        for action, model in (
            ("view", product_model),
            ("view", branch_user_model),
            ("view", qrbagmodel),
            ("add", qrbagmodel),
            ("change", qrbagmodel),
        ):
            branch_users.permissions.add(get_permission(action, model))

        for action, model in (
            ("view", product_model),
            ("view", kiosk_user_model),
            ("view", qrbagmodel),
            ("add", qrbagmodel),
            ("change", qrbagmodel),
        ):
            kiosk_users.permissions.add(get_permission(action, model))

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
            ("view", kiosk_user_model),
            ("add", kiosk_user_model),
            ("change", kiosk_user_model),
            ("delete", kiosk_user_model),
            ("view", refund_method_model),
            ("add", refund_method_model),
            ("change", refund_method_model),
            ("delete", refund_method_model),
            ("view", qrbagmodel),
            ("change", qrbagmodel),
            ("add", email_model),
            ("view", kiosk_model),
            ("change", kiosk_model),
            ("delete", kiosk_model),
            ("view", company_model),
            ("change", company_model),
            ("delete", company_model),
            ("view", company_branch_model),
            ("change", company_branch_model),
            ("delete", company_branch_model),
            ("view", deposit_payout_model),
            ("view", deposit_payout_item_model),
            ("change", deposit_payout_item_model),
        ):
            esani_admins.permissions.add(get_permission(action, model))
