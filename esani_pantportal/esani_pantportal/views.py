# SPDX-FileCopyrightText: 2023 Magenta 2023
#
# SPDX-License-Identifier: MPL-2.0

from django.contrib.auth.views import LoginView


class PantportalLoginView(LoginView):
    template_name = "esani_pantportal/login.html"
