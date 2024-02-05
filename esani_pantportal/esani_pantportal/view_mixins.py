# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
from typing import Iterable, Optional

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.views.generic import UpdateView

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

    @property
    def two_factor_setup_required(self):
        return TemplateResponse(
            request=self.request,
            status=403,
            template="two_factor/core/otp_required.html",
        )

    def check_permissions(self) -> Optional[HttpResponse]:
        if not self.has_permissions:
            return self.access_denied
        elif (
            self.request.user.is_esani_admin
            and not self.request.user.is_verified()
            and not settings.BYPASS_2FA
        ):
            return self.two_factor_setup_required
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
        - For Kiosk users only users in the same kiosk are returned
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

    @property
    def same_branch(self):
        branch = self.get_object().get_branch()
        user_branch = self.request.user.branch
        if branch and user_branch:
            return branch == user_branch
        else:
            return False

    @property
    def same_company(self):
        company = self.get_object().get_company()
        user_company = self.request.user.company
        if company and user_company:
            return company == user_company
        else:
            return False

    @property
    def same_workplace(self):
        if self.request.user.user_type in [BRANCH_USER, KIOSK_USER]:
            return self.same_branch
        elif self.request.user.user_type == COMPANY_USER:
            return self.same_company


class UpdateViewMixin(PermissionRequiredMixin, UpdateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_fields"] = list(context["form"].fields.keys())

        if self.request.user.is_esani_admin:
            context["can_approve"] = True
            context["can_edit"] = True
        else:
            context["can_approve"] = False
            context["can_edit"] = (
                self.same_workplace
                and self.has_permissions
                and self.request.user.is_admin
            )
        return context

    def form_invalid(self, form):
        """
        If the form is invalid, leave all input fields open.
        This indicates that nothing was edited
        """
        context = self.get_context_data(form=form)
        context["form_fields_to_show"] = form.changed_data
        return self.render_to_response(context)
