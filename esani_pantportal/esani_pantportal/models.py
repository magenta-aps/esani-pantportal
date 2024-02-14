# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0

import datetime
import hashlib
import logging
import random
import string
from typing import Union

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import CharField, CheckConstraint, Q, Value
from django.db.models.functions import Cast, Concat, LPad
from django.utils.translation import gettext as _
from simple_history.models import HistoricalRecords

logger = logging.getLogger(__name__)


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
    ("D", "Dåse"),
    ("A", "Anden"),
]

DANISH_PANT_CHOICES = [
    ("J", "Ja"),
    ("N", "Nej"),
    ("U", "Ukendt"),
]


ADMIN_GROUPS = ["EsaniAdmins", "CompanyAdmins", "BranchAdmins", "KioskAdmins"]


ESANI_USER = 1
BRANCH_USER = 2
COMPANY_USER = 3
KIOSK_USER = 4

# Note: We use these strings in html templates to evaluate the type of a user.
# Be careful when changing them.
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


diameter_constraints = settings.PRODUCT_CONSTRAINTS["diameter"]
height_constraints = settings.PRODUCT_CONSTRAINTS["height"]
capacity_constraints = settings.PRODUCT_CONSTRAINTS["capacity"]


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

    account_number = models.PositiveBigIntegerField(
        verbose_name=_("konto nr."),
        help_text=_("Pant konto nr. (valgfri)"),
        null=True,
        blank=True,
        default=None,
    )

    invoice_mail = models.EmailField(
        verbose_name=_("Fakturamail"),
        help_text=_("Mail adresse som faktura skal sendes til (valgfri)"),
        null=True,
        blank=True,
        default=None,
    )

    @staticmethod
    def get_from_id(external_id: str) -> Union["Company", "CompanyBranch", "Kiosk"]:
        type_map = {
            Company.customer_id_prefix: Company,
            CompanyBranch.customer_id_prefix: CompanyBranch,
            Kiosk.customer_id_prefix: Kiosk,
        }
        try:
            prefix, pk = external_id.split("-")
            cls = type_map[prefix]
            pk = int(pk)
        except (AttributeError, KeyError, ValueError):
            logger.exception("could not process external id %r", external_id)
            raise
        else:
            return cls.objects.get(pk=pk)

    @staticmethod
    def annotate_external_customer_id(cls, length=5, fill="0"):
        prefix = f"{cls.customer_id_prefix}-"
        return Concat(
            Value(prefix),
            LPad(
                Cast("id", output_field=CharField()),
                length,
                Value(fill),
                output_field=CharField(),
            ),
            output_field=CharField(),
        )

    @property
    def external_customer_id(self):
        if not hasattr(self, "customer_id_prefix"):
            raise AttributeError(
                f"{self.__class__.__name__} has no `customer_id_prefix` attribute"
            )
        return f"{self.customer_id_prefix}-{self.id:05}"


