from django.db import models


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
    cvr = models.IntegerField(
        verbose_name=_("CVR Nummer"),
        help_text=_("CVR Nummer"),
        unique=True,
    )
    address = models.CharField(
        verbose_name=_("Addresse"),
        help_text=_("Firmaets registrerede addresse"),
        max_length=400,
    )
    phone = models.IntegerField(
        verbose_name=_("Telefonnummer"),
        help_text=_("Firmaets telefonnummer inkl. landekode"),
    )
    tilladelsesnummer = models.IntegerField(
        verbose_name=_("Tilladelsesnummer"),
        help_text=_(
            "Firmaets tilladelsesnummer for import af ethanolholdige drikkevarer"
        ),
        null=True,
        blank=True,
    )


class PackagingRegistration(models.Model):
    class Meta:
        ordering = ["registration_nuber"]

    registration_number = models.IntegerField(
        verbose_name=_("Afgiftsanmeldelsesnummer"),
        help_text=_("Afgiftsanmeldelsesnummer"),
        unique=True,
    )
    company = models.ForeignKey(
        "Company",
        on_delete=models.PROTECT,
        related_name="packaging_registration",
    )
    tax_group = models.IntegerField(
        verbose_name=_("Afgiftsgruppe"),
        help_text=_("Afgiftsgruppe"),
    )
    product_type = models.CharField(
        verbose_name=_("Vareart"),
        help_text=_("Vareart"),
        max_length=200,
    )
    quantity = models.IntegerField(
        verbose_name=_("Antal"),
        help_text=_("Styks pant-pligtig emballage importeret"),
    )
