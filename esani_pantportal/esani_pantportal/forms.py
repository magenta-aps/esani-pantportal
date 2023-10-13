from django.forms import ModelForm

from esani_pantportal.form_mixins import BootstrapForm
from esani_pantportal.models import Product


class ProductRegisterForm(ModelForm, BootstrapForm):
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
