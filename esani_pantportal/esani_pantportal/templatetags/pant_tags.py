# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
from urllib.parse import quote

from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.db.models import BooleanField
from django.template.defaultfilters import register, yesno
from django.utils.translation import gettext_lazy as _

from esani_pantportal.models import (
    BRANCH_TYPE_CHOICES,
    COMPANY_TYPE_CHOICES,
    DANISH_PANT_CHOICES,
    PRODUCT_MATERIAL_CHOICES,
    PRODUCT_SHAPE_CHOICES,
    USER_TYPE_CHOICES,
)
from esani_pantportal.util import add_parameters_to_url


@register.filter
def add_back_url(url, back_url):
    return add_parameters_to_url(url, {"back": quote(back_url)})


@register.filter
def verbose_name(item, field):
    try:
        name = item._meta.get_field(field).verbose_name
    except FieldDoesNotExist:
        return item.get_field_name(field)
    else:
        if name and name[0].isupper():
            return name
        else:
            return name.capitalize()


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
        value = getattr(obj, attr, None)
        field = None
        try:
            # Look for field on model instance
            field = obj._meta.get_field(attr)
        except FieldDoesNotExist:
            try:
                # Look for field in annotations
                query = obj._meta.default_manager.get_queryset().query
                annotation = query.annotations[attr]
                field = annotation.output_field
            except (AttributeError, KeyError):
                pass
        if isinstance(field, BooleanField):
            return yesno(value, _("Ja,Nej"))
        return str(value or _("Udefineret"))


@register.filter
def user_type(user_type_id):
    for c in USER_TYPE_CHOICES:
        if c[0] == user_type_id:
            return c[1]


@register.filter
def material(material_id):
    for c in PRODUCT_MATERIAL_CHOICES:
        if c[0] == material_id:
            return c[1]


@register.filter
def shape(shape_id):
    for c in PRODUCT_SHAPE_CHOICES:
        if c[0] == shape_id:
            return c[1]


@register.filter
def company_type(company_type_id):
    for c in COMPANY_TYPE_CHOICES:
        if c[0] == company_type_id:
            return c[1]


@register.filter
def branch_type(branch_type_id):
    for c in BRANCH_TYPE_CHOICES:
        if c[0] == branch_type_id:
            return c[1]


@register.filter
def danish(danish_id):
    for c in DANISH_PANT_CHOICES:
        if c[0] == danish_id:
            return c[1]


@register.filter
def constraints_string(key, unit):
    product_constraints = settings.PRODUCT_CONSTRAINTS
    product_shape_dict = {p[0]: p[1] for p in PRODUCT_SHAPE_CHOICES}
    output = []
    for shape, [minv, maxv] in product_constraints[key].items():
        if shape != "A":
            output += [product_shape_dict[shape] + f": [{minv}-{maxv}{unit}]"]
    return ", ".join(output)


@register.filter
def truefalse(boolean):
    return "true" if boolean else "false"


@register.filter
def has_two_factor(user):
    return user.totpdevice_set.count() > 0


@register.filter
def get(dictionary, key):
    return dictionary[key]
