# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
from functools import cached_property
from io import BytesIO
from typing import Any, Dict
from urllib.parse import unquote

import pandas as pd
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.contrib.auth.views import LoginView, LogoutView
from django.core.exceptions import ValidationError
from django.forms import model_to_dict
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, FormView, ListView, UpdateView, View

from esani_pantportal.forms import (
    MultipleProductRegisterForm,
    PantPortalAuthenticationForm,
    ProductFilterForm,
    ProductRegisterForm,
    RegisterBranchUserMultiForm,
    RegisterCompanyUserMultiForm,
    RegisterEsaniUserForm,
    UserFilterForm,
)
from esani_pantportal.models import (
    BRANCH_USER,
    COMPANY_USER,
    ESANI_USER,
    KIOSK_USER,
    BranchUser,
    Company,
    CompanyBranch,
    CompanyUser,
    EsaniUser,
    Product,
    User,
)
from esani_pantportal.templatetags.pant_tags import user_type
from esani_pantportal.util import default_dataframe, remove_parameter_from_url
from esani_pantportal.view_mixins import PermissionRequiredMixin


class PantportalLoginView(LoginView):
    template_name = "esani_pantportal/login.html"
    form_class = PantPortalAuthenticationForm


class PantportalLogoutView(LogoutView):
    template_name = "esani_pantportal/login.html"


class ProductRegisterView(PermissionRequiredMixin, CreateView):
    model = Product
    form_class = ProductRegisterForm
    template_name = "esani_pantportal/product/form.html"
    required_permissions = ["esani_pantportal.add_product"]

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("pant:product_register_success")


class RegisterEsaniUserView(PermissionRequiredMixin, CreateView):
    model = EsaniUser
    form_class = RegisterEsaniUserForm
    template_name = "esani_pantportal/user/esani_user/form.html"
    required_permissions = ["esani_pantportal.add_esaniuser"]
    required_groups = ["EsaniAdmins"]

    def get_success_url(self):
        return reverse("pant:user_register_success")

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.set_password(form.cleaned_data["password"])
        self.object.save()
        self.object.groups.add(Group.objects.get(name="EsaniAdmins"))
        return super().form_valid(form)


class RegisterBranchUserView(CreateView):
    model = BranchUser
    form_class = RegisterBranchUserMultiForm
    template_name = "esani_pantportal/user/branch_user/form.html"

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)

        # dict of companies and which shops they own
        branch_dict = {}
        for company in Company.objects.all():
            branches = CompanyBranch.objects.filter(company__pk=company.pk)
            branch_dict[company.pk] = [b.pk for b in branches]

        context_data["branch_dict"] = branch_dict

        return context_data


class RegisterBranchUserPublicView(RegisterBranchUserView):
    def get_success_url(self):
        return reverse("pant:login")


class RegisterBranchUserAdminView(PermissionRequiredMixin, RegisterBranchUserView):
    required_permissions = ["esani_pantportal.add_branchuser"]
    allowed_user_types = [ESANI_USER, BRANCH_USER, COMPANY_USER]

    def get_success_url(self):
        return reverse("pant:user_register_success")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["show_admin_flag"] = True
        kwargs["allow_multiple_admins"] = True
        kwargs["approved"] = True
        if self.request.user.user_type == BRANCH_USER:
            kwargs["company"] = self.request.user.branch.company
            kwargs["branch"] = self.request.user.branch
        elif self.request.user.user_type == COMPANY_USER:
            kwargs["company"] = self.request.user.company
        return kwargs


class RegisterCompanyUserView(CreateView):
    model = CompanyUser
    form_class = RegisterCompanyUserMultiForm
    template_name = "esani_pantportal/user/company_user/form.html"


class RegisterCompanyUserPublicView(RegisterCompanyUserView):
    def get_success_url(self):
        return reverse("pant:login")


class RegisterCompanyUserAdminView(PermissionRequiredMixin, RegisterCompanyUserView):
    required_permissions = ["esani_pantportal.add_companyuser"]
    allowed_user_types = [ESANI_USER, COMPANY_USER]

    def get_success_url(self):
        return reverse("pant:user_register_success")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["show_admin_flag"] = True
        kwargs["allow_multiple_admins"] = True
        kwargs["approved"] = True
        if self.request.user.user_type == COMPANY_USER:
            kwargs["company"] = self.request.user.company
        return kwargs


class SearchView(LoginRequiredMixin, FormView, ListView):
    paginate_by = 20

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

        # indehold alle ord, case insensitive
        for field in ("product_name", "barcode", "username", "user_type"):
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
            **{**kwargs, "actions_template": self.actions_template}
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
        elif key in ["phone", "groups"]:
            value = str(value)
        elif key == "user_type":
            value = user_type(value)

        return value