class Company(AbstractCompany):
    customer_id_prefix = "1"

    cvr = models.PositiveIntegerField(
        verbose_name=_("CVR-nummer"),
        help_text=_("CVR Nummer"),
        unique=True,
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

    municipality = models.CharField(
        verbose_name=_("Kommune"),
        help_text=_("Butikken eller firmaets hjemkommune (valgfri)"),
        max_length=255,
        default="",
        blank=True,
    )

    invoice_company_branch = models.BooleanField(
        verbose_name=_("Send faktura/kreditnota/mv. til den enkelte butik"),
        default=True,
    )

    def __str__(self):
        name = self.name
        cvr = self.cvr
        return f"{name} - cvr: {cvr}"

    def get_branch(self):
        return None

    def get_company(self):
        return self


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

    qr_compensation = models.FloatField(
        verbose_name=_("Håndterings-godtgørelse for QR-poser"),
        help_text=_(
            "Håndterings-godtgørelse for QR-poser, angivet i øre (100=1DKK, 25=0.25DKK)"
        ),
        default=0,
    )

    def get_branch(self):
        return self

    @property
    def customer_invoice_account_id(self):
        return None


class CompanyBranch(Branch):
    customer_id_prefix = "2"

    class Meta:
        verbose_name = _("Butik")
        verbose_name_plural = _("Butikker")
        abstract = False

    company = models.ForeignKey(
        "Company",
        verbose_name=_("Virksomhed"),
        help_text=_("Virksomhed som denne butik tilhører"),
        on_delete=models.PROTECT,
        related_name="branches",
    )

    def __str__(self):
        name = self.name
        company = self.company
        return f"{name} - {company}"

    def get_company(self):
        return self.company

    @property
    def customer_invoice_account_id(self):
        if self.company.invoice_company_branch:
            return None
        else:
            return self.company.external_customer_id


class Kiosk(Branch):
    customer_id_prefix = "3"

    class Meta:
        verbose_name = _("Kiosk")
        verbose_name_plural = _("Kiosker")
        abstract = False

    cvr = models.PositiveIntegerField(
        verbose_name=_("CVR Nummer"),
        help_text=_("CVR Nummer"),
        unique=True,
    )

    def __str__(self):
        name = self.name
        cvr = self.cvr
        return f"{name} - cvr: {cvr}"

    def get_company(self):
        return None


class ReverseVendingMachine(models.Model):
    class Meta:
        verbose_name = _("Pant metode")
        verbose_name_plural = _("Pant metoder")
        abstract = False
        ordering = ["serial_number"]

    # Note: Compensation seems to be dependent on the kind of machine a branch has.
    # See
    # https://danskretursystem.dk/app/uploads/2023/05/Haandteringsgodtgoerelse_2023.pdf
    # For a possible (future?) scenario.
    compensation = models.FloatField(
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

    company_branch = models.ForeignKey(
        "CompanyBranch",
        verbose_name=_("Afdeling"),
        help_text=_("Afdeling hvor denne maskine står"),
        on_delete=models.PROTECT,
        related_name="rvms",
        null=True,
        blank=True,
        default=None,
    )

    kiosk = models.ForeignKey(
        "Kiosk",
        verbose_name=_("Butik"),
        help_text=_("Butik hvor denne maskine står"),
        on_delete=models.PROTECT,
        related_name="rvms",
        null=True,
        blank=True,
        default=None,
    )

    def get_branch(self):
        return self.company_branch or self.kiosk

    def get_company(self):
        return self.company_branch.company if self.company_branch else None


class ImportJob(models.Model):
    class Meta:
        ordering = ["-date"]

    imported_by = models.ForeignKey(
        "User",
        related_name="importjobs",
        on_delete=models.SET_NULL,  # Vi kan slette brugere og beholde deres jobs
        null=True,
        verbose_name=_("Importeret af"),
    )

    file_name = models.CharField(
        verbose_name=_("Filnavn"),
        help_text=_("Navn på det importerede fil"),
        max_length=200,
    )

    date = models.DateTimeField(
        verbose_name=_("Importdato"),
        help_text=_("Dato som filen blev importeret på"),
    )

    def __str__(self):
        return "{date} ({user}): '{file_name}'".format(
            file_name=self.file_name,
            user=self.imported_by,
            date=self.date.strftime("%Y-%m-%d %H:%M"),
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

        constraints = [
            models.CheckConstraint(
                check=models.Q(
                    shape="F",
                    height__gte=height_constraints["F"][0],
                    height__lte=height_constraints["F"][1],
                )
                | models.Q(
                    shape="D",
                    height__gte=height_constraints["D"][0],
                    height__lte=height_constraints["D"][1],
                )
                | models.Q(
                    shape="A",
                    height__gte=height_constraints["A"][0],
                    height__lte=height_constraints["A"][1],
                ),
                name="height_constraints",
            ),
            models.CheckConstraint(
                check=models.Q(
                    shape="F",
                    diameter__gte=diameter_constraints["F"][0],
                    diameter__lte=diameter_constraints["F"][1],
                )
                | models.Q(
                    shape="D",
                    diameter__gte=diameter_constraints["D"][0],
                    diameter__lte=diameter_constraints["D"][1],
                )
                | models.Q(
                    shape="A",
                    diameter__gte=diameter_constraints["A"][0],
                    diameter__lte=diameter_constraints["A"][1],
                ),
                name="diameter_constraints",
            ),
            models.CheckConstraint(
                check=models.Q(
                    shape="F",
                    capacity__gte=capacity_constraints["F"][0],
                    capacity__lte=capacity_constraints["F"][1],
                )
                | models.Q(
                    shape="D",
                    capacity__gte=capacity_constraints["D"][0],
                    capacity__lte=capacity_constraints["D"][1],
                )
                | models.Q(
                    shape="A",
                    capacity__gte=capacity_constraints["A"][0],
                    capacity__lte=capacity_constraints["A"][1],
                ),
                name="capacity_constraints",
            ),
        ]

    history = HistoricalRecords(history_change_reason_field=models.TextField(null=True))

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
        max_length=44,
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
        choices=((True, "Ja"), (False, "Nej")),
    )
    approval_date = models.DateField(
        verbose_name=_("Godkendt dato"),
        help_text=_("Dato som dette produkt blev godkendt på"),
        default=None,
        null=True,
        blank=True,
    )
    creation_date = models.DateField(
        verbose_name=_("Oprettelsesdato"),
        help_text=_("Dato som dette produkt blev oprettet på"),
        default=None,
        null=True,
        blank=True,
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
    import_job = models.ForeignKey(
        "ImportJob",
        verbose_name=_("Fil"),
        help_text=_("Fil import som blev brugt for at importere dette produkt"),
        on_delete=models.SET_NULL,  # Vi kan slette jobs og beholde deres produkter
        null=True,
        default=None,
        blank=True,
        related_name="products",
    )

    def save(self, *args, **kwargs):
        if self.approved and not self.approval_date:
            self.approval_date = datetime.date.today()
        if not self.creation_date:
            self.creation_date = datetime.date.today()
        super().save(*args, **kwargs)

    def get_branch(self):
        return self.created_by.branch if self.created_by else None

    def get_company(self):
        return self.created_by.company if self.created_by else None


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

    @staticmethod
    def qr_code_exists(qr):
        # Check if we issued this QR code.
        url_prefix = settings.QR_URL_PREFIX
        qr_url = f"{url_prefix}{qr}"
        found = any(
            (True for g in QRCodeGenerator.objects.all() if g.check_qr_code(qr_url))
        )

        return found

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


class ProductListViewPreferences(models.Model):
    class Meta:
        abstract = True

    show_material = models.BooleanField(default=True)
    show_shape = models.BooleanField(default=True)
    show_danish = models.BooleanField(default=True)
    show_height = models.BooleanField(default=False)
    show_diameter = models.BooleanField(default=False)
    show_weight = models.BooleanField(default=False)
    show_capacity = models.BooleanField(default=False)
    show_approval_date = models.BooleanField(default=False)
    show_creation_date = models.BooleanField(default=False)
    show_file_name = models.BooleanField(default=False)


class UserListViewPreferences(models.Model):
    class Meta:
        abstract = True

    show_branch = models.BooleanField(default=True)
    show_company = models.BooleanField(default=True)
    show_is_admin = models.BooleanField(default=True)
    show_approved = models.BooleanField(default=True)
    show_phone = models.BooleanField(default=False)
    show_newsletter = models.BooleanField(default=False)
    show_email = models.BooleanField(default=False)


class CompanyListViewPreferences(models.Model):
    class Meta:
        abstract = True

    show_company_address = models.BooleanField(default=True, verbose_name=_("Adresse"))
    show_company_postal_code = models.BooleanField(
        default=False, verbose_name=_("Postnr.")
    )
    show_company_municipality = models.BooleanField(
        default=True, verbose_name=_("Kommune")
    )
    show_company_city = models.BooleanField(default=True, verbose_name=_("By"))
    show_company_country = models.BooleanField(default=False, verbose_name=_("Land"))
    show_company_phone = models.BooleanField(
        default=False, verbose_name=_("Telefonnummer")
    )
    show_company_registration_number = models.BooleanField(
        default=False, verbose_name=_("Registreringsnummer")
    )
    show_company_account_number = models.BooleanField(
        default=False, verbose_name=_("Kontonummer")
    )
    show_company_invoice_mail = models.BooleanField(
        default=False, verbose_name=_("Fakturamail")
    )
    show_company_company_type = models.BooleanField(
        default=False, verbose_name=_("Virksomhedstype")
    )
    show_company_branch_type = models.BooleanField(
        default=False, verbose_name=_("Butikstype")
    )
    show_company_invoice_company_branch = models.BooleanField(
        default=False, verbose_name=_("Faktura til butik")
    )
    show_company_location_id = models.BooleanField(
        default=False, verbose_name=_("Lokation ID")
    )
    show_company_customer_id = models.BooleanField(
        default=False, verbose_name=_("Kunde ID")
    )
    show_company_qr_compensation = models.BooleanField(
        default=False, verbose_name=_("Håndterings-godtgørelse for QR-poser")
    )
    show_company_company = models.BooleanField(
        default=False, verbose_name=_("Virksomhed")
    )
    show_company_cvr = models.BooleanField(default=False, verbose_name=_("CVR"))


class User(
    AbstractUser,
    ProductListViewPreferences,
    UserListViewPreferences,
    CompanyListViewPreferences,
):
    class Meta:
        verbose_name = _("Bruger")
        verbose_name_plural = _("Brugere")
        abstract = False
        ordering = ["username"]

    user_type = models.PositiveSmallIntegerField(
        choices=USER_TYPE_CHOICES, verbose_name=_("Brugertype")
    )

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

    newsletter = models.BooleanField(
        verbose_name=_("Nyhedsbrev"),
        help_text=_("Brugeren har godkendt at modtage nyhedsbreve"),
        default=True,
        choices=((True, "Ja"), (False, "Nej")),
    )

    email = models.EmailField(
        verbose_name=_("Email"),
        help_text=_("Brugerens emailadresse"),
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

    @property
    def is_esani_admin(self):
        return self.groups.filter(name="EsaniAdmins").exists()

    @property
    def is_admin(self):
        return self.groups.filter(name__in=ADMIN_GROUPS).exists()

    def get_branch(self):
        return self.branch

    def get_company(self):
        return self.company


class EsaniUser(User):
    class Meta:
        verbose_name = _("Esani bruger")
        verbose_name_plural = _("Esani brugere")
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
        verbose_name = _("Butiks bruger")
        verbose_name_plural = _("Butiks brugere")
        abstract = False

    branch = models.ForeignKey(
        "CompanyBranch",
        verbose_name=_("Butik"),
        help_text=_("Butik hvor denne bruger arbejder"),
        on_delete=models.PROTECT,
        related_name="users",
    )

    def save(self, *args, **kwargs):
        self.user_type = BRANCH_USER
        return super().save(*args, **kwargs)

    def __str__(self):
        username = self.username
        return f"{username} - Branch User"


class CompanyUser(User):
    class Meta:
        verbose_name = _("Virksomheds bruger")
        verbose_name_plural = _("Virksomheds brugere")
        abstract = False

    company = models.ForeignKey(
        "Company",
        verbose_name=_("Virksomhed"),
        help_text=_("Virksomhed hvor denne bruger arbejder"),
        on_delete=models.PROTECT,
        related_name="users",
    )

    def save(self, *args, **kwargs):
        self.user_type = COMPANY_USER
        return super().save(*args, **kwargs)

    def __str__(self):
        username = self.username
        return f"{username} - Company User"


class KioskUser(User):
    class Meta:
        verbose_name = _("Kiosk bruger")
        verbose_name_plural = _("Kiosk brugere")
        abstract = False

    branch = models.ForeignKey(
        "Kiosk",
        verbose_name=_("Butik"),
        help_text=_("Butik hvor denne bruger arbejder"),
        on_delete=models.PROTECT,
        related_name="users",
    )

    def save(self, *args, **kwargs):
        self.user_type = KIOSK_USER
        return super().save(*args, **kwargs)

    def __str__(self):
        username = self.username
        return f"{username} - Kiosk User"


class DepositPayout(models.Model):
    """Represents a single CSV file of received bottle deposits."""

    SOURCE_TYPE_CSV = "csv"
    SOURCE_TYPE_API = "api"

    SOURCE_TYPES = [
        (SOURCE_TYPE_CSV, _("Clearing-rapporter (CSV)")),
        (SOURCE_TYPE_API, _("QR-sække (API)")),
    ]

    source_identifier = models.CharField(
        _("Kilde-ID (filnavn eller URL)"),
        max_length=255,
    )

    source_type = models.CharField(
        _("Kilde-type"),
        max_length=3,
        choices=SOURCE_TYPES,
    )

    from_date = models.DateField(
        _("Fra-dato"),
        db_index=True,
    )

    to_date = models.DateField(
        _("Til-dato"),
        db_index=True,
    )

    item_count = models.PositiveIntegerField()
    """Contains the 'final' item count at end of CSV file"""

    def __str__(self):
        return f"{self.get_source_type_display()} ({self.source_identifier})"


class DepositPayoutItem(models.Model):
    """Represents a line in a CSV file of received bottle deposits."""

    class Meta:
        ordering = ["-date"]

    deposit_payout = models.ForeignKey(
        DepositPayout,
        on_delete=models.CASCADE,
    )

    company_branch = models.ForeignKey(
        CompanyBranch,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_("Butik"),
    )
    """If the RVM serial number matches a known company branch, we link this item to the
    company branch"""

    kiosk = models.ForeignKey(
        Kiosk,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_("Kiosk"),
    )
    """If the RVM serial number matches a known kiosk, we link this item to the kiosk"""

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_("Produkt"),
        related_name="deposit_items",
    )
    """If the bar code matches a known product, we link this item to the product"""

    location_id = models.PositiveIntegerField()
    """Holds the raw value of the location ID in the CSV file line"""

    rvm_serial = models.PositiveIntegerField()
    """Serial number of RVM (= 'Reverse vending machine', aka. 'flaskeautomat')"""

    date = models.DateField()
    """Date for when items have been processed by the RVM.
    Can be before `DepositPayout.from_date` in case of offline situations.`"""

    barcode = models.CharField(
        validators=[validate_barcode_length, validate_digit],
    )
    """Holds the raw value of the barcode in the CSV file line"""

    count = models.PositiveIntegerField()
    """Each CSV file line can represent a number of bottles, if they share the same
    barcode."""

    consumer_session_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
    )

    consumer_identity = models.CharField(
        max_length=32,
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.count}x {self.barcode}"


class QRBag(models.Model):
    qr = models.CharField(
        unique=True,
        max_length=200,  # TODO: Hvor lange er vores QR-koder?
    )
    owner = models.ForeignKey(
        User,
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
    )
    company_branch = models.ForeignKey(
        CompanyBranch,
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
    )
    kiosk = models.ForeignKey(
        Kiosk,
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
    )
    active = models.BooleanField(
        default=True,
    )
    status = models.CharField(
        max_length=20,
    )
    updated = models.DateTimeField(
        auto_now=True,
    )
    history = HistoricalRecords()

    class Meta:
        constraints = [
            CheckConstraint(
                check=Q(company_branch__isnull=True) | Q(kiosk__isnull=True),
                name="has_only_company_branch_or_kiosk",
            )
        ]
        ordering = ["-updated"]


class QRStatus(models.Model):
    code = models.CharField(
        unique=True,
        max_length=20,
    )
    name_da = models.CharField(
        max_length=50,
    )
    name_kl = models.CharField(
        max_length=50,
    )


class SentEmail(models.Model):
    class Meta:
        verbose_name = _("Sendte emails")
        abstract = False

    to = models.CharField(
        verbose_name=_("Modtager"),
        help_text=_("Modtager(e) af email"),
        max_length=300,
    )
    subject = models.CharField(
        verbose_name=_("Emne"),
        help_text=_("Emailens emne"),
        max_length=200,
    )
    body = models.TextField(
        verbose_name=_("Indhold"),
        help_text=_("Emailens indhold"),
        max_length=300,
    )


class ERPProductMapping(models.Model):
    """
    Each `ERPProductMapping` object represents one unique product ID in the external
    ERP system.
    This model determines which external product ID and rates to use for different
    types of exported lines on ERP credit notas.
    """

    class Meta:
        verbose_name = _("Eksternt varenummer")
        verbose_name_plural = _("Eksterne varenumre")
        unique_together = [("category", "specifier")]

    CATEGORY_DEPOSIT = "deposit"
    CATEGORY_HANDLING = "handling"
    CATEGORY_BAG = "bag"
    CATEGORY_CHOICES = [
        (CATEGORY_DEPOSIT, _("Pant")),
        (CATEGORY_HANDLING, _("Håndteringsgodtgørelse")),
        (CATEGORY_BAG, _("Pose")),
    ]

    SPECIFIER_RVM = "rvm"
    SPECIFIER_BAG = "bag"
    SPECIFIER_CHOICES = [
        (SPECIFIER_RVM, _("Pant eller håndteringsgodtgørelse, fra automat")),
        (SPECIFIER_BAG, _("Pant eller håndteringsgodtgørelse, fra QR-pose")),
    ]

    item_number = models.PositiveSmallIntegerField(
        verbose_name=_("Varenummer i eksternt system (ERP)"),
        unique=True,
    )

    rate = models.SmallIntegerField(
        verbose_name=_("Sats ('pris' pr. enhed) i øre"),
        null=True,
        blank=True,
    )

    text = models.CharField(
        verbose_name=_("Tekst på varelinjer"),
        max_length=100,
    )

    category = models.CharField(
        verbose_name=_("Overordnet type af varelinje"),
        choices=CATEGORY_CHOICES,
        max_length=10,
    )

    specifier = models.CharField(
        verbose_name=_("Specifik type af varelinje"),
        choices=SPECIFIER_CHOICES
        + [
            (str(item["prefix"]), item["name"])
            for item in settings.QR_GENERATOR_SERIES.values()
        ],
        max_length=10,
    )

    def __str__(self):
        return f"{self.item_number} ({self.get_category_display()})"
