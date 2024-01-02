# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from esani_pantportal.models import (
    BranchUser,
    Company,
    CompanyBranch,
    CompanyUser,
    EsaniUser,
    Kiosk,
    KioskUser,
)


class Command(BaseCommand):
    help = "Creates dummy users"

    def handle(self, *args, **options):
        if settings.ENVIRONMENT in ("production", "staging"):
            raise Exception(f"Will not create dummy users in {settings.ENVIRONMENT}")
        company_admin_group = Group.objects.get(name="CompanyAdmins")
        branch_admin_group = Group.objects.get(name="BranchAdmins")
        kiosk_admin_group = Group.objects.get(name="KioskAdmins")
        branch_user_group = Group.objects.get(name="BranchUsers")
        esani_user_group = Group.objects.get(name="EsaniAdmins")

        brugseni, created = Company.objects.update_or_create(
            cvr=15787406,
            defaults={
                "name": "Brugseni",
                "address": "Aqqusinersuaq 4, 2 th. P.O.Box 1092 ",
                "postal_code": "1092",
                "city": "Nuuk",
                "municipality": "Semersooq",
                "country": "Grønland",
                "phone": "+299 36 35 00",
                "company_type": "A",
            },
        )

        brugseni_natalie, created = CompanyBranch.objects.update_or_create(
            name="Brugseni Natalie",
            defaults={
                "name": "Brugseni Natalie",
                "address": "57RR+M9M, Iiminaq",
                "postal_code": "3905",
                "city": "Nuuk",
                "municipality": "Semersooq",
                "phone": "+299 36 35 01",
                "location_id": "00432",
                "customer_id": "1234",
                "company": brugseni,
                "branch_type": "D",
            },
        )

        brugseni_nuuk, created = CompanyBranch.objects.update_or_create(
            name="Brugseni Nuuk",
            defaults={
                "address": "Brugsen, Aqqusinersuaq 2",
                "postal_code": "3900",
                "city": "Nuuk",
                "municipality": "Semersooq",
                "phone": "+299 32 11 22",
                "location_id": "004321",
                "customer_id": "12345",
                "company": brugseni,
                "branch_type": "D",
            },
        )

        branch_user, created = BranchUser.objects.update_or_create(
            defaults={
                "first_name": "Rip",
                "last_name": "And",
                "email": "rip.and@brugseni.dk",
                "password": make_password("rip"),
                "is_active": True,
                "is_staff": False,
                "is_superuser": False,
                "branch": brugseni_natalie,
                "phone": "+299 36 35 03",
                "approved": True,
            },
            username="rip",
        )
        branch_user.groups.add(branch_user_group)

        branch_admin, created = BranchUser.objects.update_or_create(
            defaults={
                "first_name": "Anders",
                "last_name": "And",
                "email": "anders.and@brugseni.dk",
                "password": make_password("anders"),
                "is_active": True,
                "is_staff": False,
                "is_superuser": False,
                "branch": brugseni_natalie,
                "phone": "+299 36 35 03",
                "approved": True,
            },
            username="anders",
        )
        branch_admin.groups.add(branch_admin_group)

        branch_admin, created = BranchUser.objects.update_or_create(
            defaults={
                "first_name": "Andersine",
                "last_name": "And",
                "email": "Andersine.and@brugseni.dk",
                "password": make_password("andersine"),
                "is_active": True,
                "is_staff": False,
                "is_superuser": False,
                "branch": brugseni_natalie,
                "phone": "+299 36 35 03",
                "approved": True,
            },
            username="andersine",
        )
        branch_admin.groups.add(branch_admin_group)

        branch_admin, created = BranchUser.objects.update_or_create(
            defaults={
                "first_name": "Kim",
                "last_name": "Larsen",
                "email": "K.larsen@brugseni.dk",
                "password": make_password("kim"),
                "is_active": True,
                "is_staff": False,
                "is_superuser": False,
                "branch": brugseni_nuuk,
                "phone": "+299 36 35 03",
                "approved": True,
            },
            username="kim",
        )
        branch_admin.groups.add(branch_admin_group)

        esani_user, created = EsaniUser.objects.update_or_create(
            defaults={
                "first_name": "ESANI",
                "last_name": "Admin",
                "email": "admin@esani.dk",
                "password": make_password("admin"),
                "newsletter": False,
                "is_active": True,
                "is_staff": False,
                "is_superuser": False,
                "phone": "+299 36 35 04",
            },
            username="admin",
        )
        esani_user.groups.add(esani_user_group)

        company_user, created = CompanyUser.objects.update_or_create(
            defaults={
                "first_name": "Alfred",
                "last_name": "Pennyworth",
                "email": "A.pennyworth@brugseni.dk",
                "password": make_password("alfred"),
                "newsletter": False,
                "is_active": True,
                "is_staff": False,
                "is_superuser": False,
                "company": brugseni,
                "phone": "+299 36 35 03",
                "approved": True,
            },
            username="alfred",
        )
        company_user.groups.add(company_admin_group)

        nuuk_kiosk, created = Kiosk.objects.update_or_create(
            cvr=15787407,
            defaults={
                "name": "Kamik",
                "address": "57C8+9F6, Nuuk",
                "postal_code": "3900",
                "city": "Nuuk",
                "phone": "+299 32 11 22",
                "location_id": "2",
                "customer_id": "22",
            },
        )

        kiosk_user, created = KioskUser.objects.update_or_create(
            defaults={
                "first_name": "Oswald",
                "last_name": "Cobblepot",
                "email": "O.cobblepot@brugseni.dk",
                "password": make_password("oswald"),
                "is_active": True,
                "is_staff": False,
                "is_superuser": False,
                "branch": nuuk_kiosk,
                "phone": "+299 36 35 03",
                "approved": True,
            },
            username="oswald",
        )
        kiosk_user.groups.add(kiosk_admin_group)
