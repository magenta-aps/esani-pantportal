# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
import datetime
import logging
import os
import sys
from functools import cache, cached_property
from io import BytesIO
from typing import Any
from urllib.parse import quote
from uuid import UUID

import pandas as pd
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.contrib.auth.views import LogoutView, PasswordChangeView
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.db.models import (
    Aggregate,
    BooleanField,
    Case,
    Count,
    ExpressionWrapper,
    F,
    FloatField,
    Max,
    Min,
    OuterRef,
    PositiveIntegerField,
    Q,
    QuerySet,
    Subquery,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Coalesce, Concat
from django.forms import model_to_dict
from django.http import (
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseNotFound,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import redirect
from django.templatetags.l10n import localize
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    TemplateView,
    UpdateView,
    View,
)
from django_fsm import can_proceed
from django_otp import devices_for_user
from django_stubs_ext import StrPromise
from project.settings import DEFAULT_FROM_EMAIL
from simple_history.utils import bulk_update_with_history
from two_factor.views import LoginView, SetupView
from xlsxwriter import Workbook
from xlsxwriter.worksheet import Worksheet

from esani_pantportal.exports.uniconta.exports import CreditNoteExport, DebtorExport
from esani_pantportal.forms import (
    ChangePasswordForm,
    CompanyFilterForm,
    DepositPayoutForm,
    DepositPayoutItemFilterForm,
    DepositPayoutItemFormSet,
    GenerateQRForm,
    MultipleProductRegisterForm,
    NewsEmailForm,
    PantPortalAuthenticationForm,
    PantPortalAuthenticationTokenForm,
    ProductFilterForm,
    ProductRegisterForm,
    ProductUpdateForm,
    QRBagFilterForm,
    RegisterCompanyBranchUserMultiForm,
    RegisterCompanyUserMultiForm,
    RegisterEsaniUserForm,
    RegisterKioskUserMultiForm,
    ReverseVendingMachineFilterForm,
    ReverseVendingMachineRegisterForm,
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
    ESANI_USER,
    KIOSK_USER,
    AbstractCompany,
    BranchUser,
    Company,
    CompanyBranch,
    CompanyListViewPreferences,
    CompanyUser,
    DepositPayout,
    DepositPayoutItem,
    ERPCreditNoteExport,
    ERPProductMapping,
    EsaniUser,
    ImportJob,
    Kiosk,
    KioskUser,
    Product,
    ProductListViewPreferences,
    ProductState,
    QRBag,
    QRStatus,
    ReverseVendingMachine,
    User,
    UserListViewPreferences,
)
from esani_pantportal.templatetags.pant_tags import (
    branch_type,
    company_type,
    danish,
    material,
    shape,
    user_type,
)
from esani_pantportal.types import ANNOTATION, BOOTSTRAP_BUTTON, PREFERENCES_CLASS
from esani_pantportal.util import (
    add_parameters_to_url,
    default_dataframe,
    float_to_string,
    get_back_url,
)
from esani_pantportal.view_mixins import (
    FormWithFormsetView,
    IsAdminMixin,
    PermissionRequiredMixin,
    UpdateViewMixin,
)

logger = logging.getLogger(__name__)


class AboutView(LoginRequiredMixin, TemplateView):
    template_name = "esani_pantportal/about.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["version"] = settings.VERSION
        return context


class PantportalLoginView(LoginView):
    AUTH_STEP = "auth"
    TOKEN_STEP = "token"

    form_list = (
        (AUTH_STEP, PantPortalAuthenticationForm),
        (TOKEN_STEP, PantPortalAuthenticationTokenForm),
    )

    def get_form_list(self):
        form_list = super().get_form_list()

        # In case we wish to bypass 2FA we should never go to the token step.
        if settings.BYPASS_2FA and self.TOKEN_STEP in form_list:
            del form_list[self.TOKEN_STEP]

        return form_list

    def get_form(self, step=None, data=None, files=None):
        """
        Returns the form for the step. Overwritten because the default method hard-codes
        the form for the token-step as AuthenticationTokenForm instead of
        PantPortalAuthenticationTokenForm
        """
        if step is None:
            step = self.steps.current

        form_class = self.get_form_list()[step]
        kwargs = self.get_form_kwargs(step)
        kwargs.update(
            {
                "data": data,
                "files": files,
                "prefix": self.get_form_prefix(step, form_class),
                "initial": self.get_form_initial(step),
            }
        )

        return form_class(**kwargs)


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
        try:
            with transaction.atomic():
                return super().form_valid(form)
        except IntegrityError:
            # Expected error: 'duplicate key value violates unique constraint
            # "barcode_unique_when_not_deleted"'.
            messages.add_message(
                self.request,
                messages.ERROR,
                _("Der eksisterer allerede et produkt med denne stregkode"),
            )
            return super().form_invalid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["product_constraints"] = settings.PRODUCT_CONSTRAINTS
        context["barcodes"] = {
            product.barcode: {
                "state": product.state,
                "rejection": product.rejection,
            }
            for product in Product.objects.exclude(state=ProductState.DELETED)
        }
        return context

    def get_success_url(self):
        return reverse("pant:product_register_success")


class ReverseVendingMachineRegisterView(
    IsAdminMixin, PermissionRequiredMixin, CreateView
):
    model = ReverseVendingMachine
    form_class = ReverseVendingMachineRegisterForm
    template_name = "esani_pantportal/reverse_vending_machine/form.html"
    required_permissions = ["esani_pantportal.add_reversevendingmachine"]

    def get_success_url(self):
        return reverse("pant:rvm_list")

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


class RegisterBranchUserView(IsAdminMixin, _PrevalidateCreateView):
    model = BranchUser
    form_class = RegisterCompanyBranchUserMultiForm
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


class RegisterCompanyUserView(IsAdminMixin, _PrevalidateCreateView):
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


class RegisterKioskUserView(IsAdminMixin, _PrevalidateCreateView):
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


class SearchView(LoginRequiredMixin, FormView):
    paginate_by = 100
    annotations: dict[str, ANNOTATION] = {}
    search_fields_exact: list[str] = []
    search_fields: list[str] = []
    fixed_columns: dict[str, StrPromise] = {}
    preferences_class: PREFERENCES_CLASS | None = None
    can_edit_multiple = False
    actions: dict[StrPromise, BOOTSTRAP_BUTTON] = {}

    def get(self, request, *args, **kwargs):
        self.form = self.get_form()
        if self.form.is_valid():
            if self.request.GET.get("format", None) == "excel":
                return self.get_queryset_as_excel_file_download(self.get_queryset())
            return self.form_valid(self.form)
        else:
            return self.form_invalid(self.form)

    def get_action_html(self, item, label, button_class):
        url = self.get_action_url(item, label)
        return f'<a href="{url}" class="{button_class}">{label}</a>'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method == "GET":
            kwargs["data"] = self.request.GET
        return kwargs

    @cached_property
    def search_data(self):
        data = self.form.cleaned_data
        search_data = {"offset": 0}

        if data.get("json"):
            # limit = None means "all data" when BootstrapTable is in charge.
            search_data["limit"] = data["limit"]
        else:
            # limit = None means "default value" when loading the page.
            search_data["limit"] = data["limit"] or self.paginate_by

        for key, value in data.items():
            if key not in ("json",) and value not in ("", None):
                if key in ("offset", "limit"):
                    value = int(value)
                search_data[key] = value
        if search_data["offset"] < 0:
            search_data["offset"] = 0
        if search_data["limit"] and search_data["limit"] < 1:
            search_data["limit"] = 1
        # // = Python floor division
        if search_data["limit"]:
            search_data["page_number"] = (
                search_data["offset"] // search_data["limit"]
            ) + 1
        else:
            search_data["page_number"] = 1

        return {k: getattr(v, "pk", v) for k, v in search_data.items()}

    @cache
    def annotate_field(self, string):
        annotation_dicts = [
            getattr(self, d) for d in dir(self) if d.endswith("annotations")
        ]

        for annotation_dict in annotation_dicts:
            if string + "_annotation" in annotation_dict:
                return string + "_annotation"
        return string

    def filter_qs(self, qs):
        data = self.search_data
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
        return qs

    def sort_qs(self, qs):
        data = self.search_data
        sort = data.get("sort", None)
        if sort:
            reverse = "-" if data.get("order", None) == "desc" else ""
            order_args = [
                f"{reverse}{s}" for s in self.annotate_field(sort).split("_or_")
            ]
            qs = qs.order_by(*order_args)
        return qs

    def get_queryset(self):
        qs = self.model.objects.all().annotate(**self.annotations)

        qs = self.filter_qs(qs)
        qs = self.sort_qs(qs)
        return qs

    def form_valid(self, form):
        qs = self.get_queryset()
        total = qs.count()
        offset = self.search_data["offset"]
        limit = self.search_data["limit"]
        items = qs[offset : offset + limit] if limit else qs[offset:]
        context = self.get_context_data(
            items=items,
            total=total,
            search_data=self.search_data,
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

    @cached_property
    def regular_columns(self):
        return [[key, value, True] for key, value in self.get_fixed_columns().items()]

    @cached_property
    def filterable_columns(self):
        if self.preferences_class:
            user = self.request.user
            meta = self.preferences_class._meta
            preferences, _ = self.preferences_class.objects.get_or_create(user=user)
            fields = [f for f in meta.fields if f.name.startswith("show_")]
            return [
                [
                    f.name.replace("show_", ""),
                    f.verbose_name,
                    getattr(preferences, f.name),
                ]
                for f in fields
            ]
        else:
            return []

    @cached_property
    def columns(self):
        return self.regular_columns + self.filterable_columns

    def get_fixed_columns(self):
        return self.fixed_columns

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["filterable_columns"] = self.filterable_columns
        context["columns"] = self.columns
        context["actions"] = self.actions
        context["data_defer_url"] = add_parameters_to_url(
            self.request.get_full_path(), {"json": 1}
        )
        context["can_edit_multiple"] = self.can_edit_multiple
        if self.preferences_class:
            context["preferences_class_name"] = self.preferences_class.__name__
        return context

    def get_fields(self, model=None):
        return [c[0] for c in self.columns]

    def model_to_dict(self, item_obj):
        model_dict = {"id": item_obj.id}
        for field in self.get_fields():
            value = getattr(item_obj, self.annotate_field(field), None)
            model_dict[field] = getattr(value, "pk", value)
        return model_dict

    def item_to_json_dict(
        self, item_obj: object, context: dict[str, object], index: int
    ) -> dict[str, object]:
        item = self.model_to_dict(item_obj)
        json_dict = {
            key: self.map_value(item, key, context) for key in list(item.keys())
        }
        if self.actions:
            json_dict["actions"] = " ".join(
                [
                    self.get_action_html(item_obj, action, button_class)
                    for action, button_class in self.actions.items()
                ]
            )

        if self.can_edit_multiple and hasattr(item_obj, "id"):
            json_dict["select"] = (
                f'<div class="p-1"><input type="checkbox" id="select_{item_obj.id}" '
                f'value="{item_obj.id}" /></div>'
            )

        return json_dict

    def map_value(self, item, key, context):
        return item[key]

    def get_view_name(self) -> str:
        # This is expected to be overridden by views implementing `SearchView`
        return gettext("Unavngivet")  # pragma: no cover

    def get_queryset_as_excel_file_download(self, queryset: QuerySet) -> HttpResponse:
        view_name: str = self.get_view_name()
        buf: BytesIO = BytesIO()
        workbook: Workbook = Workbook(
            buf,
            {
                "strings_to_urls": False,
                "default_date_format": "dd/mm/yy",
                "remove_timezone": True,
                "in_memory": True,
                "constant_memory": True,
            },
        )
        worksheet: Worksheet = workbook.add_worksheet(view_name)

        # Add handler for writing `UUID` values to Excel sheet
        def write_uuid(worksheet, row, col, uuid, cell_format=None):
            return worksheet.write_string(row, col, str(uuid), cell_format)

        worksheet.add_write_handler(UUID, write_uuid)

        # Write header (column names)
        for col, (field, name, enabled) in enumerate(self.columns):
            worksheet.write(0, col, str(name))

        # Write data (one row for each row in queryset)
        for row, obj in enumerate(queryset, start=1):
            data = {
                key: val
                for key, val in self.model_to_dict(obj).items()
                if key not in ("id", "pk")
            }
            for col, (key, val) in enumerate(data.items()):
                worksheet.write(row, col, val)

        worksheet.autofit()
        workbook.close()

        content_type = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response = HttpResponse(buf.getvalue(), content_type=content_type)
        response["Content-Disposition"] = f"attachment; filename={view_name}.xlsx"
        return response


class CompanySearchView(PermissionRequiredMixin, SearchView):
    template_name = "esani_pantportal/company/list.html"
    actions = {_("Vis"): "btn btn-sm btn-primary"}
    model = AbstractCompany
    form_class = CompanyFilterForm
    preferences_class = CompanyListViewPreferences

    external_customer_id = AbstractCompany.annotate_external_customer_id

    # The kiosk, company and company_branch annotation dicts must have the same keys
    # in the same order. Otherwise qs.union fails.
    kiosk_annotations = {
        "object_class_name": Value("Kiosk"),
        "object_class_name_verbose": Value("Kiosk"),
        "external_customer_id_annotation": external_customer_id(Kiosk),
        "company_type_annotation": Value("-"),
        "branch_type_annotation": F("branch_type"),
        "country_annotation": Value("-"),
        "invoice_company_branch_annotation": Value("-"),
        "location_id_annotation": F("location_id"),
        "customer_id_annotation": F("customer_id"),
        "qr_compensation_annotation": F("qr_compensation"),
        "company_annotation": Value("-"),
        "cvr_annotation": F("cvr"),
    }

    company_annotations = {
        "object_class_name": Value("Company"),
        "object_class_name_verbose": Value("Virksomhed"),
        "external_customer_id_annotation": external_customer_id(Company),
        "company_type_annotation": F("company_type"),
        "branch_type_annotation": Value("-"),
        "country_annotation": F("country"),
        "invoice_company_branch_annotation": Case(
            When(
                Q(invoice_company_branch=True),
                then=Value("Ja"),
            ),
            default=Value("Nej"),
        ),
        "location_id_annotation": Value(None, output_field=PositiveIntegerField()),
        "customer_id_annotation": Value(None, output_field=PositiveIntegerField()),
        "qr_compensation_annotation": Value(None, output_field=FloatField()),
        "company_annotation": Value("-"),
        "cvr_annotation": F("cvr"),
    }

    company_branch_annotations = {
        "object_class_name": Value("CompanyBranch"),
        "object_class_name_verbose": Value("Butik"),
        "external_customer_id_annotation": external_customer_id(CompanyBranch),
        "company_type_annotation": Value("-"),
        "branch_type_annotation": F("branch_type"),
        "country_annotation": Value("-"),
        "invoice_company_branch_annotation": Value("-"),
        "location_id_annotation": F("location_id"),
        "customer_id_annotation": F("customer_id"),
        "qr_compensation_annotation": F("qr_compensation"),
        "company_annotation": F("company__name"),
        "cvr_annotation": Value(None, output_field=PositiveIntegerField()),
    }

    search_fields = ["name", "address", "postal_code", "city"]
    search_fields_exact = ["object_class_name"]

    fixed_columns = {
        "external_customer_id": _("Kundenummer"),
        "name": _("Navn"),
        "object_class_name_verbose": _("Type"),
    }

    def get_action_url(self, item, *args):
        if item.object_class_name == "Company":
            url_name = "pant:company_update"
        elif item.object_class_name == "CompanyBranch":
            url_name = "pant:company_branch_update"
        elif item.object_class_name == "Kiosk":
            url_name = "pant:kiosk_update"

        base_url = reverse(url_name, kwargs={"pk": item.id})
        back_url = self.request.get_full_path()
        return add_parameters_to_url(base_url, {"back": quote(back_url)})

    def item_to_json_dict(self, item_obj, context, index):
        json_dict = super().item_to_json_dict(item_obj, context, index)
        json_dict["object_class_name"] = item_obj.object_class_name
        return json_dict

    def check_permissions(self):
        if not self.request.user.is_esani_admin:
            return self.access_denied
        else:
            return super().check_permissions()

    def get_queryset_field_list(self) -> list[str]:
        fields = super().get_fields()

        # Remove annotated fields
        for field in fields.copy():
            if self.annotate_field(field) != field:
                fields.remove(field)

        fields.remove("object_class_name_verbose")

        return fields

    def get_kiosk_queryset(self):
        return Kiosk.objects.only(*self.get_queryset_field_list()).annotate(
            **self.kiosk_annotations,
            **self.annotations,
        )

    def get_company_queryset(self):
        return Company.objects.only(*self.get_queryset_field_list()).annotate(
            **self.company_annotations,
            **self.annotations,
        )

    def get_company_branch_queryset(self):
        return CompanyBranch.objects.only(*self.get_queryset_field_list()).annotate(
            **self.company_branch_annotations,
            **self.annotations,
        )

    def get_union_queryset(self):
        qs0 = self.get_kiosk_queryset()
        qs1 = self.get_company_queryset()
        qs2 = self.get_company_branch_queryset()
        return qs0.union(qs1, qs2, all=True)

    def get_queryset(self):
        qs0 = self.filter_qs(self.get_kiosk_queryset())
        qs1 = self.filter_qs(self.get_company_queryset())
        qs2 = self.filter_qs(self.get_company_branch_queryset())
        union = qs0.union(qs1, qs2, all=True)
        return self.sort_qs(union.order_by("name"))

    def map_value(self, item, key, context):
        value = super().map_value(item, key, context)

        if key in ["object_class_name_verbose", "invoice_company_branch"]:
            value = _(value)
        elif key == "company_type":
            value = company_type(value)
        elif key == "branch_type":
            value = branch_type(value)
        elif key == "qr_compensation" and value:
            if int(value) == value:
                value = int(value)
            value = str(value) + " øre"
        elif type(value) in [float, int] and value:
            value = str(value)

        return value or "-"

    def get_view_name(self) -> str:
        return gettext("Virksomheder")  # pragma: no cover


class ProductSearchView(SearchView):
    template_name = "esani_pantportal/product/list.html"
    model = Product
    form_class = ProductFilterForm
    preferences_class = ProductListViewPreferences
    annotations = {
        "file_name": F("import_job__file_name"),
    }
    can_edit_multiple = True
    search_fields = ["product_name", "barcode"]
    search_fields_exact = ["state", "approved", "import_job"]
    fixed_columns = {
        "product_name": _("Produktnavn"),
        "barcode": _("Stregkode"),
        "status": _("Status"),
    }
    actions = {_("Vis"): "btn btn-sm btn-primary"}

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["user"] = self.request.user
        return form_kwargs

    def get_action_url(self, item, *args):
        return reverse("pant:product_view", kwargs={"pk": item.id})

    def item_to_json_dict(self, item_obj, context, index):
        json_dict = super().item_to_json_dict(item_obj, context, index)
        json_dict["file_name"] = item_obj.file_name or "-"
        return json_dict

    def map_value(self, item, key, context):
        value = super().map_value(item, key, context)

        if key == "material":
            value = material(value)
        elif key == "shape":
            value = shape(value)
        elif key == "danish":
            value = danish(value)
        elif "_date" in key and value:
            value = value.strftime("%-d. %b %Y")

        return value or "-"

    def filter_qs(self, qs):
        qs = super().filter_qs(qs)
        qs = qs.exclude(state=ProductState.DELETED)
        return qs

    def get_view_name(self) -> str:
        return gettext("Produkter")  # pragma: no cover


class BranchSearchView(PermissionRequiredMixin, SearchView):
    """
    SearchView which merges the `company_branch` and `kiosk` fields on objects and
    treats them as one.
    """

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related("company_branch", "kiosk")
        qs = qs.annotate(
            company_branch_or_kiosk=Coalesce(
                F("company_branch__name"), F("kiosk__name")
            ),
        )
        data = self.search_data

        branch_qs = self.model.objects.none()
        for field in ["company_branch__name", "kiosk__name"]:
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

        # Only allow branch/company/kiosk users to see Objects in their own company
        user = self.request.user
        if user.user_type == KIOSK_USER:
            qs = qs.filter(kiosk__pk=user.branch.pk)
        elif user.user_type == BRANCH_USER:
            qs = qs.filter(company_branch__pk=user.branch.pk)
        elif user.user_type == COMPANY_USER:
            qs = qs.filter(company_branch__company__pk=user.company.pk)
        return qs


class ReverseVendingMachineSearchView(BranchSearchView):
    template_name = "esani_pantportal/reverse_vending_machine/list.html"
    model = ReverseVendingMachine
    form_class = ReverseVendingMachineFilterForm
    required_permissions = ["esani_pantportal.view_reversevendingmachine"]

    search_fields = ["serial_number"]
    actions = {_("Fjern"): "btn btn-sm btn-danger"}

    def get_action_html(self, item, label, button_class):
        id = item.id
        return f'<a id="delete_{id}" value="{id}" class="{button_class}">{label}</a>'

    def get_fixed_columns(self):
        fixed_columns = {
            "serial_number": _("Serienummer"),
            "company_branch_or_kiosk": _("Butik"),
            # "city": _("By"),  # TODO: reintroduce in other MR regarding city display
        }
        if self.request.user.is_esani_admin:
            fixed_columns["compensation"] = _("Håndteringsgodtgørelse")
        return fixed_columns

    def map_value(self, item, key, context):
        value = super().map_value(item, key, context)
        if key == "compensation" and value and value != "-":
            value = float_to_string(value) + " øre"
        return value or "-"

    def get_view_name(self) -> str:
        return gettext("Pantmaskiner")  # pragma: no cover


def _get_qr_bag_filtered_annotation(aggregate: Aggregate, valid: bool) -> Aggregate:
    """Create an aggregate suitable for use by the `QRBagSearchView` `annotations`
    attribute.
    Depending on whether `valid` is True or False, the aggregate returned will either
    process only "valid" items, or only "invalid" items.
    "Valid" items are deposit payout items that have both a `product` FK and whose
    `barcode` is not NULL.
    """
    condition = Q(
        deposit_items__product__isnull=False,
        deposit_items__barcode__isnull=False,
    )
    aggregate.filter = condition if valid else ~condition
    return aggregate


class QRBagSearchView(BranchSearchView):
    template_name = "esani_pantportal/qrbag/list.html"
    actions = {_("Historik"): "btn btn-sm btn-secondary"}
    model = QRBag
    form_class = QRBagFilterForm
    required_permissions = ["esani_pantportal.view_qrbag"]

    search_fields = ["qr"]
    search_fields_exact = ["status"]

    fixed_columns = {
        "qr": _("QR kode"),
        "company_branch_or_kiosk": _("Butik"),
        "status": _("Status"),
        "updated": _("Opdateret"),
        # Annotations
        "num_valid_deposited": _("Optalt, godkendt"),
        "num_invalid_deposited": _("Optalt, afvist"),
        "value_of_valid_deposited": _("Samlet pantværdi (kr.)"),
    }

    annotations = {
        "num_valid_deposited": _get_qr_bag_filtered_annotation(
            Sum("deposit_items__count"),
            True,
        ),
        "num_invalid_deposited": _get_qr_bag_filtered_annotation(
            Sum("deposit_items__count"),
            False,
        ),
        "value_of_valid_deposited": _get_qr_bag_filtered_annotation(
            Sum(
                F("deposit_items__count")
                * F("deposit_items__product__refund_value")
                / Value(100),
            ),
            True,
        ),
    }

    def get_action_url(self, item, *args):
        base_url = reverse("pant:qrbag_history", kwargs={"pk": item.id})
        back_url = self.request.get_full_path()
        return add_parameters_to_url(base_url, {"back": quote(back_url)})

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related("company_branch", "kiosk")
        return qs

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def filter_qs(self, qs):
        # Support multiple-choice filtering on `status`
        status = self.search_data.pop("status", None)
        if status not in (None, "", [""], []):  # skip empty values
            qs = qs.filter(status__in=status)
        # Process the other search criteria (except `status`)
        return super().filter_qs(qs)

    def sort_qs(self, qs):
        data = self.search_data
        sort = data.get("sort", None)
        if sort in self.annotations:
            desc = data.get("order", None) == "desc"
            qs = qs.order_by(
                F(sort).asc(
                    descending=desc,
                    **({"nulls_last": True} if desc else {"nulls_first": True}),
                )
            )
            return qs
        else:
            return super().sort_qs(qs)

    def map_value(self, item, key, context):
        value = super().map_value(item, key, context)

        if isinstance(value, (datetime.date, datetime.datetime)):
            value = value.strftime("%-d. %b %Y")
        elif key == "status":
            return self._qr_status_names[value]
        elif key in ("num_valid_deposited", "num_invalid_deposited"):
            if item["status"] in ("esani_optalt", "esani_udbetalt"):
                return value or 0

        return value or "-"

    def get_view_name(self) -> str:
        return gettext("Pantposer")  # pragma: no cover

    @cached_property
    def _qr_status_names(self) -> dict[str, str]:
        return {
            code: name for code, name in QRStatus.objects.values_list("code", "name_da")
        }


class UserSearchView(PermissionRequiredMixin, SearchView):
    template_name = "esani_pantportal/user/list.html"
    actions = {_("Vis"): "btn btn-sm btn-primary"}
    model = User
    form_class = UserFilterForm
    preferences_class = UserListViewPreferences
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

    fixed_columns = {
        "username": _("Brugernavn"),
        "full_name": _("Navn"),
        "user_type": _("Brugertype"),
    }

    def get_action_url(self, item, *args):
        return reverse("pant:user_view", kwargs={"pk": item.id})

    def item_to_json_dict(self, item_obj, context, index):
        json_dict = super().item_to_json_dict(item_obj, context, index)
        user_is_admin = item_obj.is_admin_annotation
        json_dict["full_name"] = item_obj.full_name
        json_dict["branch"] = item_obj.branch_annotation
        json_dict["company"] = item_obj.company_annotation
        json_dict["is_admin"] = _("Ja") if user_is_admin else _("Nej")
        json_dict["newsletter"] = _("Ja") if item_obj.newsletter else _("Nej")
        return json_dict

    def map_value(self, item, key, context):
        value = super().map_value(item, key, context)

        if key == "approved":
            value = _("Ja") if value else _("Nej")
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

    def get_view_name(self) -> str:
        return gettext("Brugere")  # pragma: no cover


class BaseCompanyUpdateView(IsAdminMixin, UpdateViewMixin):
    template_name = "esani_pantportal/company/view.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["back_url"] = get_back_url(self.request, "")
        context["users"] = self.object.users.all()
        context["is_admin"] = self.request.user.user_type == ESANI_USER

        return context

    def get_success_url(self):
        return self.request.get_full_path()


class CompanyUpdateView(BaseCompanyUpdateView):
    required_permissions = ["esani_pantportal.change_company"]
    model = Company
    form_class = UpdateCompanyForm

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["delete_url"] = reverse(
            "pant:company_delete", kwargs={"pk": self.object.pk}
        )
        context["branches"] = self.object.branches.all()
        context["object_type"] = "company"

        if not context["users"] and not context["branches"]:
            context["can_delete"] = True

        return context

    def check_permissions(self):
        if self.request.user.is_esani_admin or self.same_company:
            return super().check_permissions()
        else:
            return self.access_denied


class CompanyBranchUpdateView(BaseCompanyUpdateView):
    required_permissions = ["esani_pantportal.change_companybranch"]
    model = CompanyBranch
    form_class = UpdateBranchForm

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["delete_url"] = reverse(
            "pant:company_branch_delete", kwargs={"pk": self.object.pk}
        )
        context["rvms"] = self.object.rvms.all()
        context["object_type"] = "company_branch"
        if not context["users"] and not context["rvms"]:
            context["can_delete"] = True
        return context

    def form_valid(self, form):
        if "company" in form.changed_data and not self.request.user.is_esani_admin:
            raise ValidationError(
                "Only ESANI admins may change the parent-company of a branch"
            )

        return super().form_valid(form)

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

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["delete_url"] = reverse(
            "pant:kiosk_delete", kwargs={"pk": self.object.pk}
        )
        context["rvms"] = self.object.rvms.all()
        context["object_type"] = "kiosk"
        if not context["users"] and not context["rvms"]:
            context["can_delete"] = True
        return context

    def check_permissions(self):
        if self.request.user.is_esani_admin or self.same_branch:
            return super().check_permissions()
        else:
            return self.access_denied


class DepositPayoutSearchView(PermissionRequiredMixin, SearchView):
    template_name = "esani_pantportal/deposit_payout/list.html"
    model = DepositPayoutItem
    form_class = DepositPayoutItemFilterForm
    required_permissions = ["esani_pantportal.view_depositpayout"]
    can_edit_multiple = True

    search_fields_exact = ["company_branch", "kiosk"]
    search_fields = []

    fixed_columns = {
        "source": _("Kæde, butik (eller RVM-serienummer)"),
        "product": _("Produkt (eller stregkode)"),
        "product__refund_value": _("Pantværdi (i øre)"),
        "count": _("Antal"),
        "date": _("Dato"),
        "already_exported": _("Allerede eksporteret"),
    }

    annotations = {
        "source": Coalesce("company_branch__company__name", "kiosk__name"),
        "already_exported": ExpressionWrapper(
            Q(file_id__isnull=False),
            output_field=BooleanField(),
        ),
    }

    def post(self, request, *args, **kwargs):
        # Instantiate form and trigger validation.
        # This is required by `filter_qs` which in turn is called from `get_queryset`.
        self.form = self.get_form_class()(self.request.GET)
        form_is_valid = self.form.is_valid()

        # If POST contains "selection=all-wet" or "selection=all-dry", process all
        # objects in queryset.
        # If POST contains "selection=selected-wet" or "selected-dry", use the specific
        # ID list in "ids" to filter the queryset.
        if request.POST.get("selection", "") in ("all-wet", "all-dry"):
            qs = self.get_queryset()
        else:
            ids = request.POST.get("ids")
            if ids is not None:
                ids = [int(id) for id in ids.split(",")]
                qs = self.get_queryset().filter(id__in=ids)
            else:
                qs = DepositPayoutItem.objects.none()
                logger.info(
                    "When passing `selection=selected-wet` or `selection=selected-dry`,"
                    "you must also pass a list of IDs in `ids`."
                )

        date_min = qs.aggregate(Min("date"))["date__min"]
        date_max = qs.aggregate(Max("date"))["date__max"]

        if form_is_valid and qs.exists():
            from_date = self.form.cleaned_data.get("from_date") or date_min
            to_date = self.form.cleaned_data.get("to_date") or date_max
            dry = request.POST.get("selection", "").endswith("-dry")
            export = CreditNoteExport(from_date, to_date, qs, dry=dry)
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = (
                f"attachment; filename={export.get_filename()}"
            )
            export.as_csv(response)
            if not dry:
                ERPCreditNoteExport.objects.create(
                    file_id=export.get_file_id(),
                    from_date=from_date,
                    to_date=to_date,
                    created_by=request.user,
                )
            return response
        else:
            messages.add_message(
                request,
                messages.ERROR,
                _("Ingen linjer er valgt"),
            )
            return redirect(".")

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related(
            "company_branch__company",
            "kiosk",
            "product",
            "deposit_payout",
            "qr_bag",
        )
        return qs

    def filter_qs(self, qs):
        qs = super().filter_qs(qs)

        from_date = self.form.cleaned_data.get("from_date")
        to_date = self.form.cleaned_data.get("to_date")
        if from_date:
            qs = qs.filter(date__gte=from_date)
        if to_date:
            qs = qs.filter(date__lte=to_date)

        already_exported = self.form.cleaned_data.get("already_exported")
        if already_exported is False:
            qs = qs.filter(file_id__isnull=True)

        return qs

    @staticmethod
    def span(text, title):
        return f'<span class="text-danger" title="{title}">{text}</span>'

    def item_to_json_dict(self, item_obj, context, index):
        json_dict = super().item_to_json_dict(item_obj, context, index)

        company_branch = item_obj.company_branch
        kiosk = item_obj.kiosk
        product = item_obj.product

        source_error = _("Ingen matchende kæde eller butik, viser RVM-serienummer")
        barcode_not_found_error = _("Intet matchende produkt, viser stregkoden")
        manual_payout_error = _(
            "Intet produkt tilknyttet - udbetaling er oprettet manuelt"
        )

        if company_branch:
            json_dict["source"] = str(company_branch) + ", " + company_branch.city
        elif kiosk:
            json_dict["source"] = str(kiosk) + ", " + kiosk.city
        else:
            json_dict["source"] = self.span(item_obj.rvm_serial, source_error)

        if product:
            json_dict["product"] = product.product_name
            json_dict["product__refund_value"] = product.refund_value
        else:
            barcode = item_obj.barcode
            if item_obj.deposit_payout.source_type == "manual":
                json_dict["product"] = self.span("x" * 12, manual_payout_error)
            elif barcode:
                json_dict["product"] = self.span(barcode, barcode_not_found_error)

            json_dict["product__refund_value"] = "-"

        json_dict["date"] = item_obj.date.strftime("%-d. %b %Y")
        json_dict["already_exported"] = (
            _("Ja") if item_obj.already_exported else _("Nej")
        )

        return json_dict


class ERPCreditNoteExportSearchView(PermissionRequiredMixin, SearchView):
    template_name = "esani_pantportal/erp_credit_note_export/list.html"
    form_class = DepositPayoutItemFilterForm  # FIXME: not actually used
    model = ERPCreditNoteExport
    required_permissions = ["esani_pantportal.view_erpcreditnoteexport"]

    search_fields = []
    fixed_columns = {
        "file_id": _("Fil-ID"),
        "from_date": _("Fra-dato"),
        "to_date": _("Til-dato"),
        "created_at": _("Oprettet d."),
        "count": _("Antal pantdata-linjer"),
    }
    actions = {_("Download"): "btn btn-sm btn-primary"}

    def get_queryset(self):
        qs = self.model.objects.annotate(
            count=Subquery(
                DepositPayoutItem.objects.filter(file_id=OuterRef("file_id"))
                .values("file_id")
                .annotate(_count=Count("id"))
                .values("_count"),
                output_field=PositiveIntegerField(),
            )
        )
        qs = self.filter_qs(qs)
        qs = self.sort_qs(qs)
        return qs

    def get(self, request, *args, **kwargs):
        file_id = self.request.GET.get("file_id")
        if file_id:
            try:
                erp_export = ERPCreditNoteExport.objects.get(file_id=file_id)
            except ERPCreditNoteExport.DoesNotExist:
                return HttpResponseNotFound()

            items = DepositPayoutItem.objects.filter(file_id=file_id)
            if items.exists():
                export = CreditNoteExport(
                    erp_export.from_date,
                    erp_export.to_date,
                    items,
                    dry=True,
                    file_id=file_id,
                )
                response = HttpResponse(content_type="text/csv")
                response["Content-Disposition"] = (
                    f"attachment; filename={export.get_filename()}"
                )
                export.as_csv(response)
                return response
            else:
                messages.add_message(
                    request,
                    messages.ERROR,
                    _("Ingen linjer fundet for det angivne fil-ID"),
                )
                return redirect(".")

        return super().get(request, *args, **kwargs)

    def get_action_url(self, item, label):
        return f"?file_id={item.file_id}"

    def item_to_json_dict(self, item_obj, context, index):
        json_dict = super().item_to_json_dict(item_obj, context, index)
        for field in ("from_date", "to_date", "created_at"):
            json_dict[field] = localize(json_dict[field])
        return json_dict


class ProductUpdateView(UpdateViewMixin):
    model = Product
    template_name = "esani_pantportal/product/view.html"
    form_class = ProductUpdateForm

    def get_queryset(self):
        return self.model.objects.get_queryset()

    def check_permissions(self):
        if self.request.method == "GET":
            self.required_permissions = ["esani_pantportal.view_product"]
        else:
            self.required_permissions = ["esani_pantportal.change_product"]

        return super().check_permissions()

    def get_latest_relevant_history(self):
        return self.object.history.exclude(
            Q(history_change_reason="Ændret") | Q(history_change_reason__isnull=True)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = context["object"]

        context["back_url"] = get_back_url(self.request, "")

        if product.approved and not self.request.user.is_esani_admin:
            context["can_edit"] = False

        if self.request.user.is_esani_admin:
            context["can_approve"] = can_proceed(product.approve)
            context["can_unapprove"] = can_proceed(product.unapprove)
            context["can_reject"] = can_proceed(product.reject)
            context["can_unreject"] = can_proceed(product.unreject)

        qs = self.get_latest_relevant_history()
        if qs:
            context["latest_history"] = qs.order_by("-history_date")[0]

        return context

    def form_valid(self, form):
        # Since we are not calling `super().form_valid(...)`, we manually call
        # `check_permissions`.
        # We are not calling `super().form_valid(...)` as that will in turn call
        # `form.save()`, updating `self.object.state` before we have a chance to
        # capture its old value.
        response = self.check_permissions()
        if response:
            return response

        old_state_name = form.instance.get_state_display()

        def get_change_reason(new_state: ProductState) -> str:
            return f"Status ændret fra {old_state_name} til {new_state.label}"

        # Populate `self.object` with values from form, but do not update the
        # underlying DB object yet.
        self.object = form.save(commit=False)

        if not self.request.user.is_esani_admin:
            approved = self.get_object().approved
            if approved:
                return self.access_denied
            if not self.same_workplace:
                return self.access_denied
            if "action" in form.changed_data:
                return self.access_denied
            self.object._change_reason = "Ændret"
        else:
            # Action is one of "approve", "unapprove", "reject" or "unreject".
            # If "normal" save, "action" is not present in form data.
            action = form.cleaned_data.get("action")
            if action == "approve":
                self.object.approve()
                self.object._change_reason = "Godkendt"
            elif action == "unapprove":
                self.object.unapprove()
                self.object._change_reason = get_change_reason(
                    ProductState.AWAITING_APPROVAL
                )
            elif action == "reject":
                rejection_message = form.cleaned_data.get("rejection_message")
                self.object.rejection = rejection_message
                self.object.reject()
                self.object._change_reason = "Afvist"
            elif action == "unreject":
                self.object.unreject()
                self.object._change_reason = get_change_reason(
                    ProductState.AWAITING_APPROVAL
                )
            else:
                self.object._change_reason = "Ændret"

        self.object.save()

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return get_back_url(self.request, self.request.get_full_path())


class ProductHistoryView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = "esani_pantportal/product/history.html"
    context_object_name = "historical_product"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["histories"] = self.object.history.exclude(
            Q(history_change_reason="Ændret") | Q(history_change_reason__isnull=True)
        ).order_by("-history_date")
        return context


class QRBagHistoryView(LoginRequiredMixin, DetailView):
    model = QRBag
    template_name = "esani_pantportal/qrbag/history.html"
    context_object_name = "historical_qrbag"

    def get_context_data(self, **kwargs):
        deposit_payout_items = (
            self.object.deposit_items.select_related("product")
            .annotate(value=F("count") * F("product__refund_value") / Value(100))
            .order_by(
                F("product__product_name").asc(nulls_last=True),
                F("product__barcode"),
            )
        )

        context = super().get_context_data(**kwargs)
        context["histories"] = self.object.history.all().order_by("-history_date")
        context["deposit_payout_items"] = deposit_payout_items
        context["total_count"] = deposit_payout_items.aggregate(val=Sum("count"))["val"]
        context["total_value"] = deposit_payout_items.aggregate(
            val=Sum(F("count") * F("product__refund_value")) / Value(100)
        )["val"]
        context["back_url"] = get_back_url(self.request, reverse("pant:qrbag_list"))
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

    def check_permissions(self):
        if self.get_object() == self.request.user:
            # A user should always be able to see and edit their own user-profile.
            return None
        else:
            return super().check_permissions()

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
        branch_attributes = ["customer_id"]
        if self.request.user.user_type == ESANI_USER:
            branch_attributes.append("qr_compensation")
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
        if form.cleaned_data["disable_two_factor"]:
            for device in devices_for_user(self.object):
                device.delete()
            return redirect(
                add_parameters_to_url(
                    self.get_success_url(),
                    {"disable_two_factor_success": 1, "two_factor_success": 0},
                )
            )
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
    object: User
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


class BaseCompanyDeleteView(PermissionRequiredMixin, DeleteView):
    object: Company | CompanyBranch | Kiosk

    def get_success_url(self):
        back_url = get_back_url(self.request, reverse("pant:company_list"))
        return add_parameters_to_url(back_url, {"delete_success": 1})


class CompanyDeleteView(BaseCompanyDeleteView):
    object: Company
    model = Company
    required_permissions = ["esani_pantportal.delete_company"]


class CompanyBranchDeleteView(BaseCompanyDeleteView):
    object: CompanyBranch
    model = CompanyBranch
    required_permissions = ["esani_pantportal.delete_companybranch"]


class KioskDeleteView(BaseCompanyDeleteView):
    object: Kiosk
    model = Kiosk
    required_permissions = ["esani_pantportal.delete_kiosk"]


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

        existing_barcodes = {
            product.barcode: (product.state, product.rejection)
            for product in Product.objects.exclude(state=ProductState.DELETED)
        }

        job = ImportJob(
            imported_by=self.request.user,
            file_name=form.filename,
            date=now(),
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
                state, rejection = existing_barcodes[barcode]
                if state == ProductState.REJECTED:
                    failures.append({product_name: {gettext("Afvist"): [rejection]}})
                continue
            try:
                product = Product(**product_dict)
                product.import_job = job
                product.full_clean(exclude=["state"])
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


class CsvDebtorView(CsvTemplateView):
    def get(self, request, *args, **kwargs):
        export = DebtorExport()
        filename = f"debitor_{datetime.date.today().strftime('%Y-%m-%d')}.csv"
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f"attachment; filename={filename}"
        export.as_csv(response)
        return response


class CsvCompaniesView(CsvTemplateView):
    @staticmethod
    def obj_to_dict(obj, fields):
        obj_dict = dict(
            {"external_customer_id": obj.external_customer_id},
            **model_to_dict(obj, fields=fields),
        )
        if "company" in fields:
            obj_dict["company"] = obj.company.name

        return obj_dict

    def create_dataframe(self, company_class):
        fields = [field.name for field in company_class._meta.fields]
        df = pd.DataFrame(
            [self.obj_to_dict(obj, fields) for obj in company_class.objects.all()]
        )
        df["object_class_name"] = company_class.__name__

        # Remove decimals from integer columns
        for col in [
            "registration_number",
            "account_number",
            "cvr",
            "customer_id",
        ]:
            if col in df.columns:
                df[col] = df[col].astype("Int64")

        return df

    def get(self, request, *args, **kwargs):
        company_df = self.create_dataframe(Company)
        company_branch_df = self.create_dataframe(CompanyBranch)
        kiosk_df = self.create_dataframe(Kiosk)
        df = pd.concat([company_df, company_branch_df, kiosk_df])
        df["branch_type"] = df["branch_type"].apply(branch_type)
        df["company_type"] = df["company_type"].apply(company_type)

        timestamp = now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_all_companies.csv"

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f"attachment; filename={filename}"
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

        state_map = dict(ProductState.choices)

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
            column_map["state"] = "Status"
            qs = Product.objects.exclude(state=ProductState.DELETED)
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
                    "state",
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
            df = df.replace({"state": state_map})
        df = df.rename(column_map, axis=1)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f"attachment; filename={filename}"
        df.to_csv(path_or_buf=response, sep=";", index=False)

        return response


class ProductDeleteView(PermissionRequiredMixin, DeleteView):
    object: Product
    model = Product
    required_permissions = ["esani_pantportal.delete_product"]

    def form_valid(self, form):
        if not self.request.user.is_esani_admin and not self.same_workplace:
            return self.access_denied

        if can_proceed(self.object.delete):
            self.object.delete()
            self.object._change_reason = "Slettet"
            self.object.save()
        else:
            return self.access_denied

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        back_url = get_back_url(self.request, reverse("pant:product_list"))
        return add_parameters_to_url(back_url, {"delete_success": 1})


class ReverseVendingMachineDeleteView(PermissionRequiredMixin, DeleteView):
    object: ReverseVendingMachine
    model = ReverseVendingMachine
    required_permissions = ["esani_pantportal.delete_reversevendingmachine"]

    def form_valid(self, form):
        if not self.request.user.is_esani_admin and not self.same_workplace:
            return self.access_denied
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("pant:rvm_list")


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
            to=[DEFAULT_FROM_EMAIL],
            bcc=to_list,
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
        return reverse("pant:newsletter_send")


class UpdateListViewPreferences(View):
    def post(self, request, *args, **kwargs):
        preferences_class_name = request.POST.get("preferences_class_name")
        model = getattr(sys.modules[__name__], preferences_class_name)
        preferences, _ = model.objects.get_or_create(user=self.request.user)

        for field in model._meta.fields:
            if field.name in request.POST and field.name.startswith("show_"):
                show_field = request.POST[field.name].lower() == "true"
                setattr(preferences, field.name, show_field)
        preferences.save()
        return HttpResponse("ok")


class _MultipleProductStateUpdate(View, PermissionRequiredMixin):
    """Base class for views that can update the state of multiple products"""

    def post(self, request, *args, **kwargs):
        if not self.request.user.is_esani_admin:
            return self.access_denied

        ids = [int(id) for id in self.request.POST.getlist("ids[]")]
        products = Product.objects.filter(id__in=ids)
        num = 0

        for product in products:
            if self.can_proceed(product):
                self.update(product)
                num += 1

        bulk_update_with_history(
            products,
            Product,
            self.get_affected_fields(),
            default_change_reason=self.get_change_reason(),
        )

        return JsonResponse(
            {
                "total": len(ids),
                "updated": num,
                "state_choices": self._get_state_choices(),
            }
        )

    def can_proceed(self, product: Product) -> bool:
        raise NotImplementedError("must be implemented by subclass")  # pragma: nocover

    def update(self, product: Product) -> None:
        raise NotImplementedError("must be implemented by subclass")  # pragma: nocover

    def get_change_reason(self) -> str:
        raise NotImplementedError("must be implemented by subclass")  # pragma: nocover

    def get_affected_fields(self) -> list[str]:
        return ["state"]

    def _get_state_choices(self) -> list[dict[str, Any]]:
        form = ProductFilterForm(user=self.request.user)
        field = form.fields["state"]
        choices = [
            {"value": value, "label": label}
            for value, label in field.choices  # type: ignore
        ]
        return choices


class MultipleProductApproveView(_MultipleProductStateUpdate):
    def can_proceed(self, product: Product) -> bool:
        return can_proceed(product.approve)

    def update(self, product: Product) -> None:
        product.approve()

    def get_change_reason(self) -> str:
        return "Godkendt"


class MultipleProductRejectView(_MultipleProductStateUpdate):
    def can_proceed(self, product: Product) -> bool:
        return can_proceed(product.reject)

    def update(self, product: Product) -> None:
        product.reject()
        product.rejection = self.request.POST.get("rejection")

    def get_change_reason(self) -> str:
        return "Afvist"

    def get_affected_fields(self) -> list[str]:
        return super().get_affected_fields() + ["rejection"]


class MultipleProductDeleteView(_MultipleProductStateUpdate):
    def can_proceed(self, product: Product) -> bool:
        return can_proceed(product.delete)

    def update(self, product: Product) -> None:
        product.delete()

    def get_change_reason(self) -> str:
        return "Slettet"


class TwoFactorSetup(SetupView):
    form_list = [("method", PantPortalAuthenticationTokenForm)]

    def get_success_url(self):
        return add_parameters_to_url(
            reverse("pant:user_view", kwargs={"pk": self.request.user.id}),
            {"two_factor_success": 1},
        )


class GenerateQRView(FormView):
    form_class = GenerateQRForm
    template_name = "esani_pantportal/qr/generate.html"

    def form_valid(self, form):
        bag_type = form.cleaned_data["bag_type"]
        bag_name = settings.QR_GENERATOR_SERIES[bag_type]["name"]
        number_of_codes = form.cleaned_data["number_of_codes"]

        csv_file = call_command("generate_qr_codes", bag_type, number_of_codes)
        df = pd.read_csv(csv_file, sep=";", dtype=str)

        with BytesIO() as b:
            sheet_name = f"{bag_name} x {number_of_codes}"

            writer = pd.ExcelWriter(
                b,
                engine="xlsxwriter",
                engine_kwargs={"options": {"strings_to_urls": False}},
            )
            df.to_excel(writer, sheet_name=sheet_name, index=False)

            # Set column-widths
            writer.sheets[sheet_name].set_column(0, 0, 45)
            writer.sheets[sheet_name].set_column(1, 1, 10)
            writer.sheets[sheet_name].set_column(2, 2, 15)
            writer.close()

            excel_filename = os.path.basename(csv_file).replace(".csv", ".xlsx")
            content_type = (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            response = HttpResponse(b.getvalue(), content_type=content_type)
            response["Content-Disposition"] = f"attachment; filename={excel_filename}"
            return response


class CsvUsersView(CsvTemplateView):
    def get(self, request, *args, **kwargs):
        if not request.user.is_esani_admin:
            return HttpResponseForbidden("Permission denied!")

        # Query
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        users_all_query = User.objects.all()

        # Dynamically get all field names from the User model
        initial_fields = ["id", "username", "email", "first_name", "last_name"]
        excluded_fields = ["password"]
        other_fields = [
            f.name
            for f in User._meta.fields
            if f.name not in initial_fields and f.name not in excluded_fields
        ]
        field_names = initial_fields + other_fields

        df = pd.DataFrame(users_all_query.values(*field_names))

        users_map = {user.id: user for user in users_all_query}

        def company_attr(user_id, field):
            user = users_map[user_id]
            company = user.branch or user.company
            if company:
                return getattr(company, field)
            elif user.user_type == ESANI_USER and field == "name":
                return "ESANI"

        for field in [f.name for f in AbstractCompany._meta.fields]:
            df[f"company_{field}"] = df["id"].map(lambda id: company_attr(id, field))

        # Convert column "user_type" to a text instead of the integer value
        df["user_type"] = df["user_type"].map(
            {
                ESANI_USER: "ESANI_USER",
                BRANCH_USER: "BRANCH_USER",
                COMPANY_USER: "COMPANY_USER",
                KIOSK_USER: "KIOSK_USER",
            }
        )

        # Response
        filename = f"{timestamp}_full_user_list.csv"
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f"attachment; filename={filename}"
        df.to_csv(path_or_buf=response, sep=";", index=False)
        return response


class DepositItemFormSetView(PermissionRequiredMixin, FormWithFormsetView):
    model = DepositPayout
    form_class = DepositPayoutForm
    formset_class = DepositPayoutItemFormSet
    template_name = "esani_pantportal/deposit_payout/formset.html"

    required_permissions = [
        "esani_pantportal.add_depositpayout",
        "esani_pantportal.add_depositpayoutitem",
    ]

    def get_success_url(self):
        return reverse("pant:deposit_payout_list")

    def get_context_data(self, *args, **kwargs):
        mapping = ERPProductMapping.objects.get(
            specifier=ERPProductMapping.SPECIFIER_MANUAL,
            category=ERPProductMapping.CATEGORY_HANDLING,
        )

        context = super().get_context_data(*args, **kwargs)
        context["rate"] = mapping.rate
        return context

    def form_valid(self, form, formset):
        if formset.is_valid():
            items = []
            from_date = None
            to_date = None
            for subform in formset:
                item = subform.save(commit=False)
                items.append(item)

                if not from_date or from_date > item.date:
                    from_date = item.date

                if not to_date or to_date < item.date:
                    to_date = item.date

        item_count = len(items)
        source_identifier = " - ".join(
            [
                self.request.user.username,
                now().strftime("%Y-%m-%d %H:%M:%S"),
            ]
        )

        with transaction.atomic():
            deposit_payout = self.model.objects.create(
                source_type="manual",
                item_count=item_count,
                from_date=from_date,
                to_date=to_date,
                source_identifier=source_identifier,
            )
            for item in items:
                item.deposit_payout = deposit_payout
            DepositPayoutItem.objects.bulk_create(items)

        messages.add_message(
            self.request,
            messages.INFO,
            _("{item_count} pantdata-linjer oprettet").format(item_count=item_count),
        )
        return super().form_valid(form, formset)
