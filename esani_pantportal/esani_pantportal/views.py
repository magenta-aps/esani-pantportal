# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from django.contrib.auth.views import LoginView
from django.views.generic import TemplateView


class PantportalLoginView(LoginView):
    template_name = "esani_pantportal/login.html"


class LoginRequiredView(TemplateView):
    # Denne side er ikke i settings.LOGIN_WHITELISTED_URLS,
    # så middleware vil vise en login-side hvis man ikke er logget ind
    template_name = "esani_pantportal/logged_in.html"
