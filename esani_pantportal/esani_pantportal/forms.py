import os

import pandas as pd
from betterforms.multiform import MultiModelForm
from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import EMPTY_VALUES
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

from esani_pantportal.form_mixins import BootstrapForm, MaxSizeFileField
from esani_pantportal.models import (
    DANISH_PANT_CHOICES,
    PRODUCT_MATERIAL_CHOICES,
    PRODUCT_SHAPE_CHOICES,
    USER_TYPE_CHOICES,
    BranchUser,
    Company,
    CompanyBranch,
    EsaniUser,
    Product,
    User,
    validate_barcode_length,
    validate_digit,
)
from esani_pantportal.util import (
    join_strings_human_readable,
    make_valid_choices_str,
    read_csv,
    read_excel,
)


class PantPortalAuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.approved:
            raise ValidationError("Bruger er ikke godkendt af en ESANI medarbejder")


class ProductRegisterForm(forms.ModelForm, BootstrapForm):
    class Meta:
        model = Product
        fields = (
            "product_name",
            "barcode",
            "material",
            "height",
            "diameter",
            "weight",
            "capacity",
            "shape",
            "danish",
        )


class RegisterUserForm(forms.ModelForm, BootstrapForm):
    class Meta:
        model = User
        fields = (
            "username",
            "password",
            "password2",
            "phone",
            "first_name",
            "last_name",
            "email",
        )
        widgets = {
            "password": forms.PasswordInput(render_value=True),
            "password2": forms.PasswordInput(render_value=True),
        }

    password2 = forms.CharField(
        widget=forms.PasswordInput(render_value=True),
        label=_("Gentag Adgangskode"),
    )

    def clean_password(self):
        password = self.cleaned_data["password"]
        validate_password(password)
        return password

    def clean_password2(self):
        data = self.cleaned_data
        password = data.get("password", "")
        password2 = data.pop("password2")

        if password and password != password2:
            raise forms.ValidationError(_("Adgangskoder er ikke ens"))
        return password2


class RegisterBranchUserForm(RegisterUserForm):
    class Meta:
        model = BranchUser
        fields = (
            "username",
            "password",
            "password2",
            "phone",
            "first_name",
            "last_name",
            "email",
            "branch",
            "admin",
        )
        widgets = {
            "password": forms.PasswordInput(render_value=True),
            "password2": forms.PasswordInput(render_value=True),
        }

    admin = forms.BooleanField(
        initial=True,
        label=_("Admin rettigheder"),
        help_text=_(
            "Brugere med admin rettigheder kan blandt andet oprette andre brugere, "
            "registrere produkter og ændre produkter."
        ),
        required=False,
    )


class RegisterEsaniUserForm(RegisterUserForm):
    class Meta:
        model = EsaniUser
        fields = (
            "username",
            "password",
            "password2",
            "phone",
            "first_name",
            "last_name",
            "email",
        )
        widgets = {
            "password": forms.PasswordInput(render_value=True),
            "password2": forms.PasswordInput(render_value=True),
        }


class RegisterBranchForm(forms.ModelForm, BootstrapForm):
    class Meta:
        model = CompanyBranch
        fields = (
            "name",
            "address",
            "postal_code",
            "city",
            "phone",
            "location_id",
            "customer_id",
            "company",
            "branch_type",
            "registration_number",
            "account_number",
            "invoice_mail",
            "municipality",
        )


class RegisterCompanyForm(forms.ModelForm, BootstrapForm):
    class Meta:
        model = Company
        fields = (
            "name",
            "address",
            "postal_code",
            "city",
            "phone",
            "cvr",
            "permit_number",
            "company_type",
            "registration_number",
            "account_number",
            "invoice_mail",
            "country",
            "municipality",
        )


