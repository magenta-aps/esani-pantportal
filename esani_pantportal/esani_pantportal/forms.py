import os

import pandas as pd
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

from esani_pantportal.form_mixins import BootstrapForm, MaxSizeFileField

from esani_pantportal.util import (  # isort: skip
    read_csv,
    read_excel,
    make_valid_choices_str,
    join_strings_human_readable,
)

from esani_pantportal.models import (  # isort: skip
    Product,
    PRODUCT_MATERIAL_CHOICES,
    PRODUCT_SHAPE_CHOICES,
    TAX_GROUP_CHOICES,
    validate_digit,
    validate_barcode_length,
)


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
            "tax_group",
        )


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
    refund_value_col = forms.CharField(
        initial=defaults["refund_value"],
        label=_("Pantværdi-kolonnenavn"),
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
    tax_group_col = forms.CharField(
        initial=defaults["tax_group"],
        label=_("Afgiftsgruppe-kolonnenavn"),
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
        self.tax_groups_link = mark_safe(
            f'<a href="{reverse("pant:tax_groups")}" target="_blank">'
            + _("her")
            + "</a>"
        )

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

    def clean_refund_value_col(self):
        col_name = self.cleaned_data["refund_value_col"]
        self.rename_dict[col_name] = "refund_value"
        column_exists = self.validate_that_column_exists(col_name)
        if column_exists:
            self.validate_positive_integer(col_name)
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

    def clean_tax_group_col(self):
        col_name = self.cleaned_data["tax_group_col"]
        self.rename_dict[col_name] = "tax_group"
        column_exists = self.validate_that_column_exists(col_name)
        if column_exists:
            self.validate_column_contents(
                col_name,
                TAX_GROUP_CHOICES,
                error_message=_("Gyldige afgiftsgrupper er defineret {her}.").format(
                    her=self.tax_groups_link
                ),
            )
        return col_name
