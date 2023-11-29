# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

import hashlib
import random
import string

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models, transaction
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

DANISH_PANT_CHOICES = [
    ("J", "Ja"),
    ("N", "Nej"),
    ("U", "Ukendt"),
]


REFUND_METHOD_CHOICES = [
    ("K", "Flaskeautomat m/komprimator"),
    ("S", "Flaskeautomat m/sikkerhedscontainer"),
    ("SK", "Flaskeautomat m/komprimator m/sikkerhedscontainer"),
    ("S", "Sække"),
    ("M", "Manuel sortering"),
    ("A", "Anden"),
]


ESANI_USER = 1
BRANCH_USER = 2
COMPANY_USER = 3
KIOSK_USER = 4

USER_TYPE_CHOICES = (
    (ESANI_USER, "Esanibruger"),
    (BRANCH_USER, "Butiksbruger"),
    (COMPANY_USER, "Virksomhedsbruger"),
    (KIOSK_USER, "Kioskbruger"),
)

BRANCH_TYPE_CHOICES = (
    ("D", "Detail"),
    ("H", "Hotel/Restauration/Bar"),
    ("F", "Forening"),
    ("A", "Andet"),
)

COMPANY_TYPE_CHOICES = (
    ("E", "Eksportør"),
    ("A", "Andet"),
)


class AbstractCompany(models.Model):
    class Meta:
        abstract = True

    name = models.CharField(
        verbose_name=_("Navn"),
        help_text=_("Firma eller butiksnavn"),
        max_length=255,
    )
    address = models.CharField(
        verbose_name=_("Adresse"),
        help_text=_("Butikken eller firmaets registrerede adresse"),
        max_length=255,
    )

    postal_code = models.CharField(
        verbose_name=_("Postnr."),
        help_text=_("Butikken eller firmaets registrerede postnummer"),
        max_length=10,
    )

    municipality = models.CharField(
        verbose_name=_("Kommune"),
        help_text=_("Butikken eller firmaets registrerede kommunenavn"),
        max_length=255,
    )

    city = models.CharField(
        verbose_name=_("By"),
        help_text=_("Butikken eller firmaets registrerede bynavn"),
        max_length=255,
    )

    phone = models.CharField(
        verbose_name=_("Telefonnummer"),
        help_text=_("Butikken eller firmaets telefonnummer inkl. landekode"),
        max_length=30,
    )

    registration_number = models.PositiveIntegerField(
        verbose_name=_("reg. nr."),
        help_text=_("Pant konto reg. nr. (valgfri)"),
        null=True,
        blank=True,
        default=None,
    )

    account_number = models.PositiveIntegerField(
        verbose_name=_("konto nr."),
        help_text=_("Pant konto nr. (valgfri)"),
        null=True,
        blank=True,
        default=None,
    )

    invoice_mail = models.EmailField(
        verbose_name=_("Faktura mail"),
        help_text=_("Mail adresse som faktura skal sendes til (valgfri)"),
        null=True,
        blank=True,
        default=None,
    )

    esani_customer_id = models.PositiveIntegerField(
        verbose_name=_("Konto"),
        help_text=_("Butikkens kontonummer hos ESANI (udfyldes af ESANI)"),
        null=True,
        blank=True,
        default=None,
    )


class Company(AbstractCompany):
    cvr = models.PositiveIntegerField(
        verbose_name=_("CVR Nummer"),
        help_text=_("CVR Nummer"),
        unique=True,
    )
    permit_number = models.PositiveIntegerField(
        verbose_name=_("Tilladelsesnummer"),
        help_text=_(
            "Firmaets tilladelsesnummer for import "
            "af ethanolholdige drikkevarer (valgfri)"
        ),
        null=True,
        blank=True,
    )

    company_type = models.CharField(
        verbose_name=_("Virksomhedstype"),
        help_text=_("Virksomhedstype"),
        choices=COMPANY_TYPE_CHOICES,
    )

    country = models.CharField(
        verbose_name=_("Land"),
        help_text=_("Butikken eller firmaets registrerede landenavn"),
        max_length=255,
    )

    def __str__(self):
        name = self.name
        cvr = self.cvr
        return f"{name} - cvr: {cvr}"


class Branch(AbstractCompany):
    class Meta:
        abstract = True

    location_id = models.PositiveIntegerField(
        verbose_name=_("LokationsID"),
        help_text=_("Butikkens lokation ID (valgfri)"),
        null=True,
        blank=True,
        default=None,
    )

    customer_id = models.PositiveIntegerField(
        verbose_name=_("Kundenummer"),
        help_text=_("Butikkens kundenummer hos Tomra (valgfri)"),
        null=True,
        blank=True,
    )

    branch_type = models.CharField(
        verbose_name=_("Branche"),
        help_text=_("Branche-type"),
        choices=BRANCH_TYPE_CHOICES,
    )