class RegisterBranchUserMultiForm(MultiModelForm, BootstrapForm):
    def __init__(
        self,
        *args,
        allow_multiple_admins=False,
        approved=False,
        company=None,
        branch=None,
        show_admin_flag=False,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        # If the branch form is filled out we don't need this field
        self.forms["user"].fields["branch"].required = False

        # Dict with default values for required fields
        self.required = {"branch": {}, "company": {}}

        # If the branch is selected from the dropdown, we don't need the branch form
        for field_name in self.forms["branch"].fields.keys():
            self.required["branch"][field_name] = (
                self.forms["branch"].fields[field_name].required
            )
            self.forms["branch"].fields[field_name].required = False

        # If the company is selected from the dropdown, we don't need the company form
        for field_name in self.forms["company"].fields.keys():
            self.required["company"][field_name] = (
                self.forms["company"].fields[field_name].required
            )
            self.forms["company"].fields[field_name].required = False

        self.parent_form_dict = {"branch": "user", "company": "branch"}
        self.allow_multiple_admins = allow_multiple_admins
        self.approved = approved
        self.company = company
        self.branch = branch
        self.show_admin_flag = show_admin_flag

        if company:
            self.forms["branch"].initial = {"company": company}
            self.allow_changing_company = False
            self.company_str = str(company)
        else:
            self.allow_changing_company = True

        if branch:
            self.forms["user"].initial = {"branch": branch}
            self.allow_changing_branch = False
            self.branch_str = str(branch)
        else:
            self.allow_changing_branch = True

    form_classes = {
        "user": RegisterBranchUserForm,
        "branch": RegisterBranchForm,
        "company": RegisterCompanyForm,
    }

    @staticmethod
    def has_admin_users(branch):
        users = BranchUser.objects.filter(
            branch__pk=branch.pk, groups__name="CompanyAdmins"
        )
        return True if users else False

    def check_subform(self, form_name, allowed_empty_keys=[]):
        # Check a sub-form for empty keys
        form = self.forms[form_name]
        for key, value in self.cleaned_data.get(form_name, {}).items():
            if key in allowed_empty_keys:
                continue
            elif not self.required[form_name][key]:
                continue
            elif value in EMPTY_VALUES:
                form._errors[key] = form.error_class([_("Dette felt må ikke være tom")])

        # If any of the fields are empty (or something else is wrong):
        if not form.is_valid():
            parent_form = self.forms[self.parent_form_dict[form_name]]

            # If there are errors in the branch-form:
            # Demand that the branch is selected from the dropdown in the user-form.

            # If there are errors in the company-form:
            # Demand that the company is selected from the dropdown in the branch-form.
            parent_form._errors[form_name] = parent_form.error_class(
                [_("Dette felt må ikke være tom")]
            )
            self.add_crossform_error(
                _("'{form_name}' formular indeholder tomme felter").format(
                    form_name=form_name
                )
            )

    def clean(self):
        branch_from_list = self.cleaned_data.get("user", {}).get("branch", "")
        company_from_list = self.cleaned_data.get("branch", {}).get("company", "")
        admin = self.cleaned_data.get("user", {}).get("admin", "")

        if (
            branch_from_list
            and self.has_admin_users(branch_from_list)
            and not self.allow_multiple_admins
            and admin
        ):
            self.add_crossform_error(
                _(
                    "Denne butik har allerede en admin bruger. "
                    "Bed venligst din admin om at oprette dig."
                )
            )

        user_form_valid = self.forms["user"].is_valid()
        branch_form_valid = self.forms["branch"].is_valid()

        if user_form_valid and not branch_from_list:
            # If the branch is not picked from the list we should not allow
            # fields to be empty in the branch-form
            self.check_subform("branch", allowed_empty_keys=["company"])

            if branch_form_valid and not company_from_list:
                # If the company is not picked from the list we should not
                # allow fields to be empty in the company-form
                self.check_subform("company")

        return self.cleaned_data

    def save(self, commit=True):
        objects = super().save(commit=False)

        company_from_list = self.company or self.cleaned_data["branch"]["company"]
        branch_from_list = self.branch or self.cleaned_data["user"]["branch"]
        admin = self.cleaned_data["user"]["admin"]

        if branch_from_list:
            branch = branch_from_list
        else:
            branch = objects["branch"]

            if company_from_list:
                company = company_from_list
            else:
                company = objects["company"]
                if commit:
                    company.save()

            branch.company = company
            if commit:
                branch.save()

        user = objects["user"]
        user.branch = branch
        user.approved = self.approved

        user.set_password(self.cleaned_data["user"]["password"])
        if commit:
            user.save()

        group_name = "CompanyAdmins" if admin else "CompanyUsers"
        user.groups.add(Group.objects.get(name=group_name))

        return user


class SortPaginateForm(forms.Form):
    json = forms.BooleanField(required=False)
    sort = forms.CharField(required=False)
    order = forms.CharField(required=False)
    offset = forms.IntegerField(required=False)
    limit = forms.IntegerField(required=False)


class ProductFilterForm(SortPaginateForm, BootstrapForm):
    product_name = forms.CharField(required=False)
    barcode = forms.CharField(required=False)
    approved = forms.NullBooleanField(
        required=False,
        widget=forms.Select(choices=((None, "-"), (True, _("Ja")), (False, _("Nej")))),
    )


class UserFilterForm(SortPaginateForm, BootstrapForm):
    username = forms.CharField(required=False)
    user_type = forms.ChoiceField(
        choices=[(None, "-")] + list(USER_TYPE_CHOICES), required=False
    )
    approved = forms.NullBooleanField(
        required=False,
        widget=forms.Select(choices=((None, "-"), (True, _("Ja")), (False, _("Nej")))),
    )


def validate_file_extension(value, valid_extensions):
    ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
    if not ext.lower() in valid_extensions:
        raise ValidationError(
            _(
                "Filtype er ikke understøttet. "
                "Understøttede filtyper er {valid_extensions}."
            ).format(valid_extensions=valid_extensions)
        )


class MultipleProductRegisterForm(BootstrapForm):
    defaults = settings.DEFAULT_CSV_HEADER_DICT
    sheet_name = forms.CharField(
        initial="Ark1",
        label=_("Ark"),
    )

    file = MaxSizeFileField(
        max_size=10000000,
        label=_("Filnavn"),
    )

    sep = forms.ChoiceField(
        choices=[(";", ";"), (",", ",")],
        label=_("CSV seperator"),
    )

    barcode_col = forms.CharField(
        initial=defaults["barcode"],
        label=_("Stregkode-kolonnenavn"),
    )
    product_name_col = forms.CharField(
        initial=defaults["product_name"],
        label=_("Produktnavn-kolonnenavn"),
    )
    material_col = forms.CharField(
        initial=defaults["material"],
        label=_("Materiale-kolonnenavn"),
    )
    height_col = forms.CharField(
        initial=defaults["height"],
        label=_("Højde-kolonnenavn"),
    )
    diameter_col = forms.CharField(
        initial=defaults["diameter"],
        label=_("Diameter-kolonnenavn"),
    )
    weight_col = forms.CharField(
        initial=defaults["weight"],
        label=_("Vægt-kolonnenavn"),
    )
    capacity_col = forms.CharField(
        initial=defaults["capacity"],
        label=_("Volumen-kolonnenavn"),
    )
    shape_col = forms.CharField(
        initial=defaults["shape"],
        label=_("Form-kolonnenavn"),
    )
    danish_col = forms.CharField(
        initial=defaults["danish"],
        label=_("Dansk pant-kolonnenavn"),
    )

    def __init__(self, *args, **kwargs):
        self.filename = None
        self.rename_dict = {}
        self.df = pd.DataFrame()
        self.valid_extensions = [".csv", ".xlsx", ".xls"]

        self.valid_extensions_str = join_strings_human_readable(
            ["'{ext}'".format(ext=ext) for ext in self.valid_extensions]
        )
        self.valid_materials = make_valid_choices_str(PRODUCT_MATERIAL_CHOICES)
        self.valid_shapes = make_valid_choices_str(PRODUCT_SHAPE_CHOICES)
        self.valid_danish_strings = make_valid_choices_str(DANISH_PANT_CHOICES)

        super().__init__(*args, **kwargs)

    def validate_that_column_exists(self, col):
        """
        Validate that a field is a column in the dataframe. Returns True if the
        column is found, False if it is not.
        """
        if len(self.df.columns) <= 1:
            # These errors are caught by clean_sep and clean_file
            # No need to report them here also
            return False
        elif col not in self.df.columns:
            raise ValidationError(
                _("Ugyldig header: '{col}' er ikke i datafilens første række.").format(
                    col=col
                )
            )
        return True

    def validate_column_contents(self, col, choices, error_message=""):
        """
        Check that all values in a column are among a set of choices
        """
        valid_contents = [c[0] for c in choices]
        valid_choices_str = make_valid_choices_str(choices)

        if not error_message:
            error_message = _("Gyldige valgmuligheder er: {valid_choices_str}.").format(
                valid_choices_str=valid_choices_str
            )

        for row_number in self.df.index:
            value = self.df.loc[row_number, col]
            if value not in valid_contents:
                raise ValidationError(
                    mark_safe(
                        _(
                            "'{value}' i række {row_number} er ugyldigt. "
                            "{error_message}"
                        ).format(
                            value=value,
                            row_number=row_number,
                            error_message=error_message,
                        )
                    )
                )

    def validate_barcodes(self, barcode_col):
        for row_number in self.df.index:
            barcode = self.df.loc[row_number, barcode_col]
            try:
                validate_barcode_length(barcode)
                validate_digit(barcode)
            except ValidationError as e:
                raise ValidationError(
                    _(
                        "Stregkode '{barcode}' i række {row_number} er ugyldig: "
                        "{error}."
                    ).format(barcode=barcode, row_number=row_number, error=e.message)
                )

    def validate_uniqueness(self, col):
        """
        Validate that there are no duplicate values in a column
        """
        duplicates = self.df.duplicated(col, keep=False)

        rows_with_duplicates = self.df.index[duplicates].astype(str)
        duplicate_values = self.df.loc[duplicates, col].unique().astype(str)

        duplicate_values_str = join_strings_human_readable(duplicate_values)
        rows_with_duplicates_str = join_strings_human_readable(rows_with_duplicates)

        number_of_duplicates = len(duplicate_values)

        if number_of_duplicates == 1:
            raise ValidationError(
                _(
                    "Værdi '{duplicate_values_str}' er ikke unik. "
                    "Der er dubletter i række {rows_with_duplicates_str}."
                ).format(
                    duplicate_values_str=duplicate_values_str,
                    rows_with_duplicates_str=rows_with_duplicates_str,
                )
            )
        elif number_of_duplicates > 1:
            raise ValidationError(
                _(
                    "Værdier '{duplicate_values_str}' er ikke unikke. "
                    "Der er dubletter i række {rows_with_duplicates_str}."
                ).format(
                    duplicate_values_str=duplicate_values_str,
                    rows_with_duplicates_str=rows_with_duplicates_str,
                )
            )

    def validate_positive_integer(self, col):
        """
        Check that contents of a column are integer
        """
        if self.df.dtypes[col] == "object":
            raise ValidationError(_("Kolonne indeholder værdier som ikke er tal."))

        for row_number in self.df.index:
            value = self.df.loc[row_number, col]

            if pd.isnull(value):
                raise ValidationError(
                    _("Række {row_number} er tom.").format(row_number=row_number)
                )
            elif int(value) != value:
                raise ValidationError(
                    _(
                        "Værdien '{value}' i række {row_number} er ikke en hel værdi."
                    ).format(value=value, row_number=row_number)
                )
            elif value < 0:
                raise ValidationError(
                    _("Værdien '{value}' i række {row_number} er negativ.").format(
                        value=value, row_number=row_number
                    )
                )

    def clean_file(self):
        data = self.cleaned_data["file"]
        validate_file_extension(data, self.valid_extensions)
        sheet_name = self.cleaned_data["sheet_name"]
        sep = self.data["sep"]

        dtype = {self.data["barcode_col"]: str}
        if data.content_type == "text/csv":
            df = read_csv(data, sep=sep, dtype=dtype)
        else:
            df = read_excel(data, dtype=dtype, sheet_name=sheet_name)

        # Update index so it resembles the row-number in excel
        df.index = [i + 2 for i in df.index]

        self.filename = data.name
        self.df = df
        return data

    def clean_sep(self):
        sep = self.cleaned_data["sep"]
        if len(self.df.columns) == 1:
            raise ValidationError(
                _(
                    "Kun en kolonne fundet i datafilen. "
                    "Er CSV separator = '{sep}' rigtig?"
                ).format(sep=sep)
            )
        return sep

    def clean_product_name_col(self):
        col_name = self.cleaned_data["product_name_col"]
        self.rename_dict[col_name] = "product_name"
        self.validate_that_column_exists(col_name)
        return col_name

    def clean_barcode_col(self):
        col_name = self.cleaned_data["barcode_col"]
        self.rename_dict[col_name] = "barcode"
        column_exists = self.validate_that_column_exists(col_name)
        if column_exists:
            self.validate_barcodes(col_name)
            self.validate_uniqueness(col_name)
        return col_name

    def clean_material_col(self):
        col_name = self.cleaned_data["material_col"]
        self.rename_dict[col_name] = "material"
        column_exists = self.validate_that_column_exists(col_name)
        if column_exists:
            self.validate_column_contents(col_name, PRODUCT_MATERIAL_CHOICES)
        return col_name

    def clean_height_col(self):
        col_name = self.cleaned_data["height_col"]
        self.rename_dict[col_name] = "height"
        column_exists = self.validate_that_column_exists(col_name)
        if column_exists:
            self.validate_positive_integer(col_name)
        return col_name

    def clean_diameter_col(self):
        col_name = self.cleaned_data["diameter_col"]
        self.rename_dict[col_name] = "diameter"
        column_exists = self.validate_that_column_exists(col_name)
        if column_exists:
            self.validate_positive_integer(col_name)
        return col_name

    def clean_weight_col(self):
        col_name = self.cleaned_data["weight_col"]
        self.rename_dict[col_name] = "weight"
        column_exists = self.validate_that_column_exists(col_name)
        if column_exists:
            self.validate_positive_integer(col_name)
        return col_name

    def clean_capacity_col(self):
        col_name = self.cleaned_data["capacity_col"]
        self.rename_dict[col_name] = "capacity"
        column_exists = self.validate_that_column_exists(col_name)
        if column_exists:
            self.validate_positive_integer(col_name)
        return col_name

    def clean_shape_col(self):
        col_name = self.cleaned_data["shape_col"]
        self.rename_dict[col_name] = "shape"
        column_exists = self.validate_that_column_exists(col_name)
        if column_exists:
            self.validate_column_contents(col_name, PRODUCT_SHAPE_CHOICES)
        return col_name

    def clean_danish_col(self):
        col_name = self.cleaned_data["danish_col"]
        self.rename_dict[col_name] = "danish"
        column_exists = self.validate_that_column_exists(col_name)
        if column_exists:
            self.validate_column_contents(col_name, DANISH_PANT_CHOICES)
