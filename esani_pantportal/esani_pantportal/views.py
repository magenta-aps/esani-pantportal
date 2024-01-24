# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
import datetime
import logging
from functools import cached_property
from io import BytesIO
from typing import Any, Dict
from urllib.parse import unquote

import pandas as pd
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.db.models import Case, F, Q, Value, When
from django.db.models.functions import Coalesce, Concat
from django.forms import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect
from django.template import loader
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
    View,
)
from project.settings import DEFAULT_FROM_EMAIL
from simple_history.utils import bulk_update_with_history, update_change_reason

from esani_pantportal.forms import (
    ChangePasswordForm,
    DepositPayoutItemFilterForm,
    MultipleProductRegisterForm,
    NewsEmailForm,
    PantPortalAuthenticationForm,
    ProductFilterForm,
    ProductRegisterForm,
    ProductUpdateForm,
    RefundMethodFilterForm,
    RefundMethodRegisterForm,
    RegisterBranchUserMultiForm,
    RegisterCompanyUserMultiForm,
    RegisterEsaniUserForm,
    RegisterKioskUserMultiForm,
    SetPasswordForm,
    UpdateBranchForm,
    UpdateCompanyForm,
    UpdateKioskForm,
    UserFilterForm,
    UserUpdateForm,
)
from esani_pantportal.models import (
    ADMIN_GROUPS,
    BRANCH_USER,
    COMPANY_USER,
    KIOSK_USER,
    BranchUser,
    Company,
    CompanyBranch,
    CompanyUser,
    DepositPayoutItem,
    EsaniUser,
    ImportJob,
    Kiosk,
    KioskUser,
    Product,
    RefundMethod,
    User,
)
from esani_pantportal.templatetags.pant_tags import danish, material, shape, user_type
from esani_pantportal.util import (
    add_parameters_to_url,
    default_dataframe,
    float_to_string,
    remove_parameter_from_url,
)
from esani_pantportal.view_mixins import PermissionRequiredMixin

logger = logging.getLogger(__name__)


class AboutView(TemplateView):
    template_name = "esani_pantportal/about.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["version"] = settings.VERSION
        return context


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
        self.object._change_reason = "Oprettet"
        self.object.created_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["product_constraints"] = settings.PRODUCT_CONSTRAINTS
        context["barcodes"] = [product.barcode for product in Product.objects.all()]
        return context

    def get_success_url(self):
        return reverse("pant:product_register_success")


class RefundMethodRegisterView(PermissionRequiredMixin, CreateView):
    model = RefundMethod
    form_class = RefundMethodRegisterForm
    template_name = "esani_pantportal/refund_method/form.html"
    required_permissions = ["esani_pantportal.add_refundmethod"]

    def get_success_url(self):
        return reverse("pant:refund_method_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        user = self.request.user

        if user.user_type == KIOSK_USER:
            kwargs["kiosks"] = [user.branch]
            kwargs["branches"] = []
        elif user.user_type == BRANCH_USER:
            kwargs["kiosks"] = []
            kwargs["branches"] = [user.branch]
        elif user.user_type == COMPANY_USER:
            kwargs["kiosks"] = []
            kwargs["branches"] = list(user.company.branches.all())

        return kwargs


class RegisterEsaniUserView(PermissionRequiredMixin, CreateView):
    model = EsaniUser
    form_class = RegisterEsaniUserForm
    template_name = "esani_pantportal/user/esani_user/form.html"
    required_permissions = ["esani_pantportal.add_esaniuser"]

    def get_success_url(self):
        return reverse("pant:user_register_success")

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.set_password(form.cleaned_data["password"])
        self.object.save()
        self.object.groups.add(Group.objects.get(name="EsaniAdmins"))
        return super().form_valid(form)


class _PrevalidateCreateView(CreateView):
    def post(self, request, *args, **kwargs):
        subform_name = request.POST.get("prevalidate")
        if subform_name:
            subform_class = self.form_class.form_classes.get(subform_name)
            if subform_class:
                form_data = {
                    key.replace("%s-" % subform_name, ""): val
                    for key, val in request.POST.items()
                }
                subform = subform_class(form_data)
                return JsonResponse({"errors": subform.errors})
        return super().post(request, *args, **kwargs)


class RegisterBranchUserView(_PrevalidateCreateView):
    model = BranchUser
    form_class = RegisterBranchUserMultiForm
    template_name = "esani_pantportal/user/branch_user/form.html"

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)

        # dict of companies and which shops they own
        branch_dict = {}
        for company in Company.objects.all():
            branches = company.branches.all()
            branch_dict[company.pk] = [b.pk for b in branches]

        context_data["branch_dict"] = branch_dict

        return context_data


