from django import forms
from django.utils.translation import gettext_lazy as _

from esani_pantportal.form_mixins import BootstrapForm
from esani_pantportal.models import Product


class ProductRegisterForm(forms.ModelForm, BootstrapForm):
    class Meta:
        model = Product
        fields = (
            "product_name",
            "barcode",
            "tax_group",
            "product_type",
            "material_type",
            "height",
            "diameter",
            "weight",
            "capacity",
            "shape",
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
