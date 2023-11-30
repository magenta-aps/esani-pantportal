# -*- coding: utf-8 -*-
from typing import Iterable, Optional

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.template.response import TemplateResponse

from esani_pantportal.models import (
    BRANCH_USER,
    COMPANY_USER,
    KIOSK_USER,
    BranchUser,
    CompanyUser,
    KioskUser,
)


class PermissionRequiredMixin(LoginRequiredMixin):
    # Liste af permissions påkræves for adgang
    required_permissions: Iterable[str] = ()

    @property
    def access_denied(self):
        user_permissions = set(self.request.user.get_all_permissions())
        return TemplateResponse(
            request=self.request,
            status=403,
            template="esani_pantportal/access_denied.html",
            context={
                "missing_permissions": set(self.required_permissions).difference(
                    user_permissions
                )
            },
            headers={"Cache-Control": "no-cache"},
        )

    def check_permissions(self) -> Optional[HttpResponse]:
        if not self.has_permissions:
            return self.access_denied
        return None

    @property
    def permissions_ok(self) -> bool:
        user = self.request.user
        required_permissions = set(self.required_permissions)
        user_permissions = set(user.get_all_permissions())
        permissions_ok = required_permissions.issubset(user_permissions)
        return permissions_ok

    @property
    def has_permissions(self) -> bool:
        user = self.request.user
        if user.is_superuser:
            return True

        return self.permissions_ok

    def get(self, request, *args, **kwargs):
        return self.check_permissions() or super().get(request, *args, **kwargs)

    def form_valid(self, form):
        return self.check_permissions() or super().form_valid(form)

    @property
    def users_in_same_company(self):
        """
        Return a list of IDs of users in the same company as the user calling this
        method.

        - For company users all users in the same company are returned. Including
          branches which report to the user's company.
        - For branch users only users in the same branch are returned.
        - For Kiosk users only users in the same kioks are returned
        - For ESANI users nothing is returned.
        """
        username = self.request.user.username
        if self.request.user.user_type == BRANCH_USER:
            branch_id = BranchUser.objects.get(username=username).branch.id
            user_ids = [u.id for u in BranchUser.objects.filter(branch__id=branch_id)]

        elif self.request.user.user_type == COMPANY_USER:
            company_id = CompanyUser.objects.get(username=username).company.id
            company_user_ids = [
                u.id for u in CompanyUser.objects.filter(company__id=company_id)
            ]

            branch_user_ids = [
                u.id for u in BranchUser.objects.filter(branch__company__id=company_id)
            ]

            user_ids = company_user_ids + branch_user_ids

        elif self.request.user.user_type == KIOSK_USER:
            branch_id = KioskUser.objects.get(username=username).branch.id
            user_ids = [u.id for u in KioskUser.objects.filter(branch__id=branch_id)]
        else:
            user_ids = []

        return user_ids