class RegisterBranchUserPublicView(RegisterBranchUserView):
    def get_success_url(self):
        return reverse("pant:login")


class RegisterBranchUserAdminView(PermissionRequiredMixin, RegisterBranchUserView):
    required_permissions = ["esani_pantportal.add_branchuser"]

    def get_success_url(self):
        return reverse("pant:user_register_success")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["show_admin_flag"] = True
        kwargs["allow_multiple_admins"] = True
        kwargs["show_captcha"] = False
        kwargs["approved"] = True
        if self.request.user.user_type == BRANCH_USER:
            kwargs["company"] = self.request.user.branch.company
            kwargs["branch"] = self.request.user.branch
        elif self.request.user.user_type == COMPANY_USER:
            kwargs["company"] = self.request.user.company
        return kwargs


class RegisterCompanyUserView(_PrevalidateCreateView):
    model = CompanyUser
    form_class = RegisterCompanyUserMultiForm
    template_name = "esani_pantportal/user/company_user/form.html"


class RegisterCompanyUserPublicView(RegisterCompanyUserView):
    def get_success_url(self):
        return reverse("pant:login")


class RegisterCompanyUserAdminView(PermissionRequiredMixin, RegisterCompanyUserView):
    required_permissions = ["esani_pantportal.add_companyuser"]

    def get_success_url(self):
        return reverse("pant:user_register_success")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["show_admin_flag"] = True
        kwargs["show_captcha"] = False
        kwargs["allow_multiple_admins"] = True
        kwargs["approved"] = True
        if self.request.user.user_type == COMPANY_USER:
            kwargs["company"] = self.request.user.company
        return kwargs


class RegisterKioskUserView(_PrevalidateCreateView):
    model = KioskUser
    form_class = RegisterKioskUserMultiForm
    template_name = "esani_pantportal/user/kiosk_user/form.html"


class RegisterKioskUserPublicView(RegisterKioskUserView):
    def get_success_url(self):
        return reverse("pant:login")


class RegisterKioskUserAdminView(PermissionRequiredMixin, RegisterKioskUserView):
    required_permissions = ["esani_pantportal.add_kioskuser"]

    def get_success_url(self):
        return reverse("pant:user_register_success")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["show_admin_flag"] = True
        kwargs["show_captcha"] = False
        kwargs["allow_multiple_admins"] = True
        kwargs["approved"] = True
        if self.request.user.user_type == KIOSK_USER:
            kwargs["branch"] = self.request.user.branch
        return kwargs


class SearchView(LoginRequiredMixin, FormView, ListView):
    paginate_by = 20
    select_template = None
    annotations = {}
    search_fields_exact = []

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
        return {k: getattr(v, "pk", v) for k, v in search_data.items()}

    def annotate_field(self, string):
        if string + "_annotation" in self.annotations:
            return string + "_annotation"
        else:
            return string

    def get_queryset(self):
        data = self.search_data
        qs = self.model.objects.all().annotate(**self.annotations)

        # django-filter kan gøre det samme, men der er ingen grund til at
        # overkomplicere tingene

        for field in self.search_fields_exact:  # præcist match
            if data.get(field, None) not in (None, ""):  # False er en gyldig værdi
                qs = qs.filter(**{field: data[field]})

        # indehold alle ord, case insensitive
        for field in self.search_fields:
            if data.get(field, None) not in (None, ""):
                qs = qs.filter(
                    **{
                        self.annotate_field(field) + "__icontains": part
                        for part in data[field].split()
                        if part
                    }
                )

        sort = data.get("sort", None)
        if sort:
            reverse = "-" if data.get("order", None) == "desc" else ""
            order_args = [
                f"{reverse}{s}" for s in self.annotate_field(sort).split("_or_")
            ]
            qs = qs.order_by(*order_args)

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
            select_template=self.select_template,
        )
        items = [
            self.item_to_json_dict(item, context, index)
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
        self, item_obj: Any, context: Dict[str, Any], index: int
    ) -> Dict[str, Any]:
        item = model_to_dict(item_obj)
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
        if key == "select":
            return loader.render_to_string(
                self.select_template,
                {"item": item, **context},
                self.request,
            )
        return item[key]


