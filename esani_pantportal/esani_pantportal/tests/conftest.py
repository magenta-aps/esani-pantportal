# -*- coding: utf-8 -*-
from django.contrib.auth.models import Group
from django.core.management import call_command

from esani_pantportal.models import CompanyUser


class LoginMixin:
    def login(self, group="EsaniAdmins"):
        username = f"testuser_{group}"
        qs = CompanyUser.objects.filter(username=username)
        if not qs:
            user = CompanyUser.objects.create_user(
                username=username,
                password="12345",
                email="test@test.com",
            )
        else:
            user = qs[0]
        call_command("create_groups")
        user.groups.add(Group.objects.get(name=group))
        self.client.login(username=f"testuser_{group}", password="12345")

        return user
