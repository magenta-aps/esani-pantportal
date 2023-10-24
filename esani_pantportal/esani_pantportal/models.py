# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext as _


# Custom validators
def validate_barcode_length(barcode: str):
    if not len(barcode) in [8, 12, 13]:
        raise ValidationError(_("Stregkoden skal være 8, 12 eller 13 cifre lang"))


def validate_digit(string: str):
    if not string.isdigit():
        raise ValidationError(_("Stregkoden må kun bestå af tal"))


PRODUCT_MATERIAL_CHOICES = [
    ("P", "PET"),
    ("A", "Aluminium"),
    ("S", "Stål"),
    ("G", "Glas"),
]

PRODUCT_SHAPE_CHOICES = [
    ("F", "Flaske"),
    ("A", "Anden"),
]


class Company(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=["name", "cvr"]),
        ]

    name = models.CharField(
        verbose_name=_("Firmanavn"),
        help_text=_("Firmanavn"),
        max_length=255,
    )
    cvr = models.PositiveIntegerField(
        verbose_name=_("CVR Nummer"),
        help_text=_("CVR Nummer"),
        unique=True,
    )
    address = models.CharField(
        verbose_name=_("Addresse"),
        help_text=_("Firmaets registrerede addresse"),
        max_length=400,
    )
    phone = models.PositiveIntegerField(
        verbose_name=_("Telefonnummer"),
        help_text=_("Firmaets telefonnummer inkl. landekode"),
    )
    permit_number = models.PositiveIntegerField(
        verbose_name=_("Tilladelsesnummer"),
        help_text=_(
            "Firmaets tilladelsesnummer for import af ethanolholdige drikkevarer"
        ),
        null=True,
        blank=True,
    )


class PackagingRegistration(models.Model):
    class Meta:
        ordering = ["date"]

    registration_number = models.PositiveIntegerField(
        verbose_name=_("Afgiftsanmeldelsesnummer"),
        help_text=_("Afgiftsanmeldelsesnummer"),
        unique=True,
    )
    registration_company = models.ForeignKey(
        "Company",
        verbose_name=_("Anmelder"),
        help_text=_("Firma ansvarligt for afgiftsanmeldelsen"),
        on_delete=models.PROTECT,
        related_name="registered_packaging",
    )
    recipient_company = models.ForeignKey(
        "Company",
        verbose_name=_("Varemodtager"),
        help_text=_("Firma, som skal modtage varerne og betale pant"),
        on_delete=models.PROTECT,
        related_name="received_packaging",
    )
    date = models.DateField(
        _("Dato"),
        auto_now_add=True,
        db_index=True,
    )


class ProductLine(models.Model):
    packaging_registration = models.ForeignKey(
        PackagingRegistration,
        on_delete=models.CASCADE,
    )

    quantity = models.PositiveIntegerField(
        verbose_name=_("Antal"),
        help_text=_("Styks pant-pligtig emballage importeret"),
    )
    product = models.ForeignKey(
        "Product",
        verbose_name=_("Produkt"),
        help_text=_("Indmeldte produkt"),
        on_delete=models.PROTECT,
        related_name="product_line",
    )


class Product(models.Model):
    class Meta:
        ordering = ["product_name", "barcode"]
        permissions = [
            (
                "approve_product",
                "User is allowed to approve products awaiting registration",
            )
        ]

    product_name = models.CharField(
        verbose_name=_("Produktnavn"),
        help_text=_("Navn på det pågældende produkt"),
        max_length=200,
    )
    barcode = models.CharField(
        verbose_name=_("Stregkode"),
        help_text=_("Stregkode for et indmeldt produkt"),
        unique=True,
        validators=[validate_barcode_length, validate_digit],
    )
    refund_value = models.PositiveIntegerField(
        verbose_name=_("Pantværdi"),
        help_text=_("Pantværdi, angivet i øre (100=1DKK, 25=0.25DKK)"),
        default=200,  # 2kr.
    )
    approved = models.BooleanField(
        verbose_name=_("Godkendt"),
        help_text=_("Produkt godkendt til pantsystemet af en ESANI medarbejder"),
        default=False,
    )
    material = models.CharField(
        verbose_name=_("Materiale"),
        help_text=_("Kategori for emballagens materiale."),
        choices=PRODUCT_MATERIAL_CHOICES,
    )
    height = models.PositiveIntegerField(
        verbose_name=_("Højde"),
        help_text=_("Emballagens højde i millimeter"),
    )
    diameter = models.PositiveIntegerField(
        verbose_name=_("Diameter"),
        help_text=_("Emballagens diameter i millimeter"),
    )
    weight = models.PositiveIntegerField(
        verbose_name=_("Vægt"),
        help_text=_("Tør/tom vægt af emballagen i gram"),
    )
    capacity = models.PositiveIntegerField(
        verbose_name=_("Volumen"),
        help_text=_("Emballagens volumen i milliliter"),
    )
    shape = models.CharField(
        verbose_name=_("Form"),
        help_text=_("Kategori for emballagens form."),
        choices=PRODUCT_SHAPE_CHOICES,
    )