class ProductSearchView(SearchView):
    template_name = "esani_pantportal/product/list.html"
    actions_template = "esani_pantportal/product/actions.html"
    select_template = "esani_pantportal/product/select.html"
    model = Product
    form_class = ProductFilterForm
    annotations = {"file_name": F("import_job__file_name")}

    search_fields = ["product_name", "barcode"]
    search_fields_exact = ["approved", "import_job"]

    def item_to_json_dict(self, item_obj, context, index):
        json_dict = super().item_to_json_dict(item_obj, context, index)
        json_dict["select"] = self.map_value(model_to_dict(item_obj), "select", context)
        json_dict["file_name"] = item_obj.file_name or "-"
        return json_dict

    def map_value(self, item, key, context):
        value = super().map_value(item, key, context)

        if key == "approved":
            value = _("Ja") if value else _("Nej")
        elif key == "material":
            value = material(value)
        elif key == "shape":
            value = shape(value)
        elif key == "danish":
            value = danish(value)
        elif "_date" in key and value:
            value = value.strftime("%-d. %b %Y")

        return value or "-"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if self.request.user.is_esani_admin:
            # Statistics on approved products for ESANI admins
            # Other users don't need to see this because they cannot approve anyway.
            context["approved_products"] = Product.objects.filter(approved=True).count()
            context["pending_products"] = Product.objects.filter(approved=False).count()
            context["can_edit_multiple"] = True
        return context


class RefundMethodSearchView(PermissionRequiredMixin, SearchView):
    template_name = "esani_pantportal/refund_method/list.html"
    actions_template = "esani_pantportal/refund_method/actions.html"
    model = RefundMethod
    form_class = RefundMethodFilterForm
    required_permissions = ["esani_pantportal.view_refundmethod"]

    search_fields = ["serial_number"]

    def map_value(self, item, key, context):
        value = super().map_value(item, key, context)

        if key in ["branch", "kiosk"]:
            if value and key == "branch":
                value = CompanyBranch.objects.get(pk=int(value)).name
            elif value and key == "kiosk":
                value = Kiosk.objects.get(pk=int(value)).name
            else:
                value = ""
        elif key == "compensation":
            value = float_to_string(value) + " øre"

        return value or ""

    def item_to_json_dict(self, *args, **kwargs):
        json_dict = super().item_to_json_dict(*args, **kwargs)
        json_dict["branch_or_kiosk"] = json_dict["branch"] or json_dict["kiosk"]
        return json_dict

    def get_queryset(self):
        qs = super().get_queryset()
        data = self.search_data

        branch_qs = self.model.objects.none()
        for field in ["branch__name", "kiosk__name"]:
            if data.get(field, None) not in (None, ""):
                branch_qs = branch_qs | self.model.objects.all().filter(
                    **{
                        field + "__icontains": part
                        for part in data[field].split()
                        if part
                    }
                )

        if branch_qs:
            qs = qs & branch_qs

        # Only allow branch/company/kiosk users to see machines in their own company
        user = self.request.user
        if user.user_type == KIOSK_USER:
            qs = qs.filter(kiosk__pk=user.branch.pk)
        elif user.user_type == BRANCH_USER:
            qs = qs.filter(branch__pk=user.branch.pk)
        elif user.user_type == COMPANY_USER:
            qs = qs.filter(branch__company__pk=user.company.pk)
        return qs


