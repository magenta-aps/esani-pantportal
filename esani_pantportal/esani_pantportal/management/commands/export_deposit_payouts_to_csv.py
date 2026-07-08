# SPDX-FileCopyrightText: 2026 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
import csv
import datetime
import os

from django.core.management.base import BaseCommand, CommandError

from esani_pantportal.models import DepositPayoutItem

HEADER = [
    "Kæde, butik (eller RVM-serienummer)",
    "Produkt (eller stregkode)",
    "Pantværdi (i øre)",
    "Antal",
    "Dato",
    "Allerede eksporteret",
    "Stregkode/Ean",
    "By",
]

FIELDS = [
    "company_branch__company__name",
    "kiosk__name",
    "rvm_serial",
    "product__product_name",
    "product__refund_value",
    "count",
    "date",
    "file_id",
    "barcode",
    "company_branch__city__name",
    "kiosk__city__name",
]


class Command(BaseCommand):
    help = (
        "Export deposit-payout items to a CSV file on disk. Intended for very "
        "large exports (millions of rows) that cannot be produced inside a web "
        "request. The rows are streamed straight to disk, so memory usage stays "
        "flat regardless of how many rows are exported."
    )

    def add_arguments(self, parser):
        parser.add_argument("path", type=str, help="Folder in which to save the file")
        parser.add_argument(
            "--from-date",
            type=self._parse_date,
            help="Only include items on or after this date (YYYY-MM-DD)",
        )
        parser.add_argument(
            "--to-date",
            type=self._parse_date,
            help="Only include items on or before this date (YYYY-MM-DD)",
        )
        parser.add_argument(
            "--company-branch",
            type=int,
            help="Only include items for this company branch (ID)",
        )
        parser.add_argument(
            "--kiosk",
            type=int,
            help="Only include items for this kiosk (ID)",
        )
        parser.add_argument(
            "--not-exported-only",
            action="store_true",
            help="Only include items that have not already been exported",
        )
        parser.add_argument(
            "--chunk-size",
            type=int,
            default=5000,
            help="Number of rows to fetch from the database per batch",
        )
        parser.add_argument(
            "--delimiter",
            type=str,
            default=";",
            help="CSV field delimiter (default: ';')",
        )
        parser.add_argument(
            "--filename",
            type=str,
            help="Output file name (default: '<timestamp>_deposit_payouts.csv')",
        )

    @staticmethod
    def _parse_date(value):
        try:
            return datetime.datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            raise CommandError(f"Invalid date {value!r}, expected format YYYY-MM-DD")

    def get_queryset(self, options):
        qs = DepositPayoutItem.objects.all()

        if options["from_date"]:
            qs = qs.filter(date__gte=options["from_date"])
        if options["to_date"]:
            qs = qs.filter(date__lte=options["to_date"])
        if options["company_branch"]:
            qs = qs.filter(company_branch_id=options["company_branch"])
        if options["kiosk"]:
            qs = qs.filter(kiosk_id=options["kiosk"])
        if options["not_exported_only"]:
            qs = qs.filter(file_id__isnull=True)

        # Drop the model's default `-date` ordering. Sorting 19M rows is expensive
        # and unnecessary for a full data dump, and clearing it lets Postgres stream
        # rows straight from a server-side cursor.
        return qs.order_by()

    @staticmethod
    def row_to_csv(row):
        (
            branch_company_name,
            kiosk_name,
            rvm_serial,
            product_name,
            refund_value,
            count,
            date,
            file_id,
            barcode,
            branch_city,
            kiosk_city,
        ) = row

        return [
            branch_company_name or kiosk_name or rvm_serial or "",
            product_name or "",
            refund_value if refund_value is not None else "-",
            count,
            date.isoformat() if date else "",
            file_id is not None,
            barcode or "",
            branch_city or kiosk_city or "-",
        ]

    def handle(self, *args, **options):
        path = options["path"]
        if not os.path.isdir(path):
            raise CommandError(f"{path!r} is not a directory")

        filename = options["filename"] or (
            datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + "_deposit_payouts.csv"
        )
        full_path = os.path.join(path, filename)

        qs = self.get_queryset(options)
        rows = qs.values_list(*FIELDS).iterator(chunk_size=options["chunk_size"])

        count = 0
        with open(full_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=options["delimiter"])
            writer.writerow(HEADER)
            for row in rows:
                writer.writerow(self.row_to_csv(row))
                count += 1
                if count % 1_000_000 == 0:
                    self.stdout.write(f"...{count:,} rows written")  # pragma: no cover

        self.stdout.write(self.style.SUCCESS(f"Wrote {count:,} rows to {full_path}"))
        return full_path
