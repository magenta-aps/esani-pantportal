# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
from functools import cached_property
from io import BytesIO
from typing import Any, Dict
from urllib.parse import unquote

import pandas as pd
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.core.exceptions import ValidationError
from django.forms import model_to_dict
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from esani_pantportal.util import default_dataframe, remove_parameter_from_url
from esani_pantportal.view_mixins import PermissionRequiredMixin

from esani_pantportal.models import (  # isort: skip
    TAX_GROUP_CHOICES,
    CompanyUser,
    Product,
    Branch,
    Company,
)

from django.views.generic import (  # isort: skip
    CreateView,
    FormView,
    ListView,
    UpdateView,
    View,
    TemplateView,
)
from esani_pantportal.forms import (  # isort: skip
    MultipleProductRegisterForm,
    ProductRegisterForm,
    ProductFilterForm,
    UserRegisterMultiForm,
)


class PantportalLoginView(LoginView):
    template_name = "esani_pantportal/login.html"


class PantportalLogoutView(LogoutView):
    template_name = "esani_pantportal/login.html"


class ProductRegisterView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductRegisterForm
    template_name = "esani_pantportal/product/form.html"

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("pant:product_register_success")


class UserRegisterView(CreateView):
    model = CompanyUser
    form_class = UserRegisterMultiForm
    template_name = "esani_pantportal/user/form.html"

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)

        # dict of companies and which shops they own
        branch_dict = {}
        for company in Company.objects.all():
            branches = Branch.objects.filter(company__pk=company.pk)
            branch_dict[company.pk] = [b.pk for b in branches]

        context_data["branch_dict"] = branch_dict

        return context_data

    def get_success_url(self):
        return reverse("pant:login")


class ProductSearchView(LoginRequiredMixin, FormView, ListView):
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
        # // = Python floor division
        search_data["page_number"] = (search_data["offset"] // search_data["limit"]) + 1
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


class ProductDetailView(PermissionRequiredMixin, UpdateView):
    model = Product
    template_name = "esani_pantportal/product/view.html"
    fields = (
        "approved",
        "product_name",
        "barcode",
        "refund_value",
        "tax_group",
        "danish",
        "material",
        "height",
        "diameter",
        "weight",
        "capacity",
        "shape",
    )
    required_permissions = ["esani_pantportal.change_product"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tax_groups"] = dict(TAX_GROUP_CHOICES)
        context["form_fields"] = self.fields

        if self.can_approve:
            context["can_approve"] = True
            context["can_edit"] = True
        else:
            context["can_approve"] = False
            context["can_edit"] = self.get_object().created_by == self.request.user
        return context

    def form_valid(self, form):
        if not self.can_approve:
            approved = self.get_object().approved
            if approved:
                return self.access_denied
            if self.get_object().created_by != self.request.user:
                return self.access_denied

        return self.check_permissions() or super().form_valid(form)

    def form_invalid(self, form):
        """
        If the form is invalid, leave all input fields open.
        This indicates that nothing was edited
        """
        context = self.get_context_data(form=form)
        context["form_fields_to_show"] = form.changed_data
        return self.render_to_response(context)

    def get_success_url(self):
        back_url = unquote(self.request.GET.get("back", ""))

        approved = self.get_object().approved
        if approved:
            if back_url:
                return remove_parameter_from_url(back_url, "json")
            else:
                return reverse("pant:product_list")
        else:
            return self.request.get_full_path()


class MultipleProductRegisterView(LoginRequiredMixin, FormView):
    template_name = "esani_pantportal/product/import.html"
    form_class = MultipleProductRegisterForm

    def form_valid(self, form):
        products = form.df.rename(form.rename_dict, axis=1).to_dict(orient="records")
        existing_barcodes = Product.objects.values_list("barcode", flat=True).distinct()
        failures = []
        success_count = 0
        existing_products_count = 0
        products_to_save = []
        for product_dict in products:
            barcode = product_dict["barcode"]
            product_name = product_dict["product_name"]
            if barcode in existing_barcodes:
                existing_products_count += 1
                continue
            try:
                product_dict["approved"] = False
                product = Product(**product_dict)
                product.created_by = self.request.user
                product.full_clean()
                products_to_save.append(product)
                success_count += 1
            except ValidationError as e:
                failures.append({product_name: e.message_dict})

        context = self.get_context_data(form=form)
        failure_count = len(failures)
        context["failures"] = failures
        context["success_count"] = success_count
        context["failure_count"] = failure_count
        context["existing_products_count"] = existing_products_count
        context["total_count"] = failure_count + success_count + existing_products_count
        context["filename"] = form.filename

        for product in products_to_save:
            product.save()

        return self.render_to_response(context=context)


class ExcelTemplateView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        with BytesIO() as b:
            df = default_dataframe()
            sheet_name = "Ark1"

            writer = pd.ExcelWriter(b, engine="xlsxwriter")
            df.to_excel(writer, sheet_name=sheet_name, index=False)

            for col_idx in range(len(df.columns)):
                writer.sheets[sheet_name].set_column(col_idx, col_idx, 18)
            writer.close()

            filename = "template.xlsx"
            response = HttpResponse(
                b.getvalue(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            response["Content-Disposition"] = "attachment; filename=%s" % filename
            return response


class CsvTemplateView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        df = default_dataframe()

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=template.csv"

        df.to_csv(path_or_buf=response, sep=";", index=False)
        return response


class TaxGroupView(LoginRequiredMixin, TemplateView):
    template_name = "esani_pantportal/product/tax_groups.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tax_group_choices"] = TAX_GROUP_CHOICES
        return context
