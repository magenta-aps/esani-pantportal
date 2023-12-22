# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
from django.contrib.auth.models import Group
from django.core.management import call_command

from esani_pantportal.models import BranchUser, Company, CompanyBranch, EsaniUser


class LoginMixin:
    def login(self, group="EsaniAdmins"):
        username = f"testuser_{group}"

        if group == "EsaniAdmins":
            user_model = EsaniUser
            kwargs = {}
        elif group in ["BranchAdmins", "BranchUsers"]:
            user_model = BranchUser

            company = Company.objects.create(
                name="test company",
                cvr=92312345,
                address="foo",
                postal_code="123",
                city="test city",
                phone="+4544457845",
                permit_number=2,
            )
            branch = CompanyBranch.objects.create(
                company=company,
                name="test branch",
                address="foodora",
                postal_code="12311",
                city="test town",
                phone="+4542457845",
                location_id=3,
            )
            kwargs = {"branch": branch}

        qs = user_model.objects.filter(username=username)
        if not qs:
            user = user_model.objects.create_user(
                username=username,
                password="12345",
                email="test@test.com",
                **kwargs,
            )
        else:
            user = qs[0]
        call_command("create_groups")
        user.groups.add(Group.objects.get(name=group))
        self.client.login(username=f"testuser_{group}", password="12345")

        return user
