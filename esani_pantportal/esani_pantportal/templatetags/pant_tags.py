from urllib.parse import quote

from django.conf import settings
from django.template.defaultfilters import register
from django.utils.translation import gettext_lazy as _

from esani_pantportal.models import (
    PRODUCT_SHAPE_CHOICES,
    REFUND_METHOD_CHOICES,
    USER_TYPE_CHOICES,
)


@register.filter
def verbose_name(item, field):
    return item._meta.get_field(field).verbose_name.title()


@register.filter
def quote_url(url):
    return quote(url)


@register.filter
def get_display_name(obj, attr):
    """
    Returns the display name of an object field
    """
    try:
        return getattr(obj, f"get_{attr}_display")()
    except AttributeError:
        return str(getattr(obj, attr) or _("Udefineret"))


@register.filter
def user_type(user_type_id):
    for c in USER_TYPE_CHOICES:
        if c[0] == user_type_id:
            return c[1]


@register.filter
def refund_method(refund_method_id):
    for c in REFUND_METHOD_CHOICES:
        if c[0] == refund_method_id:
            return c[1]


@register.filter
def is_user_object(obj):
    return True if obj._meta.verbose_name.endswith("user") else False


@register.filter
def yesno(boolean):
    return _("Ja") if boolean else _("Nej")


@register.filter
def constraints_string(key, unit):
    product_constraints = settings.PRODUCT_CONSTRAINTS
    product_shape_dict = {p[0]: p[1] for p in PRODUCT_SHAPE_CHOICES}
    output = []
    for shape, [minv, maxv] in product_constraints[key].items():
        if shape != "A":
            output += [product_shape_dict[shape] + f": [{minv}-{maxv}{unit}]"]
    return ", ".join(output)