class CompanyBranch(Branch):
    company = models.ForeignKey(
        "Company",
        verbose_name=_("Virksomhed"),
        help_text=_("Virksomhed som denne butik tilhører"),
        on_delete=models.PROTECT,
        related_name="company",
    )

    def __str__(self):
        name = self.name
        company = self.company
        return f"{name} - {company}"


class Kiosk(Branch):
    cvr = models.PositiveIntegerField(
        verbose_name=_("CVR Nummer"),
        help_text=_("CVR Nummer"),
        unique=True,
    )

    permit_number = models.PositiveIntegerField(
        verbose_name=_("Tilladelsesnummer"),
        help_text=_(
            "Butikkens tilladelsesnummer for import "
            "af ethanolholdige drikkevarer (valgfri)"
        ),
        null=True,
        blank=True,
    )

    def __str__(self):
        name = self.name
        cvr = self.cvr
        return f"{name} - cvr: {cvr}"


class RefundMethod(models.Model):
    # Note: Compensation seems to be dependent on the kind of machine a branch has.
    # See
    # https://danskretursystem.dk/app/uploads/2023/05/Haandteringsgodtgoerelse_2023.pdf
    # For a possible (future?) scenario.
    compensation = models.PositiveIntegerField(
        verbose_name=_("Håndterings-godtgørelse"),
        help_text=_("Håndterings-godtgørelse, angivet i øre (100=1DKK, 25=0.25DKK)"),
        default=0,
    )

    serial_number = models.CharField(
        verbose_name=_("Serienummer"),
        help_text=_("Maskinens serienummer"),
        null=True,
        blank=True,
    )

    method = models.CharField(
        verbose_name=_("Pantmetode"),
        help_text=_("Måden at pant bliver registreret på"),
        choices=REFUND_METHOD_CHOICES,
    )

    branch = models.ForeignKey(
        "CompanyBranch",
        verbose_name=_("Kæde"),
        help_text=_("Kæde hvor denne maskine står"),
        on_delete=models.PROTECT,
        related_name="kæde",
        null=True,
        blank=True,
        default=None,
    )

    kiosk = models.ForeignKey(
        "Kiosk",
        verbose_name=_("Butik"),
        help_text=_("Butik hvor denne maskine står"),
        on_delete=models.PROTECT,
        related_name="kiosk",
        null=True,
        blank=True,
        default=None,
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

    created_by = models.ForeignKey(
        "User",
        related_name="products",
        on_delete=models.SET_NULL,  # Vi kan slette brugere og beholde deres anmeldelser
        null=True,
        verbose_name=_("Oprettet af"),
    )

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
        default=settings.DEFAULT_REFUND_VALUE,  # 2kr.
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
    danish = models.CharField(
        verbose_name=_("Dansk pant"),
        help_text=_("Der er Dansk pant på dette produkt"),
        default="U",
        choices=DANISH_PANT_CHOICES,
    )


class QRCodeGenerator(models.Model):
    """Class for generating QR codes."""

    count = models.PositiveIntegerField(
        verbose_name=_("Antal QR-koder"),
        help_text="Antal QR-koder genereret indtil nu",
        default=0,  # Always start at zero.
    )
    name = models.CharField(
        verbose_name=_("Navn"),
        help_text=_("Navn på denne serie af QR-koder"),
        unique=True,
        blank=False,
        max_length=200,
    )
    prefix = models.PositiveIntegerField(unique=True)

    def _get_salt(self, qr_seqno):
        """Return salt used for this sequence number if available"""

        salt = ""
        if 0 <= qr_seqno < self.count:
            # Code is in range.
            for i in self.intervals.all():
                # This could be done more elegantly with an interval dictionary
                # but performance-wise it's not going to matter.
                if i.start <= qr_seqno < i.start + i.increment:
                    salt = i.salt
        return salt

    @staticmethod
    def _generate_qr(qr_seqno, salt, prefix):
        id_str = str(qr_seqno).zfill(settings.QR_ID_LENGTH)
        cc_generator = hashlib.sha256()
        cc_generator.update((id_str + salt).encode("utf8"))
        control_code = cc_generator.hexdigest()[: settings.QR_HASH_LENGTH]
        url_prefix = settings.QR_URL_PREFIX

        return f"{url_prefix}{prefix}{id_str}{control_code}"

    def generate_qr_codes(self, increment, salt=None):
        """Generate a new batch of QR codes"""

        with transaction.atomic():
            if not salt:
                # Generate random string to use as salt.
                salt = "".join(random.choice(string.ascii_letters) for i in range(128))

            new_interval = QRCodeInterval(
                generator=self, start=self.count, increment=increment, salt=salt
            )
            # The necessary data are in place - now generate list of QR codes.
            qr_codes = [
                self._generate_qr(self.count + i, salt, self.prefix)
                for i in range(increment)
            ]
            # Save changes
            self.count = self.count + increment
            self.save()
            new_interval.save()
        # And return
        return qr_codes

    def check_qr_code(self, qr_code):
        """Parse QR code, return ID if successful"""
        qr_id = None
        # Do the parsing
        # First, check that the QR code looks right
        expected_qr_length = (
            len(settings.QR_URL_PREFIX)
            + len(str(self.prefix))
            + settings.QR_ID_LENGTH
            + settings.QR_HASH_LENGTH
        )
        expected_prefix = settings.QR_URL_PREFIX + str(self.prefix)
        if len(qr_code) != expected_qr_length or not qr_code.startswith(
            expected_prefix
        ):
            # Not a QR code generated by us - wrong format
            return None
        qr_id = qr_code.removeprefix(expected_prefix)[0 : settings.QR_ID_LENGTH]

        # Find salt for this ID
        try:
            qr_seqno = int(qr_id.lstrip("0") or "0")
        except ValueError:
            # Not a QR code generated by us.
            return None

        salt = self._get_salt(qr_seqno)

        check_qr = self._generate_qr(qr_seqno, salt, self.prefix)

        if qr_code == check_qr:
            return str(self.prefix) + qr_id
        else:
            # Not a QR code generated by us - wrong control digits
            return None

    def __str__(self):
        return f"{self.name} - {self.prefix} ({self.count})"


class QRCodeInterval(models.Model):
    """Intervals generated for at given QR code"""

    class Meta:
        ordering = ["start"]

    generator = models.ForeignKey(
        QRCodeGenerator,
        on_delete=models.CASCADE,
        related_name="intervals",
    )

    start = models.PositiveIntegerField()
    increment = models.PositiveIntegerField()
    salt = models.CharField(max_length=200)

    def __str__(self):
        gen_name = self.generator.name
        start = self.start
        end = self.start + self.increment
        return f"{gen_name}[{start}:{end}] - {self.salt}"


class User(AbstractUser):
    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"
        abstract = False
        ordering = ["username"]

    user_type = models.PositiveSmallIntegerField(choices=USER_TYPE_CHOICES)

    phone = models.CharField(
        verbose_name=_("Telefonnummer"),
        help_text=_("Brugerens telefonnummer inkl. landekode"),
        max_length=30,
    )

    approved = models.BooleanField(
        verbose_name=_("Godkendt"),
        help_text=_("Bruger godkendt af en ESANI medarbejder"),
        default=False,
        choices=((True, "Ja"), (False, "Nej")),
    )

    @property
    def user_profile(self):
        if self.user_type == BRANCH_USER:
            return BranchUser.objects.get(username=self.username)
        elif self.user_type == KIOSK_USER:
            return KioskUser.objects.get(username=self.username)
        elif self.user_type == ESANI_USER:
            return EsaniUser.objects.get(username=self.username)
        elif self.user_type == COMPANY_USER:
            return CompanyUser.objects.get(username=self.username)

    @property
    def branch(self):
        if self.user_type in [BRANCH_USER, KIOSK_USER]:
            return self.user_profile.branch
        else:
            return None

    @property
    def company(self):
        if self.user_type == BRANCH_USER:
            return self.user_profile.branch.company
        elif self.user_type == COMPANY_USER:
            return self.user_profile.company
        else:
            return None


class EsaniUser(User):
    class Meta:
        verbose_name = "esaniuser"
        verbose_name_plural = "esaniusers"
        abstract = False

    def save(self, *args, **kwargs):
        self.user_type = ESANI_USER
        self.approved = True
        return super().save(*args, **kwargs)

    def __str__(self):
        username = self.username
        return f"{username} - ESANI User"


class BranchUser(User):
    class Meta:
        verbose_name = "branchuser"
        verbose_name_plural = "branchusers"
        abstract = False

    branch = models.ForeignKey(
        "CompanyBranch",
        verbose_name=_("Butik"),
        help_text=_("Butik hvor denne bruger arbejder"),
        on_delete=models.PROTECT,
        related_name="user_branch",
    )

    def save(self, *args, **kwargs):
        self.user_type = BRANCH_USER
        return super().save(*args, **kwargs)

    def __str__(self):
        username = self.username
        return f"{username} - Branch User"


class CompanyUser(User):
    class Meta:
        verbose_name = "companyuser"
        verbose_name_plural = "companyusers"
        abstract = False

    company = models.ForeignKey(
        "Company",
        verbose_name=_("Virksomhed"),
        help_text=_("Virksomhed hvor denne bruger arbejder"),
        on_delete=models.PROTECT,
        related_name="user_company",
    )

    def save(self, *args, **kwargs):
        self.user_type = COMPANY_USER
        return super().save(*args, **kwargs)

    def __str__(self):
        username = self.username
        return f"{username} - Company User"


class KioskUser(User):
    class Meta:
        verbose_name = "kioskuser"
        verbose_name_plural = "kioskusers"
        abstract = False

    branch = models.ForeignKey(
        "Kiosk",
        verbose_name=_("Butik"),
        help_text=_("Butik hvor denne bruger arbejder"),
        on_delete=models.PROTECT,
        related_name="user_kiosk",
    )

    def save(self, *args, **kwargs):
        self.user_type = KIOSK_USER
        return super().save(*args, **kwargs)

    def __str__(self):
        username = self.username
        return f"{username} - Kiosk User"
