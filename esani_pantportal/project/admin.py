# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from django.contrib.admin import AdminSite
from django.contrib.auth.forms import AuthenticationForm


class EsaniPantAdminSite(AdminSite):
    site_header = "ESANI Pant Administration"
    login_template = "esani_pantportal/login.html"
    login_form = AuthenticationForm

    def has_permission(self, request):
        """
        Allow access to simple admin if user is superuser or can approve products
        (is an ESANI employee)
        """
        if request.user.is_active:
            if request.user.is_superuser or request.user.has_perm(
                "auth.approve_product"
            ):
                return True
        return False


pantadmin = EsaniPantAdminSite(name="pantadmin")
