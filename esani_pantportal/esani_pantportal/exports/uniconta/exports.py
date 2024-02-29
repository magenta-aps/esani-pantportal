# SPDX-FileCopyrightText: 2024 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
import csv
import logging
import sys
from itertools import groupby
from uuid import uuid4

from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import (
    BooleanField,
    Case,
    CharField,
    ExpressionWrapper,
    F,
    OuterRef,
    PositiveIntegerField,
    Q,
    Subquery,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Cast, Coalesce, Concat, LPad

from esani_pantportal.models import (
    Company,
    CompanyBranch,
    DepositPayout,
    ERPProductMapping,
    Kiosk,
    QRBag,
    ReverseVendingMachine,
)

logger = logging.getLogger(__name__)


class CreditNoteExport:
    def __init__(
        self,
        from_date,
        to_date,
        queryset,
        dry=True,  # False: updates underlying objects
    ):
        self._from_date = from_date
        self._to_date = to_date
        self._queryset = queryset
        self._dry = dry

        self._file_id = uuid4()

        self._field_names = [
            "customer_id",
            "customer_invoice_account_id",
            "customer_name",
            "customer_cvr",
            "customer_location_id",
            "product_id",
            "product_name",
            "quantity",
            "unit_price",
            "total",
            "from_date",
            "to_date",
        ]

        self._qs = self._get_base_queryset(queryset)
        self._bag_type_prefixes = ERPProductMapping.objects.filter(
            category=ERPProductMapping.CATEGORY_BAG
        ).values_list("specifier", flat=True)

    def __iter__(self):
        for row in self._qs:
            yield from self._get_lines_for_row(row)
        if not self._dry:
            # Update status of all related QR bags to `esani_udbetalt`
            has_qr_bag = self._queryset.filter(qr_bag__isnull=False)
            qr_bags = QRBag.objects.filter(
                id__in=has_qr_bag.values_list("qr_bag__id", flat=True)
            )
            qr_bags.update(status="esani_udbetalt")

            # Mark all deposit payout items as exported
            self._queryset.filter(file_id__isnull=True).update(file_id=self._file_id)

    def as_csv(self, stream=sys.stdout, delimiter=";"):
        if self._dry:
            field_names = self._field_names + ["already_exported"]
        else:
            field_names = self._field_names + ["file_id"]
        writer = csv.DictWriter(stream, field_names, delimiter=delimiter)
        writer.writeheader()
        writer.writerows(self)

    def get_filename(self):
        from_date = self._from_date.strftime("%Y-%m-%d")
        to_date = self._to_date.strftime("%Y-%m-%d")
        return f"kreditnota_{from_date}_{to_date}_{self._file_id}.csv"

    def _get_base_queryset(self, queryset):
        annotations = dict(
            type=F("deposit_payout__source_type"),
            source=Case(
                When(company_branch__isnull=False, then=Value("company_branch")),
                When(kiosk__isnull=False, then=Value("kiosk")),
                default=Value(""),
            ),
            source_id=Coalesce("company_branch__id", "kiosk__id"),
            product_refund_value=F("product__refund_value"),
            rvm_refund_value=Subquery(
                ReverseVendingMachine.objects.filter(
                    serial_number=Cast(OuterRef("rvm_serial"), output_field=CharField())
                ).values("compensation")
            ),
        )

        group_by = [
            "source",
            "source_id",
            "type",
            "product_refund_value",
            "rvm_refund_value",
        ]

        if self._dry:
            annotations.update(
                already_exported=ExpressionWrapper(
                    Q(file_id__isnull=False),
                    output_field=BooleanField(),
                ),
            )
            group_by.append("already_exported")
        else:
            queryset = queryset.filter(file_id__isnull=True)

        return (
            queryset.select_related("product", "company_branch__company", "kiosk")
            .annotate(**annotations)
            .exclude(product__isnull=True)
            .exclude(source_id__isnull=True)
            .values(*group_by)
            .annotate(
                count=Sum("count"),
                bag_qrs=ArrayAgg("consumer_identity", distinct=True),
            )
            .order_by(
                "source",
                "source_id",
                "-type",
                "product_refund_value",
                "rvm_refund_value",
            )
        )

    def _get_rate(self, category: str, specifier: str) -> ERPProductMapping:
        return ERPProductMapping.objects.get(category=category, specifier=specifier)

    def _get_lines_for_row(self, row):
        customer = self._get_customer(row)

        def line(category, specifier, quantity, unit_price=None):
            rate = self._get_rate(category, specifier)
            unit_price = int(unit_price if unit_price is not None else rate.rate)

            result = {
                "customer_id": customer.external_customer_id,
                "customer_invoice_account_id": customer.customer_invoice_account_id,
                "customer_name": customer.name,
                "customer_cvr": (
                    customer.cvr
                    if isinstance(customer, Kiosk)
                    else customer.company.cvr
                ),
                "customer_location_id": customer.location_id,
                "product_id": rate.item_number,
                "product_name": rate.text,
                "quantity": quantity,
                "unit_price": unit_price,
                "total": quantity * unit_price,
                "from_date": self._from_date.strftime("%Y-%m-%d"),
                "to_date": self._to_date.strftime("%Y-%m-%d"),
            }

            if self._dry:
                result["already_exported"] = "y" if row["already_exported"] else "n"
            else:
                result["file_id"] = self._file_id

            return result

        # Produce "Pant (pose)", "Håndteringsgodtgørelse (pose)" and
        # "Lille pose"/"Stor pose" lines.
        if row["type"] == DepositPayout.SOURCE_TYPE_API:
            yield line(
                ERPProductMapping.CATEGORY_DEPOSIT,
                ERPProductMapping.SPECIFIER_BAG,
                row["count"],
                unit_price=row["product_refund_value"],
            )
            yield line(
                ERPProductMapping.CATEGORY_HANDLING,
                ERPProductMapping.SPECIFIER_BAG,
                row["count"],
                unit_price=customer.qr_compensation,
            )
            for prefix, count in self._get_bag_groups(row):
                yield line(ERPProductMapping.CATEGORY_BAG, prefix, count)

        # Produce "Pant (automat)" and "Håndteringsgodtgørelse (automat)" lines
        elif row["type"] == DepositPayout.SOURCE_TYPE_CSV:
            yield line(
                ERPProductMapping.CATEGORY_DEPOSIT,
                ERPProductMapping.SPECIFIER_RVM,
                row["count"],
                unit_price=row["product_refund_value"],
            )
            yield line(
                ERPProductMapping.CATEGORY_HANDLING,
                ERPProductMapping.SPECIFIER_RVM,
                row["count"],
                unit_price=row["rvm_refund_value"],
            )

    def _get_bag_groups(self, row) -> list[tuple[str, int]]:
        def _get_bag_type(qr):
            for bag_type_prefix in self._bag_type_prefixes:
                if qr.startswith(bag_type_prefix):
                    return bag_type_prefix
            logger.warning("Cannot find bag type prefix for unknown bag QR %r", qr)

        if row["bag_qrs"]:
            qrs = [qr for qr in row["bag_qrs"] if qr is not None]
            return [
                (k, len(set(v)))
                for k, v in groupby(sorted(qrs), key=_get_bag_type)
                if k is not None
            ]
        else:
            return []

    def _get_customer(self, row):
        if row["source"] == "company_branch":
            companies = CompanyBranch.objects.filter(id=row["source_id"])
            return companies.first()
        elif row["source"] == "kiosk":
            kiosks = Kiosk.objects.filter(id=row["source_id"])
            return kiosks.first()


class DebtorExport:
    def __init__(self):
        self._common = [
            "name",
            "phone",  # includes prefix (e.g. +299)
            "address",
            "postal_code",
            "city",
            "registration_number",
            "account_number",
            "invoice_mail",
        ]
        self._qs = self._get_queryset()

    def _get_queryset(self):
        def external_customer_id(prefix, length=5, fill="0"):
            prefix = f"{prefix}-"
            return Concat(
                Value(prefix),
                LPad(
                    Cast("id", output_field=CharField()),
                    length,
                    Value(fill),
                ),
                output_field=CharField(),
            )

        qs1 = Company.objects.values(*self._common).annotate(
            _cvr=F("cvr"),
            _location_id=Value(None, output_field=PositiveIntegerField()),
            _id=external_customer_id("1"),
        )
        qs2 = CompanyBranch.objects.values(*self._common).annotate(
            _cvr=Subquery(
                Company.objects.filter(id=OuterRef("company__id")).values("cvr")
            ),
            _location_id=F("location_id"),
            _id=external_customer_id("2"),
        )
        qs3 = Kiosk.objects.values(*self._common).annotate(
            _cvr=F("cvr"),
            _location_id=F("location_id"),
            _id=external_customer_id("3"),
        )

        return qs1.union(qs2).union(qs3).order_by(*["_id"] + self._common)

    def as_csv(self, stream=sys.stdout, delimiter=";"):
        def transform(row: dict) -> dict:
            return {
                "id": row["_id"],
                "name": row["name"],
                "phone": row["phone"],
                "address": row["address"],
                "postal_code": row["postal_code"],
                "city": row["city"],
                "registration_number": row["registration_number"],
                "account_number": row["account_number"],
                "invoice_mail": row["invoice_mail"],
                "cvr": row["_cvr"],
                "location_id": row["_location_id"],
            }

        transformed = [transform(row) for row in self._get_queryset()]
        writer = csv.DictWriter(stream, transformed[0].keys(), delimiter=delimiter)
        writer.writeheader()
        writer.writerows(transformed)
