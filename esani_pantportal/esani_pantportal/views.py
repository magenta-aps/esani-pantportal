# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from django.contrib.auth.views import LoginView
from django.urls import reverse
from django.views.generic import CreateView, ListView, UpdateView

from esani_pantportal.forms import ProductRegisterForm
from esani_pantportal.models import Product


class PantportalLoginView(LoginView):
    template_name = "esani_pantportal/login.html"


class ProductRegisterView(CreateView):
    model = Product
    form_class = ProductRegisterForm
    template_name = "esani_pantportal/product/form.html"

    def get_success_url(self):
        return reverse("pant:product_register_success")


class ProductListView(ListView):
    model = Product
    template_name = "esani_pantportal/product/list.html"
    paginate_by = 20


class ProductDetailView(UpdateView):
    model = Product
    template_name = "esani_pantportal/product/view.html"
    fields = ("approved",)

    def get_success_url(self):
        return self.request.GET.get("back", reverse("product_list"))