class UserSearchView(PermissionRequiredMixin, SearchView):
    template_name = "esani_pantportal/user/list.html"
    actions_template = "esani_pantportal/user/actions.html"
    model = User
    form_class = UserFilterForm
    required_permissions = ["esani_pantportal.view_user"]

    search_fields = ["username", "user_type", "branch", "company"]
    search_fields_exact = ["approved"]
    annotations = {
        "is_admin_annotation": Q(groups__name__in=ADMIN_GROUPS),
        "branch_annotation": Case(
            When(
                Q(user_type=BRANCH_USER),
                then=F("branchuser__branch__name"),
            ),
            When(
                Q(user_type=KIOSK_USER),
                then=F("kioskuser__branch__name"),
            ),
            default=Value("-"),
        ),
        "company_annotation": Case(
            When(
                Q(user_type=COMPANY_USER),
                then=F("companyuser__company__name"),
            ),
            When(
                Q(user_type=BRANCH_USER),
                then=F("branchuser__branch__company__name"),
            ),
            default=Value("-"),
        ),
        "full_name": Concat("first_name", Value(" "), "last_name"),
    }

    def item_to_json_dict(self, item_obj, context, index):
        json_dict = super().item_to_json_dict(item_obj, context, index)
        user_is_admin = item_obj.is_admin_annotation
        json_dict["full_name"] = item_obj.full_name
        json_dict["branch"] = item_obj.branch_annotation
        json_dict["company"] = item_obj.company_annotation
        json_dict["is_admin"] = _("Ja") if user_is_admin else _("Nej")
        return json_dict

    def map_value(self, item, key, context):
        value = super().map_value(item, key, context)

        if key == "approved":
            value = _("Ja") if value else _("Nej")
        elif key == "groups":
            value = str(value)
        elif key == "user_type":
            value = user_type(value)
        return value

    def get_queryset(self):
        qs = super().get_queryset()

        # Only allow branch/company/kiosk users to see users of their own branch/company
        user_ids = self.users_in_same_company
        if user_ids:
            qs = qs.filter(pk__in=user_ids)
        return qs


class BaseCompanyUpdateView(PermissionRequiredMixin, UpdateView):
    template_name = "esani_pantportal/company/form.html"

    def get_success_url(self):
        return unquote(self.request.GET.get("back", ""))


class CompanyUpdateView(BaseCompanyUpdateView):
    required_permissions = ["esani_pantportal.change_company"]
    model = Company
    form_class = UpdateCompanyForm

    def check_permissions(self):
        if self.request.user.is_esani_admin or self.same_company:
            return super().check_permissions()
        else:
            return self.access_denied


class CompanyBranchUpdateView(BaseCompanyUpdateView):
    required_permissions = ["esani_pantportal.change_companybranch"]
    model = CompanyBranch
    form_class = UpdateBranchForm

    def check_permissions(self):
        company = self.request.user.company
        if self.request.user.is_esani_admin or self.same_branch:
            return super().check_permissions()
        elif company and self.get_object() in company.branches.all():
            return super().check_permissions()
        else:
            return self.access_denied


class KioskUpdateView(BaseCompanyUpdateView):
    required_permissions = ["esani_pantportal.change_kiosk"]
    model = Kiosk
    form_class = UpdateKioskForm

    def check_permissions(self):
        if self.request.user.is_esani_admin or self.same_branch:
            return super().check_permissions()
        else:
            return self.access_denied


class DepositPayoutSearchView(PermissionRequiredMixin, ListView, FormView):
    template_name = "esani_pantportal/deposit_payout/list.html"
    context_object_name = "items"
    model = DepositPayoutItem
    form_class = DepositPayoutItemFilterForm
    required_permissions = ["esani_pantportal.view_depositpayout"]
    paginate_by = 20

    _reserved = ("sort", "order", "page", "size")

    def post(self, request, *args, **kwargs):
        # This is a dummy implementation which demonstrates how to process POST
        # requests for this view.
        # If POST contains "selection=all", process all objects in queryset.
        # If POST contains one more item IDs in "id", process only the objects given by
        # those IDs.
        if request.POST.get("selection", "") == "all":
            return JsonResponse({"all": True, "count": self.get_queryset().count()})
        else:
            ids = [int(id) for id in request.POST.getlist("id")]
            return JsonResponse(
                {"all": False, "count": self.get_queryset().filter(id__in=ids).count()}
            )
        return HttpResponseRedirect(".")  # pragma: no cover

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related(
            "company_branch__company", "kiosk", "product", "deposit_payout"
        )

        # Annotate queryset to enable sorting on expressions
        qs = qs.annotate(
            source=Coalesce("company_branch__company__name", "kiosk__name"),
        )

        # Apply filters
        filters = {
            name: val
            for name, val in self.request.GET.items()
            if (name not in self._reserved) and (val not in ("", None))
        }
        if filters:
            qs = qs.filter(**filters)

        # Apply sort order
        sort_field = self.request.GET.get("sort")
        sort_order = self.request.GET.get("order")
        if sort_field and sort_order:
            qs = qs.order_by("%s%s" % ("-" if sort_order == "desc" else "", sort_field))

        return qs

    def get_paginate_by(self, queryset):
        return self._get_page_size()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_size"] = self._get_page_size()
        context["page_number"] = self.request.GET.get("page", 1)
        context["sort_name"] = self.request.GET.get("sort", "")
        context["sort_order"] = self.request.GET.get("order", "")
        return context

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs.update({"data": self.request.GET})
        return form_kwargs

    def _get_page_size(self):
        return int(self.request.GET.get("size", self.paginate_by))


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


