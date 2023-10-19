# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
from functools import cached_property
from math import ceil
from typing import Any, Dict

from django.contrib.auth.views import LoginView
from django.forms import model_to_dict
from django.http import JsonResponse
from django.template import loader
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, FormView, ListView, UpdateView

from esani_pantportal.forms import ProductFilterForm, ProductRegisterForm
from esani_pantportal.models import Product


class PantportalLoginView(LoginView):
    template_name = "esani_pantportal/login.html"


class ProductRegisterView(CreateView):
    model = Product
    form_class = ProductRegisterForm
    template_name = "esani_pantportal/product/form.html"

    def get_success_url(self):
        return reverse("pant:product_register_success")


class ProductSearchView(FormView, ListView):
    template_name = "esani_pantportal/product/list.html"
    actions_template = "esani_pantportal/product/actions.html"
    model = Product
    paginate_by = 20
    form_class = ProductFilterForm

    def get(self, request, *args, **kwargs):
        self.form = self.get_form()
        if self.form.is_valid():
            self.object_list = self.get_queryset()
            return self.form_valid(self.form)
        else:
            return self.form_invalid(self.form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method == "GET":
            kwargs["data"] = self.request.GET
        return kwargs

    @cached_property
    def search_data(self):
        data = self.form.cleaned_data
        search_data = {"offset": 0, "limit": self.paginate_by}
        for key, value in data.items():
            if key not in ("json",) and value not in ("", None):
                if key in ("offset", "limit"):
                    value = int(value)
                search_data[key] = value
        if search_data["offset"] < 0:
            search_data["offset"] = 0
        if search_data["limit"] < 1:
            search_data["limit"] = 1
        search_data["page_number"] = ceil(
            (search_data["offset"] + 1) / search_data["limit"]
        )
        return search_data

    def get_queryset(self):
        data = self.search_data
        qs = self.model.objects.all()

        # django-filter kan gøre det samme, men der er ingen grund til at overkomplicere tingene

        for field in ("approved",):  # præcist match
            if data.get(field, None) not in (None, ""):  # False er en gyldig værdi
                qs = qs.filter(**{field: data[field]})

        for field in ("product_name", "barcode"):  # indehold alle ord, case insensitive
            if data.get(field, None) not in (None, ""):
                qs = qs.filter(
                    **{
                        field + "__icontains": part
                        for part in data[field].split()
                        if part
                    }
                )

        sort = data.get("sort", None)
        if sort:
            reverse = "-" if data.get("order", None) == "desc" else ""
            qs = qs.order_by(f"{reverse}{sort}")

        return qs

    def form_valid(self, form):
        qs = self.get_queryset()
        total = qs.count()
        offset = self.search_data["offset"]
        limit = self.search_data["limit"]
        items = qs[offset : offset + limit]
        context = self.get_context_data(
            items=items,
            total=total,
            search_data=self.search_data,
            actions_template=self.actions_template,
        )
        items = [
            self.item_to_json_dict(model_to_dict(item), context, index)
            for index, item in enumerate(items)
        ]
        context["items"] = items
        if form.cleaned_data["json"]:
            return JsonResponse(
                {
                    "total": total,
                    "items": items,
                }
            )
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            **{
                **kwargs,
                "actions_template": self.actions_template
                # "form": self.get_form()
            }
        )

    def item_to_json_dict(
        self, item: Dict[str, Any], context: Dict[str, Any], index: int
    ) -> Dict[str, Any]:
        return {
            key: self.map_value(item, key, context)
            for key in list(item.keys()) + ["actions"]
        }

    def map_value(self, item, key, context):
        if key == "actions":
            return loader.render_to_string(
                self.actions_template,
                {"item": item, **context},
                self.request,
            )
        value = item[key]
        if key == "approved":
            value = _("Ja") if value else _("Nej")
        return value


class ProductDetailView(UpdateView):
    model = Product
    template_name = "esani_pantportal/product/view.html"
    fields = ("approved",)

    def get_success_url(self):
        return self.request.GET.get("back", reverse("pant:product_list"))