class ProductSearchView(SearchView):
    template_name = "esani_pantportal/product/list.html"
    actions_template = "esani_pantportal/product/actions.html"
    model = Product
    form_class = ProductFilterForm


class UserSearchView(PermissionRequiredMixin, SearchView):
    template_name = "esani_pantportal/user/list.html"
    actions_template = "esani_pantportal/user/actions.html"
    model = User
    form_class = UserFilterForm
    required_permissions = ["esani_pantportal.view_user"]

    def get_queryset(self):
        qs = super().get_queryset()

        # Only allow branch/company/kiosk users to see users of their own branch/company
        user_ids = self.users_in_same_company
        if user_ids:
            qs = qs.filter(pk__in=user_ids)

        return qs


class DetailView(PermissionRequiredMixin, UpdateView):
    @property
    def same_branch(self):
        obj = self.get_object()
        author_branch = getattr(obj, "created_by", obj).branch
        user_branch = self.request.user.branch
        if author_branch and user_branch:
            return author_branch == user_branch
        else:
            return False

    @property
    def same_company(self):
        obj = self.get_object()
        author_company = getattr(obj, "created_by", obj).company
        user_company = self.request.user.company
        if author_company and user_company:
            return author_company == user_company
        else:
            return False

    @property
    def same_workplace(self):
        if self.request.user.user_type in [BRANCH_USER, KIOSK_USER]:
            return self.same_branch
        elif self.request.user.user_type == COMPANY_USER:
            return self.same_company

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_fields"] = self.fields

        if self.request.user.is_esani_admin:
            context["can_approve"] = True
            context["can_edit"] = True
        else:
            context["can_approve"] = False
            context["can_edit"] = self.same_workplace and self.has_permissions
        return context

    def form_invalid(self, form):
        """
        If the form is invalid, leave all input fields open.
        This indicates that nothing was edited
        """
        context = self.get_context_data(form=form)
        context["form_fields_to_show"] = form.changed_data
        return self.render_to_response(context)


class ProductDetailView(DetailView):
    model = Product
    template_name = "esani_pantportal/product/view.html"
    fields = (
        "approved",
        "product_name",
        "barcode",
        "danish",
        "material",
        "height",
        "diameter",
        "weight",
        "capacity",
        "shape",
    )
    required_permissions = ["esani_pantportal.change_product"]

    def form_valid(self, form):
        if not self.request.user.is_esani_admin:
            approved = self.get_object().approved
            if approved:
                return self.access_denied
            if not self.same_workplace:
                return self.access_denied

        return super().form_valid(form)

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


class UserDetailView(DetailView):
    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        context_data["user"] = self.request.user
        context_data["profile"] = context_data["object"].user_profile

        common_attributes = ["name", "address", "postal_code", "city", "phone"]
        branch_attributes = ["customer_id"]
        company_attributes = ["cvr", "permit_number"]
        kiosk_attributes = ["cvr", "permit_number"]

        context_data["branch_info_attributes"] = common_attributes + branch_attributes
        if context_data["object"].user_type == KIOSK_USER:
            context_data["branch_info_attributes"].extend(kiosk_attributes)
        context_data["company_info_attributes"] = common_attributes + company_attributes
        return context_data

    def get(self, request, *args, **kwargs):
        user = self.get_object()

        user_ids = self.users_in_same_company
        if not self.request.user.is_esani_admin and user.id not in user_ids:
            return self.access_denied

        user_verbose = user.user_profile._meta.verbose_name
        self.required_permissions = [f"esani_pantportal.change_{user_verbose}"]

        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        return self.request.get_full_path()

    def form_valid(self, form):
        user_ids = self.users_in_same_company
        if user_ids and self.get_object().id not in user_ids:
            return self.access_denied
        else:
            return super().form_valid(form)


class EsaniAdminUserDetailView(UserDetailView):
    model = User
    template_name = "esani_pantportal/user/view.html"
    fields = (
        "username",
        "first_name",
        "last_name",
        "email",
        "phone",
        "approved",
    )
    required_groups = ["EsaniAdmins"]


class CompanyAdminUserDetailView(UserDetailView):
    model = User
    template_name = "esani_pantportal/user/view.html"
    fields = (
        "username",
        "first_name",
        "last_name",
        "email",
        "phone",
    )


class MultipleProductRegisterView(PermissionRequiredMixin, FormView):
    template_name = "esani_pantportal/product/import.html"
    form_class = MultipleProductRegisterForm
    required_permissions = ["esani_pantportal.add_product"]

    def form_valid(self, form):
        if not self.has_permissions:
            return self.access_denied

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