class ProductUpdateView(UpdateViewMixin):
    model = Product
    template_name = "esani_pantportal/product/view.html"
    form_class = ProductUpdateForm

    def check_permissions(self):
        if self.request.method == "GET":
            self.required_permissions = ["esani_pantportal.view_product"]
        else:
            self.required_permissions = ["esani_pantportal.change_product"]

        return super().check_permissions()

    def get_latest_relevant_history(self):
        return self.object.history.filter(
            Q(history_change_reason="Oprettet")
            | Q(history_change_reason="Godkendt")
            | Q(  # NOTE: Gjort Inaktiv not yet implemented
                history_change_reason="Gjort Inaktiv"
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["back_url"] = self.request.GET.get("back", "")
        if context["object"].approved and not self.request.user.is_esani_admin:
            context["can_edit"] = False
        qs = self.get_latest_relevant_history()
        if qs:
            context["latest_history"] = qs.order_by("-history_date")[0]
        return context

    def form_valid(self, form):
        if not self.request.user.is_esani_admin:
            approved = self.get_object().approved
            if approved:
                return self.access_denied
            if not self.same_workplace:
                return self.access_denied
            if "approved" in form.changed_data:
                return self.access_denied
        return super().form_valid(form)

    def get_success_url(self):
        back_url = unquote(self.request.GET.get("back", ""))
        approved = self.get_object().approved
        latest_history_qs = self.get_latest_relevant_history()
        recently_approved = bool(
            latest_history_qs
            and latest_history_qs.order_by("-history_date")[0].history_change_reason
            == "Godkendt"
        )
        if approved:
            if recently_approved:
                update_change_reason(self.get_object(), "Ændret")
                return self.request.get_full_path()
            else:
                update_change_reason(self.get_object(), "Godkendt")
            if back_url:
                return remove_parameter_from_url(back_url, "json")
            else:
                return reverse("pant:product_list")
        else:
            if recently_approved:
                update_change_reason(self.get_object(), "Gjort Inaktiv")
            else:
                update_change_reason(self.get_object(), "Ændret")
            return self.request.get_full_path()


class ProductHistoryView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = "esani_pantportal/product/history.html"
    context_object_name = "historical_product"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["histories"] = self.object.history.filter(
            Q(history_change_reason="Oprettet")
            | Q(history_change_reason="Godkendt")
            | Q(history_change_reason="Gjort Inaktiv")
        ).order_by("-history_date")
        return context


class SameCompanyMixin(PermissionRequiredMixin):
    def check_permissions(self):
        user = self.get_object()
        if not self.request.user.is_esani_admin:
            user_ids = self.users_in_same_company
            if user.id not in user_ids:
                return self.access_denied

        user_model_name = user.user_profile._meta.model_name

        if self.request.method == "GET":
            self.required_permissions = [f"esani_pantportal.view_{user_model_name}"]
        else:
            self.required_permissions = [f"esani_pantportal.change_{user_model_name}"]

        return super().check_permissions()


class UserUpdateView(SameCompanyMixin, UpdateViewMixin):
    model = User
    template_name = "esani_pantportal/user/view.html"
    form_class = UserUpdateForm

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        context_data["user"] = self.request.user
        context_data["profile"] = (
            context_data["object"]
            if context_data["form"].is_valid()
            else User.objects.get(pk=context_data["object"].pk)
        ).user_profile

        common_attributes = [
            "name",
            "address",
            "postal_code",
            "municipality",
            "city",
            "phone",
        ]
        branch_attributes = ["customer_id", "qr_compensation"]
        company_attributes = ["cvr"]
        kiosk_attributes = ["cvr"]

        context_data["branch_info_attributes"] = common_attributes + branch_attributes
        if context_data["object"].user_type == KIOSK_USER:
            context_data["branch_info_attributes"].extend(kiosk_attributes)
        context_data["company_info_attributes"] = common_attributes + company_attributes
        return context_data

    def get_success_url(self):
        return self.request.get_full_path()

    def form_valid(self, form):
        if "approved" in form.changed_data and not self.request.user.is_esani_admin:
            return self.access_denied
        else:
            return super().form_valid(form)


class SetPasswordView(SameCompanyMixin, UpdateView):
    template_name = "esani_pantportal/user/password/set.html"
    model = User
    form_class = SetPasswordForm

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        context_data["user"] = self.request.user
        return context_data

    def get_success_url(self):
        kwargs = {"pk": self.object.pk}
        return reverse("pant:user_view", kwargs=kwargs)


class UserDeleteView(SameCompanyMixin, DeleteView):
    model = User

    def get_success_url(self):
        return reverse("pant:user_list") + "?delete_success=1"

    def form_valid(self, form):
        if self.object.id == self.request.user.id:
            # Hvis en bruger forsøger at fjerne sig selv: tilbage til login skærm
            super().form_valid(form)
            return redirect(reverse("pant:login"))
        else:
            return super().form_valid(form)


class ChangePasswordView(PermissionRequiredMixin, PasswordChangeView):
    template_name = "esani_pantportal/user/password/change.html"
    form_class = ChangePasswordForm

    def get_success_url(self):
        kwargs = {"pk": self.request.user.pk}
        return reverse("pant:user_view", kwargs=kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        update_session_auth_hash(self.request, form.user)
        return response


class MultipleProductRegisterView(PermissionRequiredMixin, FormView):
    template_name = "esani_pantportal/product/import.html"
    form_class = MultipleProductRegisterForm
    required_permissions = ["esani_pantportal.add_product"]

    def form_valid(self, form):
        if not self.has_permissions:
            return self.access_denied

        products = form.df.rename(form.rename_dict, axis=1).to_dict(orient="records")
        existing_barcodes = Product.objects.values_list("barcode", flat=True).distinct()
        job = ImportJob(
            imported_by=self.request.user,
            file_name=form.filename,
            date=datetime.datetime.now(),
        )
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
                product.import_job = job
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

        job.save()
        for product in products_to_save:
            product._change_reason = "Oprettet"
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
            content_type = (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            response = HttpResponse(
                b.getvalue(),
                content_type=content_type,
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


class CsvProductsView(CsvTemplateView):
    def get(self, request, approved, *args, **kwargs):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        material_type_map = {
            "P": "PET",
            "A": "Aluminium",
            "S": "Steel",
            "G": "Glass",
        }

        column_map = {
            "barcode": "Barcode",
            "product_name": "ProductName",
            "material": "MaterialType",
            "height": "Height",
            "diameter": "Diameter",
            "weight": "Weight",
            "capacity": "Capacity",
            "shape": "Shape",
        }

        shape_map = {"F": "Bottle", "A": "Other", "D": "Other"}
        approval_map = {True: "Approved", False: "Pending"}

        if bool(approved):
            qs = Product.objects.filter(approved=True)
            filename = f"{timestamp}_product_list.csv"
            all_products = list(
                qs.values(
                    "barcode",
                    "product_name",
                    "material",
                    "height",
                    "diameter",
                    "weight",
                    "capacity",
                    "shape",
                )
            )
        else:
            column_map["approved"] = "Approved by ESANI A/S"
            qs = Product.objects.all()
            filename = f"{timestamp}_full_product_list.csv"
            all_products = list(
                qs.values(
                    "barcode",
                    "product_name",
                    "material",
                    "height",
                    "diameter",
                    "weight",
                    "capacity",
                    "shape",
                    "approved",
                )
            )

        df = pd.DataFrame(all_products)
        df = df.replace(
            {
                "material": material_type_map,
                "shape": shape_map,
            }
        )
        if not bool(approved):
            df = df.replace({"approved": approval_map})
        df = df.rename(column_map, axis=1)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f"attachment; filename={filename}"
        df.to_csv(path_or_buf=response, sep=";", index=False)

        return response


class ProductDeleteView(PermissionRequiredMixin, DeleteView):
    model = Product
    required_permissions = ["esani_pantportal.delete_product"]

    def form_valid(self, form):
        if not self.request.user.is_esani_admin and not self.same_workplace:
            return self.access_denied
        return super().form_valid(form)

    def get_success_url(self):
        back_url = unquote(self.request.GET.get("back", ""))
        return_url = (
            remove_parameter_from_url(back_url, "json")
            if back_url
            else reverse("pant:product_list")
        )
        return add_parameters_to_url(return_url, {"delete_success": 1})


class RefundMethodDeleteView(PermissionRequiredMixin, DeleteView):
    model = RefundMethod
    required_permissions = ["esani_pantportal.delete_refundmethod"]

    def form_valid(self, form):
        if not self.request.user.is_esani_admin and not self.same_workplace:
            return self.access_denied
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("pant:refund_method_list")


class NewsEmailView(PermissionRequiredMixin, FormView):
    form_class = NewsEmailForm
    template_name = "esani_pantportal/email/form.html"
    required_permissions = ["esani_pantportal.add_sentemail"]

    def form_valid(self, form):
        to_list = [user.email for user in User.objects.filter(newsletter=True)]
        data = form.cleaned_data

        msg = EmailMultiAlternatives(
            subject=data["subject"],
            body=data["body"],
            from_email=DEFAULT_FROM_EMAIL,
            to=to_list,
            reply_to=[DEFAULT_FROM_EMAIL],
        )
        if settings.ENVIRONMENT != "production":
            msg.subject += " NOTE: THIS IS A TEST!"
        #    msg.metadata = {"o:testmode": True}
        #    msg.headers = {"o:testmode": True}
        msg.tags = ["newsletter"]
        # NOTE: To include html images
        # Include an inline image in the html:
        # logo_cid = attach_inline_image_file(msg, "path/to/file")
        # html = """<img alt="Logo" src="cid:{logo_cid}">
        #          <p>Please <a href="https://example.com/activate">activate</a>
        #          your account</p>""".format(logo_cid=logo_cid)
        # msg.attach_alternative(html, "text/html")
        msg.send()
        logger.info("Email succesfully sent")
        messages.add_message(
            self.request,
            messages.INFO,
            "Nyhedsbrevet blev sendt",
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("pant:send_newsletter")


class UpdateProductViewPreferences(UpdateView):
    model = User
    fields = [
        "show_material",
        "show_shape",
        "show_danish",
        "show_height",
        "show_diameter",
        "show_weight",
        "show_capacity",
        "show_approval_date",
        "show_creation_date",
        "show_file_name",
    ]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        obj = self.get_object()

        # Set initial values
        data = kwargs["data"].copy()
        for field in [f for f in self.fields if f not in data]:
            data[field] = getattr(obj, field)
        kwargs["data"] = data
        return kwargs

    def get_success_url(self):
        return reverse("pant:product_list")


class MultipleProductApproveView(View, PermissionRequiredMixin):
    def post(self, request, *args, **kwargs):
        if not self.request.user.is_esani_admin:
            return self.access_denied

        ids = [int(id) for id in self.request.POST.getlist("ids[]")]
        products = Product.objects.filter(id__in=ids)
        for product in products:
            product.approved = True

        bulk_update_with_history(
            products, Product, ["approved"], default_change_reason="Godkendt"
        )

        return JsonResponse({"status_code": 200})


class MultipleProductDeleteView(View, PermissionRequiredMixin):
    def post(self, request, *args, **kwargs):
        if not self.request.user.is_esani_admin:
            return self.access_denied

        ids = [int(id) for id in self.request.POST.getlist("ids[]")]
        products = Product.objects.filter(id__in=ids)

        if products.filter(approved=True):
            response = JsonResponse({"error": _("Godkendte produkter må ikke fjernes")})
            response.status_code = 403
            return response

        products_to_delete = products.filter(deposit_items__isnull=True)
        protected_products = products.difference(products_to_delete)

        deleted_products_count = products_to_delete.count()
        protected_products_count = protected_products.count()

        protected_products_message = _(
            "Kunne ikke fjerne følgende {amount} produkter: {products}; {reason}"
        ).format(
            amount=protected_products_count,
            products=", ".join([p.product_name for p in protected_products]),
            reason=_("Produkt er tilknyttet en eller flere udbetalings-objekter"),
        )

        products_to_delete.delete()
        return JsonResponse(
            {
                "status_code": 200,
                "deleted_products": deleted_products_count,
                "protected_products": protected_products_count,
                "protected_products_message": protected_products_message,
            }
        )
