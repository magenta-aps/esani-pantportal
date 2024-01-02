# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
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
from django.forms import model_to_dict
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.template import loader
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DeleteView,
    FormView,
    ListView,
    UpdateView,
    View,
)
from project.settings import DEFAULT_FROM_EMAIL

from esani_pantportal.forms import (
    ChangePasswordForm,
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
    UserFilterForm,
    UserUpdateForm,
)
from esani_pantportal.models import (
    BRANCH_USER,
    COMPANY_USER,
    KIOSK_USER,
    BranchUser,
    Company,
    CompanyBranch,
    CompanyUser,
    EsaniUser,
    Kiosk,
    KioskUser,
    Product,
    RefundMethod,
    User,
)
from esani_pantportal.templatetags.pant_tags import (
    danish,
    material,
    refund_method,
    shape,
    user_type,
)
from esani_pantportal.util import (
    default_dataframe,
    float_to_string,
    remove_parameter_from_url,
)
from esani_pantportal.view_mixins import PermissionRequiredMixin

logger = logging.getLogger(__name__)


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


class RegisterBranchUserView(CreateView):
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


class RegisterKioskUserView(CreateView):
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
        kwargs["allow_multiple_admins"] = True
        kwargs["approved"] = True
        if self.request.user.user_type == KIOSK_USER:
            kwargs["branch"] = self.request.user.branch
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
                        field + "__icontains": part
                        for part in data[field].split()
                        if part
                    }
                )

        sort = data.get("sort", None)
        if sort:
            reverse = "-" if data.get("order", None) == "desc" else ""
            order_args = [f"{reverse}{s}" for s in sort.split("_or_")]
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
        return item[key]


class ProductSearchView(SearchView):
    template_name = "esani_pantportal/product/list.html"
    actions_template = "esani_pantportal/product/actions.html"
    model = Product
    form_class = ProductFilterForm

    search_fields = ["product_name", "barcode"]
    search_fields_exact = ["approved"]

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
        return value

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if self.request.user.is_esani_admin:
            # Statistics on approved products for ESANI admins
            # Other users don't need to see this because they cannot approve anyway.
            context["approved_products"] = Product.objects.filter(approved=True).count()
            context["pending_products"] = Product.objects.filter(approved=False).count()
        return context


class RefundMethodSearchView(PermissionRequiredMixin, SearchView):
    template_name = "esani_pantportal/refund_method/list.html"
    actions_template = "esani_pantportal/refund_method/actions.html"
    model = RefundMethod
    form_class = RefundMethodFilterForm
    required_permissions = ["esani_pantportal.view_refundmethod"]

    search_fields = ["serial_number"]
    search_fields_exact = ["method"]

    def map_value(self, item, key, context):
        value = super().map_value(item, key, context)

        if key == "method":
            value = refund_method(value)
        elif key in ["branch", "kiosk"]:
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

    search_fields = ["username", "user_type"]
    search_fields_exact = ["approved"]

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


class UpdateViewMixin(PermissionRequiredMixin, UpdateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_fields"] = list(context["form"].fields.keys())

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


class ProductUpdateView(UpdateViewMixin):
    model = Product
    template_name = "esani_pantportal/product/view.html"
    form_class = ProductUpdateForm
    required_permissions = ["esani_pantportal.change_product"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if context["object"].approved and not self.request.user.is_esani_admin:
            context["can_edit"] = False
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
        if approved:
            if back_url:
                return remove_parameter_from_url(back_url, "json")
            else:
                return reverse("pant:product_list")
        else:
            return self.request.get_full_path()


class SameCompanyMixin:
    def get(self, request, *args, **kwargs):
        user = self.get_object()
        if not self.request.user.is_esani_admin:
            user_ids = self.users_in_same_company
            if user.id not in user_ids:
                return self.access_denied

        user_verbose = user.user_profile._meta.verbose_name
        self.required_permissions = [f"esani_pantportal.change_{user_verbose}"]

        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        if not self.request.user.is_esani_admin:
            user_ids = self.users_in_same_company
            if self.get_object().id not in user_ids:
                return self.access_denied
        return super().form_valid(form)


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
        branch_attributes = ["customer_id"]
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


class SetPasswordView(PermissionRequiredMixin, SameCompanyMixin, UpdateView):
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


class UserDeleteView(SameCompanyMixin, PermissionRequiredMixin, DeleteView):
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


class ProductDeleteView(PermissionRequiredMixin, DeleteView):
    model = Product
    required_permissions = ["esani_pantportal.delete_product"]

    def form_valid(self, form):
        if not self.request.user.is_esani_admin and not self.same_workplace:
            return self.access_denied
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("pant:product_list") + "?delete_success=1"


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
            msg.metadata = {"o:testmode": True}
            msg.headers = {"o:testmode": True}
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
