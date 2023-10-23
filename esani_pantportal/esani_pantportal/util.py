# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0


import pandas as pd
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from esani_pantportal.models import (  # isort: skip
    PRODUCT_MATERIAL_CHOICES,
    PRODUCT_SHAPE_CHOICES,
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

    material_types = iter([p[0] for p in PRODUCT_MATERIAL_CHOICES])
    shapes = iter([p[0] for p in PRODUCT_SHAPE_CHOICES] * 2)

    for i in range(4):
        df.loc[i, defaults["product_name"]] = f"Produkt {i}"
        df.loc[i, defaults["barcode"]] = f"0000000{i}"
        df.loc[i, defaults["refund_value"]] = 200
        df.loc[i, defaults["tax_group"]] = 2
        df.loc[i, defaults["product_type"]] = "Øl"
        df.loc[i, defaults["material_type"]] = next(material_types)
        df.loc[i, defaults["height"]] = 150
        df.loc[i, defaults["diameter"]] = 20
        df.loc[i, defaults["weight"]] = 200
        df.loc[i, defaults["capacity"]] = 33
        df.loc[i, defaults["shape"]] = next(shapes)
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
