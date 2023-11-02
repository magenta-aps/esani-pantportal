# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0


from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import pandas as pd
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from esani_pantportal.models import (  # isort: skip
    PRODUCT_MATERIAL_CHOICES,
    PRODUCT_SHAPE_CHOICES,
    TAX_GROUP_CHOICES,
    DANISH_PANT_CHOICES,
)


def read_csv(*args, **kwargs):
    """
    Read a csv file and throw validationError if unsuccessful
    """
    try:
        return pd.read_csv(*args, **kwargs)
    except Exception as e:
        raise ValidationError(e)


def read_excel(*args, **kwargs):
    """
    Read an excel file and throw validationError if unsuccessful
    """
    try:
        return pd.read_excel(*args, **kwargs)
    except Exception as e:
        raise ValidationError(e)


def default_dataframe():
    """
    Returns a dataframe with default column titles and some example values
    """

    defaults = settings.DEFAULT_CSV_HEADER_DICT
    df = pd.DataFrame(columns=defaults.values())

    materials = iter([p[0] for p in PRODUCT_MATERIAL_CHOICES])
    shapes = iter([p[0] for p in PRODUCT_SHAPE_CHOICES] * 2)
    tax_groups = iter([p[0] for p in TAX_GROUP_CHOICES])
    danish = iter([p[0] for p in DANISH_PANT_CHOICES] * 2)

    for i in range(4):
        df.loc[i, defaults["product_name"]] = f"Produkt {i}"
        df.loc[i, defaults["barcode"]] = f"0000000{i}"
        df.loc[i, defaults["refund_value"]] = 200
        df.loc[i, defaults["material"]] = next(materials)
        df.loc[i, defaults["height"]] = 150
        df.loc[i, defaults["diameter"]] = 20
        df.loc[i, defaults["weight"]] = 200
        df.loc[i, defaults["capacity"]] = 33
        df.loc[i, defaults["shape"]] = next(shapes)
        df.loc[i, defaults["tax_group"]] = next(tax_groups)
        df.loc[i, defaults["danish"]] = next(danish)
    return df


def join_strings_human_readable(strings: list[str]):
    """
    Joins strings together in a gramatically correct way.
    """
    if len(strings) == 0:
        return ""
    elif len(strings) == 1:
        return strings[0]
    else:
        return ", ".join(strings[:-1]) + " " + _("og") + " " + strings[-1]


def make_valid_choices_str(choices):
    """
    takes a  'choices' tuple and returns a human-readable string
    """
    return join_strings_human_readable([f"'{c[0]}' ({c[1]})" for c in choices])


def remove_parameter_from_url(url, key_to_remove):
    """
    Remove a parameter from an URL.
    """
    u = urlparse(url)
    query = parse_qs(u.query, keep_blank_values=True)
    query.pop(key_to_remove, None)
    u = u._replace(query=urlencode(query, True))
    return urlunparse(u)
