# -*- coding: utf-8 -*-
from typing import Iterable, Optional

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.template.response import TemplateResponse


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
    def has_permissions(self) -> bool:
        user = self.request.user
        if user.is_superuser:
            return True

        required_permissions = set(self.required_permissions)
        user_permissions = set(user.get_all_permissions())
        return required_permissions.issubset(user_permissions)

    @property
    def can_approve(self) -> bool:
        # Only ESANI employees can approve products
        user = self.request.user
        if user.groups.filter(name="EsaniAdmins").exists() or user.is_superuser:
            return True
        else:
            return False
