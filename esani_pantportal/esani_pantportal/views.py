# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from django.contrib.auth.views import LoginView
from django.urls import reverse
from django.views.generic import CreateView, TemplateView

from esani_pantportal.forms import ProductRegisterForm
from esani_pantportal.models import Product


class PantportalLoginView(LoginView):
    template_name = "esani_pantportal/login.html"


class LoginRequiredView(TemplateView):
    # Denne side er ikke i settings.LOGIN_WHITELISTED_URLS,
    # så middleware vil vise en login-side hvis man ikke er logget ind
    template_name = "esani_pantportal/logged_in.html"


class ProductRegisterView(CreateView):
    model = Product
    form_class = ProductRegisterForm
    template_name = "esani_pantportal/product/form.html"

    def get_success_url(self):
        return reverse("product_register_success")
