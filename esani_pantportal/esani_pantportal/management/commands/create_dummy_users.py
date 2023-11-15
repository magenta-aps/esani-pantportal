# -*- coding: utf-8 -*-

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from esani_pantportal.models import Branch, Company, CompanyUser


class Command(BaseCommand):
    help = "Creates dummy users"

    def handle(self, *args, **options):
        if settings.ENVIRONMENT in ("production", "staging"):
            raise Exception(f"Will not create dummy users in {settings.ENVIRONMENT}")
        company_admin_group = Group.objects.get(name="CompanyAdmins")
        company_user_group = Group.objects.get(name="CompanyUsers")
        esani_user_group = Group.objects.get(name="EsaniAdmins")

        brugseni, created = Company.objects.update_or_create(
            cvr=15787406,
            defaults={
                "name": "Brugseni",
                "address": "Aqqusinersuaq 4, 2 th. P.O.Box 1092 3900 Nuuk",
                "phone": "+299 36 35 00",
                "permit_number": None,
            },
        )

        brugseni_natalie, created = Branch.objects.update_or_create(
            company=brugseni,
            defaults={
                "name": "Brugseni Natalie",
                "address": "57RR+M9M, Iiminaq",
                "postal_code": "3905",
                "city": "Nuuk",
                "phone": "+299 36 35 01",
                "location_id": "00432",
                "customer_id": "1234",
            },
        )

        company_user, created = CompanyUser.objects.update_or_create(
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
            },
            username="rip",
        )
        company_user.groups.add(company_user_group)

        company_admin, created = CompanyUser.objects.update_or_create(
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
            },
            username="anders",
        )
        company_admin.groups.add(company_admin_group)

        company_admin, created = CompanyUser.objects.update_or_create(
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
            },
            username="andersine",
        )
        company_admin.groups.add(company_admin_group)

        esani_user, created = CompanyUser.objects.update_or_create(
            defaults={
                "first_name": "ESANI",
                "last_name": "Admin",
                "email": "admin@esani.dk",
                "password": make_password("admin"),
                "is_active": True,
                "is_staff": False,
                "is_superuser": False,
                "branch": None,
                "phone": "+299 36 35 04",
            },
            username="admin",
        )
        esani_user.groups.add(esani_user_group)
